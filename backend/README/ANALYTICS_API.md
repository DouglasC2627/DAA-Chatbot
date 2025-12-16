# Analytics API Documentation

This document describes the analytics API endpoints for embedding visualization and analysis.

## Overview

The Analytics API provides comprehensive endpoints for analyzing document embeddings and evaluating RAG system performance. All endpoints require a valid project ID and return JSON responses.

**Base Path:** `/api/analytics`

## Endpoints

### 1. Get Embeddings

Fetch raw embeddings data for visualization and analysis.

**Endpoint:** `GET /api/analytics/projects/{project_id}/embeddings`

**Parameters:**
- `project_id` (path, required): Project identifier
- `document_id` (query, optional): Filter to specific document
- `limit` (query, optional): Maximum embeddings to return (default: 500, max: 2000)
- `include_text` (query, optional): Include chunk text in response (default: false)

**Response:**
```json
{
  "embeddings": [
    {
      "chunk_id": "doc1_chunk0",
      "document_id": 1,
      "document_name": "example.pdf",
      "chunk_index": 0,
      "embedding": [0.123, -0.456, ...],
      "text": "optional chunk text",
      "metadata": {}
    }
  ],
  "total": 150,
  "limit": 500
}
```

---

### 2. Compute Dimensionality Reduction

Transform high-dimensional embeddings to 2D/3D for visualization using PCA, t-SNE, or UMAP.

**Endpoint:** `POST /api/analytics/projects/{project_id}/dimensionality-reduction`

**Request Body:**
```json
{
  "method": "pca",           // "pca" | "tsne" | "umap"
  "dimensions": 2,           // 2 or 3
  "document_ids": [1, 2],    // optional filter
  "n_samples": 500,          // max samples (10-2000)
  "perplexity": 30,          // t-SNE only (5-50)
  "n_neighbors": 15          // UMAP only (2-50)
}
```

**Response:**
```json
{
  "method": "pca",
  "dimensions": 2,
  "total_points": 150,
  "explained_variance": 0.85,
  "points": [
    {
      "x": 1.23,
      "y": -0.45,
      "z": null,
      "chunk_id": "doc1_chunk0",
      "chunk_index": 0,
      "document_id": 1,
      "document_name": "example.pdf",
      "text_preview": "First 100 characters..."
    }
  ]
}
```

**Notes:**
- PCA is fastest, good for initial exploration
- t-SNE preserves local structure, slower computation
- UMAP requires `umap-learn` package installation

---

### 3. Compute Similarity Matrix

Calculate pairwise cosine similarity between documents or chunks for heatmap visualization.

**Endpoint:** `POST /api/analytics/projects/{project_id}/similarity-matrix`

**Request Body:**
```json
{
  "scope": "document",       // "document" | "chunk"
  "document_ids": [1, 2],    // optional filter
  "max_items": 20            // max matrix size (2-100)
}
```

**Response:**
```json
{
  "scope": "document",
  "items": [
    {
      "id": "1",
      "label": "example.pdf"
    }
  ],
  "matrix": [
    [1.0, 0.85, 0.72],
    [0.85, 1.0, 0.68],
    [0.72, 0.68, 1.0]
  ]
}
```

**Notes:**
- Document-level scope averages embeddings per document
- Matrix is symmetric with 1.0 on diagonal
- Keep `max_items` ≤ 50 for performance

---

### 4. Get Embedding Statistics

Retrieve statistical metrics about project embeddings.

**Endpoint:** `GET /api/analytics/projects/{project_id}/embedding-stats`

**Response:**
```json
{
  "total_chunks": 250,
  "total_documents": 5,
  "embedding_dimension": 768,
  "embedding_model": "nomic-embed-text",
  "stats": {
    "mean_norm": 1.02,
    "std_norm": 0.15,
    "mean_similarity": 0.65,
    "min_similarity": 0.12,
    "max_similarity": 0.98
  },
  "document_breakdown": [
    {
      "document_id": 1,
      "document_name": "example.pdf",
      "chunk_count": 50,
      "avg_norm": 1.01
    }
  ]
}
```

---

### 5. Test Query Retrieval

Test RAG retrieval quality by querying embeddings and viewing ranked results.

**Endpoint:** `POST /api/analytics/projects/{project_id}/test-retrieval`

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "top_k": 10,               // number of results (1-20)
  "return_embeddings": false // include query embedding vector
}
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "query_embedding": null,
  "results": [
    {
      "chunk_id": "doc1_chunk5",
      "document_id": 1,
      "document_name": "ml_intro.pdf",
      "chunk_index": 5,
      "text": "Machine learning is...",
      "score": 0.92,         // cosine similarity
      "distance": 0.08       // 1 - score
    }
  ],
  "stats": {
    "avg_score": 0.78,
    "max_score": 0.92,
    "min_score": 0.65
  }
}
```

---

## Service Layer

The analytics endpoints are powered by `AnalyticsService` in `backend/services/analytics_service.py`.

### Key Methods

```python
class AnalyticsService:
    async def get_embeddings_for_project(
        db: AsyncSession,
        project_id: int,
        document_ids: Optional[List[int]] = None,
        limit: int = 500,
        include_text: bool = False
    ) -> List[EmbeddingData]

    def compute_dimensionality_reduction(
        embeddings: np.ndarray,
        method: str,
        dimensions: int,
        perplexity: int = 30,
        n_neighbors: int = 15
    ) -> np.ndarray

    def compute_similarity_matrix(
        embeddings: np.ndarray
    ) -> np.ndarray

    async def compute_embedding_statistics(
        db: AsyncSession,
        project_id: int
    ) -> Dict[str, Any]

    async def test_query_retrieval(
        project_id: int,
        query: str,
        top_k: int = 10,
        return_embeddings: bool = False
    ) -> Dict[str, Any]
```

### Dependencies

Analytics functionality requires these Python packages:
- `scikit-learn>=1.3.0` - PCA, t-SNE implementations
- `umap-learn>=0.5.5` - UMAP dimensionality reduction
- `numpy>=1.24.0` - Array operations

Install with:
```bash
pip install scikit-learn umap-learn numpy
```

---

## Performance Considerations

### Sampling
- Limit embeddings to 500-1000 for visualization
- Use `n_samples` parameter to control dataset size
- Larger samples = longer computation but better representation

### Caching
- Consider caching dimensionality reduction results
- t-SNE computation can take 10-60 seconds for 1000+ points
- PCA is fastest alternative for quick exploration

### Computation Costs
- **PCA:** O(n × d²) where n = samples, d = dimensions (fast)
- **t-SNE:** O(n² log n) (slowest, best local structure)
- **UMAP:** O(n^1.14) (good balance of speed and quality)
- **Similarity Matrix:** O(n²) for n items (quadratic growth)

### Recommendations
- Use PCA for quick initial exploration
- Use t-SNE for final visualization with ≤1000 points
- Keep similarity matrix ≤50×50 for responsiveness
- Enable text only when needed (increases payload size)

---

## Error Handling

All endpoints return standard HTTP status codes:
- `200 OK` - Successful request
- `400 Bad Request` - Invalid parameters or insufficient data
- `404 Not Found` - Project not found
- `500 Internal Server Error` - Server-side computation error

Example error response:
```json
{
  "detail": "Not enough embeddings for dimensionality reduction (need at least 2)"
}
```

---

## Example Usage

### Python
```python
import requests

# Get embeddings
response = requests.get(
    f"http://localhost:8000/api/analytics/projects/{project_id}/embeddings",
    params={"limit": 100, "include_text": True}
)
embeddings = response.json()

# Compute t-SNE
response = requests.post(
    f"http://localhost:8000/api/analytics/projects/{project_id}/dimensionality-reduction",
    json={
        "method": "tsne",
        "dimensions": 2,
        "n_samples": 500,
        "perplexity": 30
    }
)
tsne_data = response.json()
```

### TypeScript
```typescript
import analyticsApi from '@/lib/analytics-api';

// Get embeddings
const data = await analyticsApi.getEmbeddings(projectId, {
  limit: 500,
  include_text: true
});

// Compute PCA
const result = await analyticsApi.getDimensionalityReduction(projectId, {
  method: 'pca',
  dimensions: 2,
  n_samples: 500
});

// Test retrieval
const results = await analyticsApi.testRetrieval(projectId, {
  query: 'machine learning',
  top_k: 10
});
```

---

## Related Documentation

- **Frontend Components:** See `frontend/README/README.md` for analytics UI components
- **Vector Store:** See `backend/core/vectorstore.py` for embedding storage
- **RAG Pipeline:** See `backend/core/rag_pipeline.py` for retrieval implementation
