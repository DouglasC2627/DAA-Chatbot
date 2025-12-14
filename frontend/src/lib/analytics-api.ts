/**
 * Analytics API Client
 * Handles all requests to the analytics endpoints
 */

import axios from 'axios';
import type {
  EmbeddingsListResponse,
  DimReductionRequest,
  DimReductionResponse,
  SimilarityMatrixRequest,
  SimilarityMatrixResponse,
  EmbeddingStatsResponse,
  TestRetrievalRequest,
  TestRetrievalResponse,
} from '@/types/analytics';

// Use same axios instance configuration as main API
const API_BASE_URL = typeof window === 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  : '';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds for potentially long-running operations
});

// Request interceptor for adding auth tokens
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    if (config.data && !(config.data instanceof FormData) && !config.headers['Content-Type']) {
      config.headers['Content-Type'] = 'application/json';
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
    }
    return Promise.reject(error);
  }
);

/**
 * Analytics API endpoints
 */
export const analyticsApi = {
  /**
   * Get embeddings for a project
   */
  getEmbeddings: async (
    projectId: number,
    params?: {
      document_id?: number;
      limit?: number;
      include_text?: boolean;
    }
  ): Promise<EmbeddingsListResponse> => {
    const response = await apiClient.get<EmbeddingsListResponse>(
      `/api/analytics/projects/${projectId}/embeddings`,
      { params }
    );
    return response.data;
  },

  /**
   * Compute dimensionality reduction (t-SNE, UMAP, PCA)
   */
  getDimensionalityReduction: async (
    projectId: number,
    request: DimReductionRequest
  ): Promise<DimReductionResponse> => {
    const response = await apiClient.post<DimReductionResponse>(
      `/api/analytics/projects/${projectId}/dimensionality-reduction`,
      request
    );
    return response.data;
  },

  /**
   * Compute similarity matrix for heatmap
   */
  getSimilarityMatrix: async (
    projectId: number,
    request: SimilarityMatrixRequest
  ): Promise<SimilarityMatrixResponse> => {
    const response = await apiClient.post<SimilarityMatrixResponse>(
      `/api/analytics/projects/${projectId}/similarity-matrix`,
      request
    );
    return response.data;
  },

  /**
   * Get embedding statistics
   */
  getEmbeddingStats: async (
    projectId: number
  ): Promise<EmbeddingStatsResponse> => {
    const response = await apiClient.get<EmbeddingStatsResponse>(
      `/api/analytics/projects/${projectId}/embedding-stats`
    );
    return response.data;
  },

  /**
   * Test query retrieval
   */
  testRetrieval: async (
    projectId: number,
    request: TestRetrievalRequest
  ): Promise<TestRetrievalResponse> => {
    const response = await apiClient.post<TestRetrievalResponse>(
      `/api/analytics/projects/${projectId}/test-retrieval`,
      {
        query: request.query,
        top_k: request.top_k || 10,
        return_embeddings: request.return_embeddings || false,
      }
    );
    return response.data;
  },
};

export default analyticsApi;
