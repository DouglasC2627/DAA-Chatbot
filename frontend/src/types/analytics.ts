/**
 * Type definitions for analytics features
 * Mirrors backend Pydantic models for type safety
 */

// Individual embedding data point
export interface EmbeddingData {
  chunk_id: string;
  document_id: number;
  document_name: string;
  chunk_index: number;
  embedding: number[];
  text?: string;
  metadata?: Record<string, any>;
}

// Response from embeddings list endpoint
export interface EmbeddingsListResponse {
  embeddings: EmbeddingData[];
  total: number;
  limit: number;
}

// Dimensionality reduction request parameters
export interface DimReductionRequest {
  method: 'tsne' | 'umap' | 'pca';
  dimensions: 2 | 3;
  document_ids?: number[];
  n_samples?: number;
  perplexity?: number;  // t-SNE
  n_neighbors?: number; // UMAP
}

// Single point in reduced dimensional space
export interface DimReductionPoint {
  x: number;
  y: number;
  z?: number;
  chunk_id: string;
  document_id: number;
  document_name: string;
  text_preview: string;
}

// Dimensionality reduction response
export interface DimReductionResponse {
  method: string;
  dimensions: number;
  points: DimReductionPoint[];
  total_points: number;
  explained_variance?: number;
}

// Similarity matrix request parameters
export interface SimilarityMatrixRequest {
  scope: 'document' | 'chunk';
  document_ids?: number[];
  max_items?: number;
}

// Item in similarity matrix
export interface SimilarityMatrixItem {
  id: string;
  label: string;
}

// Similarity matrix response
export interface SimilarityMatrixResponse {
  scope: string;
  items: SimilarityMatrixItem[];
  matrix: number[][];
}

// Embedding statistics response
export interface EmbeddingStatsResponse {
  total_chunks: number;
  total_documents: number;
  embedding_dimension: number;
  embedding_model: string;
  stats: {
    mean_norm: number;
    std_norm: number;
    min_norm: number;
    max_norm: number;
    avg_similarity: number;
  };
  document_breakdown: Array<{
    document_id: number;
    document_name: string;
    chunk_count: number;
    avg_norm: number;
    std_norm?: number;
  }>;
}

// Test retrieval request parameters
export interface TestRetrievalRequest {
  query: string;
  top_k?: number;
  return_embeddings?: boolean;
}

// Single retrieval result
export interface RetrievalResult {
  chunk_id: string;
  document_id: number;
  document_name: string;
  chunk_index: number;
  text: string;
  score: number;
  distance: number;
}

// Test retrieval response
export interface TestRetrievalResponse {
  query: string;
  query_embedding?: number[];
  results: RetrievalResult[];
  stats: {
    avg_score: number;
    min_score: number;
    max_score: number;
    score_distribution: number[];
  };
}

// UI-specific types

export type ReductionMethod = 'tsne' | 'umap' | 'pca';
export type VisualizationDimensions = 2 | 3;
export type SimilarityScope = 'document' | 'chunk';
export type ColorMode = 'document' | 'similarity';

export interface VisualizationSettings {
  method: ReductionMethod;
  dimensions: VisualizationDimensions;
  colorMode: ColorMode;
  selectedDocuments: number[];
}

export interface HeatmapSettings {
  scope: SimilarityScope;
  selectedDocuments: number[];
  maxItems: number;
}

export interface RetrievalTestSettings {
  query: string;
  topK: number;
  returnEmbeddings: boolean;
}
