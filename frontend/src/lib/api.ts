// API Client for DAA Chatbot Backend
import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  Document,
  Chat,
  Message,
  SendMessageRequest,
  SendMessageResponse,
  GoogleDriveFile,
  GoogleDriveImportRequest,
  LLMModel,
  SystemStats,
  SystemSettings,
  UserSettings,
  InstalledModels,
  PopularModel,
  APIResponse,
  PaginatedResponse,
  BulkDocumentUploadResponse,
} from '@/types';

// ============================================================================
// Axios Instance Configuration
// ============================================================================

// Use relative URL in browser to leverage Next.js rewrites, direct URL in SSR
const API_BASE_URL = typeof window === 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  : ''; // Empty string makes axios use relative URLs

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
});

// Request interceptor for adding auth tokens and Content-Type
apiClient.interceptors.request.use(
  (config) => {
    // Add JWT token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Set Content-Type for JSON requests if not already set
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
  (error: AxiosError) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token');
      // You can dispatch a logout action here if needed
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// Project API
// ============================================================================

export const projectApi = {
  // List all projects
  list: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/api/projects');
    return response.data || [];
  },

  // Get project by ID
  get: async (id: number): Promise<Project> => {
    const response = await apiClient.get<Project>(`/api/projects/${id}`);
    if (!response.data) {
      throw new Error('Project not found');
    }
    return response.data;
  },

  // Create new project
  create: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await apiClient.post<Project>('/api/projects', data);
    if (!response.data) {
      throw new Error('Failed to create project');
    }
    return response.data;
  },

  // Update project
  update: async (id: number, data: UpdateProjectRequest): Promise<Project> => {
    const response = await apiClient.put<Project>(`/api/projects/${id}`, data);
    if (!response.data) {
      throw new Error('Failed to update project');
    }
    return response.data;
  },

  // Delete project
  delete: async (id: number, hardDelete: boolean = true): Promise<void> => {
    await apiClient.delete(`/api/projects/${id}`, {
      params: { hard_delete: hardDelete },
    });
  },

  // Export project
  export: async (id: number): Promise<Blob> => {
    const response = await apiClient.post(
      `/api/projects/${id}/export`,
      {},
      { responseType: 'blob' }
    );
    return response.data;
  },

  // Import project
  import: async (file: File): Promise<Project> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<APIResponse<Project>>('/api/projects/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    if (!response.data.data) {
      throw new Error('Failed to import project');
    }
    return response.data.data;
  },
};

// ============================================================================
// Document API
// ============================================================================

export const documentApi = {
  // List documents for a project
  list: async (projectId: number): Promise<any[]> => {
    const response = await apiClient.get(`/api/projects/${projectId}/documents`);
    return response.data || [];
  },

  // Get document by ID
  get: async (id: number): Promise<any> => {
    const response = await apiClient.get(`/api/documents/${id}`);
    return response.data;
  },

  // Upload documents to a project
  upload: async (projectId: number, files: File[]): Promise<BulkDocumentUploadResponse> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await apiClient.post(`/api/projects/${projectId}/documents/bulk`, formData);

    return response.data;
  },

  // Delete document
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/documents/${id}`);
  },

  // Get document content
  getContent: async (id: number): Promise<string> => {
    const response = await apiClient.get<APIResponse<{ content: string }>>(
      `/api/documents/${id}/content`
    );
    return response.data.data?.content || '';
  },

  // Process uploaded documents
  process: async (documentIds: number[]): Promise<void> => {
    await apiClient.post('/api/documents/process', { document_ids: documentIds });
  },

  // Download document file
  download: async (id: number): Promise<Blob> => {
    const response = await apiClient.get(`/api/documents/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// ============================================================================
// Chat API
// ============================================================================

export const chatApi = {
  // List chats for a project
  list: async (projectId: number): Promise<Chat[]> => {
    const response = await apiClient.get<Chat[]>(`/api/projects/${projectId}/chats`);
    return response.data || [];
  },

  // Get chat by ID
  get: async (id: number): Promise<Chat> => {
    const response = await apiClient.get<Chat>(`/api/chats/${id}`);
    if (!response.data) {
      throw new Error('Chat not found');
    }
    return response.data;
  },

  // Create new chat
  create: async (projectId: number, title?: string): Promise<Chat> => {
    const response = await apiClient.post<Chat>(`/api/chats`, {
      project_id: projectId,
      title: title || 'New Chat',
    });
    if (!response.data) {
      throw new Error('Failed to create chat');
    }
    return response.data;
  },

  // Delete chat
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/chats/${id}`);
  },

  // Get chat history (messages)
  getHistory: async (chatId: number): Promise<Message[]> => {
    const response = await apiClient.get<Message[]>(`/api/chats/${chatId}/messages`);
    return response.data || [];
  },

  // Send message (non-streaming)
  sendMessage: async (chatId: number, data: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await apiClient.post<SendMessageResponse>(
      `/api/chats/${chatId}/messages`,
      data
    );
    if (!response.data) {
      throw new Error('Failed to send message');
    }
    return response.data;
  },

  // Update chat
  update: async (id: number, title: string): Promise<Chat> => {
    const response = await apiClient.put<Chat>(`/api/chats/${id}`, {
      title,
    });
    if (!response.data) {
      throw new Error('Failed to update chat');
    }
    return response.data;
  },

  // Search chats
  search: async (projectId: number, query: string): Promise<Chat[]> => {
    const response = await apiClient.get<Chat[]>(`/api/projects/${projectId}/chats/search`, {
      params: { q: query },
    });
    return response.data || [];
  },

  // Export chat as Markdown
  exportMarkdown: async (id: number): Promise<void> => {
    const response = await apiClient.get(`/api/chats/${id}/export/markdown`, {
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `chat_${id}.md`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // Export chat as JSON
  exportJSON: async (id: number): Promise<void> => {
    const response = await apiClient.get(`/api/chats/${id}/export/json`, {
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `chat_${id}.json`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

// ============================================================================
// Integration API
// ============================================================================

export const integrationApi = {
  // List available integrations
  list: async (): Promise<string[]> => {
    const response = await apiClient.get<APIResponse<string[]>>('/api/integrations');
    return response.data.data || [];
  },

  // Google Drive OAuth
  googleAuth: async (): Promise<{ auth_url: string }> => {
    const response = await apiClient.post<APIResponse<{ auth_url: string }>>(
      '/api/integrations/google/auth'
    );
    if (!response.data.data) {
      throw new Error('Failed to initiate Google auth');
    }
    return response.data.data;
  },

  // List Google Drive files
  googleListFiles: async (): Promise<GoogleDriveFile[]> => {
    const response = await apiClient.get<APIResponse<GoogleDriveFile[]>>(
      '/api/integrations/google/files'
    );
    return response.data.data || [];
  },

  // Import from Google Drive
  googleImport: async (data: GoogleDriveImportRequest): Promise<BulkDocumentUploadResponse> => {
    const response = await apiClient.post<APIResponse<BulkDocumentUploadResponse>>(
      '/api/integrations/google/import',
      data
    );
    if (!response.data.data) {
      throw new Error('Failed to import from Google Drive');
    }
    return response.data.data;
  },
};

// ============================================================================
// System API
// ============================================================================

export const systemApi = {
  // Get current settings from database
  getSettings: async (): Promise<UserSettings> => {
    const response = await apiClient.get<UserSettings>('/api/settings');
    return response.data;
  },

  // Update model settings
  updateModels: async (data: {
    llm_model?: string;
    embedding_model?: string;
  }): Promise<UserSettings> => {
    const response = await apiClient.put<UserSettings>('/api/settings/models', data);
    return response.data;
  },

  // Get installed models
  getInstalledModels: async (): Promise<InstalledModels> => {
    const response = await apiClient.get<InstalledModels>('/api/settings/models/installed');
    return response.data;
  },

  // Get popular models
  getPopularModels: async (): Promise<{
    llm_models: PopularModel[];
    embedding_models: PopularModel[];
  }> => {
    const response = await apiClient.get('/api/settings/models/popular');
    return response.data;
  },

  // Install a model
  pullModel: async (modelName: string): Promise<void> => {
    await apiClient.post('/api/settings/models/pull', { model_name: modelName });
  },

  // Search for models
  searchModels: async (query: string, modelType?: 'llm' | 'embedding'): Promise<PopularModel[]> => {
    const params = new URLSearchParams({ query });
    if (modelType) {
      params.append('model_type', modelType);
    }
    const response = await apiClient.get(`/api/settings/models/search?${params.toString()}`);
    return response.data;
  },

  // Legacy methods (kept for compatibility)
  listModels: async (): Promise<LLMModel[]> => {
    const response = await apiClient.get<APIResponse<LLMModel[]>>('/api/system/models');
    return response.data.data || [];
  },

  getStats: async (): Promise<SystemStats> => {
    const response = await apiClient.get<APIResponse<SystemStats>>('/api/system/stats');
    if (!response.data.data) {
      throw new Error('Failed to fetch system stats');
    }
    return response.data.data;
  },

  updateSettings: async (settings: Partial<SystemSettings>): Promise<SystemSettings> => {
    const response = await apiClient.post<APIResponse<SystemSettings>>(
      '/api/system/settings',
      settings
    );
    if (!response.data.data) {
      throw new Error('Failed to update settings');
    }
    return response.data.data;
  },

  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    const response =
      await apiClient.get<APIResponse<{ status: string; timestamp: string }>>('/api/health');
    if (!response.data.data) {
      throw new Error('Health check failed');
    }
    return response.data.data;
  },
};

// ============================================================================
// Export API client and all API modules
// ============================================================================

export default apiClient;

export const api = {
  projects: projectApi,
  documents: documentApi,
  chats: chatApi,
  integrations: integrationApi,
  system: systemApi,
};
