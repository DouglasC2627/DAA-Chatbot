"""
Tests for RAG Pipeline implementation.

This test suite verifies:
- Retrieval logic from vector store
- Prompt template construction
- Context injection
- Source tracking and attribution
- Relevance scoring
- Response generation (non-streaming and streaming)
- End-to-end RAG workflow
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.rag_pipeline import (
    RAGPipeline,
    RAGError,
    RetrievedDocument,
    RAGResponse
)


class TestRetrievedDocument:
    """Test RetrievedDocument dataclass."""

    def test_score_calculation(self):
        """Test that score is calculated correctly from distance."""
        doc = RetrievedDocument(
            id="test_id",
            content="test content",
            metadata={'document_id': 1},
            distance=0.0
        )
        # Distance 0 should give score close to 1
        assert doc.score > 0.99

        doc2 = RetrievedDocument(
            id="test_id_2",
            content="test content 2",
            metadata={},
            distance=2.0
        )
        # Higher distance should give lower score
        assert doc2.score < doc.score
        assert doc2.score < 0.2

    def test_metadata_extraction(self):
        """Test metadata property extraction."""
        doc = RetrievedDocument(
            id="test_id",
            content="test content",
            metadata={
                'document_id': 42,
                'chunk_index': 5,
                'page': 3
            },
            distance=0.5
        )

        assert doc.document_id == 42
        assert doc.chunk_index == 5
        assert doc.metadata['page'] == 3

    def test_metadata_extraction_missing_fields(self):
        """Test metadata extraction when fields are missing."""
        doc = RetrievedDocument(
            id="test_id",
            content="test content",
            metadata={},
            distance=0.5
        )

        assert doc.document_id is None
        assert doc.chunk_index is None


class TestRAGResponse:
    """Test RAGResponse dataclass."""

    def test_to_dict_conversion(self):
        """Test conversion to dictionary format."""
        sources = [
            RetrievedDocument(
                id="doc1",
                content="content 1",
                metadata={'document_id': 1},
                distance=0.3
            ),
            RetrievedDocument(
                id="doc2",
                content="content 2",
                metadata={'document_id': 2, 'chunk_index': 1},
                distance=0.5
            )
        ]

        response = RAGResponse(
            answer="This is the answer",
            sources=sources,
            model="llama3.2",
            prompt_tokens=100,
            completion_tokens=50
        )

        result = response.to_dict()

        assert result['answer'] == "This is the answer"
        assert result['model'] == "llama3.2"
        assert result['prompt_tokens'] == 100
        assert result['completion_tokens'] == 50
        assert len(result['sources']) == 2
        assert result['sources'][0]['id'] == "doc1"
        assert result['sources'][0]['content'] == "content 1"
        assert 'score' in result['sources'][0]
        assert 'distance' in result['sources'][0]


class TestRAGPipeline:
    """Test RAGPipeline main functionality."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        mock = Mock()
        mock.generate_embedding_async = AsyncMock(return_value=[0.1, 0.2, 0.3])
        return mock

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        mock = Mock()
        mock.search = Mock(return_value={
            'ids': ['doc1', 'doc2', 'doc3'],
            'documents': [
                'This is document 1 content',
                'This is document 2 content',
                'This is document 3 content'
            ],
            'metadatas': [
                {'document_id': 1, 'chunk_index': 0},
                {'document_id': 2, 'chunk_index': 1},
                {'document_id': 3, 'chunk_index': 0}
            ],
            'distances': [0.2, 0.4, 0.6]
        })
        return mock

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        mock = Mock()
        mock.default_model = "llama3.2"
        mock.chat = AsyncMock(return_value="This is the generated answer")

        async def mock_stream():
            for token in ["This ", "is ", "streaming ", "answer"]:
                yield token

        mock.chat_stream = Mock(return_value=mock_stream())
        return mock

    @pytest.fixture
    def rag_pipeline(self, mock_embedding_service, mock_vector_store, mock_llm_client):
        """Create RAG pipeline with mocked dependencies."""
        return RAGPipeline(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            llm_client=mock_llm_client,
            top_k=5,
            min_relevance_score=0.3
        )

    @pytest.mark.asyncio
    async def test_retrieve_context(self, rag_pipeline, mock_embedding_service, mock_vector_store):
        """Test context retrieval from vector store."""
        documents = await rag_pipeline.retrieve_context(
            query="What is the meaning of life?",
            project_id=1
        )

        # Verify embedding service was called
        mock_embedding_service.generate_embedding_async.assert_called_once_with(
            "What is the meaning of life?"
        )

        # Verify vector store was called
        mock_vector_store.search.assert_called_once()
        call_kwargs = mock_vector_store.search.call_args[1]
        assert call_kwargs['project_id'] == 1
        assert call_kwargs['n_results'] == 5

        # Verify documents were returned
        assert len(documents) == 3
        assert all(isinstance(doc, RetrievedDocument) for doc in documents)
        assert documents[0].id == 'doc1'
        assert documents[0].content == 'This is document 1 content'

    @pytest.mark.asyncio
    async def test_retrieve_context_with_relevance_filter(self, rag_pipeline, mock_vector_store):
        """Test that low-relevance documents are filtered out."""
        # Set up vector store to return one low-relevance document
        mock_vector_store.search = Mock(return_value={
            'ids': ['doc1', 'doc2'],
            'documents': ['Good content', 'Bad content'],
            'metadatas': [{'document_id': 1}, {'document_id': 2}],
            'distances': [0.2, 5.0]  # Second document is very far (low relevance)
        })

        rag_pipeline.min_relevance_score = 0.3

        documents = await rag_pipeline.retrieve_context(
            query="test query",
            project_id=1
        )

        # Only the first document should pass the filter
        assert len(documents) == 1
        assert documents[0].id == 'doc1'

    def test_build_context_prompt(self, rag_pipeline):
        """Test context prompt construction."""
        documents = [
            RetrievedDocument(
                id="doc1",
                content="Python is a programming language",
                metadata={'document_id': 1, 'chunk_index': 0},
                distance=0.2
            ),
            RetrievedDocument(
                id="doc2",
                content="It was created by Guido van Rossum",
                metadata={'document_id': 1, 'chunk_index': 1},
                distance=0.3
            )
        ]

        prompt = rag_pipeline.build_context_prompt(
            query="What is Python?",
            documents=documents
        )

        # Verify prompt contains context documents
        assert "Python is a programming language" in prompt
        assert "It was created by Guido van Rossum" in prompt

        # Verify prompt contains source attribution
        assert "[Source 1" in prompt
        assert "[Source 2" in prompt
        assert "Document ID: 1" in prompt

        # Verify prompt contains the question
        assert "What is Python?" in prompt

    def test_build_context_prompt_empty_documents(self, rag_pipeline):
        """Test context prompt with no documents."""
        prompt = rag_pipeline.build_context_prompt(
            query="What is Python?",
            documents=[]
        )

        # Should return just the query
        assert prompt == "What is Python?"

    def test_build_chat_messages(self, rag_pipeline):
        """Test chat messages array construction."""
        documents = [
            RetrievedDocument(
                id="doc1",
                content="Test content",
                metadata={},
                distance=0.2
            )
        ]

        chat_history = [
            {'role': 'user', 'content': 'Previous question'},
            {'role': 'assistant', 'content': 'Previous answer'}
        ]

        messages = rag_pipeline.build_chat_messages(
            query="Current question",
            documents=documents,
            chat_history=chat_history,
            max_history=5
        )

        # Verify structure
        assert len(messages) >= 4  # system + history(2) + current
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'Previous question'
        assert messages[2]['role'] == 'assistant'
        assert messages[-1]['role'] == 'user'
        assert 'Current question' in messages[-1]['content']

    def test_build_chat_messages_limits_history(self, rag_pipeline):
        """Test that chat history is limited to max_history."""
        documents = []

        # Create long history
        chat_history = [
            {'role': 'user', 'content': f'Question {i}'}
            for i in range(10)
        ]

        messages = rag_pipeline.build_chat_messages(
            query="Current question",
            documents=documents,
            chat_history=chat_history,
            max_history=3
        )

        # Should have: system + 3 history + current = 5 messages
        assert len(messages) == 5

    @pytest.mark.asyncio
    async def test_generate_answer(self, rag_pipeline, mock_llm_client):
        """Test non-streaming answer generation."""
        response = await rag_pipeline.generate_answer(
            query="What is AI?",
            project_id=1,
            chat_history=[],
            model="llama3.2",
            temperature=0.7
        )

        # Verify response structure
        assert isinstance(response, RAGResponse)
        assert response.answer == "This is the generated answer"
        assert response.model == "llama3.2"
        assert len(response.sources) == 3

        # Verify LLM was called
        mock_llm_client.chat.assert_called_once()
        call_kwargs = mock_llm_client.chat.call_args[1]
        assert call_kwargs['model'] == "llama3.2"
        assert call_kwargs['temperature'] == 0.7

    @pytest.mark.asyncio
    async def test_generate_answer_no_documents(self, rag_pipeline, mock_vector_store):
        """Test answer generation when no relevant documents are found."""
        # Mock vector store to return no results
        mock_vector_store.search = Mock(return_value={
            'ids': [],
            'documents': [],
            'metadatas': [],
            'distances': []
        })

        response = await rag_pipeline.generate_answer(
            query="Obscure question",
            project_id=1
        )

        # Should still generate a response
        assert isinstance(response, RAGResponse)
        assert len(response.sources) == 0

    @pytest.mark.asyncio
    async def test_generate_answer_stream(self, rag_pipeline):
        """Test streaming answer generation."""
        events = []

        async for event in rag_pipeline.generate_answer_stream(
            query="What is AI?",
            project_id=1,
            model="llama3.2"
        ):
            events.append(event)

        # Verify event sequence
        assert len(events) > 0

        # First event should be sources
        assert events[0]['type'] == 'sources'
        assert 'data' in events[0]
        assert len(events[0]['data']) == 3

        # Middle events should be tokens
        token_events = [e for e in events if e['type'] == 'token']
        assert len(token_events) > 0

        # Last event should be done
        assert events[-1]['type'] == 'done'
        assert events[-1]['data']['model'] == 'llama3.2'
        assert events[-1]['data']['sources_count'] == 3

    @pytest.mark.asyncio
    async def test_generate_answer_error_handling(self, rag_pipeline, mock_embedding_service):
        """Test error handling in answer generation."""
        # Make embedding service fail
        mock_embedding_service.generate_embedding_async = AsyncMock(
            side_effect=Exception("Embedding failed")
        )

        with pytest.raises(RAGError) as exc_info:
            await rag_pipeline.generate_answer(
                query="Test query",
                project_id=1
            )

        assert "RAG generation failed" in str(exc_info.value)

    def test_update_config(self, rag_pipeline):
        """Test configuration updates."""
        # Initial values
        assert rag_pipeline.top_k == 5
        assert rag_pipeline.min_relevance_score == 0.3

        # Update config
        rag_pipeline.update_config(
            top_k=10,
            min_relevance_score=0.5,
            system_prompt="New system prompt"
        )

        # Verify updates
        assert rag_pipeline.top_k == 10
        assert rag_pipeline.min_relevance_score == 0.5
        assert rag_pipeline.system_prompt == "New system prompt"

    def test_update_config_partial(self, rag_pipeline):
        """Test partial configuration updates."""
        original_prompt = rag_pipeline.system_prompt

        # Update only top_k
        rag_pipeline.update_config(top_k=7)

        assert rag_pipeline.top_k == 7
        assert rag_pipeline.min_relevance_score == 0.3  # Unchanged
        assert rag_pipeline.system_prompt == original_prompt  # Unchanged


class TestRAGPipelineIntegration:
    """Integration tests that test multiple components together."""

    @pytest.mark.asyncio
    async def test_full_rag_workflow(self):
        """Test complete RAG workflow with all components."""
        # Create mocks
        mock_embedding = Mock()
        mock_embedding.generate_embedding_async = AsyncMock(
            return_value=[0.1] * 384
        )

        mock_vector = Mock()
        mock_vector.search = Mock(return_value={
            'ids': ['chunk1'],
            'documents': ['FastAPI is a modern web framework'],
            'metadatas': [{'document_id': 1, 'chunk_index': 0}],
            'distances': [0.15]
        })

        mock_llm = Mock()
        mock_llm.default_model = "llama3.2"
        mock_llm.chat = AsyncMock(
            return_value="FastAPI is a modern, fast web framework for building APIs with Python."
        )

        # Create pipeline
        pipeline = RAGPipeline(
            embedding_service=mock_embedding,
            vector_store=mock_vector,
            llm_client=mock_llm
        )

        # Execute full workflow
        response = await pipeline.generate_answer(
            query="What is FastAPI?",
            project_id=1,
            chat_history=[],
            temperature=0.7
        )

        # Verify complete workflow
        assert response.answer == "FastAPI is a modern, fast web framework for building APIs with Python."
        assert len(response.sources) == 1
        assert response.sources[0].content == "FastAPI is a modern web framework"
        assert response.sources[0].metadata['document_id'] == 1
        assert response.model == "llama3.2"

        # Verify all components were called
        mock_embedding.generate_embedding_async.assert_called()
        mock_vector.search.assert_called()
        mock_llm.chat.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
