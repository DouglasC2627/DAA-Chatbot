"""
Analytics API routes.

Endpoints:
- GET /api/analytics/projects/{project_id}/embeddings - Fetch embeddings data
- POST /api/analytics/projects/{project_id}/dimensionality-reduction - Compute t-SNE/UMAP/PCA
- POST /api/analytics/projects/{project_id}/similarity-matrix - Compute similarity heatmap
- GET /api/analytics/projects/{project_id}/embedding-stats - Get embedding statistics
- POST /api/analytics/projects/{project_id}/test-retrieval - Test query retrieval
"""

import logging
from typing import List, Optional, Dict, Any, Literal
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from core.database import get_db
from services.analytics_service import analytics_service, AnalyticsServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# Request/Response Models

class EmbeddingDataResponse(BaseModel):
    """Response model for individual embedding data."""
    chunk_id: str
    document_id: int
    document_name: str
    chunk_index: int
    embedding: List[float]
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingsListResponse(BaseModel):
    """Response model for list of embeddings."""
    embeddings: List[EmbeddingDataResponse]
    total: int
    limit: int


class DimReductionRequest(BaseModel):
    """Request model for dimensionality reduction."""
    method: Literal["tsne", "umap", "pca"] = Field(
        default="pca",
        description="Dimensionality reduction method"
    )
    dimensions: Literal[2, 3] = Field(
        default=2,
        description="Number of output dimensions"
    )
    document_ids: Optional[List[int]] = Field(
        default=None,
        description="Filter to specific documents"
    )
    n_samples: Optional[int] = Field(
        default=500,
        ge=10,
        le=2000,
        description="Maximum number of samples to process"
    )
    perplexity: Optional[int] = Field(
        default=30,
        ge=5,
        le=50,
        description="t-SNE perplexity parameter"
    )
    n_neighbors: Optional[int] = Field(
        default=15,
        ge=2,
        le=50,
        description="UMAP n_neighbors parameter"
    )


class DimReductionPoint(BaseModel):
    """Single point in reduced space."""
    x: float
    y: float
    z: Optional[float] = None
    chunk_id: str
    chunk_index: int
    document_id: int
    document_name: str
    text_preview: str


class DimReductionResponse(BaseModel):
    """Response model for dimensionality reduction."""
    method: str
    dimensions: int
    points: List[DimReductionPoint]
    total_points: int
    explained_variance: Optional[float] = None


class SimilarityMatrixRequest(BaseModel):
    """Request model for similarity matrix computation."""
    scope: Literal["document", "chunk"] = Field(
        default="document",
        description="Compute similarity at document or chunk level"
    )
    document_ids: Optional[List[int]] = Field(
        default=None,
        description="Filter to specific documents"
    )
    max_items: Optional[int] = Field(
        default=50,
        ge=2,
        le=100,
        description="Maximum number of items in matrix"
    )


class SimilarityMatrixItem(BaseModel):
    """Item in similarity matrix."""
    id: str
    label: str


class SimilarityMatrixResponse(BaseModel):
    """Response model for similarity matrix."""
    scope: str
    items: List[SimilarityMatrixItem]
    matrix: List[List[float]]


class EmbeddingStatsResponse(BaseModel):
    """Response model for embedding statistics."""
    total_chunks: int
    total_documents: int
    embedding_dimension: int
    embedding_model: str
    stats: Dict[str, float]
    document_breakdown: List[Dict[str, Any]]


class TestRetrievalRequest(BaseModel):
    """Request model for query retrieval testing."""
    query: str = Field(..., min_length=1, description="Test query string")
    top_k: int = Field(default=10, ge=1, le=20, description="Number of results to retrieve")
    return_embeddings: bool = Field(
        default=False,
        description="Whether to return query embedding vector"
    )


class RetrievalResult(BaseModel):
    """Single retrieval result."""
    chunk_id: str
    document_id: int
    document_name: str
    chunk_index: int
    text: str
    score: float
    distance: float


class TestRetrievalResponse(BaseModel):
    """Response model for query retrieval testing."""
    query: str
    query_embedding: Optional[List[float]] = None
    results: List[RetrievalResult]
    stats: Dict[str, Any]


# API Endpoints

@router.get("/projects/{project_id}/embeddings", response_model=EmbeddingsListResponse)
async def get_embeddings(
    project_id: int,
    document_id: Optional[int] = Query(None, description="Filter to specific document"),
    limit: int = Query(500, ge=1, le=2000, description="Maximum embeddings to return"),
    include_text: bool = Query(False, description="Include chunk text in response"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch embeddings for a project.

    Args:
        project_id: Project ID
        document_id: Optional document ID filter
        limit: Maximum number of embeddings to return
        include_text: Whether to include chunk text
        db: Database session

    Returns:
        List of embeddings with metadata
    """
    try:
        # Build document_ids list if filter provided
        document_ids = [document_id] if document_id else None

        # Fetch embeddings
        embeddings_data = await analytics_service.get_embeddings_for_project(
            db=db,
            project_id=project_id,
            document_ids=document_ids,
            limit=limit,
            include_text=include_text
        )

        # Convert to response model
        embeddings_response = [
            EmbeddingDataResponse(
                chunk_id=ed.chunk_id,
                document_id=ed.document_id,
                document_name=ed.document_name,
                chunk_index=ed.chunk_index,
                embedding=ed.embedding,
                text=ed.text,
                metadata=ed.metadata
            )
            for ed in embeddings_data
        ]

        return EmbeddingsListResponse(
            embeddings=embeddings_response,
            total=len(embeddings_response),
            limit=limit
        )

    except AnalyticsServiceError as e:
        logger.error(f"Error fetching embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch embeddings: {str(e)}"
        )


@router.post(
    "/projects/{project_id}/dimensionality-reduction",
    response_model=DimReductionResponse
)
async def compute_dimensionality_reduction(
    project_id: int,
    request: DimReductionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compute dimensionality reduction on embeddings.

    Args:
        project_id: Project ID
        request: Dimensionality reduction parameters
        db: Database session

    Returns:
        Reduced coordinates with metadata for visualization
    """
    try:
        # Fetch embeddings
        embeddings_data = await analytics_service.get_embeddings_for_project(
            db=db,
            project_id=project_id,
            document_ids=request.document_ids,
            limit=request.n_samples,
            include_text=True
        )

        if len(embeddings_data) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough embeddings for dimensionality reduction (need at least 2)"
            )

        # Convert to numpy array
        embeddings_array = np.array([ed.embedding for ed in embeddings_data])

        # Compute dimensionality reduction
        reduced_coords = analytics_service.compute_dimensionality_reduction(
            embeddings=embeddings_array,
            method=request.method,
            dimensions=request.dimensions,
            perplexity=request.perplexity,
            n_neighbors=request.n_neighbors
        )

        # Build response points
        points = []
        for i, ed in enumerate(embeddings_data):
            # Create text preview (first 100 chars)
            text_preview = ed.text[:100] + "..." if ed.text and len(ed.text) > 100 else (ed.text or "")

            point = DimReductionPoint(
                x=float(reduced_coords[i, 0]),
                y=float(reduced_coords[i, 1]),
                z=float(reduced_coords[i, 2]) if request.dimensions == 3 else None,
                chunk_id=ed.chunk_id,
                chunk_index=ed.chunk_index,
                document_id=ed.document_id,
                document_name=ed.document_name,
                text_preview=text_preview
            )
            points.append(point)

        return DimReductionResponse(
            method=request.method,
            dimensions=request.dimensions,
            points=points,
            total_points=len(points),
            explained_variance=None  # TODO: Add for PCA
        )

    except AnalyticsServiceError as e:
        logger.error(f"Error in dimensionality reduction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/projects/{project_id}/similarity-matrix",
    response_model=SimilarityMatrixResponse
)
async def compute_similarity_matrix(
    project_id: int,
    request: SimilarityMatrixRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compute pairwise similarity matrix for heatmap visualization.

    Args:
        project_id: Project ID
        request: Similarity matrix parameters
        db: Database session

    Returns:
        Similarity matrix with item labels
    """
    try:
        # Fetch embeddings
        embeddings_data = await analytics_service.get_embeddings_for_project(
            db=db,
            project_id=project_id,
            document_ids=request.document_ids,
            limit=request.max_items if request.scope == "chunk" else 1000,
            include_text=False
        )

        if len(embeddings_data) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough embeddings for similarity matrix (need at least 2)"
            )

        if request.scope == "document":
            # Group by document and average embeddings
            doc_groups: Dict[int, List[List[float]]] = {}
            doc_names: Dict[int, str] = {}

            for ed in embeddings_data:
                if ed.document_id not in doc_groups:
                    doc_groups[ed.document_id] = []
                    doc_names[ed.document_id] = ed.document_name
                doc_groups[ed.document_id].append(ed.embedding)

            # Limit to max_items documents
            doc_ids = list(doc_groups.keys())[:request.max_items]

            # Average embeddings per document
            doc_embeddings = []
            items = []
            for doc_id in doc_ids:
                avg_embedding = np.mean(doc_groups[doc_id], axis=0)
                doc_embeddings.append(avg_embedding)
                items.append(
                    SimilarityMatrixItem(
                        id=str(doc_id),
                        label=doc_names[doc_id]
                    )
                )

            embeddings_array = np.array(doc_embeddings)

        else:  # chunk level
            # Limit to max_items chunks
            limited_embeddings = embeddings_data[:request.max_items]
            embeddings_array = np.array([ed.embedding for ed in limited_embeddings])

            items = [
                SimilarityMatrixItem(
                    id=ed.chunk_id,
                    label=f"{ed.document_name} - Chunk {ed.chunk_index}"
                )
                for ed in limited_embeddings
            ]

        # Compute similarity matrix
        similarity_matrix = analytics_service.compute_similarity_matrix(embeddings_array)

        # Convert to list of lists
        matrix_list = similarity_matrix.tolist()

        return SimilarityMatrixResponse(
            scope=request.scope,
            items=items,
            matrix=matrix_list
        )

    except AnalyticsServiceError as e:
        logger.error(f"Error computing similarity matrix: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/projects/{project_id}/embedding-stats",
    response_model=EmbeddingStatsResponse
)
async def get_embedding_statistics(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistical metrics about embeddings.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Embedding statistics and per-document breakdown
    """
    try:
        stats = await analytics_service.compute_embedding_statistics(
            db=db,
            project_id=project_id
        )

        return EmbeddingStatsResponse(**stats)

    except AnalyticsServiceError as e:
        logger.error(f"Error computing statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/projects/{project_id}/test-retrieval",
    response_model=TestRetrievalResponse
)
async def test_query_retrieval(
    project_id: int,
    request: TestRetrievalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Test query retrieval and visualize results.

    Args:
        project_id: Project ID
        request: Test query parameters
        db: Database session

    Returns:
        Retrieved chunks with scores and statistics
    """
    try:
        result = await analytics_service.test_query_retrieval(
            project_id=project_id,
            query=request.query,
            top_k=request.top_k,
            return_embeddings=request.return_embeddings
        )

        # Convert to response model
        results_response = [
            RetrievalResult(**r)
            for r in result['results']
        ]

        return TestRetrievalResponse(
            query=result['query'],
            query_embedding=result['query_embedding'],
            results=results_response,
            stats=result['stats']
        )

    except AnalyticsServiceError as e:
        logger.error(f"Error in query retrieval test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
