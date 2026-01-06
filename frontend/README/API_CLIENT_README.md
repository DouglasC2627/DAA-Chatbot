# API Client Documentation

This document provides comprehensive documentation for the frontend API client, data fetching strategies, and backend integration.

## Table of Contents

- [Overview](#overview)
- [API Client Setup](#api-client-setup)
- [HTTP Client (Axios)](#http-client-axios)
- [React Query Integration](#react-query-integration)
- [WebSocket Client](#websocket-client)
- [API Functions](#api-functions)
  - [Projects API](#projects-api)
  - [Documents API](#documents-api)
  - [Chat API](#chat-api)
  - [Analytics API](#analytics-api)
- [Error Handling](#error-handling)
- [Request/Response Interceptors](#requestresponse-interceptors)
- [Best Practices](#best-practices)

## Overview

The frontend communicates with the FastAPI backend through:
- **HTTP REST API** for CRUD operations (using Axios + React Query)
- **WebSocket** for real-time chat streaming (using Socket.IO)

**Technology Stack:**
- **Axios** (1.12+): HTTP client
- **TanStack Query** (React Query 5.x): Server state management
- **Socket.IO Client** (4.8+): WebSocket communication

## API Client Setup

### Environment Configuration

**File:** `.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**Access in code:**
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const WS_URL = process.env.NEXT_PUBLIC_WS_URL;
```

### Base Configuration

**File:** `src/lib/config.ts`

```typescript
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  isDevelopment: process.env.NODE_ENV === 'development',
} as const;
```

---

## HTTP Client (Axios)

### Axios Instance

**File:** `src/lib/api.ts`

```typescript
import axios, { AxiosError } from 'axios';
import { config } from './config';

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: config.apiUrl,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log requests in development
    if (config.isDevelopment) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Log responses in development
    if (config.isDevelopment) {
      console.log(`[API Response] ${response.config.url}`, response.data);
    }
    return response;
  },
  (error: AxiosError) => {
    // Handle errors globally
    handleApiError(error);
    return Promise.reject(error);
  }
);
```

### Error Handler

```typescript
function handleApiError(error: AxiosError) {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.detail || error.message;

    switch (status) {
      case 400:
        toast.error(`Bad Request: ${message}`);
        break;
      case 401:
        toast.error('Unauthorized. Please log in.');
        // Redirect to login
        break;
      case 404:
        toast.error('Resource not found');
        break;
      case 500:
        toast.error('Server error. Please try again later.');
        break;
      default:
        toast.error(`Error: ${message}`);
    }
  } else if (error.request) {
    // Request made but no response
    toast.error('Network error. Please check your connection.');
  } else {
    // Error setting up request
    toast.error('An unexpected error occurred');
  }
}
```

---

## React Query Integration

### QueryClient Setup

**File:** `src/components/providers/QueryProvider.tsx`

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            retry: 1,
            refetchOnWindowFocus: false,
          },
          mutations: {
            onError: (error) => {
              console.error('Mutation error:', error);
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### Query Keys

**File:** `src/lib/queryKeys.ts`

```typescript
export const queryKeys = {
  // Projects
  projects: ['projects'] as const,
  project: (id: number) => ['project', id] as const,
  projectStats: (id: number) => ['project', id, 'stats'] as const,

  // Documents
  documents: (projectId: number) => ['documents', projectId] as const,
  document: (id: number) => ['document', id] as const,

  // Chats
  chats: (projectId: number) => ['chats', projectId] as const,
  chat: (id: number) => ['chat', id] as const,
  messages: (chatId: number) => ['messages', chatId] as const,

  // Analytics
  embeddings: (projectId: number, method: string, dims: number) =>
    ['embeddings', projectId, method, dims] as const,
  similarity: (projectId: number, level: string) =>
    ['similarity', projectId, level] as const,
} as const;
```

---

## API Functions

### Projects API

**File:** `src/lib/api.ts`

#### Get All Projects

```typescript
export interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  document_count: number;
  chat_count: number;
}

export async function getProjects(): Promise<Project[]> {
  const response = await apiClient.get('/api/projects');
  return response.data;
}

// React Query hook
export function useProjects() {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: getProjects,
  });
}
```

#### Get Single Project

```typescript
export async function getProject(id: number): Promise<Project> {
  const response = await apiClient.get(`/api/projects/${id}`);
  return response.data;
}

// React Query hook
export function useProject(id: number) {
  return useQuery({
    queryKey: queryKeys.project(id),
    queryFn: () => getProject(id),
    enabled: !!id,
  });
}
```

#### Create Project

```typescript
export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export async function createProject(
  data: CreateProjectRequest
): Promise<Project> {
  const response = await apiClient.post('/api/projects', data);
  return response.data;
}

// React Query mutation hook
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      // Invalidate projects query to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      toast.success('Project created successfully');
    },
  });
}
```

#### Update Project

```typescript
export interface UpdateProjectRequest {
  name?: string;
  description?: string;
}

export async function updateProject(
  id: number,
  data: UpdateProjectRequest
): Promise<Project> {
  const response = await apiClient.put(`/api/projects/${id}`, data);
  return response.data;
}

// React Query mutation hook
export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateProjectRequest }) =>
      updateProject(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.project(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      toast.success('Project updated');
    },
  });
}
```

#### Delete Project

```typescript
export async function deleteProject(id: number): Promise<void> {
  await apiClient.delete(`/api/projects/${id}`);
}

// React Query mutation hook
export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      toast.success('Project deleted');
    },
  });
}
```

---

### Documents API

#### Upload Document

```typescript
export async function uploadDocument(
  projectId: number,
  file: File
): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post(
    `/api/projects/${projectId}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
}

// React Query mutation hook with progress
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      file,
      onProgress,
    }: {
      projectId: number;
      file: File;
      onProgress?: (progress: number) => void;
    }) => {
      const formData = new FormData();
      formData.append('file', file);

      return apiClient.post(`/api/projects/${projectId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          onProgress?.(percentCompleted);
        },
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents(variables.projectId),
      });
      toast.success('Document uploaded successfully');
    },
  });
}
```

#### Get Documents

```typescript
export interface Document {
  id: number;
  project_id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: 'processing' | 'completed' | 'failed';
  created_at: string;
  processed_at: string | null;
  metadata?: Record<string, any>;
}

export async function getDocuments(projectId: number): Promise<Document[]> {
  const response = await apiClient.get(`/api/projects/${projectId}/documents`);
  return response.data;
}

// React Query hook
export function useDocuments(projectId: number) {
  return useQuery({
    queryKey: queryKeys.documents(projectId),
    queryFn: () => getDocuments(projectId),
    enabled: !!projectId,
  });
}
```

#### Delete Document

```typescript
export async function deleteDocument(id: number): Promise<void> {
  await apiClient.delete(`/api/documents/${id}`);
}

// React Query mutation hook
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document deleted');
    },
  });
}
```

---

### Chat API

#### Get Chats

```typescript
export interface Chat {
  id: number;
  project_id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export async function getChats(projectId: number): Promise<Chat[]> {
  const response = await apiClient.get(`/api/projects/${projectId}/chats`);
  return response.data;
}

// React Query hook
export function useChats(projectId: number) {
  return useQuery({
    queryKey: queryKeys.chats(projectId),
    queryFn: () => getChats(projectId),
    enabled: !!projectId,
  });
}
```

#### Get Messages

```typescript
export interface Message {
  id: number;
  chat_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  metadata?: {
    sources?: SourceReference[];
  };
}

export async function getMessages(chatId: number): Promise<Message[]> {
  const response = await apiClient.get(`/api/chats/${chatId}/messages`);
  return response.data;
}

// React Query hook
export function useMessages(chatId: number) {
  return useQuery({
    queryKey: queryKeys.messages(chatId),
    queryFn: () => getMessages(chatId),
    enabled: !!chatId,
    // Refetch less frequently since WebSocket handles updates
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

#### Create Chat

```typescript
export async function createChat(
  projectId: number,
  title: string
): Promise<Chat> {
  const response = await apiClient.post(`/api/projects/${projectId}/chats`, {
    title,
  });
  return response.data;
}

// React Query mutation hook
export function useCreateChat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, title }: { projectId: number; title: string }) =>
      createChat(projectId, title),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.chats(variables.projectId),
      });
      toast.success('Chat created');
    },
  });
}
```

---

### Analytics API

**File:** `src/lib/analytics-api.ts`

#### Get Embeddings

```typescript
export interface EmbeddingPoint {
  chunk_id: string;
  document_id: number;
  document_name: string;
  chunk_index: number;
  text: string;
  coordinates: number[]; // [x, y] or [x, y, z]
  norm: number;
}

export interface EmbeddingsResponse {
  embeddings: EmbeddingPoint[];
  method: string;
  dimensions: number;
  stats: {
    total_chunks: number;
    total_documents: number;
    avg_norm: number;
    std_norm: number;
  };
}

export async function getEmbeddings(
  projectId: number,
  method: 'pca' | 'tsne' | 'umap' = 'pca',
  dimensions: 2 | 3 = 2
): Promise<EmbeddingsResponse> {
  const response = await apiClient.get(
    `/api/projects/${projectId}/analytics/embeddings`,
    {
      params: { reduction_method: method, dimensions },
    }
  );
  return response.data;
}

// React Query hook
export function useEmbeddings(
  projectId: number,
  method: 'pca' | 'tsne' | 'umap',
  dimensions: 2 | 3
) {
  return useQuery({
    queryKey: queryKeys.embeddings(projectId, method, dimensions),
    queryFn: () => getEmbeddings(projectId, method, dimensions),
    enabled: !!projectId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}
```

#### Get Similarity Matrix

```typescript
export interface SimilarityMatrixResponse {
  similarity_matrix: number[][];
  labels: string[];
  level: 'document' | 'chunk';
  method: 'cosine';
}

export async function getSimilarityMatrix(
  projectId: number,
  level: 'document' | 'chunk' = 'document',
  limit: number = 50
): Promise<SimilarityMatrixResponse> {
  const response = await apiClient.get(
    `/api/projects/${projectId}/analytics/similarity`,
    {
      params: { level, limit },
    }
  );
  return response.data;
}

// React Query hook
export function useSimilarityMatrix(
  projectId: number,
  level: 'document' | 'chunk'
) {
  return useQuery({
    queryKey: queryKeys.similarity(projectId, level),
    queryFn: () => getSimilarityMatrix(projectId, level),
    enabled: !!projectId,
  });
}
```

---

## WebSocket Client

**File:** `src/lib/websocket.ts`

### Socket.IO Setup

```typescript
import { io, Socket } from 'socket.io-client';
import { config } from './config';

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    socket = io(config.wsUrl, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    // Connection events
    socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  return socket;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}
```

### WebSocket Hook

**File:** `src/hooks/useWebSocket.ts`

```typescript
import { useEffect, useState } from 'react';
import { getSocket } from '@/lib/websocket';

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const socket = getSocket();

  useEffect(() => {
    function onConnect() {
      setIsConnected(true);
    }

    function onDisconnect() {
      setIsConnected(false);
    }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
    };
  }, [socket]);

  return { socket, isConnected };
}
```

### Chat Streaming

```typescript
export function useChatStream(chatId: number) {
  const { socket, isConnected } = useWebSocket();
  const [isStreaming, setIsStreaming] = useState(false);
  const queryClient = useQueryClient();

  const sendMessage = useCallback(
    (message: string, projectId: number) => {
      if (!isConnected) {
        toast.error('Not connected to server');
        return;
      }

      setIsStreaming(true);

      // Emit message
      socket.emit('send_message', {
        chat_id: chatId,
        message,
        project_id: projectId,
      });
    },
    [socket, isConnected, chatId]
  );

  useEffect(() => {
    if (!socket) return;

    function onMessageChunk(data: { chat_id: number; chunk: string }) {
      if (data.chat_id === chatId) {
        // Update streaming message in store
        useChatStore.getState().appendStreamingChunk(data.chunk);
      }
    }

    function onMessageComplete(data: {
      chat_id: number;
      message_id: number;
      content: string;
      sources: any[];
    }) {
      if (data.chat_id === chatId) {
        setIsStreaming(false);

        // Clear streaming state
        useChatStore.getState().clearStreaming();

        // Invalidate messages query to refetch
        queryClient.invalidateQueries({
          queryKey: queryKeys.messages(chatId),
        });
      }
    }

    function onError(data: { error: string; chat_id: number }) {
      if (data.chat_id === chatId) {
        setIsStreaming(false);
        toast.error(data.error);
      }
    }

    socket.on('message_chunk', onMessageChunk);
    socket.on('message_complete', onMessageComplete);
    socket.on('error', onError);

    return () => {
      socket.off('message_chunk', onMessageChunk);
      socket.off('message_complete', onMessageComplete);
      socket.off('error', onError);
    };
  }, [socket, chatId, queryClient]);

  return { sendMessage, isStreaming };
}
```

---

## Error Handling

### Custom Error Types

```typescript
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error') {
    super(message);
    this.name = 'NetworkError';
  }
}
```

### Error Boundary

```typescript
'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-4">
            <h2>Something went wrong</h2>
            <p>{this.state.error?.message}</p>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
```

---

## Best Practices

### 1. Use Query Keys Consistently

```typescript
// ✅ Good: Centralized query keys
const { data } = useQuery({
  queryKey: queryKeys.project(id),
  queryFn: () => getProject(id),
});

// ❌ Bad: Inline query keys
const { data } = useQuery({
  queryKey: ['project', id],
  queryFn: () => getProject(id),
});
```

### 2. Handle Loading and Error States

```typescript
// ✅ Good
function MyComponent() {
  const { data, isLoading, error } = useProjects();

  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;

  return <ProjectList projects={data} />;
}
```

### 3. Optimistic Updates

```typescript
const mutation = useMutation({
  mutationFn: updateProject,
  onMutate: async (newData) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: queryKeys.project(id) });

    // Snapshot previous value
    const previous = queryClient.getQueryData(queryKeys.project(id));

    // Optimistically update
    queryClient.setQueryData(queryKeys.project(id), newData);

    return { previous };
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(queryKeys.project(id), context?.previous);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.project(id) });
  },
});
```

### 4. Request Cancellation

```typescript
const { data } = useQuery({
  queryKey: ['search', searchTerm],
  queryFn: async ({ signal }) => {
    const response = await apiClient.get('/api/search', {
      params: { q: searchTerm },
      signal, // Pass abort signal
    });
    return response.data;
  },
});
```

### 5. Type Safety

```typescript
// ✅ Good: Full type safety
async function getProject(id: number): Promise<Project> {
  const response = await apiClient.get<Project>(`/api/projects/${id}`);
  return response.data;
}

// ❌ Bad: No types
async function getProject(id) {
  const response = await apiClient.get(`/api/projects/${id}`);
  return response.data;
}
```

---

## Additional Resources

- [Axios Documentation](https://axios-http.com/docs/intro)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Socket.IO Client Documentation](https://socket.io/docs/v4/client-api/)
- [React Query Best Practices](https://tkdodo.eu/blog/practical-react-query)
