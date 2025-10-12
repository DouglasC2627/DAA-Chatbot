"""
Text chunking module for splitting documents into manageable pieces.

This module provides:
- Recursive text splitting with overlap
- Token-aware chunking using tiktoken
- Document-type specific chunking strategies
- Configurable chunk sizes and overlap
"""

import logging
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import tiktoken

from models.document import DocumentType

logger = logging.getLogger(__name__)


class ChunkingStrategy(str, Enum):
    """Available chunking strategies."""
    RECURSIVE = "recursive"
    TOKEN_BASED = "token_based"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    FIXED_SIZE = "fixed_size"


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""
    chunk_index: int
    document_id: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    token_count: Optional[int] = None
    source_section: Optional[str] = None


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    text: str
    metadata: ChunkMetadata

    def __len__(self) -> int:
        """Return character length of chunk."""
        return len(self.text)

    @property
    def word_count(self) -> int:
        """Get word count of chunk."""
        return len(self.text.split())


class TextChunker:
    """Service for splitting text into chunks."""

    # Default separators for recursive splitting (in order of priority)
    DEFAULT_SEPARATORS = [
        "\n\n",  # Double newline (paragraphs)
        "\n",    # Single newline
        ". ",    # Sentences
        "! ",    # Exclamations
        "? ",    # Questions
        "; ",    # Semicolons
        ", ",    # Commas
        " ",     # Spaces
        ""       # Characters (last resort)
    ]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            encoding_name: Tiktoken encoding name for token counting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding_name = encoding_name

        # Initialize tiktoken encoder
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoding {encoding_name}: {e}")
            self.tokenizer = None

        logger.info(
            f"TextChunker initialized: chunk_size={chunk_size}, "
            f"overlap={chunk_overlap}, encoding={encoding_name}"
        )

    def chunk_text(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        document_id: Optional[int] = None,
        **kwargs
    ) -> List[TextChunk]:
        """
        Split text into chunks using specified strategy.

        Args:
            text: Text to chunk
            strategy: Chunking strategy to use
            document_id: Optional document ID for metadata
            **kwargs: Additional parameters for specific strategies

        Returns:
            List of TextChunk objects

        Raises:
            ValueError: If strategy is not supported
        """
        if not text.strip():
            return []

        logger.info(f"Chunking text of length {len(text)} using {strategy.value} strategy")

        # Route to appropriate chunking method
        if strategy == ChunkingStrategy.RECURSIVE:
            chunks = self._chunk_recursive(text, **kwargs)
        elif strategy == ChunkingStrategy.TOKEN_BASED:
            chunks = self._chunk_token_based(text, **kwargs)
        elif strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(text, **kwargs)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(text, **kwargs)
        elif strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(text, **kwargs)
        else:
            raise ValueError(f"Unsupported chunking strategy: {strategy}")

        # Add metadata to chunks
        result = []
        for i, chunk_text in enumerate(chunks):
            # Calculate token count if tokenizer available
            token_count = None
            if self.tokenizer:
                token_count = len(self.tokenizer.encode(chunk_text))

            metadata = ChunkMetadata(
                chunk_index=i,
                document_id=document_id,
                token_count=token_count
            )

            result.append(TextChunk(text=chunk_text, metadata=metadata))

        logger.info(f"Created {len(result)} chunks")
        return result

    def _chunk_recursive(
        self,
        text: str,
        separators: Optional[List[str]] = None
    ) -> List[str]:
        """
        Recursively split text using a hierarchy of separators.

        Args:
            text: Text to split
            separators: List of separators to try (in order)

        Returns:
            List of text chunks
        """
        separators = separators or self.DEFAULT_SEPARATORS
        chunks = []

        def split_text(text: str, sep_index: int = 0) -> List[str]:
            """Recursively split text."""
            if len(text) <= self.chunk_size:
                return [text] if text.strip() else []

            if sep_index >= len(separators):
                # No more separators, split by character
                return self._chunk_fixed_size(text)

            separator = separators[sep_index]

            if separator == "":
                # Character-level split (last resort)
                return self._chunk_fixed_size(text)

            # Split by current separator
            splits = text.split(separator)

            current_chunk = []
            current_size = 0

            result = []

            for i, split in enumerate(splits):
                split_size = len(split)

                # Add separator back (except for last split)
                if i < len(splits) - 1:
                    split_size += len(separator)

                # Check if adding this split would exceed chunk size
                if current_size + split_size > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = separator.join(current_chunk)
                    if i < len(splits) - 1:
                        chunk_text += separator

                    result.append(chunk_text)

                    # Start new chunk with overlap
                    overlap_text = chunk_text[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                    current_chunk = [overlap_text] if overlap_text else []
                    current_size = len(overlap_text)

                # Add split to current chunk
                current_chunk.append(split)
                current_size += split_size

            # Add remaining chunk
            if current_chunk:
                chunk_text = separator.join(current_chunk)
                result.append(chunk_text)

            # Recursively split chunks that are too large
            final_result = []
            for chunk in result:
                if len(chunk) > self.chunk_size:
                    final_result.extend(split_text(chunk, sep_index + 1))
                else:
                    final_result.append(chunk)

            return final_result

        chunks = split_text(text)

        # Filter out empty chunks
        return [chunk for chunk in chunks if chunk.strip()]

    def _chunk_token_based(
        self,
        text: str,
        max_tokens: Optional[int] = None
    ) -> List[str]:
        """
        Split text based on token count.

        Args:
            text: Text to split
            max_tokens: Maximum tokens per chunk (defaults to approximate chunk_size)

        Returns:
            List of text chunks
        """
        if not self.tokenizer:
            logger.warning("Tokenizer not available, falling back to recursive chunking")
            return self._chunk_recursive(text)

        # Approximate tokens per chunk (rough estimate: 1 token ≈ 4 characters)
        max_tokens = max_tokens or (self.chunk_size // 4)
        overlap_tokens = self.chunk_overlap // 4

        # Encode text to tokens
        tokens = self.tokenizer.encode(text)

        chunks = []
        start = 0

        while start < len(tokens):
            # Get chunk of tokens
            end = start + max_tokens
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move start position with overlap
            start = end - overlap_tokens

        return [chunk for chunk in chunks if chunk.strip()]

    def _chunk_by_sentence(self, text: str) -> List[str]:
        """
        Split text by sentences.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        # Simple sentence splitting using regex
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap (last few sentences)
                if self.chunk_overlap > 0:
                    overlap_sentences = []
                    overlap_size = 0

                    for sent in reversed(current_chunk):
                        if overlap_size + len(sent) <= self.chunk_overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_size += len(sent)
                        else:
                            break

                    current_chunk = overlap_sentences
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_size

        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return [chunk for chunk in chunks if chunk.strip()]

    def _chunk_by_paragraph(self, text: str) -> List[str]:
        """
        Split text by paragraphs.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        # Split by double newlines (paragraphs)
        paragraphs = text.split("\n\n")

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            if current_size + para_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append("\n\n".join(current_chunk))

                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    overlap_paras = []
                    overlap_size = 0

                    for p in reversed(current_chunk):
                        if overlap_size + len(p) <= self.chunk_overlap:
                            overlap_paras.insert(0, p)
                            overlap_size += len(p)
                        else:
                            break

                    current_chunk = overlap_paras
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(para)
            current_size += para_size

        # Add remaining chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return [chunk for chunk in chunks if chunk.strip()]

    def _chunk_fixed_size(self, text: str) -> List[str]:
        """
        Split text into fixed-size chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap

        return [chunk for chunk in chunks if chunk.strip()]

    def get_optimal_strategy(self, document_type: DocumentType) -> ChunkingStrategy:
        """
        Get optimal chunking strategy for document type.

        Args:
            document_type: Type of document

        Returns:
            Recommended chunking strategy
        """
        strategy_map = {
            DocumentType.PDF: ChunkingStrategy.RECURSIVE,
            DocumentType.DOCX: ChunkingStrategy.PARAGRAPH,
            DocumentType.TXT: ChunkingStrategy.RECURSIVE,
            DocumentType.MD: ChunkingStrategy.PARAGRAPH,
            DocumentType.CSV: ChunkingStrategy.FIXED_SIZE,
            DocumentType.XLSX: ChunkingStrategy.FIXED_SIZE,
        }

        return strategy_map.get(document_type, ChunkingStrategy.RECURSIVE)

    def estimate_chunks(self, text: str) -> int:
        """
        Estimate number of chunks without actually chunking.

        Args:
            text: Text to analyze

        Returns:
            Estimated number of chunks
        """
        text_length = len(text)
        effective_chunk_size = self.chunk_size - self.chunk_overlap

        if effective_chunk_size <= 0:
            return 0

        estimated = (text_length + effective_chunk_size - 1) // effective_chunk_size
        return max(1, estimated)


# Create global chunker instances with different configurations
default_chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
small_chunker = TextChunker(chunk_size=500, chunk_overlap=100)
large_chunker = TextChunker(chunk_size=2000, chunk_overlap=400)


# Convenience functions
def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
    document_id: Optional[int] = None,
    **kwargs
) -> List[TextChunk]:
    """
    Chunk text with specified parameters.

    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks
        strategy: Chunking strategy to use
        document_id: Optional document ID for metadata
        **kwargs: Additional parameters

    Returns:
        List of TextChunk objects
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_text(text, strategy=strategy, document_id=document_id, **kwargs)


def chunk_document_text(
    text: str,
    document_type: DocumentType,
    document_id: Optional[int] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[TextChunk]:
    """
    Chunk document text using optimal strategy for document type.

    Args:
        text: Text to chunk
        document_type: Type of document
        document_id: Optional document ID for metadata
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks

    Returns:
        List of TextChunk objects
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    strategy = chunker.get_optimal_strategy(document_type)

    logger.info(f"Chunking {document_type.value} document with {strategy.value} strategy")

    return chunker.chunk_text(
        text=text,
        strategy=strategy,
        document_id=document_id
    )
