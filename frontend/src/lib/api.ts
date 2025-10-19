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
  APIResponse,
  PaginatedResponse,
  BulkDocumentUploadResponse,
} from '@/types';

// ============================================================================
// Axios Instance Configuration
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/projects/${id}`);
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
};

// ============================================================================
// Chat API
// ============================================================================

export const chatApi = {
  // List chats for a project
  list: async (projectId: number): Promise<Chat[]> => {
    const response = await apiClient.get<APIResponse<Chat[]>>(`/api/projects/${projectId}/chats`);
    return response.data.data || [];
  },

  // Get chat by ID
  get: async (id: number): Promise<Chat> => {
    const response = await apiClient.get<APIResponse<Chat>>(`/api/chats/${id}`);
    if (!response.data.data) {
      throw new Error('Chat not found');
    }
    return response.data.data;
  },

  // Create new chat
  create: async (projectId: number, title?: string): Promise<Chat> => {
    const response = await apiClient.post<APIResponse<Chat>>(`/api/projects/${projectId}/chats`, {
      title: title || 'New Chat',
    });
    if (!response.data.data) {
      throw new Error('Failed to create chat');
    }
    return response.data.data;
  },

  // Delete chat
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/chats/${id}`);
  },

  // Get chat history (messages)
  getHistory: async (chatId: number): Promise<Message[]> => {
    const response = await apiClient.get<APIResponse<Message[]>>(`/api/chats/${chatId}`);
    return response.data.data || [];
  },

  // Send message (non-streaming)
  sendMessage: async (chatId: number, data: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await apiClient.post<APIResponse<SendMessageResponse>>(
      `/api/chats/${chatId}/messages`,
      data
    );
    if (!response.data.data) {
      throw new Error('Failed to send message');
    }
    return response.data.data;
  },

  // Export chat
  export: async (id: number, format: 'md' | 'json' | 'pdf' = 'md'): Promise<Blob> => {
    const response = await apiClient.post(
      `/api/chats/${id}/export`,
      { format },
      { responseType: 'blob' }
    );
    return response.data;
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
  // List available LLM models
  listModels: async (): Promise<LLMModel[]> => {
    const response = await apiClient.get<APIResponse<LLMModel[]>>('/api/system/models');
    return response.data.data || [];
  },

  // Get system statistics
  getStats: async (): Promise<SystemStats> => {
    const response = await apiClient.get<APIResponse<SystemStats>>('/api/system/stats');
    if (!response.data.data) {
      throw new Error('Failed to fetch system stats');
    }
    return response.data.data;
  },

  // Update system settings
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

  // Health check
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
