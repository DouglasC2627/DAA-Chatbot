// WebSocket Client for Real-time Communication with Socket.IO
import { io, Socket } from 'socket.io-client';
import { useEffect, useState, useCallback } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface SourceDocument {
  id: string;
  content: string;
  metadata: Record<string, any>;
  score: number;
}

export interface MessageTokenEvent {
  chat_id: number;
  token: string;
}

export interface MessageSourcesEvent {
  chat_id: number;
  sources: SourceDocument[];
}

export interface MessageCompleteEvent {
  chat_id: number;
  metadata: {
    model: string;
    sources_count: number;
  };
}

export interface DocumentStatusEvent {
  document_id: number;
  status: 'processing' | 'completed' | 'failed';
  progress?: number;
}

export interface ProjectUpdateEvent {
  type: string;
  data: Record<string, any>;
}

export interface ErrorEvent {
  message: string;
  chat_id?: number;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'reconnecting' | 'error';

// ============================================================================
// WebSocket Configuration
// ============================================================================

const WS_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// WebSocket Client Class
// ============================================================================

class WebSocketClient {
  private socket: Socket | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private currentProjectId: number | null = null;
  private connectionStatus: ConnectionStatus = 'disconnected';

  // Event handlers
  private statusChangeHandlers: ((status: ConnectionStatus) => void)[] = [];
  private messageTokenHandlers: ((data: MessageTokenEvent) => void)[] = [];
  private messageSourcesHandlers: ((data: MessageSourcesEvent) => void)[] = [];
  private messageCompleteHandlers: ((data: MessageCompleteEvent) => void)[] = [];
  private documentStatusHandlers: ((data: DocumentStatusEvent) => void)[] = [];
  private projectUpdateHandlers: ((data: ProjectUpdateEvent) => void)[] = [];
  private errorHandlers: ((data: ErrorEvent) => void)[] = [];

  // ============================================================================
  // Connection Management
  // ============================================================================

  connect(auth?: { token?: string }): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;
      this.updateStatus('connecting');

      this.socket = io(WS_URL, {
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        reconnectionDelayMax: 5000,
        auth: auth || {},
      });

      this.setupSocketListeners();

      this.socket.on('connect', () => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.updateStatus('connected');
        console.log('[WebSocket] Connected:', this.socket?.id);
        resolve();
      });

      this.socket.on('connect_error', (error: Error) => {
        console.error('[WebSocket] Connection error:', error);
        this.isConnecting = false;
        this.reconnectAttempts++;

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          this.updateStatus('error');
          const errorMessage = `Failed to connect after ${this.maxReconnectAttempts} attempts`;
          this.errorHandlers.forEach((handler) => handler({ message: errorMessage }));
          reject(new Error(errorMessage));
        } else {
          this.updateStatus('reconnecting');
        }
      });

      // Set timeout for initial connection
      setTimeout(() => {
        if (this.isConnecting) {
          this.isConnecting = false;
          this.updateStatus('error');
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });
  }

  disconnect(): void {
    if (this.socket) {
      // Leave current project if joined
      if (this.currentProjectId !== null) {
        this.leaveProject(this.currentProjectId);
      }

      this.socket.disconnect();
      this.socket = null;
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.currentProjectId = null;
      this.updateStatus('disconnected');
      console.log('[WebSocket] Disconnected');
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getStatus(): ConnectionStatus {
    return this.connectionStatus;
  }

  private updateStatus(status: ConnectionStatus): void {
    this.connectionStatus = status;
    this.statusChangeHandlers.forEach((handler) => handler(status));
  }

  // ============================================================================
  // Socket Event Listeners
  // ============================================================================

  private setupSocketListeners(): void {
    if (!this.socket) return;

    // Connection status
    this.socket.on('connection_status', (data: { status: string }) => {
      console.log('[WebSocket] Connection status:', data.status);
    });

    // Message streaming events
    this.socket.on('message_received', (data: { chat_id: number; status: string }) => {
      console.log('[WebSocket] Message received:', data);
    });

    this.socket.on('message_sources', (data: MessageSourcesEvent) => {
      console.log('[WebSocket] Message sources:', data);
      this.messageSourcesHandlers.forEach((handler) => handler(data));
    });

    this.socket.on('message_token', (data: MessageTokenEvent) => {
      this.messageTokenHandlers.forEach((handler) => handler(data));
    });

    this.socket.on('message_complete', (data: MessageCompleteEvent) => {
      console.log('[WebSocket] Message complete:', data);
      this.messageCompleteHandlers.forEach((handler) => handler(data));
    });

    // Project room events
    this.socket.on('project_joined', (data: { project_id: number; status: string }) => {
      console.log('[WebSocket] Joined project:', data.project_id);
      this.currentProjectId = data.project_id;
    });

    this.socket.on('project_left', (data: { project_id: number; status: string }) => {
      console.log('[WebSocket] Left project:', data.project_id);
      this.currentProjectId = null;
    });

    // Real-time updates
    this.socket.on('document_status', (data: DocumentStatusEvent) => {
      console.log('[WebSocket] Document status:', data);
      this.documentStatusHandlers.forEach((handler) => handler(data));
    });

    this.socket.on('project_update', (data: ProjectUpdateEvent) => {
      console.log('[WebSocket] Project update:', data);
      this.projectUpdateHandlers.forEach((handler) => handler(data));
    });

    // Ping/pong for health check
    this.socket.on('pong', (data: { timestamp: number }) => {
      const latency = Date.now() - data.timestamp;
      console.log('[WebSocket] Pong received, latency:', latency, 'ms');
    });

    // Error handling
    this.socket.on('error', (data: ErrorEvent) => {
      console.error('[WebSocket] Error:', data.message);
      this.errorHandlers.forEach((handler) => handler(data));
    });

    // Disconnection
    this.socket.on('disconnect', (reason: string) => {
      console.log('[WebSocket] Disconnected:', reason);
      this.updateStatus('disconnected');

      if (reason === 'io server disconnect') {
        // Server initiated disconnect, reconnect manually
        this.connect();
      }
    });

    // Reconnection events
    this.socket.on('reconnect_attempt', (attemptNumber: number) => {
      console.log('[WebSocket] Reconnect attempt:', attemptNumber);
      this.updateStatus('reconnecting');
    });

    this.socket.on('reconnect', (attemptNumber: number) => {
      console.log('[WebSocket] Reconnected after', attemptNumber, 'attempts');
      this.reconnectAttempts = 0;
      this.updateStatus('connected');

      // Rejoin project if we were in one
      if (this.currentProjectId !== null) {
        this.joinProject(this.currentProjectId);
      }
    });

    this.socket.on('reconnect_failed', () => {
      console.error('[WebSocket] Reconnection failed');
      this.updateStatus('error');
    });
  }

  // ============================================================================
  // Project Room Management
  // ============================================================================

  joinProject(projectId: number): void {
    if (!this.socket?.connected) {
      console.warn('[WebSocket] Cannot join project: not connected');
      return;
    }

    console.log('[WebSocket] Joining project:', projectId);
    this.socket.emit('join_project', { project_id: projectId });
  }

  leaveProject(projectId: number): void {
    if (!this.socket?.connected) {
      console.warn('[WebSocket] Cannot leave project: not connected');
      return;
    }

    console.log('[WebSocket] Leaving project:', projectId);
    this.socket.emit('leave_project', { project_id: projectId });
    this.currentProjectId = null;
  }

  // ============================================================================
  // Message Sending
  // ============================================================================

  sendMessage(data: {
    chat_id: number;
    message: string;
    model?: string;
    temperature?: number;
    include_history?: boolean;
  }): void {
    if (!this.socket?.connected) {
      throw new Error('WebSocket not connected');
    }

    console.log('[WebSocket] Sending message:', data);
    this.socket.emit('send_message', data);
  }

  ping(): void {
    if (!this.socket?.connected) {
      console.warn('[WebSocket] Cannot ping: not connected');
      return;
    }

    this.socket.emit('ping', {});
  }

  // ============================================================================
  // Event Handler Registration
  // ============================================================================

  onStatusChange(handler: (status: ConnectionStatus) => void): () => void {
    this.statusChangeHandlers.push(handler);
    // Immediately call with current status
    handler(this.connectionStatus);

    return () => {
      const index = this.statusChangeHandlers.indexOf(handler);
      if (index > -1) {
        this.statusChangeHandlers.splice(index, 1);
      }
    };
  }

  onMessageToken(handler: (data: MessageTokenEvent) => void): () => void {
    this.messageTokenHandlers.push(handler);
    return () => {
      const index = this.messageTokenHandlers.indexOf(handler);
      if (index > -1) {
        this.messageTokenHandlers.splice(index, 1);
      }
    };
  }

  onMessageSources(handler: (data: MessageSourcesEvent) => void): () => void {
    this.messageSourcesHandlers.push(handler);
    return () => {
      const index = this.messageSourcesHandlers.indexOf(handler);
      if (index > -1) {
        this.messageSourcesHandlers.splice(index, 1);
      }
    };
  }

  onMessageComplete(handler: (data: MessageCompleteEvent) => void): () => void {
    this.messageCompleteHandlers.push(handler);
    return () => {
      const index = this.messageCompleteHandlers.indexOf(handler);
      if (index > -1) {
        this.messageCompleteHandlers.splice(index, 1);
      }
    };
  }

  onDocumentStatus(handler: (data: DocumentStatusEvent) => void): () => void {
    this.documentStatusHandlers.push(handler);
    return () => {
      const index = this.documentStatusHandlers.indexOf(handler);
      if (index > -1) {
        this.documentStatusHandlers.splice(index, 1);
      }
    };
  }

  onProjectUpdate(handler: (data: ProjectUpdateEvent) => void): () => void {
    this.projectUpdateHandlers.push(handler);
    return () => {
      const index = this.projectUpdateHandlers.indexOf(handler);
      if (index > -1) {
        this.projectUpdateHandlers.splice(index, 1);
      }
    };
  }

  onError(handler: (data: ErrorEvent) => void): () => void {
    this.errorHandlers.push(handler);
    return () => {
      const index = this.errorHandlers.indexOf(handler);
      if (index > -1) {
        this.errorHandlers.splice(index, 1);
      }
    };
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

const wsClient = new WebSocketClient();

export default wsClient;

// ============================================================================
// React Hooks for WebSocket
// ============================================================================

/**
 * Hook for WebSocket connection management
 */
export function useWebSocketConnection(options: {
  autoConnect?: boolean;
  auth?: { token?: string };
} = {}) {
  const { autoConnect = true, auth } = options;
  const [status, setStatus] = useState<ConnectionStatus>(wsClient.getStatus());

  useEffect(() => {
    const unsubscribe = wsClient.onStatusChange(setStatus);

    if (autoConnect && !wsClient.isConnected()) {
      wsClient.connect(auth).catch((error) => {
        console.error('[WebSocket Hook] Failed to connect:', error);
      });
    }

    return () => {
      unsubscribe();
    };
  }, [autoConnect, auth]);

  const connect = useCallback(() => wsClient.connect(auth), [auth]);
  const disconnect = useCallback(() => wsClient.disconnect(), []);

  return {
    status,
    isConnected: status === 'connected',
    connect,
    disconnect,
  };
}

/**
 * Hook for project room management
 */
export function useProjectRoom(projectId: number | null) {
  useEffect(() => {
    if (projectId === null || !wsClient.isConnected()) {
      return;
    }

    wsClient.joinProject(projectId);

    return () => {
      wsClient.leaveProject(projectId);
    };
  }, [projectId]);
}

/**
 * Hook for streaming chat messages
 */
export function useChatStream(chatId: number, options: {
  onToken?: (token: string) => void;
  onSources?: (sources: SourceDocument[]) => void;
  onComplete?: (metadata: { model: string; sources_count: number }) => void;
  onError?: (error: string) => void;
} = {}) {
  const { onToken, onSources, onComplete, onError } = options;

  useEffect(() => {
    const unsubscribeToken = wsClient.onMessageToken((data) => {
      if (data.chat_id === chatId && onToken) {
        onToken(data.token);
      }
    });

    const unsubscribeSources = wsClient.onMessageSources((data) => {
      if (data.chat_id === chatId && onSources) {
        onSources(data.sources);
      }
    });

    const unsubscribeComplete = wsClient.onMessageComplete((data) => {
      if (data.chat_id === chatId && onComplete) {
        onComplete(data.metadata);
      }
    });

    const unsubscribeError = wsClient.onError((data) => {
      if (data.chat_id === chatId && onError) {
        onError(data.message);
      }
    });

    return () => {
      unsubscribeToken();
      unsubscribeSources();
      unsubscribeComplete();
      unsubscribeError();
    };
  }, [chatId, onToken, onSources, onComplete, onError]);

  const sendMessage = useCallback(
    (message: string, options?: { model?: string; temperature?: number; include_history?: boolean }) => {
      wsClient.sendMessage({
        chat_id: chatId,
        message,
        ...options,
      });
    },
    [chatId]
  );

  return { sendMessage };
}

/**
 * Hook for document processing updates
 */
export function useDocumentUpdates(onStatusChange?: (data: DocumentStatusEvent) => void) {
  useEffect(() => {
    if (!onStatusChange) return;

    const unsubscribe = wsClient.onDocumentStatus(onStatusChange);
    return unsubscribe;
  }, [onStatusChange]);
}

/**
 * Hook for project updates
 */
export function useProjectUpdates(onUpdate?: (data: ProjectUpdateEvent) => void) {
  useEffect(() => {
    if (!onUpdate) return;

    const unsubscribe = wsClient.onProjectUpdate(onUpdate);
    return unsubscribe;
  }, [onUpdate]);
}
