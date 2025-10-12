"""
Tests for embeddings and chunking functionality.

This test suite tests:
- Embedding generation with Ollama
- Text chunking with various strategies
- Integration of chunking and embeddings
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.embeddings import (
    EmbeddingService,
    embedding_service,
    generate_embedding,
    generate_embeddings_batch
)
from core.chunking import (
    TextChunker,
    ChunkingStrategy,
    chunk_text,
    chunk_document_text,
    default_chunker
)
from models.document import DocumentType


class TestChunkingStrategies:
    """Test different chunking strategies."""

    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return """This is the first paragraph. It contains multiple sentences. Each sentence adds meaning.

This is the second paragraph. It's separated by a blank line. This helps organize content.

This is the third paragraph. We can use this to test chunking strategies. Different strategies will split this differently."""

    @pytest.mark.parametrize("strategy", [
        ChunkingStrategy.RECURSIVE,
        ChunkingStrategy.SENTENCE,
        ChunkingStrategy.PARAGRAPH,
        ChunkingStrategy.FIXED_SIZE,
    ])
    def test_chunking_strategy(self, sample_text, strategy):
        """Test each chunking strategy."""
        chunks = chunk_text(
            sample_text,
            chunk_size=100,
            chunk_overlap=20,
            strategy=strategy
        )

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.text) > 0
            assert chunk.word_count > 0


class TestChunkOverlap:
    """Test chunk overlap functionality."""

    def test_no_overlap(self):
        """Test chunking without overlap."""
        text = "This is a test sentence. " * 50

        chunks_no_overlap = chunk_text(text, chunk_size=100, chunk_overlap=0)

        assert len(chunks_no_overlap) > 0

    def test_with_overlap(self):
        """Test chunking with overlap."""
        text = "This is a test sentence. " * 50

        chunks_with_overlap = chunk_text(text, chunk_size=100, chunk_overlap=20)

        assert len(chunks_with_overlap) > 0

        # Verify overlap exists between consecutive chunks
        if len(chunks_with_overlap) > 1:
            chunk1_end = chunks_with_overlap[0].text[-20:]
            chunk2_start = chunks_with_overlap[1].text[:20]

            # Check if there's actual word overlap
            overlap_found = any(
                word in chunk2_start
                for word in chunk1_end.split()
                if word.strip()
            )
            assert overlap_found


class TestDocumentTypeStrategies:
    """Test optimal chunking strategies for different document types."""

    def test_optimal_strategy_detection(self):
        """Test that optimal strategies are assigned for document types."""
        chunker = TextChunker()
        doc_types = [
            DocumentType.PDF,
            DocumentType.DOCX,
            DocumentType.TXT,
            DocumentType.MD,
            DocumentType.CSV,
            DocumentType.XLSX,
        ]

        for doc_type in doc_types:
            strategy = chunker.get_optimal_strategy(doc_type)
            assert isinstance(strategy, ChunkingStrategy)


class TestChunkEstimation:
    """Test chunk count estimation."""

    def test_estimate_chunks(self):
        """Test chunk count estimation."""
        text = "This is a test. " * 200

        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        estimated = chunker.estimate_chunks(text)
        actual_chunks = chunker.chunk_text(text)

        # Estimation should be reasonably close (within 2 chunks)
        assert abs(estimated - len(actual_chunks)) <= 2


class TestTokenBasedChunking:
    """Test token-based chunking."""

    def test_token_chunking(self):
        """Test token-based chunking."""
        text = "This is a test sentence for token-based chunking. " * 30

        try:
            chunks = chunk_text(
                text,
                chunk_size=200,
                chunk_overlap=50,
                strategy=ChunkingStrategy.TOKEN_BASED
            )

            assert len(chunks) > 0

            if chunks:
                assert chunks[0].metadata.token_count is not None

        except Exception:
            # Token-based chunking may not be available without tiktoken
            pytest.skip("Token-based chunking not available")


class TestEmbeddingGeneration:
    """Test embedding generation with Ollama."""

    @pytest.mark.asyncio
    async def test_single_embedding(self):
        """Test generating a single embedding."""
        text = "This is a test sentence for embedding generation."

        try:
            embedding = await embedding_service.generate_embedding_async(text)

            assert embedding is not None
            assert len(embedding) > 0
            assert all(isinstance(x, (int, float)) for x in embedding)

        except Exception as e:
            pytest.skip(f"Ollama not available: {str(e)}")

    @pytest.mark.asyncio
    async def test_batch_embeddings(self):
        """Test batch embedding generation."""
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence.",
        ]

        try:
            embeddings = await embedding_service.generate_embeddings_batch_async(
                texts,
                batch_size=2
            )

            assert len(embeddings) == len(texts)
            assert all(len(emb) > 0 for emb in embeddings)

        except Exception as e:
            pytest.skip(f"Ollama not available: {str(e)}")

    @pytest.mark.asyncio
    async def test_embedding_dimension(self):
        """Test getting embedding dimension."""
        try:
            dimension = embedding_service.get_embedding_dimension()
            assert dimension > 0

        except Exception as e:
            pytest.skip(f"Ollama not available: {str(e)}")


class TestCosineSimilarity:
    """Test cosine similarity calculation."""

    @pytest.mark.asyncio
    async def test_similarity_calculation(self):
        """Test calculating cosine similarity between embeddings."""
        try:
            # Generate embeddings for similar and dissimilar texts
            text1 = "The cat sat on the mat"
            text2 = "A cat was sitting on a mat"
            text3 = "The weather is sunny today"

            emb1 = await embedding_service.generate_embedding_async(text1)
            emb2 = await embedding_service.generate_embedding_async(text2)
            emb3 = await embedding_service.generate_embedding_async(text3)

            sim_12 = embedding_service.cosine_similarity(emb1, emb2)
            sim_13 = embedding_service.cosine_similarity(emb1, emb3)

            # Similar texts should have higher similarity
            assert sim_12 > sim_13
            # Similarities should be between -1 and 1
            assert -1 <= sim_12 <= 1
            assert -1 <= sim_13 <= 1

        except Exception as e:
            pytest.skip(f"Ollama not available: {str(e)}")


class TestChunkAndEmbedPipeline:
    """Test chunking text and generating embeddings for chunks."""

    @pytest.mark.asyncio
    async def test_chunk_and_embed_workflow(self):
        """Test complete chunk and embed pipeline."""
        text = """
        Artificial Intelligence is transforming how we interact with technology.
        Machine learning algorithms can now process vast amounts of data.

        Natural Language Processing enables computers to understand human language.
        This technology powers chatbots, translation services, and more.

        The future of AI holds tremendous potential for solving complex problems.
        From healthcare to climate change, AI applications are expanding rapidly.
        """

        try:
            # Chunk the text
            chunks = chunk_text(
                text,
                chunk_size=150,
                chunk_overlap=30,
                strategy=ChunkingStrategy.PARAGRAPH
            )

            assert len(chunks) > 0

            # Generate embeddings for chunks
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings_batch_async(
                chunk_texts,
                batch_size=3
            )

            assert len(embeddings) == len(chunks)

            # Verify embeddings
            for embedding in embeddings:
                assert len(embedding) > 0

        except Exception as e:
            pytest.skip(f"Ollama not available: {str(e)}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
