# WebSocket Integration Documentation

This document provides comprehensive documentation for WebSocket integration using Socket.IO in the DAA Chatbot frontend.

## Table of Contents

- [Overview](#overview)
- [Setup and Configuration](#setup-and-configuration)
- [WebSocket Client](#websocket-client)
- [React Hooks](#react-hooks)
- [Event System](#event-system)
- [UI Components](#ui-components)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The DAA Chatbot uses **Socket.IO** for real-time bidirectional communication between the frontend and backend, enabling:

- **Real-time Chat Streaming**: Token-by-token message generation
- **Document Processing Updates**: Live status and progress updates
- **Project Notifications**: Multi-user project activity updates
- **Auto-Reconnection**: Automatic reconnection with exponential backoff

**Technology Stack:**
- **Socket.IO Client** (4.8+): WebSocket library
- **React Hooks**: Custom hooks for easy integration
- **TypeScript**: Full type safety for events

## Setup and Configuration

### Environment Variables

**File:** `.env.local`

```bash
# Backend API URL (WebSocket uses same origin)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The WebSocket client automatically connects to `http://localhost:8000/socket.io`.

### WebSocket Client File

**File:** `src/lib/websocket.ts`

Features:
- Singleton pattern for global connection
- Auto-reconnection with exponential backoff
- Project room management
- Type-safe event handlers
- React hooks for integration

## WebSocket Client

### Connection Management

**Direct Client Usage:**

```typescript
import wsClient from '@/lib/websocket';

// Connect
await wsClient.connect({ token: 'optional-jwt-token' });

// Check connection status
const isConnected = wsClient.isConnected();
const status = wsClient.getStatus(); // 'connected' | 'disconnected' | 'connecting' | 'reconnecting' | 'error'

// Disconnect
wsClient.disconnect();
```

### Auto-Reconnection

The client automatically handles reconnections:

- **Max Attempts**: 5
- **Initial Delay**: 1 second
- **Max Delay**: 5 seconds (exponential backoff)
- **Auto-Rejoin**: Automatically rejoins project rooms after reconnecting

**Monitoring Reconnection:**

```typescript
wsClient.onStatusChange((status) => {
  if (status === 'reconnecting') {
    console.log('Reconnecting...');
  }
  if (status === 'connected') {
    console.log('Reconnected!');
  }
});
```

### Project Rooms

WebSocket rooms isolate events by project:

```typescript
// Join a project room
wsClient.joinProject(projectId);

// Leave a project room
wsClient.leaveProject(projectId);
```

Events are only received for the current project room.

## React Hooks

### useWebSocketConnection

Manages WebSocket connection state.

**Signature:**
```typescript
const {
  status,        // ConnectionStatus
  isConnected,   // boolean
  connect,       // () => Promise<void>
  disconnect     // () => void
} = useWebSocketConnection({
  autoConnect?: boolean,      // Default: true
  auth?: { token?: string }
});
```

**Usage:**
```typescript
import { useWebSocketConnection } from '@/lib/websocket';

function MyComponent() {
  const { status, isConnected } = useWebSocketConnection({
    autoConnect: true
  });

  return (
    <div>
      Status: {status}
      {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
    </div>
  );
}
```

### useProjectRoom

Automatically manages project room join/leave.

**Signature:**
```typescript
useProjectRoom(projectId: number | null);
```

**Usage:**
```typescript
import { useProjectRoom } from '@/lib/websocket';

function ProjectChat({ projectId }: { projectId: number }) {
  // Automatically joins on mount, leaves on unmount
  useProjectRoom(projectId);

  return <div>Project {projectId} Chat</div>;
}
```

**Behavior:**
- Joins room when `projectId` is provided and connected
- Leaves room when component unmounts or `projectId` changes
- No-op if `projectId` is `null` or not connected

### useChatStream

Handles real-time chat message streaming.

**Signature:**
```typescript
const { sendMessage } = useChatStream(chatId: number, {
  onToken?: (token: string) => void,
  onSources?: (sources: SourceDocument[]) => void,
  onComplete?: (metadata: MessageMetadata) => void,
  onError?: (error: string) => void
});
```

**Usage:**
```typescript
import { useChatStream } from '@/lib/websocket';

function ChatInterface({ chatId }: { chatId: number }) {
  const [streamingText, setStreamingText] = useState('');

  const { sendMessage } = useChatStream(chatId, {
    onToken: (token) => setStreamingText(prev => prev + token),
    onSources: (sources) => console.log('Sources:', sources),
    onComplete: (metadata) => {
      console.log('Complete:', metadata);
      setStreamingText('');
    },
    onError: (error) => toast.error(error)
  });

  const handleSend = () => {
    sendMessage('What is machine learning?', {
      temperature: 0.7,
      include_history: true
    });
  };

  return (
    <div>
      <div>{streamingText}</div>
      <button onClick={handleSend}>Send</button>
    </div>
  );
}
```

### useDocumentUpdates

Listen to document processing status updates.

**Signature:**
```typescript
useDocumentUpdates((data: DocumentStatusEvent) => void);
```

**Usage:**
```typescript
import { useDocumentUpdates } from '@/lib/websocket';

function DocumentList() {
  useDocumentUpdates((data) => {
    console.log('Document update:', data);
    // { document_id: number, status: 'processing' | 'completed' | 'failed', progress?: number }

    // Invalidate queries to refetch
    queryClient.invalidateQueries(['documents']);
  });

  return <div>Documents</div>;
}
```

### useProjectUpdates

Listen to project-level notifications.

**Signature:**
```typescript
useProjectUpdates((data: ProjectUpdateEvent) => void);
```

**Usage:**
```typescript
import { useProjectUpdates } from '@/lib/websocket';

function ProjectDashboard() {
  useProjectUpdates((data) => {
    console.log('Project update:', data);
    // { type: string, data: Record<string, any> }
  });

  return <div>Dashboard</div>;
}
```

## Event System

### Available Events

**Client → Server:**
- `send_message`: Send a chat message
- `join_project`: Join a project room
- `leave_project`: Leave a project room

**Server → Client:**
- `message_token`: Streaming message token
- `message_sources`: Retrieved source documents
- `message_complete`: Message generation complete
- `document_status`: Document processing update
- `project_update`: Project notification
- `error`: Error message

### Event Handlers

Direct event subscription (lower-level API):

```typescript
import wsClient from '@/lib/websocket';

// Message streaming
const unsubToken = wsClient.onMessageToken((data) => {
  console.log('Token:', data.token);
});

const unsubSources = wsClient.onMessageSources((data) => {
  console.log('Sources:', data.sources);
});

const unsubComplete = wsClient.onMessageComplete((data) => {
  console.log('Complete:', data.metadata);
});

// Document updates
const unsubDoc = wsClient.onDocumentStatus((data) => {
  console.log('Document:', data);
});

// Project updates
const unsubProj = wsClient.onProjectUpdate((data) => {
  console.log('Project:', data);
});

// Errors
const unsubError = wsClient.onError((data) => {
  console.error('Error:', data.message);
});

// Cleanup
unsubToken();
unsubSources();
unsubComplete();
unsubDoc();
unsubProj();
unsubError();
```

## UI Components

### ConnectionStatus

Shows current WebSocket connection status.

**File:** `src/components/chat/ConnectionStatus.tsx`

**Usage:**
```tsx
import { ConnectionStatus, ConnectionStatusDot } from '@/components/chat/ConnectionStatus';

// Full status with label
<ConnectionStatus showLabel={true} />

// Just a colored dot
<ConnectionStatusDot />
```

**States:**
- 🟢 **Connected**: Green
- 🔴 **Disconnected**: Gray
- 🔵 **Connecting**: Blue (animated)
- 🟡 **Reconnecting**: Yellow (animated)
- 🔴 **Error**: Red

### TypingIndicator

Shows when AI is processing or streaming.

**File:** `src/components/chat/TypingIndicator.tsx`

**Usage:**
```tsx
import { TypingIndicator, StreamingIndicator } from '@/components/chat/TypingIndicator';

// Bouncing dots
<TypingIndicator label="AI is thinking..." />

// Streaming text with cursor
<StreamingIndicator content={streamingText} />
```

## Usage Examples

### Basic Chat Integration

```typescript
'use client';

import { useState } from 'react';
import { useWebSocketConnection, useChatStream, useProjectRoom } from '@/lib/websocket';

export default function ChatPage({ chatId, projectId }: { chatId: number; projectId: number }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState('');

  const { isConnected } = useWebSocketConnection({ autoConnect: true });
  useProjectRoom(projectId);

  const { sendMessage } = useChatStream(chatId, {
    onToken: (token) => setStreaming(prev => prev + token),
    onComplete: () => {
      setMessages(prev => [...prev, { role: 'assistant', content: streaming }]);
      setStreaming('');
    }
  });

  const handleSend = () => {
    if (!input.trim() || !isConnected) return;
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    sendMessage(input);
    setInput('');
  };

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i}>{msg.content}</div>
      ))}
      {streaming && <div>{streaming}</div>}
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={handleSend} disabled={!isConnected}>Send</button>
    </div>
  );
}
```

### Document Processing Monitor

```typescript
import { useDocumentUpdates } from '@/lib/websocket';
import { useQueryClient } from '@tanstack/react-query';

function DocumentMonitor() {
  const queryClient = useQueryClient();

  useDocumentUpdates((update) => {
    if (update.status === 'completed' || update.status === 'failed') {
      // Refetch documents when processing completes
      queryClient.invalidateQueries(['documents']);
    }

    // Show progress notification
    if (update.progress !== undefined) {
      console.log(`Document ${update.document_id}: ${update.progress}%`);
    }
  });

  return null; // This is a listener component
}
```

## Error Handling

### Connection Errors

```typescript
const { status } = useWebSocketConnection();

if (status === 'error') {
  return (
    <Alert variant="destructive">
      <AlertTitle>Connection Error</AlertTitle>
      <AlertDescription>
        Unable to connect to server. Please refresh the page.
      </AlertDescription>
    </Alert>
  );
}
```

### Stream Errors

```typescript
useChatStream(chatId, {
  onError: (error) => {
    toast({
      title: 'Message Failed',
      description: error,
      variant: 'destructive'
    });
  }
});
```

### Graceful Degradation

```typescript
function ChatComponent() {
  const { isConnected } = useWebSocketConnection();

  if (!isConnected) {
    return (
      <div>
        <p>Connecting to server...</p>
        <Button onClick={() => window.location.reload()}>
          Reload
        </Button>
      </div>
    );
  }

  return <ChatInterface />;
}
```

## Best Practices

### 1. Use Hooks Over Direct API

```typescript
// ✅ Good: Use hooks
const { isConnected } = useWebSocketConnection({ autoConnect: true });

// ❌ Bad: Manual connection management
useEffect(() => {
  wsClient.connect();
  return () => wsClient.disconnect();
}, []);
```

### 2. Auto-Join Project Rooms

```typescript
// ✅ Good: Use the hook
useProjectRoom(currentProjectId);

// ❌ Bad: Manual join/leave
useEffect(() => {
  wsClient.joinProject(projectId);
  return () => wsClient.leaveProject(projectId);
}, [projectId]);
```

### 3. Cleanup Event Listeners

```typescript
// ✅ Good: Hooks handle cleanup automatically
useChatStream(chatId, { onToken: handleToken });

// ⚠️ If using direct API, remember to cleanup
useEffect(() => {
  const unsubscribe = wsClient.onMessageToken(handleToken);
  return unsubscribe; // Important!
}, []);
```

### 4. Handle Loading States

```typescript
const [isWaiting, setIsWaiting] = useState(false);

const handleSend = () => {
  setIsWaiting(true);
  sendMessage(input);
};

useChatStream(chatId, {
  onToken: () => setIsWaiting(false),
  onComplete: () => setIsWaiting(false),
  onError: () => setIsWaiting(false)
});
```

### 5. Optimistic Updates

```typescript
const handleSend = (message: string) => {
  // Add message optimistically
  setMessages(prev => [...prev, { role: 'user', content: message }]);

  sendMessage(message);
};

useChatStream(chatId, {
  onError: (error) => {
    // Rollback on error
    setMessages(prev => prev.slice(0, -1));
    toast.error(error);
  }
});
```

## Troubleshooting

### Connection Issues

**Problem:** WebSocket not connecting

**Solutions:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/health
   ```
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for errors
4. Verify CORS configuration on backend

### Messages Not Streaming

**Problem:** Not receiving message tokens

**Solutions:**
1. Verify you're in the correct project room
2. Check `chat_id` matches the active chat
3. Check browser Network tab for WebSocket connection
4. Verify backend WebSocket handlers are running

### Auto-Reconnect Not Working

**Problem:** Doesn't reconnect after disconnect

**Solutions:**
1. Check if max reconnect attempts (5) exceeded
2. Manually refresh the page
3. Check browser console for `reconnect_failed` event
4. Verify backend accessibility

### Room Not Joined

**Problem:** Not receiving project-specific events

**Solutions:**
1. Ensure `useProjectRoom()` is called
2. Check connection status before joining
3. Verify `projectId` is correct
4. Check browser console for `joined_project` confirmation

## TypeScript Types

```typescript
// Connection status
export type ConnectionStatus =
  | 'connected'
  | 'disconnected'
  | 'connecting'
  | 'reconnecting'
  | 'error';

// Source document
export interface SourceDocument {
  id: string;
  content: string;
  metadata: Record<string, any>;
  score: number;
}

// Event types
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
```

## Additional Resources

- [Socket.IO Client Documentation](https://socket.io/docs/v4/client-api/)
- [React Hooks Patterns](https://react.dev/reference/react)
- [WebSocket Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
