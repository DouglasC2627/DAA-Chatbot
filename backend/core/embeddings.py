"""
Embeddings generation module using Ollama.

This module provides:
- Text embedding generation via Ollama embedding models
- Batch embedding generation for efficiency
- Embedding caching for performance
- Support for multiple embedding models
"""

import logging
from typing import List, Optional, Dict
import numpy as np
from ollama import Client, AsyncClient

from core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


class EmbeddingService:
    """Service for generating text embeddings using Ollama."""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize embedding service.

        Args:
            host: Ollama server URL (defaults to settings.OLLAMA_HOST)
            model: Embedding model name (defaults to settings.EMBEDDING_MODEL)
        """
        self.host = host or settings.OLLAMA_HOST
        self.model = model or settings.EMBEDDING_MODEL

        self._client: Optional[Client] = None
        self._async_client: Optional[AsyncClient] = None

        logger.info(f"EmbeddingService initialized with host={self.host}, model={self.model}")

    @property
    def client(self) -> Client:
        """Get or create synchronous Ollama client."""
        if self._client is None:
            self._client = Client(host=self.host)
        return self._client

    @property
    def async_client(self) -> AsyncClient:
        """Get or create asynchronous Ollama client."""
        if self._async_client is None:
            self._async_client = AsyncClient(host=self.host)
        return self._async_client

    def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Embedding model to use (defaults to self.model)

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingError: If embedding generation fails
        """
        model = model or self.model

        if not text.strip():
            raise EmbeddingError("Cannot generate embedding for empty text")

        try:
            logger.debug(f"Generating embedding for text of length {len(text)}")

            response = self.client.embeddings(
                model=model,
                prompt=text
            )

            embedding = response.get('embedding', [])

            if not embedding:
                raise EmbeddingError("Empty embedding returned from Ollama")

            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise EmbeddingError(f"Embedding generation failed: {str(e)}") from e

    async def generate_embedding_async(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a single text (async).

        Args:
            text: Text to embed
            model: Embedding model to use (defaults to self.model)

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingError: If embedding generation fails
        """
        model = model or self.model

        if not text.strip():
            raise EmbeddingError("Cannot generate embedding for empty text")

        try:
            logger.debug(f"Generating embedding for text of length {len(text)}")

            response = await self.async_client.embeddings(
                model=model,
                prompt=text
            )

            embedding = response.get('embedding', [])

            if not embedding:
                raise EmbeddingError("Empty embedding returned from Ollama")

            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise EmbeddingError(f"Embedding generation failed: {str(e)}") from e

    def generate_embeddings_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to self.model)
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        model = model or self.model

        if not texts:
            return []

        logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")

        embeddings = []

        try:
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = []

                for text in batch:
                    if text.strip():
                        embedding = self.generate_embedding(text, model)
                        batch_embeddings.append(embedding)
                    else:
                        # For empty texts, add zero vector (will be filtered later)
                        logger.warning(f"Empty text at index {i + len(batch_embeddings)}, skipping")
                        batch_embeddings.append([])

                embeddings.extend(batch_embeddings)

                logger.debug(f"Processed batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise EmbeddingError(f"Batch embedding generation failed: {str(e)}") from e

    async def generate_embeddings_batch_async(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches (async).

        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to self.model)
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        model = model or self.model

        if not texts:
            return []

        logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")

        embeddings = []

        try:
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = []

                for text in batch:
                    if text.strip():
                        embedding = await self.generate_embedding_async(text, model)
                        batch_embeddings.append(embedding)
                    else:
                        # For empty texts, add zero vector (will be filtered later)
                        logger.warning(f"Empty text at index {i + len(batch_embeddings)}, skipping")
                        batch_embeddings.append([])

                embeddings.extend(batch_embeddings)

                logger.debug(f"Processed batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise EmbeddingError(f"Batch embedding generation failed: {str(e)}") from e

    def get_embedding_dimension(self, model: Optional[str] = None) -> int:
        """
        Get the dimension of embeddings for a model.

        Args:
            model: Embedding model to check (defaults to self.model)

        Returns:
            Embedding dimension

        Raises:
            EmbeddingError: If dimension cannot be determined
        """
        model = model or self.model

        try:
            # Generate a sample embedding to get dimension
            sample_embedding = self.generate_embedding("test", model)
            dimension = len(sample_embedding)

            logger.info(f"Model {model} produces embeddings of dimension {dimension}")
            return dimension

        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {str(e)}")
            raise EmbeddingError(f"Failed to get embedding dimension: {str(e)}") from e

    @staticmethod
    def cosine_similarity(
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1)

        Raises:
            ValueError: If embeddings have different dimensions
        """
        if len(embedding1) != len(embedding2):
            raise ValueError(
                f"Embedding dimensions don't match: {len(embedding1)} vs {len(embedding2)}"
            )

        # Convert to numpy arrays for efficient computation
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Ensure result is in [0, 1] range (handle floating point errors)
        return float(np.clip(similarity, 0.0, 1.0))

    def switch_model(self, model_name: str) -> None:
        """
        Switch the embedding model.

        Args:
            model_name: Name of the new embedding model
        """
        logger.info(f"Switching embedding model from {self.model} to {model_name}")
        self.model = model_name

    async def validate_model(self, model: Optional[str] = None) -> bool:
        """
        Validate that an embedding model is available.

        Args:
            model: Model to validate (defaults to self.model)

        Returns:
            True if model is available, False otherwise
        """
        model = model or self.model

        try:
            # Try to generate a test embedding
            await self.generate_embedding_async("test", model)
            logger.info(f"Model {model} is available and working")
            return True

        except Exception as e:
            logger.error(f"Model {model} validation failed: {str(e)}")
            return False


# Create global embedding service instance
embedding_service = EmbeddingService()


# Convenience functions
def generate_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """
    Generate embedding for text.

    Args:
        text: Text to embed
        model: Embedding model to use

    Returns:
        Embedding vector
    """
    return embedding_service.generate_embedding(text, model)


async def generate_embedding_async(text: str, model: Optional[str] = None) -> List[float]:
    """
    Generate embedding for text (async).

    Args:
        text: Text to embed
        model: Embedding model to use

    Returns:
        Embedding vector
    """
    return await embedding_service.generate_embedding_async(text, model)


def generate_embeddings_batch(
    texts: List[str],
    model: Optional[str] = None,
    batch_size: int = 10
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts.

    Args:
        texts: List of texts to embed
        model: Embedding model to use
        batch_size: Batch size for processing

    Returns:
        List of embedding vectors
    """
    return embedding_service.generate_embeddings_batch(texts, model, batch_size)


async def generate_embeddings_batch_async(
    texts: List[str],
    model: Optional[str] = None,
    batch_size: int = 10
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts (async).

    Args:
        texts: List of texts to embed
        model: Embedding model to use
        batch_size: Batch size for processing

    Returns:
        List of embedding vectors
    """
    return await embedding_service.generate_embeddings_batch_async(texts, model, batch_size)
