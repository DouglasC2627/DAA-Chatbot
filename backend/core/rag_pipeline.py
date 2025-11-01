"""
RAG (Retrieval-Augmented Generation) Pipeline.

This module orchestrates the complete RAG flow:
1. Query embedding generation
2. Relevant document retrieval from vector store
3. Context preparation and prompt construction
4. LLM response generation with source attribution
5. Response streaming support
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass

from core.embeddings import EmbeddingService
from core.vectorstore import VectorStore
from core.llm import OllamaClient
from core.config import settings

logger = logging.getLogger(__name__)


class RAGError(Exception):
    """Raised when RAG pipeline encounters an error."""
    pass


@dataclass
class RetrievedDocument:
    """
    Represents a document chunk retrieved from the vector store.

    Attributes:
        id: Unique identifier for the chunk
        content: The text content of the chunk
        metadata: Associated metadata (document_id, page, etc.)
        distance: Similarity distance (lower is more similar)
        score: Relevance score (higher is more relevant, inverse of distance)
    """
    id: str
    content: str
    metadata: Dict[str, Any]
    distance: float

    @property
    def score(self) -> float:
        """Convert distance to relevance score (0 to 1, higher is better)."""
        # ChromaDB uses cosine distance (1 - cosine_similarity)
        # Convert to similarity score: score = 1 - distance
        # Result ranges from 0 (orthogonal) to 1 (identical)
        return max(0.0, min(1.0, 1.0 - self.distance))

    @property
    def document_id(self) -> Optional[int]:
        """Extract document ID from metadata."""
        return self.metadata.get('document_id')

    @property
    def chunk_index(self) -> Optional[int]:
        """Extract chunk index from metadata."""
        return self.metadata.get('chunk_index')


@dataclass
class RAGResponse:
    """
    Response from RAG pipeline.

    Attributes:
        answer: The generated answer text
        sources: List of retrieved documents used as context
        model: Name of the LLM model used
        prompt_tokens: Approximate input tokens used
        completion_tokens: Approximate output tokens generated
    """
    answer: str
    sources: List[RetrievedDocument]
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'answer': self.answer,
            'sources': [
                {
                    'id': src.id,
                    'content': src.content,
                    'metadata': src.metadata,
                    'score': src.score,
                    'distance': src.distance
                }
                for src in self.sources
            ],
            'model': self.model,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens
        }


class RAGPipeline:
    """
    Main RAG pipeline orchestrator.

    Handles the complete RAG workflow from query to response with source attribution.
    """

    # Default system prompt for the RAG assistant
    DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on the provided context.

Your responsibilities:
- Answer questions accurately using ONLY the information from the provided context
- If the context doesn't contain enough information to answer, say so honestly
- Cite specific parts of the context when making claims
- Be concise but thorough
- If asked about something not in the context, clearly state that

Remember: Base your answers ONLY on the provided context documents."""

    # Prompt template for injecting context
    CONTEXT_PROMPT_TEMPLATE = """Context documents:

{context}

---

Question: {question}

Please answer the question based on the context provided above. If you reference specific information, indicate which part of the context it comes from."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
        llm_client: Optional[OllamaClient] = None,
        top_k: int = 5,
        min_relevance_score: float = 0.3,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize RAG pipeline.

        Args:
            embedding_service: Service for generating embeddings
            vector_store: Vector store for document retrieval
            llm_client: LLM client for generation
            top_k: Number of documents to retrieve (default: 5)
            min_relevance_score: Minimum relevance score threshold (default: 0.3)
            system_prompt: Custom system prompt (defaults to DEFAULT_SYSTEM_PROMPT)
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.llm_client = llm_client or OllamaClient()

        self.top_k = top_k
        self.min_relevance_score = min_relevance_score
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT

        logger.info(
            f"RAG Pipeline initialized with top_k={top_k}, "
            f"min_relevance_score={min_relevance_score}"
        )

    async def retrieve_context(
        self,
        query: str,
        project_id: int,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: User query/question
            project_id: Project to search within
            top_k: Number of documents to retrieve (overrides default)
            metadata_filter: Optional metadata filter for ChromaDB

        Returns:
            List of retrieved documents with relevance scores

        Raises:
            RAGError: If retrieval fails
        """
        try:
            k = top_k or self.top_k

            logger.info(f"Retrieving context for query in project {project_id}, top_k={k}")

            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding_async(query)

            # Search vector store
            results = self.vector_store.search(
                project_id=project_id,
                query_embedding=query_embedding,
                n_results=k,
                where=metadata_filter
            )

            # Parse results into RetrievedDocument objects
            documents = []
            for i, (doc_id, content, metadata, distance) in enumerate(zip(
                results['ids'],
                results['documents'],
                results['metadatas'],
                results['distances']
            )):
                retrieved_doc = RetrievedDocument(
                    id=doc_id,
                    content=content,
                    metadata=metadata or {},
                    distance=distance
                )

                # Filter by minimum relevance score
                if retrieved_doc.score >= self.min_relevance_score:
                    documents.append(retrieved_doc)
                    logger.debug(
                        f"Retrieved doc {i+1}: score={retrieved_doc.score:.3f}, "
                        f"distance={distance:.3f}"
                    )
                else:
                    logger.debug(
                        f"Filtered out doc {i+1}: score={retrieved_doc.score:.3f} "
                        f"< threshold {self.min_relevance_score}"
                    )

            logger.info(
                f"Retrieved {len(documents)} documents "
                f"(filtered from {len(results['ids'])} by relevance threshold)"
            )

            return documents

        except Exception as e:
            logger.error(f"Context retrieval failed: {str(e)}")
            raise RAGError(f"Context retrieval failed: {str(e)}") from e

    def build_context_prompt(
        self,
        query: str,
        documents: List[RetrievedDocument]
    ) -> str:
        """
        Build the prompt with context injection.

        Args:
            query: User query
            documents: Retrieved context documents

        Returns:
            Formatted prompt with context
        """
        if not documents:
            logger.warning("No context documents provided, using query only")
            return query

        # Format context documents
        context_parts = []
        for i, doc in enumerate(documents, 1):
            # Add source attribution info in context
            source_info = f"[Source {i}"
            if doc.document_id:
                source_info += f", Document ID: {doc.document_id}"
            if doc.chunk_index is not None:
                source_info += f", Chunk: {doc.chunk_index}"
            source_info += f", Relevance: {doc.score:.2f}]"

            context_parts.append(f"{source_info}\n{doc.content}\n")

        context_text = "\n---\n\n".join(context_parts)

        # Inject into template
        prompt = self.CONTEXT_PROMPT_TEMPLATE.format(
            context=context_text,
            question=query
        )

        logger.debug(f"Built prompt with {len(documents)} context documents")

        return prompt

    def build_chat_messages(
        self,
        query: str,
        documents: List[RetrievedDocument],
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_history: int = 5
    ) -> List[Dict[str, str]]:
        """
        Build chat messages array with system prompt, history, and context.

        Args:
            query: Current user query
            documents: Retrieved context documents
            chat_history: Previous messages (list of {role, content} dicts)
            max_history: Maximum number of history messages to include

        Returns:
            List of message dictionaries for chat API
        """
        messages = []

        # Add system prompt
        messages.append({
            'role': 'system',
            'content': self.system_prompt
        })

        # Add recent chat history (if any)
        if chat_history:
            # Limit history to max_history most recent messages
            recent_history = chat_history[-max_history:] if len(chat_history) > max_history else chat_history
            messages.extend(recent_history)
            logger.debug(f"Added {len(recent_history)} messages from chat history")

        # Add current query with context
        user_message = self.build_context_prompt(query, documents)
        messages.append({
            'role': 'user',
            'content': user_message
        })

        return messages

    async def generate_answer(
        self,
        query: str,
        project_id: int,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        Generate an answer using the RAG pipeline (non-streaming).

        Args:
            query: User question
            project_id: Project context for retrieval
            chat_history: Optional conversation history
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            metadata_filter: Optional filter for document retrieval

        Returns:
            RAG response with answer and sources

        Raises:
            RAGError: If generation fails
        """
        try:
            logger.info(f"Generating RAG answer for query in project {project_id}")

            # Step 1: Retrieve context
            documents = await self.retrieve_context(
                query=query,
                project_id=project_id,
                metadata_filter=metadata_filter
            )

            if not documents:
                logger.warning("No relevant documents found for query")
                # Still try to answer without context, but inform the user
                documents = []

            # Step 2: Build chat messages
            messages = self.build_chat_messages(
                query=query,
                documents=documents,
                chat_history=chat_history
            )

            # Step 3: Generate response
            model_name = model or self.llm_client.default_model
            answer = await self.llm_client.chat(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Step 4: Create response object
            response = RAGResponse(
                answer=answer,
                sources=documents,
                model=model_name
            )

            logger.info(
                f"Generated answer of {len(answer)} characters "
                f"with {len(documents)} sources"
            )

            return response

        except Exception as e:
            logger.error(f"RAG generation failed: {str(e)}")
            raise RAGError(f"RAG generation failed: {str(e)}") from e

    async def generate_answer_stream(
        self,
        query: str,
        project_id: int,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate an answer using the RAG pipeline with streaming.

        Yields dictionaries with:
        - {'type': 'sources', 'data': [list of retrieved documents]}
        - {'type': 'token', 'data': 'text chunk'}
        - {'type': 'done', 'data': {'model': str, 'sources_count': int}}

        Args:
            query: User question
            project_id: Project context for retrieval
            chat_history: Optional conversation history
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            metadata_filter: Optional filter for document retrieval

        Yields:
            Stream events with answer chunks and metadata

        Raises:
            RAGError: If generation fails
        """
        try:
            logger.info(f"Starting streaming RAG answer for query in project {project_id}")

            # Step 1: Retrieve context
            documents = await self.retrieve_context(
                query=query,
                project_id=project_id,
                metadata_filter=metadata_filter
            )

            # Yield sources first
            yield {
                'type': 'sources',
                'data': [
                    {
                        'id': doc.id,
                        'content': doc.content,
                        'metadata': doc.metadata,
                        'score': doc.score
                    }
                    for doc in documents
                ]
            }

            # Step 2: Build chat messages
            messages = self.build_chat_messages(
                query=query,
                documents=documents,
                chat_history=chat_history
            )

            # Step 3: Stream response
            model_name = model or self.llm_client.default_model

            async for chunk in self.llm_client.chat_stream(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield {
                    'type': 'token',
                    'data': chunk
                }

            # Step 4: Yield completion metadata
            yield {
                'type': 'done',
                'data': {
                    'model': model_name,
                    'sources_count': len(documents)
                }
            }

            logger.info("Streaming RAG answer completed")

        except Exception as e:
            logger.error(f"Streaming RAG generation failed: {str(e)}")
            # Yield error event
            yield {
                'type': 'error',
                'data': str(e)
            }
            raise RAGError(f"Streaming RAG generation failed: {str(e)}") from e

    def update_config(
        self,
        top_k: Optional[int] = None,
        min_relevance_score: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> None:
        """
        Update RAG pipeline configuration.

        Args:
            top_k: New top_k value
            min_relevance_score: New relevance threshold
            system_prompt: New system prompt
        """
        if top_k is not None:
            self.top_k = top_k
            logger.info(f"Updated top_k to {top_k}")

        if min_relevance_score is not None:
            self.min_relevance_score = min_relevance_score
            logger.info(f"Updated min_relevance_score to {min_relevance_score}")

        if system_prompt is not None:
            self.system_prompt = system_prompt
            logger.info("Updated system prompt")


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()


# Convenience functions
async def generate_rag_answer(
    query: str,
    project_id: int,
    chat_history: Optional[List[Dict[str, str]]] = None,
    **kwargs
) -> RAGResponse:
    """
    Generate RAG answer using global pipeline.

    Args:
        query: User question
        project_id: Project context
        chat_history: Optional conversation history
        **kwargs: Additional parameters for generation

    Returns:
        RAG response with answer and sources
    """
    return await rag_pipeline.generate_answer(
        query=query,
        project_id=project_id,
        chat_history=chat_history,
        **kwargs
    )


async def generate_rag_answer_stream(
    query: str,
    project_id: int,
    chat_history: Optional[List[Dict[str, str]]] = None,
    **kwargs
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate streaming RAG answer using global pipeline.

    Args:
        query: User question
        project_id: Project context
        chat_history: Optional conversation history
        **kwargs: Additional parameters for generation

    Yields:
        Stream events with answer chunks and metadata
    """
    async for event in rag_pipeline.generate_answer_stream(
        query=query,
        project_id=project_id,
        chat_history=chat_history,
        **kwargs
    ):
        yield event
