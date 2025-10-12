"""
Test script for embeddings and chunking functionality.

This script tests:
- Embedding generation with Ollama
- Text chunking with various strategies
- Integration of chunking and embeddings
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

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


def test_chunking_strategies():
    """Test different chunking strategies."""
    print("\n=== Testing Chunking Strategies ===")

    # Sample text
    text = """This is the first paragraph. It contains multiple sentences. Each sentence adds meaning.

This is the second paragraph. It's separated by a blank line. This helps organize content.

This is the third paragraph. We can use this to test chunking strategies. Different strategies will split this differently."""

    strategies = [
        ChunkingStrategy.RECURSIVE,
        ChunkingStrategy.SENTENCE,
        ChunkingStrategy.PARAGRAPH,
        ChunkingStrategy.FIXED_SIZE,
    ]

    for strategy in strategies:
        chunks = chunk_text(
            text,
            chunk_size=100,
            chunk_overlap=20,
            strategy=strategy
        )

        print(f"\n{strategy.value.upper()} Strategy:")
        print(f"  Chunks created: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i + 1}: {len(chunk)} chars, {chunk.word_count} words")
            print(f"    Preview: {chunk.text[:60]}...")


def test_chunk_overlap():
    """Test chunk overlap functionality."""
    print("\n=== Testing Chunk Overlap ===")

    text = "This is a test sentence. " * 50  # Long repeated text

    # Without overlap
    chunks_no_overlap = chunk_text(text, chunk_size=100, chunk_overlap=0)
    print(f"\nWithout overlap: {len(chunks_no_overlap)} chunks")

    # With overlap
    chunks_with_overlap = chunk_text(text, chunk_size=100, chunk_overlap=20)
    print(f"With 20 char overlap: {len(chunks_with_overlap)} chunks")

    # Verify overlap
    if len(chunks_with_overlap) > 1:
        chunk1_end = chunks_with_overlap[0].text[-20:]
        chunk2_start = chunks_with_overlap[1].text[:20]

        print(f"\nOverlap verification:")
        print(f"  Chunk 1 end: '{chunk1_end}'")
        print(f"  Chunk 2 start: '{chunk2_start}'")

        # Check if there's actual overlap
        overlap_found = any(
            word in chunk2_start
            for word in chunk1_end.split()
            if word.strip()
        )
        print(f"  Overlap detected: {'✓' if overlap_found else '✗'}")


def test_document_type_strategies():
    """Test optimal chunking strategies for different document types."""
    print("\n=== Testing Document Type Strategies ===")

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
        print(f"  {doc_type.value}: {strategy.value}")


def test_chunk_estimation():
    """Test chunk count estimation."""
    print("\n=== Testing Chunk Estimation ===")

    text = "This is a test. " * 200  # Create long text

    chunker = TextChunker(chunk_size=100, chunk_overlap=20)

    estimated = chunker.estimate_chunks(text)
    actual_chunks = chunker.chunk_text(text)

    print(f"  Text length: {len(text)} characters")
    print(f"  Estimated chunks: {estimated}")
    print(f"  Actual chunks: {len(actual_chunks)}")
    print(f"  Estimation accuracy: {abs(estimated - len(actual_chunks)) <= 2}")


def test_token_based_chunking():
    """Test token-based chunking."""
    print("\n=== Testing Token-Based Chunking ===")

    text = "This is a test sentence for token-based chunking. " * 30

    try:
        chunks = chunk_text(
            text,
            chunk_size=200,
            chunk_overlap=50,
            strategy=ChunkingStrategy.TOKEN_BASED
        )

        print(f"  Created {len(chunks)} chunks")

        if chunks:
            print(f"  First chunk token count: {chunks[0].metadata.token_count}")
            print(f"  Preview: {chunks[0].text[:60]}...")

            print("  ✓ Token-based chunking successful")

    except Exception as e:
        print(f"  ✗ Token-based chunking failed: {e}")


async def test_embedding_generation():
    """Test embedding generation with Ollama."""
    print("\n=== Testing Embedding Generation ===")

    try:
        # Test single embedding
        text = "This is a test sentence for embedding generation."

        print(f"  Generating embedding for: '{text}'")

        embedding = await embedding_service.generate_embedding_async(text)

        print(f"  ✓ Embedding generated successfully")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")

        return True

    except Exception as e:
        print(f"  ✗ Embedding generation failed: {e}")
        print(f"  Note: Make sure Ollama is running and embedding model is available")
        return False


async def test_batch_embeddings():
    """Test batch embedding generation."""
    print("\n=== Testing Batch Embedding Generation ===")

    texts = [
        "First test sentence.",
        "Second test sentence.",
        "Third test sentence.",
        "Fourth test sentence.",
        "Fifth test sentence.",
    ]

    try:
        print(f"  Generating embeddings for {len(texts)} texts...")

        embeddings = await embedding_service.generate_embeddings_batch_async(
            texts,
            batch_size=2
        )

        print(f"  ✓ Generated {len(embeddings)} embeddings")
        print(f"  Embedding dimension: {len(embeddings[0]) if embeddings else 'N/A'}")

        # Test cosine similarity
        if len(embeddings) >= 2:
            similarity = embedding_service.cosine_similarity(
                embeddings[0],
                embeddings[1]
            )
            print(f"  Similarity between first two embeddings: {similarity:.4f}")

        return True

    except Exception as e:
        print(f"  ✗ Batch embedding generation failed: {e}")
        return False


async def test_embedding_dimension():
    """Test getting embedding dimension."""
    print("\n=== Testing Embedding Dimension Detection ===")

    try:
        dimension = embedding_service.get_embedding_dimension()
        print(f"  ✓ Embedding dimension: {dimension}")
        return True

    except Exception as e:
        print(f"  ✗ Failed to get embedding dimension: {e}")
        return False


async def test_chunk_and_embed():
    """Test chunking text and generating embeddings for chunks."""
    print("\n=== Testing Chunk + Embed Pipeline ===")

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
        print(f"  Chunking text ({len(text)} chars)...")
        chunks = chunk_text(
            text,
            chunk_size=150,
            chunk_overlap=30,
            strategy=ChunkingStrategy.PARAGRAPH
        )

        print(f"  Created {len(chunks)} chunks")

        # Generate embeddings for chunks
        print(f"  Generating embeddings for chunks...")
        chunk_texts = [chunk.text for chunk in chunks]

        embeddings = await embedding_service.generate_embeddings_batch_async(
            chunk_texts,
            batch_size=3
        )

        print(f"  ✓ Generated {len(embeddings)} embeddings")

        # Display chunk info
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            print(f"\n  Chunk {i + 1}:")
            print(f"    Text: {chunk.text[:60]}...")
            print(f"    Length: {len(chunk)} chars")
            print(f"    Words: {chunk.word_count}")
            print(f"    Tokens: {chunk.metadata.token_count}")
            print(f"    Embedding dim: {len(embedding)}")

        return True

    except Exception as e:
        print(f"  ✗ Chunk + Embed pipeline failed: {e}")
        return False


async def test_cosine_similarity():
    """Test cosine similarity calculation."""
    print("\n=== Testing Cosine Similarity ===")

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
        sim_23 = embedding_service.cosine_similarity(emb2, emb3)

        print(f"  Text 1: '{text1}'")
        print(f"  Text 2: '{text2}'")
        print(f"  Text 3: '{text3}'")
        print(f"\n  Similarity (1-2): {sim_12:.4f} (similar texts)")
        print(f"  Similarity (1-3): {sim_13:.4f} (different texts)")
        print(f"  Similarity (2-3): {sim_23:.4f} (different texts)")

        # Verify that similar texts have higher similarity
        if sim_12 > sim_13:
            print(f"  ✓ Similar texts have higher similarity")
        else:
            print(f"  ✗ Similarity ordering unexpected")

        return True

    except Exception as e:
        print(f"  ✗ Cosine similarity test failed: {e}")
        return False


async def run_all_tests():
    """Run all embedding and chunking tests."""
    print("=" * 60)
    print("EMBEDDINGS & CHUNKING TEST SUITE")
    print("=" * 60)

    # Chunking tests (synchronous)
    test_chunking_strategies()
    test_chunk_overlap()
    test_document_type_strategies()
    test_chunk_estimation()
    test_token_based_chunking()

    # Embedding tests (async - require Ollama)
    embedding_available = await test_embedding_generation()

    if embedding_available:
        await test_batch_embeddings()
        await test_embedding_dimension()
        await test_chunk_and_embed()
        await test_cosine_similarity()
    else:
        print("\n⚠ Skipping remaining embedding tests (Ollama not available)")
        print("  To run embedding tests:")
        print("  1. Start Ollama: ollama serve")
        print("  2. Pull embedding model: ollama pull nomic-embed-text")

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
