// Type definitions for DAA Chatbot

// ============================================================================
// Project Types
// ============================================================================

export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  document_count?: number;
  chat_count?: number;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
}

// ============================================================================
// Document Types
// ============================================================================

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  processing_status: DocumentStatus;
  error_message?: string;
  page_count?: number;
  word_count?: number;
  chunk_count?: number;
}

export enum DocumentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: DocumentStatus;
}

export interface BulkDocumentUploadResponse {
  documents: DocumentUploadResponse[];
  total: number;
  successful: number;
  failed: number;
}

// ============================================================================
// Chat Types
// ============================================================================

export interface Chat {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface Message {
  id: string;
  chat_id: string;
  role: MessageRole;
  content: string;
  sources?: SourceReference[];
  created_at: string;
  token_count?: number;
}

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
}

export interface SourceReference {
  document_id: string;
  document_name: string;
  chunk_index: number;
  page_number?: number;
  section?: string;
  content: string;
  similarity_score: number;
}

export interface SendMessageRequest {
  content: string;
  chat_id?: string;
}

export interface SendMessageResponse {
  message_id: string;
  chat_id: string;
  content: string;
  sources: SourceReference[];
}

// ============================================================================
// WebSocket Types
// ============================================================================

export interface WSMessage {
  type: WSMessageType;
  data: unknown;
}

export enum WSMessageType {
  MESSAGE_START = 'message_start',
  MESSAGE_CHUNK = 'message_chunk',
  MESSAGE_END = 'message_end',
  MESSAGE_ERROR = 'message_error',
  PROCESSING_UPDATE = 'processing_update',
  CONNECTION_ACK = 'connection_ack',
}

export interface MessageChunkData {
  chat_id: string;
  message_id: string;
  chunk: string;
  is_final: boolean;
}

export interface ProcessingUpdateData {
  document_id: string;
  status: DocumentStatus;
  progress: number;
  message?: string;
}

// ============================================================================
// Integration Types
// ============================================================================

export interface GoogleDriveFile {
  id: string;
  name: string;
  mimeType: string;
  size: number;
  modifiedTime: string;
}

export interface GoogleDriveImportRequest {
  file_ids: string[];
  project_id: string;
}

// ============================================================================
// System Types
// ============================================================================

export interface LLMModel {
  name: string;
  size: string;
  description?: string;
  parameters?: string;
}

export interface SystemStats {
  total_projects: number;
  total_documents: number;
  total_chats: number;
  storage_used: number;
  models_available: LLMModel[];
}

export interface SystemSettings {
  ollama_host: string;
  ollama_model: string;
  embedding_model: string;
  max_file_size: number;
  chunk_size: number;
  chunk_overlap: number;
  retrieval_k: number;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface APIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface ErrorResponse {
  error: string;
  message: string;
  status_code: number;
  details?: Record<string, unknown>;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface ErrorState {
  hasError: boolean;
  error?: string;
  details?: string;
}

export interface ToastConfig {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
  duration?: number;
}
