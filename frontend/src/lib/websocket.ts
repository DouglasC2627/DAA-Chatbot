// WebSocket Client for Real-time Communication
import { io, Socket } from 'socket.io-client';
import {
  WSMessage,
  WSMessageType,
  MessageChunkData,
  ProcessingUpdateData,
} from '@/types';

// ============================================================================
// WebSocket Configuration
// ============================================================================

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

type MessageHandler = (data: unknown) => void;
type ErrorHandler = (error: Error) => void;
type ConnectionHandler = () => void;

// ============================================================================
// WebSocket Client Class
// ============================================================================

class WebSocketClient {
  private socket: Socket | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<WSMessageType, MessageHandler[]> = new Map();
  private errorHandlers: ErrorHandler[] = [];
  private connectionHandlers: ConnectionHandler[] = [];
  private disconnectionHandlers: ConnectionHandler[] = [];

  constructor() {
    this.initializeHandlers();
  }

  private initializeHandlers(): void {
    // Initialize handler arrays for each message type
    Object.values(WSMessageType).forEach((type) => {
      this.messageHandlers.set(type as WSMessageType, []);
    });
  }

  // ============================================================================
  // Connection Management
  // ============================================================================

  connect(chatId?: string): Promise<void> {
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

      const token = localStorage.getItem('auth_token');
      const query: Record<string, string> = {};

      if (token) {
        query.token = token;
      }

      if (chatId) {
        query.chat_id = chatId;
      }

      this.socket = io(WS_URL, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        auth: query,
      });

      this.setupSocketListeners();

      this.socket.on('connect', () => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.connectionHandlers.forEach((handler) => handler());
        resolve();
      });

      this.socket.on('connect_error', (error: Error) => {
        this.isConnecting = false;
        this.reconnectAttempts++;

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          this.errorHandlers.forEach((handler) =>
            handler(new Error(`Failed to connect after ${this.maxReconnectAttempts} attempts`))
          );
          reject(error);
        }
      });

      // Set timeout for initial connection
      setTimeout(() => {
        if (this.isConnecting) {
          this.isConnecting = false;
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnecting = false;
      this.reconnectAttempts = 0;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // ============================================================================
  // Socket Event Listeners
  // ============================================================================

  private setupSocketListeners(): void {
    if (!this.socket) return;

    // Handle incoming messages
    this.socket.on('message', (message: WSMessage) => {
      this.handleMessage(message);
    });

    // Handle specific message types
    this.socket.on('message_chunk', (data: MessageChunkData) => {
      this.handleMessage({ type: WSMessageType.MESSAGE_CHUNK, data });
    });

    this.socket.on('message_end', (data: MessageChunkData) => {
      this.handleMessage({ type: WSMessageType.MESSAGE_END, data });
    });

    this.socket.on('message_error', (error: { message: string }) => {
      this.handleMessage({ type: WSMessageType.MESSAGE_ERROR, data: error });
    });

    this.socket.on('processing_update', (data: ProcessingUpdateData) => {
      this.handleMessage({ type: WSMessageType.PROCESSING_UPDATE, data });
    });

    this.socket.on('connection_ack', (data: unknown) => {
      this.handleMessage({ type: WSMessageType.CONNECTION_ACK, data });
    });

    // Handle disconnection
    this.socket.on('disconnect', (reason: string) => {
      console.log('WebSocket disconnected:', reason);
      this.disconnectionHandlers.forEach((handler) => handler());
    });

    // Handle errors
    this.socket.on('error', (error: Error) => {
      console.error('WebSocket error:', error);
      this.errorHandlers.forEach((handler) =>
        handler(error instanceof Error ? error : new Error(String(error)))
      );
    });
  }

  private handleMessage(message: WSMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => handler(message.data));
    }
  }

  // ============================================================================
  // Message Sending
  // ============================================================================

  send(event: string, data: unknown): void {
    if (!this.socket?.connected) {
      throw new Error('WebSocket not connected');
    }
    this.socket.emit(event, data);
  }

  sendMessage(chatId: string, content: string): void {
    this.send('send_message', { chat_id: chatId, content });
  }

  // ============================================================================
  // Event Handler Registration
  // ============================================================================

  on(messageType: WSMessageType, handler: MessageHandler): () => void {
    const handlers = this.messageHandlers.get(messageType) || [];
    handlers.push(handler);
    this.messageHandlers.set(messageType, handlers);

    // Return unsubscribe function
    return () => {
      const currentHandlers = this.messageHandlers.get(messageType) || [];
      const index = currentHandlers.indexOf(handler);
      if (index > -1) {
        currentHandlers.splice(index, 1);
        this.messageHandlers.set(messageType, currentHandlers);
      }
    };
  }

  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.push(handler);
    return () => {
      const index = this.errorHandlers.indexOf(handler);
      if (index > -1) {
        this.errorHandlers.splice(index, 1);
      }
    };
  }

  onConnect(handler: ConnectionHandler): () => void {
    this.connectionHandlers.push(handler);
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index > -1) {
        this.connectionHandlers.splice(index, 1);
      }
    };
  }

  onDisconnect(handler: ConnectionHandler): () => void {
    this.disconnectionHandlers.push(handler);
    return () => {
      const index = this.disconnectionHandlers.indexOf(handler);
      if (index > -1) {
        this.disconnectionHandlers.splice(index, 1);
      }
    };
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  off(messageType: WSMessageType, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  removeAllListeners(messageType?: WSMessageType): void {
    if (messageType) {
      this.messageHandlers.set(messageType, []);
    } else {
      this.messageHandlers.clear();
      this.initializeHandlers();
    }
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

const wsClient = new WebSocketClient();

export default wsClient;

// ============================================================================
// React Hook for WebSocket
// ============================================================================

import { useEffect, useRef } from 'react';

interface UseWebSocketOptions {
  chatId?: string;
  autoConnect?: boolean;
  onMessage?: (type: WSMessageType, data: unknown) => void;
  onError?: (error: Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    chatId,
    autoConnect = true,
    onMessage,
    onError,
    onConnect,
    onDisconnect,
  } = options;

  const unsubscribersRef = useRef<(() => void)[]>([]);

  useEffect(() => {
    if (autoConnect) {
      wsClient
        .connect(chatId)
        .catch((error) => {
          console.error('Failed to connect to WebSocket:', error);
          onError?.(error);
        });
    }

    // Set up event listeners
    if (onMessage) {
      Object.values(WSMessageType).forEach((type) => {
        const unsubscribe = wsClient.on(type as WSMessageType, (data) => {
          onMessage(type as WSMessageType, data);
        });
        unsubscribersRef.current.push(unsubscribe);
      });
    }

    if (onError) {
      const unsubscribe = wsClient.onError(onError);
      unsubscribersRef.current.push(unsubscribe);
    }

    if (onConnect) {
      const unsubscribe = wsClient.onConnect(onConnect);
      unsubscribersRef.current.push(unsubscribe);
    }

    if (onDisconnect) {
      const unsubscribe = wsClient.onDisconnect(onDisconnect);
      unsubscribersRef.current.push(unsubscribe);
    }

    // Cleanup
    return () => {
      unsubscribersRef.current.forEach((unsubscribe) => unsubscribe());
      unsubscribersRef.current = [];
    };
  }, [chatId, autoConnect, onMessage, onError, onConnect, onDisconnect]);

  return {
    send: wsClient.send.bind(wsClient),
    sendMessage: wsClient.sendMessage.bind(wsClient),
    connect: wsClient.connect.bind(wsClient),
    disconnect: wsClient.disconnect.bind(wsClient),
    isConnected: wsClient.isConnected.bind(wsClient),
  };
}
