"""
Analytics service for embeddings visualization and analysis.

This service handles:
- Fetching embeddings from vector store
- Dimensionality reduction (PCA, t-SNE, UMAP)
- Similarity matrix computation
- Embedding statistics and metrics
- Query retrieval testing
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from dataclasses import dataclass

import numpy as np
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity

try:
    from umap import UMAP
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logging.warning("UMAP not available. Install umap-learn for UMAP dimensionality reduction.")

from core.vectorstore import VectorStore, vector_store
from core.embeddings import EmbeddingService, embedding_service
from core.database import get_db
from models.document import Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class AnalyticsServiceError(Exception):
    """Raised when analytics service operations fail."""
    pass


@dataclass
class EmbeddingData:
    """Represents embedding data with metadata."""
    chunk_id: str
    document_id: int
    document_name: str
    chunk_index: int
    embedding: List[float]
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DimensionalityReductionResult:
    """Result of dimensionality reduction."""
    method: str
    dimensions: int
    points: List[Dict[str, Any]]
    explained_variance: Optional[float] = None


class AnalyticsService:
    """
    Service for embeddings analytics and visualization.

    Provides functionality for analyzing and visualizing embeddings,
    including dimensionality reduction, similarity analysis, and
    statistical metrics.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize analytics service.

        Args:
            vector_store: Vector store instance (optional, uses global if not provided)
            embedding_service: Embedding service instance (optional, uses global if not provided)
        """
        self.vector_store = vector_store or globals()['vector_store']
        self.embedding_service = embedding_service or globals()['embedding_service']
        logger.info("AnalyticsService initialized")

    async def get_embeddings_for_project(
        self,
        db: AsyncSession,
        project_id: int,
        document_ids: Optional[List[int]] = None,
        limit: int = 500,
        include_text: bool = False
    ) -> List[EmbeddingData]:
        """
        Fetch embeddings from ChromaDB for a project.

        Args:
            db: Database session
            project_id: Project ID
            document_ids: Optional list of document IDs to filter
            limit: Maximum number of embeddings to return
            include_text: Whether to include chunk text in response

        Returns:
            List of EmbeddingData objects

        Raises:
            AnalyticsServiceError: If fetching fails
        """
        try:
            # Build metadata filter if document_ids provided
            where = None
            if document_ids:
                if len(document_ids) == 1:
                    where = {"document_id": document_ids[0]}
                else:
                    # ChromaDB doesn't support $in directly, so we'll filter in Python
                    pass

            # Fetch embeddings from ChromaDB
            collection = self.vector_store.get_or_create_collection(project_id)

            # Get all or filtered embeddings
            result = collection.get(
                where=where,
                limit=limit,
                include=['embeddings', 'documents', 'metadatas']
            )

            # Get document names from database
            doc_query = select(Document.id, Document.filename).where(
                Document.project_id == project_id
            )
            if document_ids:
                doc_query = doc_query.where(Document.id.in_(document_ids))

            doc_result = await db.execute(doc_query)
            doc_map = {doc_id: filename for doc_id, filename in doc_result.fetchall()}

            # Build response
            embeddings_data = []
            for i, chunk_id in enumerate(result['ids']):
                metadata = result['metadatas'][i]
                doc_id = metadata.get('document_id')

                # Apply document_ids filter if using multiple IDs (ChromaDB doesn't support $in)
                if document_ids and len(document_ids) > 1:
                    if doc_id not in document_ids:
                        continue

                embedding_data = EmbeddingData(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    document_name=doc_map.get(doc_id, f"Document {doc_id}"),
                    chunk_index=metadata.get('chunk_index', 0),
                    embedding=result['embeddings'][i],
                    text=result['documents'][i] if include_text else None,
                    metadata=metadata
                )
                embeddings_data.append(embedding_data)

            logger.info(
                f"Fetched {len(embeddings_data)} embeddings for project {project_id}"
            )
            return embeddings_data

        except Exception as e:
            logger.error(f"Error fetching embeddings: {str(e)}")
            raise AnalyticsServiceError(f"Failed to fetch embeddings: {str(e)}")

    def compute_dimensionality_reduction(
        self,
        embeddings: np.ndarray,
        method: str = 'pca',
        dimensions: int = 2,
        **kwargs
    ) -> np.ndarray:
        """
        Compute dimensionality reduction on embeddings.

        Args:
            embeddings: Input embeddings array of shape (n_samples, n_features)
            method: Reduction method ('pca', 'tsne', 'umap')
            dimensions: Output dimensions (2 or 3)
            **kwargs: Method-specific parameters
                - perplexity: For t-SNE (default: 30)
                - n_neighbors: For UMAP (default: 15)
                - min_dist: For UMAP (default: 0.1)

        Returns:
            Reduced embeddings of shape (n_samples, dimensions)

        Raises:
            AnalyticsServiceError: If reduction fails
        """
        try:
            logger.info(
                f"Computing {method.upper()} reduction to {dimensions}D "
                f"for {len(embeddings)} embeddings"
            )

            # Normalize embeddings for better results
            embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

            # Select and configure reducer
            if method == 'pca':
                reducer = PCA(n_components=dimensions, random_state=42)

            elif method == 'tsne':
                perplexity = kwargs.get('perplexity', 30)
                # Adjust perplexity if too large for dataset
                max_perplexity = (len(embeddings) - 1) // 3
                perplexity = min(perplexity, max_perplexity)

                reducer = TSNE(
                    n_components=dimensions,
                    perplexity=perplexity,
                    random_state=42,
                    n_jobs=-1
                )

            elif method == 'umap':
                if not UMAP_AVAILABLE:
                    raise AnalyticsServiceError(
                        "UMAP not available. Install umap-learn: pip install umap-learn"
                    )

                n_neighbors = kwargs.get('n_neighbors', 15)
                min_dist = kwargs.get('min_dist', 0.1)

                # Adjust n_neighbors if too large for dataset
                n_neighbors = min(n_neighbors, len(embeddings) - 1)

                reducer = UMAP(
                    n_components=dimensions,
                    n_neighbors=n_neighbors,
                    min_dist=min_dist,
                    random_state=42
                )

            else:
                raise AnalyticsServiceError(
                    f"Unknown reduction method: {method}. "
                    f"Use 'pca', 'tsne', or 'umap'."
                )

            # Perform reduction
            reduced = reducer.fit_transform(embeddings_norm)

            logger.info(f"{method.upper()} reduction completed successfully")
            return reduced

        except Exception as e:
            logger.error(f"Error in dimensionality reduction: {str(e)}")
            raise AnalyticsServiceError(f"Dimensionality reduction failed: {str(e)}")

    def compute_similarity_matrix(
        self,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute pairwise cosine similarity matrix.

        Args:
            embeddings: Input embeddings array of shape (n_samples, n_features)

        Returns:
            Similarity matrix of shape (n_samples, n_samples)

        Raises:
            AnalyticsServiceError: If computation fails
        """
        try:
            logger.info(f"Computing similarity matrix for {len(embeddings)} embeddings")

            # Normalize embeddings for cosine similarity
            embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

            # Compute pairwise cosine similarity
            similarity_matrix = cosine_similarity(embeddings_norm)

            logger.info("Similarity matrix computed successfully")
            return similarity_matrix

        except Exception as e:
            logger.error(f"Error computing similarity matrix: {str(e)}")
            raise AnalyticsServiceError(f"Similarity matrix computation failed: {str(e)}")

    async def compute_embedding_statistics(
        self,
        db: AsyncSession,
        project_id: int
    ) -> Dict[str, Any]:
        """
        Compute statistical metrics about embeddings.

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            Dictionary with statistics

        Raises:
            AnalyticsServiceError: If computation fails
        """
        try:
            # Fetch embeddings
            embeddings_data = await self.get_embeddings_for_project(
                db, project_id, limit=2000
            )

            if not embeddings_data:
                return {
                    "total_chunks": 0,
                    "total_documents": 0,
                    "embedding_dimension": 0,
                    "embedding_model": self.embedding_service.model,
                    "stats": {},
                    "document_breakdown": []
                }

            # Convert to numpy array
            embeddings = np.array([ed.embedding for ed in embeddings_data])

            # Compute norms
            norms = np.linalg.norm(embeddings, axis=1)

            # Compute average pairwise similarity (sample if too many)
            if len(embeddings) > 100:
                # Sample 100 random embeddings for pairwise similarity
                sample_indices = np.random.choice(len(embeddings), 100, replace=False)
                sample_embeddings = embeddings[sample_indices]
                similarity_matrix = self.compute_similarity_matrix(sample_embeddings)
            else:
                similarity_matrix = self.compute_similarity_matrix(embeddings)

            # Get upper triangle (excluding diagonal) for average similarity
            upper_tri = np.triu_indices_from(similarity_matrix, k=1)
            avg_similarity = similarity_matrix[upper_tri].mean()

            # Group by document for breakdown
            doc_groups: Dict[int, List[EmbeddingData]] = {}
            for ed in embeddings_data:
                if ed.document_id not in doc_groups:
                    doc_groups[ed.document_id] = []
                doc_groups[ed.document_id].append(ed)

            document_breakdown = []
            for doc_id, doc_embeddings in doc_groups.items():
                doc_emb_array = np.array([ed.embedding for ed in doc_embeddings])
                doc_norms = np.linalg.norm(doc_emb_array, axis=1)

                document_breakdown.append({
                    "document_id": doc_id,
                    "document_name": doc_embeddings[0].document_name,
                    "chunk_count": len(doc_embeddings),
                    "avg_norm": float(doc_norms.mean()),
                    "std_norm": float(doc_norms.std())
                })

            return {
                "total_chunks": len(embeddings_data),
                "total_documents": len(doc_groups),
                "embedding_dimension": len(embeddings[0]),
                "embedding_model": self.embedding_service.model,
                "stats": {
                    "mean_norm": float(norms.mean()),
                    "std_norm": float(norms.std()),
                    "min_norm": float(norms.min()),
                    "max_norm": float(norms.max()),
                    "avg_similarity": float(avg_similarity)
                },
                "document_breakdown": document_breakdown
            }

        except Exception as e:
            logger.error(f"Error computing embedding statistics: {str(e)}")
            raise AnalyticsServiceError(f"Statistics computation failed: {str(e)}")

    async def test_query_retrieval(
        self,
        project_id: int,
        query: str,
        top_k: int = 10,
        return_embeddings: bool = False
    ) -> Dict[str, Any]:
        """
        Test query retrieval and return results with scores.

        Args:
            project_id: Project ID
            query: Test query string
            top_k: Number of results to return
            return_embeddings: Whether to return query embedding

        Returns:
            Dictionary with query results and statistics

        Raises:
            AnalyticsServiceError: If retrieval fails
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)

            # Search vector store
            results = self.vector_store.search(
                project_id=project_id,
                query_embedding=query_embedding,
                n_results=top_k
            )

            # Format results
            retrieved_chunks = []
            scores = []

            for i, chunk_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i]
                score = 1 - distance  # Convert distance to similarity score
                scores.append(score)

                metadata = results['metadatas'][0][i]
                retrieved_chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": metadata.get('document_id'),
                    "document_name": metadata.get('filename', 'Unknown'),
                    "chunk_index": metadata.get('chunk_index', 0),
                    "text": results['documents'][0][i],
                    "score": float(score),
                    "distance": float(distance)
                })

            # Compute statistics
            scores_array = np.array(scores)

            return {
                "query": query,
                "query_embedding": query_embedding if return_embeddings else None,
                "results": retrieved_chunks,
                "stats": {
                    "avg_score": float(scores_array.mean()) if len(scores) > 0 else 0.0,
                    "min_score": float(scores_array.min()) if len(scores) > 0 else 0.0,
                    "max_score": float(scores_array.max()) if len(scores) > 0 else 0.0,
                    "score_distribution": scores
                }
            }

        except Exception as e:
            logger.error(f"Error in query retrieval test: {str(e)}")
            raise AnalyticsServiceError(f"Query retrieval test failed: {str(e)}")


# Global analytics service instance
analytics_service = AnalyticsService()
