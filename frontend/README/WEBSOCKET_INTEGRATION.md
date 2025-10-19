# Frontend WebSocket Integration Guide

## Overview

The DAA Chatbot frontend now has complete WebSocket support for real-time chat streaming, document processing updates, and project notifications using Socket.IO client.

## Files Created/Updated

### Core WebSocket Client
- **`src/lib/websocket.ts`** - Main WebSocket client with Socket.IO integration
  - WebSocketClient class with connection management
  - Auto-reconnection logic
  - Event handling system
  - React hooks for easy integration

### UI Components
- **`src/components/chat/ConnectionStatus.tsx`** - Connection status indicator
- **`src/components/chat/TypingIndicator.tsx`** - Typing and streaming indicators
- **`src/components/chat/StreamingChatExample.tsx`** - Complete example implementation

## Quick Start

### 1. Basic Connection

```typescript
import { useWebSocketConnection } from '@/lib/websocket';

function MyComponent() {
  const { status, isConnected, connect, disconnect } = useWebSocketConnection({
    autoConnect: true,
    auth: { token: 'optional-jwt-token' }
  });

  return (
    <div>
      Status: {status}
      {isConnected && <p>Connected!</p>}
    </div>
  );
}
```

### 2. Project Room Management

```typescript
import { useProjectRoom } from '@/lib/websocket';

function ProjectChat({ projectId }: { projectId: number }) {
  // Automatically joins/leaves project room
  useProjectRoom(projectId);

  return <div>Joined project {projectId}</div>;
}
```

### 3. Streaming Chat Messages

```typescript
import { useChatStream } from '@/lib/websocket';

function ChatComponent({ chatId }: { chatId: number }) {
  const [streamingText, setStreamingText] = useState('');
  const [sources, setSources] = useState([]);

  const { sendMessage } = useChatStream(chatId, {
    onToken: (token) => {
      setStreamingText(prev => prev + token);
    },
    onSources: (sources) => {
      setSources(sources);
    },
    onComplete: (metadata) => {
      console.log('Stream complete:', metadata);
      // Save message to state
    },
    onError: (error) => {
      console.error('Stream error:', error);
    }
  });

  const handleSend = () => {
    sendMessage('What is this document about?', {
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

## React Hooks API

### useWebSocketConnection

Manages WebSocket connection state.

```typescript
const {
  status,        // 'connected' | 'disconnected' | 'connecting' | 'reconnecting' | 'error'
  isConnected,   // boolean
  connect,       // () => Promise<void>
  disconnect     // () => void
} = useWebSocketConnection({
  autoConnect?: boolean,  // Default: true
  auth?: { token?: string }
});
```

### useProjectRoom

Automatically joins/leaves a project room.

```typescript
useProjectRoom(projectId: number | null);
```

- Joins the project room when `projectId` is provided and connected
- Leaves the room when component unmounts or `projectId` changes
- Does nothing if `projectId` is `null` or not connected

### useChatStream

Handles real-time chat message streaming.

```typescript
const { sendMessage } = useChatStream(chatId: number, {
  onToken?: (token: string) => void,
  onSources?: (sources: SourceDocument[]) => void,
  onComplete?: (metadata: { model: string; sources_count: number }) => void,
  onError?: (error: string) => void
});

// Send a message
sendMessage(message: string, options?: {
  model?: string,
  temperature?: number,
  include_history?: boolean
});
```

### useDocumentUpdates

Listen to document processing status updates.

```typescript
useDocumentUpdates((data) => {
  console.log('Document status:', data);
  // data: { document_id: number, status: 'processing' | 'completed' | 'failed', progress?: number }
});
```

### useProjectUpdates

Listen to project-level updates.

```typescript
useProjectUpdates((data) => {
  console.log('Project update:', data);
  // data: { type: string, data: Record<string, any> }
});
```

## UI Components

### ConnectionStatus

Shows the current WebSocket connection status.

```typescript
import { ConnectionStatus, ConnectionStatusDot } from '@/components/chat/ConnectionStatus';

// Full status with icon and label
<ConnectionStatus showLabel={true} />

// Just a colored dot
<ConnectionStatusDot />
```

**States:**
- 🟢 **Connected** - Green
- 🔴 **Disconnected** - Gray
- 🔵 **Connecting** - Blue (animated)
- 🟡 **Reconnecting** - Yellow (animated)
- 🔴 **Error** - Red

### TypingIndicator

Shows when the AI is processing.

```typescript
import { TypingIndicator, StreamingIndicator } from '@/components/chat/TypingIndicator';

// Bouncing dots
<TypingIndicator label="AI is thinking..." />

// Streaming text with cursor
<StreamingIndicator content={streamingText} />
```

### StreamingChatExample

Complete working example of a streaming chat interface.

```typescript
import { StreamingChatExample } from '@/components/chat/StreamingChatExample';

<StreamingChatExample chatId={1} projectId={1} />
```

## Direct WebSocket Client API

For advanced use cases, you can use the WebSocket client directly:

```typescript
import wsClient from '@/lib/websocket';

// Connect
await wsClient.connect({ token: 'jwt-token' });

// Join project
wsClient.joinProject(projectId);

// Send message
wsClient.sendMessage({
  chat_id: 1,
  message: 'Hello',
  model: 'llama3.2',
  temperature: 0.7
});

// Listen to events
const unsubscribe = wsClient.onMessageToken((data) => {
  console.log('Token:', data.token);
});

// Clean up
unsubscribe();
wsClient.disconnect();
```

## Event Handlers

Available event handler methods:

```typescript
// Connection status changes
wsClient.onStatusChange((status) => console.log(status));

// Message streaming
wsClient.onMessageToken((data) => console.log(data.token));
wsClient.onMessageSources((data) => console.log(data.sources));
wsClient.onMessageComplete((data) => console.log(data.metadata));

// Project updates
wsClient.onDocumentStatus((data) => console.log(data));
wsClient.onProjectUpdate((data) => console.log(data));

// Errors
wsClient.onError((data) => console.error(data.message));
```

All handlers return an unsubscribe function:
```typescript
const unsubscribe = wsClient.onMessageToken(handler);
unsubscribe(); // Stop listening
```

## Auto-Reconnection

The WebSocket client automatically handles reconnections:

- **Max Attempts:** 5
- **Reconnect Delay:** 1 second (increases up to 5 seconds)
- **Auto-Rejoin:** Automatically rejoins project rooms after reconnecting

Reconnection events:
```typescript
wsClient.onStatusChange((status) => {
  if (status === 'reconnecting') {
    console.log('Attempting to reconnect...');
  }
  if (status === 'connected') {
    console.log('Reconnected successfully!');
  }
});
```

## Error Handling

### Connection Errors

```typescript
const { status } = useWebSocketConnection();

if (status === 'error') {
  // Show error UI
  return <div>Connection failed. Please refresh.</div>;
}
```

### Stream Errors

```typescript
useChatStream(chatId, {
  onError: (error) => {
    toast({
      title: 'Message failed',
      description: error,
      variant: 'destructive'
    });
  }
});
```

## Environment Variables

Configure the WebSocket URL in `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The WebSocket client will automatically connect to:
```
http://localhost:8000/socket.io
```

## TypeScript Types

```typescript
// Connection status
export type ConnectionStatus =
  | 'connected'
  | 'disconnected'
  | 'connecting'
  | 'reconnecting'
  | 'error';

// Source document from RAG retrieval
export interface SourceDocument {
  id: string;
  content: string;
  metadata: Record<string, any>;
  score: number;
}

// Event payloads
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

## Best Practices

### 1. Connection Management

```typescript
// ✅ Good: Use the hook
const { isConnected } = useWebSocketConnection({ autoConnect: true });

// ❌ Avoid: Manual connection management
useEffect(() => {
  wsClient.connect();
  return () => wsClient.disconnect();
}, []);
```

### 2. Project Rooms

```typescript
// ✅ Good: Use the hook
useProjectRoom(currentProjectId);

// ❌ Avoid: Manual join/leave
useEffect(() => {
  wsClient.joinProject(projectId);
  return () => wsClient.leaveProject(projectId);
}, [projectId]);
```

### 3. Event Cleanup

```typescript
// ✅ Good: Hooks handle cleanup automatically
useChatStream(chatId, { onToken: handleToken });

// ⚠️ If using direct API, clean up manually
useEffect(() => {
  const unsubscribe = wsClient.onMessageToken(handleToken);
  return unsubscribe;
}, []);
```

### 4. Loading States

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

## Complete Example: Chat Page

```typescript
'use client';

import { useState } from 'react';
import {
  useWebSocketConnection,
  useChatStream,
  useProjectRoom
} from '@/lib/websocket';
import { ConnectionStatus } from '@/components/chat/ConnectionStatus';
import { TypingIndicator } from '@/components/chat/TypingIndicator';

export default function ChatPage({
  params
}: {
  params: { projectId: string; chatId: string }
}) {
  const projectId = parseInt(params.projectId);
  const chatId = parseInt(params.chatId);

  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{
    role: 'user' | 'assistant';
    content: string;
  }>>([]);
  const [streaming, setStreaming] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Connect to WebSocket
  const { isConnected } = useWebSocketConnection({ autoConnect: true });

  // Join project room
  useProjectRoom(projectId);

  // Set up chat streaming
  const { sendMessage } = useChatStream(chatId, {
    onToken: (token) => setStreaming(prev => prev + token),
    onComplete: (metadata) => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: streaming
      }]);
      setStreaming('');
      setIsLoading(false);
    },
    onError: (error) => {
      console.error(error);
      setIsLoading(false);
    }
  });

  const handleSend = () => {
    if (!input.trim() || !isConnected) return;

    setMessages(prev => [...prev, { role: 'user', content: input }]);
    setIsLoading(true);
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen">
      <header className="p-4 border-b flex justify-between">
        <h1>Chat</h1>
        <ConnectionStatus />
      </header>

      <main className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>
            {msg.content}
          </div>
        ))}
        {streaming && <div className="assistant">{streaming}</div>}
        {isLoading && !streaming && <TypingIndicator />}
      </main>

      <footer className="p-4 border-t">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          disabled={!isConnected}
        />
        <button onClick={handleSend} disabled={!isConnected}>
          Send
        </button>
      </footer>
    </div>
  );
}
```

## Debugging

### Enable Verbose Logging

All WebSocket events are logged to the console with `[WebSocket]` prefix:

```
[WebSocket] Connected: abc123
[WebSocket] Joined project: 1
[WebSocket] Sending message: {...}
[WebSocket] Message sources: {...}
[WebSocket] Message token received
[WebSocket] Message complete: {...}
```

### Check Connection Status

```typescript
import wsClient from '@/lib/websocket';

console.log('Status:', wsClient.getStatus());
console.log('Connected:', wsClient.isConnected());
```

### Test Ping/Pong

```typescript
wsClient.ping(); // Check console for latency
```

## Troubleshooting

### Connection Issues

**Problem:** WebSocket not connecting

**Solutions:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for errors
4. Ensure CORS is configured on backend

### Messages Not Streaming

**Problem:** Not receiving message tokens

**Solutions:**
1. Verify you're in the correct project room
2. Check chat_id matches the active chat
3. Ensure backend WebSocket handlers are working
4. Check browser console for WebSocket events

### Auto-Reconnect Not Working

**Problem:** Doesn't reconnect after disconnect

**Solutions:**
1. Check if max reconnect attempts (5) exceeded
2. Verify backend is accessible
3. Look for `reconnect_failed` event in console
4. Manually call `connect()` if needed

## Next Steps

- Implement persistent message storage
- Add optimistic UI updates
- Integrate with existing chat components
- Add notification system for document updates
- Implement typing indicators for multiple users
