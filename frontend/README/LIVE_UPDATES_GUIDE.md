# Live Updates Guide

This document provides comprehensive documentation for implementing real-time updates in the DAA Chatbot frontend, including document processing status, notifications, and connection management.

## Table of Contents

- [Overview](#overview)
- [Components Overview](#components-overview)
- [Document Processing Status](#document-processing-status)
- [Notification Center](#notification-center)
- [Real-time Chat Synchronization](#real-time-chat-synchronization)
- [WebSocket Provider & Connection Management](#websocket-provider--connection-management)
- [Application Layout Integration](#application-layout-integration)
- [Integration Patterns](#integration-patterns)
- [Event Flow](#event-flow)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [TypeScript API Reference](#typescript-api-reference)

## Overview

The DAA Chatbot provides a comprehensive suite of real-time update features built on top of the WebSocket infrastructure:

- **Document Processing Status**: Live progress tracking for document uploads and processing
- **Notification Center**: Centralized system for user notifications with history
- **Real-time Chat Sync**: Automatic synchronization of chat data across the application
- **Connection Management**: Offline/online detection and auto-reconnection
- **Application Layout**: Pre-built layout with all real-time features integrated

**Technology Stack:**
- **WebSocket Layer**: Socket.IO client with auto-reconnection
- **State Management**: React Query for cache invalidation, Zustand for notification state
- **UI Components**: shadcn/ui with real-time updates
- **Offline Detection**: Browser online/offline events with visual feedback

## Components Overview

### Real-time Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `DocumentProcessingStatus` | Track document processing progress | `components/documents/` |
| `DocumentStatusBadge` | Inline status badge for documents | `components/documents/` |
| `NotificationCenter` | Centralized notification management | `components/notifications/` |
| `RealtimeChatUpdates` | Auto-sync chat data | `components/chat/` |
| `WebSocketProvider` | Connection state and offline handling | `components/providers/` |
| `AppLayout` | Complete layout with all features | `components/layout/` |

### Custom Hooks

| Hook | Purpose | Returns |
|------|---------|---------|
| `useNotifications()` | Programmatic notifications | `{ success, error, info }` |
| `useRealtimeChatSync()` | Auto-sync chat queries | `void` |
| `useWebSocket()` | Connection state | `{ status, isConnected, connect, disconnect }` |
| `useOnlineStatus()` | Browser online/offline | `boolean` |

## Document Processing Status

Real-time tracking of document upload and processing with visual progress indicators.

### DocumentProcessingStatus Component

**File:** `src/components/documents/DocumentProcessingStatus.tsx`

**Usage:**

```typescript
import { DocumentProcessingStatus } from '@/components/documents/DocumentProcessingStatus';

// Show all processing documents
<DocumentProcessingStatus
  onComplete={(docId) => console.log('Document completed:', docId)}
  onError={(docId, error) => console.error('Document failed:', docId, error)}
/>

// Filter to specific document
<DocumentProcessingStatus documentId={123} />
```

**Props:**

```typescript
interface DocumentProcessingStatusProps {
  documentId?: number;  // Filter to specific document ID
  onComplete?: (documentId: number) => void;
  onError?: (documentId: number, error: string) => void;
}
```

**Features:**
- Real-time progress updates (0-100%)
- Visual progress bars with percentage
- Status indicators: Processing (blue), Completed (green), Failed (red)
- Auto-removal of completed documents after 3 seconds
- Callback support for completion and error events

### DocumentStatusBadge Component

Compact inline status indicator for individual documents.

**Usage:**

```typescript
import { DocumentStatusBadge } from '@/components/documents/DocumentProcessingStatus';

// In a document list
<div className="flex items-center gap-2">
  <span>{document.name}</span>
  <DocumentStatusBadge documentId={document.id} showProgress={true} />
</div>
```

**Props:**

```typescript
interface DocumentStatusBadgeProps {
  documentId: number;     // Document to show status for
  showProgress?: boolean; // Show progress percentage (default: false)
}
```

### Document Processing Example

```typescript
'use client';

import { useState } from 'react';
import { DocumentUpload } from '@/components/documents/DocumentUpload';
import { DocumentProcessingStatus } from '@/components/documents/DocumentProcessingStatus';
import { useQueryClient } from '@tanstack/react-query';

export default function DocumentsPage({ projectId }: { projectId: number }) {
  const queryClient = useQueryClient();
  const [uploadedDocs, setUploadedDocs] = useState<number[]>([]);

  const handleUploadComplete = (docIds: number[]) => {
    setUploadedDocs(docIds);
  };

  const handleProcessingComplete = (docId: number) => {
    // Remove from tracking list
    setUploadedDocs(prev => prev.filter(id => id !== docId));

    // Refresh documents list
    queryClient.invalidateQueries(['documents', projectId]);
  };

  return (
    <div className="space-y-6">
      <DocumentUpload
        projectId={projectId}
        onUploadComplete={handleUploadComplete}
      />

      <DocumentProcessingStatus
        onComplete={handleProcessingComplete}
        onError={(docId, error) => console.error('Processing failed:', error)}
      />
    </div>
  );
}
```

## Notification Center

Centralized notification system with persistent history and toast integration.

**File:** `src/components/notifications/NotificationCenter.tsx`

### Component Usage

```typescript
import { NotificationCenter } from '@/components/notifications/NotificationCenter';

// Add to header or layout
<header>
  <nav>{/* Navigation items */}</nav>
  <NotificationCenter />
</header>
```

### Programmatic Notifications

```typescript
import { useNotifications } from '@/components/notifications/NotificationCenter';

function MyComponent() {
  const notify = useNotifications();

  const handleSuccess = () => {
    notify.success('Document Processed', 'Your document is ready to use');
  };

  const handleError = () => {
    notify.error('Processing Failed', 'Please try uploading again');
  };

  const handleInfo = () => {
    notify.info('New Update', 'A new document was added to the project');
  };

  return (
    <div>
      <button onClick={handleSuccess}>Test Success</button>
      <button onClick={handleError}>Test Error</button>
      <button onClick={handleInfo}>Test Info</button>
    </div>
  );
}
```

**Features:**
- Bell icon with unread count badge
- Dropdown notification history
- Automatic notifications for:
  - Document processing completion/failure
  - Documents added/removed from project
  - Custom project updates
- Mark as read/Mark all as read functionality
- Clear all notifications
- Time ago formatting (e.g., "2 minutes ago")
- Toast integration for important notifications
- Categorized by type (document, project, system)
- Dark mode support

## Real-time Chat Synchronization

Automatic React Query cache invalidation when chat data changes via WebSocket events.

**File:** `src/components/chat/RealtimeChatUpdates.tsx`

### Component Usage

```typescript
import { RealtimeChatUpdates } from '@/components/chat/RealtimeChatUpdates';

function ProjectPage({ projectId }: { projectId: number }) {
  return (
    <div>
      {/* Automatically invalidates caches when chat data changes */}
      <RealtimeChatUpdates
        projectId={projectId}
        onNewMessage={(chatId) => console.log('New message in chat:', chatId)}
        onChatUpdated={(chatId) => console.log('Chat updated:', chatId)}
        onChatDeleted={(chatId) => console.log('Chat deleted:', chatId)}
      />

      <ChatList projectId={projectId} />
    </div>
  );
}
```

**Props:**

```typescript
interface RealtimeChatUpdatesProps {
  projectId: number;
  onNewMessage?: (chatId: number) => void;
  onChatUpdated?: (chatId: number) => void;
  onChatDeleted?: (chatId: number) => void;
}
```

### Hook Usage

```typescript
import { useRealtimeChatSync } from '@/components/chat/RealtimeChatUpdates';

function ChatPage({ projectId, chatId }: { projectId: number; chatId: number }) {
  // Automatically syncs chat data when messages arrive
  useRealtimeChatSync(projectId, chatId);

  return <ChatInterface chatId={chatId} />;
}
```

**Features:**
- Automatically invalidates React Query caches
- Triggers on:
  - New messages added to chats
  - Chats created/updated/deleted
  - Documents added/removed affecting context
- Zero configuration required
- No polling needed
- Callback support for custom actions

## WebSocket Provider & Connection Management

Complete connection state management with offline/online detection and visual feedback.

**File:** `src/components/providers/WebSocketProvider.tsx`

### Provider Setup

```typescript
import { WebSocketProvider } from '@/components/providers/WebSocketProvider';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <WebSocketProvider showOfflineAlert={true} autoConnect={true}>
          {children}
        </WebSocketProvider>
      </body>
    </html>
  );
}
```

**Props:**

```typescript
interface WebSocketProviderProps {
  children: ReactNode;
  showOfflineAlert?: boolean;  // Show connection banners (default: true)
  autoConnect?: boolean;       // Auto-connect on mount (default: true)
}
```

### Connection State Hook

```typescript
import { useWebSocket } from '@/components/providers/WebSocketProvider';

function ConnectionIndicator() {
  const { status, isConnected, connect, disconnect } = useWebSocket();

  return (
    <div>
      <span>Status: {status}</span>
      {!isConnected && <button onClick={connect}>Reconnect</button>}
      {isConnected && <button onClick={disconnect}>Disconnect</button>}
    </div>
  );
}
```

**Hook Returns:**

```typescript
{
  status: 'connected' | 'disconnected' | 'connecting' | 'reconnecting' | 'error';
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
}
```

### Online Status Detection

```typescript
import { useOnlineStatus } from '@/components/providers/WebSocketProvider';

function OfflineWarning() {
  const isOnline = useOnlineStatus();

  if (!isOnline) {
    return <div className="banner">You are offline</div>;
  }

  return null;
}
```

### Offline Guard

Conditionally render features that require internet connection.

```typescript
import { OfflineGuard } from '@/components/providers/WebSocketProvider';

function ChatFeature() {
  return (
    <OfflineGuard fallback={<div>This feature requires internet connection</div>}>
      <ChatInterface />
    </OfflineGuard>
  );
}
```

**Features:**
- Auto-detection of browser online/offline status
- Visual banner notifications for:
  - Offline mode
  - WebSocket disconnected
  - Connection restored (auto-hides after 3s)
- Manual reconnect button when disconnected
- Auto-reconnect when coming back online
- Auto-rejoin project rooms after reconnection
- Context API for connection state sharing

## Application Layout Integration

Pre-built layout component with all real-time features integrated.

**File:** `src/components/layout/AppLayout.tsx`

### Usage

```typescript
import { AppLayout } from '@/components/layout/AppLayout';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryClientProvider client={queryClient}>
          <AppLayout>
            {children}
          </AppLayout>
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

**Includes:**
- WebSocket provider wrapping entire app
- Connection status indicator in header
- Notification center in header
- Responsive header and footer
- Conditional rendering for auth pages
- Dark mode support

## Integration Patterns

### Pattern 1: Chat with Real-time Updates

```typescript
'use client';

import { useChatStream, useProjectRoom } from '@/lib/websocket';
import { useRealtimeChatSync } from '@/components/chat/RealtimeChatUpdates';
import { OfflineGuard } from '@/components/providers/WebSocketProvider';

export default function ChatPage({
  projectId,
  chatId
}: {
  projectId: number;
  chatId: number;
}) {
  // Join WebSocket room for this project
  useProjectRoom(projectId);

  // Auto-sync chat data when changes occur
  useRealtimeChatSync(projectId, chatId);

  // Stream messages
  const { sendMessage } = useChatStream(chatId, {
    onToken: (token) => appendToMessage(token),
    onComplete: (metadata) => console.log('Message complete', metadata),
    onError: (error) => console.error('Stream error:', error)
  });

  return (
    <OfflineGuard>
      <ChatInterface onSend={sendMessage} />
    </OfflineGuard>
  );
}
```

### Pattern 2: Document Upload with Progress Tracking

```typescript
'use client';

import { DocumentUpload } from '@/components/documents/DocumentUpload';
import { DocumentProcessingStatus } from '@/components/documents/DocumentProcessingStatus';
import { useNotifications } from '@/components/notifications/NotificationCenter';
import { useQueryClient } from '@tanstack/react-query';

export default function DocumentsPage({ projectId }: { projectId: number }) {
  const notify = useNotifications();
  const queryClient = useQueryClient();

  const handleComplete = (docId: number) => {
    notify.success('Processing Complete', 'Your document is ready');
    queryClient.invalidateQueries(['documents', projectId]);
  };

  const handleError = (docId: number, error: string) => {
    notify.error('Processing Failed', error);
  };

  return (
    <div className="space-y-6">
      <DocumentUpload projectId={projectId} />

      <DocumentProcessingStatus
        onComplete={handleComplete}
        onError={handleError}
      />
    </div>
  );
}
```

### Pattern 3: Project Dashboard with All Features

```typescript
'use client';

import { useProjectRoom } from '@/lib/websocket';
import { RealtimeChatUpdates } from '@/components/chat/RealtimeChatUpdates';
import { DocumentProcessingStatus } from '@/components/documents/DocumentProcessingStatus';

export default function ProjectDashboard({ projectId }: { projectId: number }) {
  // Join project room for all real-time updates
  useProjectRoom(projectId);

  return (
    <div>
      {/* Listen to chat updates */}
      <RealtimeChatUpdates projectId={projectId} />

      {/* Show document processing status */}
      <DocumentProcessingStatus />

      {/* Rest of dashboard */}
      <ProjectOverview projectId={projectId} />
      <ChatList projectId={projectId} />
      <DocumentList projectId={projectId} />
    </div>
  );
}
```

## Event Flow

### Document Processing Flow

```
1. User uploads document via DocumentUpload component
2. Backend starts processing and emits WebSocket event
   → document_status { document_id: 1, status: 'processing', progress: 0 }
3. DocumentProcessingStatus receives event and displays progress card
4. Backend emits progress updates
   → document_status { document_id: 1, status: 'processing', progress: 25 }
   → document_status { document_id: 1, status: 'processing', progress: 50 }
   → document_status { document_id: 1, status: 'processing', progress: 75 }
5. Frontend updates progress bar in real-time
6. Backend completes processing
   → document_status { document_id: 1, status: 'completed', progress: 100 }
7. Frontend triggers onComplete callback
8. NotificationCenter shows "Document Processed" notification
9. Progress card shows success state, auto-removes after 3 seconds
10. React Query cache invalidated, document list refreshes
```

### Chat Message Flow

```
1. User sends message via sendMessage()
2. Backend processes message with RAG pipeline
3. Backend emits sources
   → message_sources { chat_id: 1, sources: [...] }
4. Frontend displays source documents
5. Backend streams response tokens
   → message_token { chat_id: 1, token: "Machine" }
   → message_token { chat_id: 1, token: " learning" }
   → message_token { chat_id: 1, token: " is..." }
6. Frontend appends tokens in real-time to message display
7. Backend completes streaming
   → message_complete { chat_id: 1, metadata: {...} }
8. Backend emits project update
   → project_update { type: 'chat_message_added', data: {...} }
9. RealtimeChatUpdates receives event
10. React Query caches invalidated
11. Chat list and message list auto-refresh
```

### Offline/Online Flow

```
1. User loses network connection
2. Browser fires 'offline' event
3. WebSocketProvider detects offline status
4. "You are offline" banner appears at top of page
5. WebSocket automatically disconnects
6. User regains network connection
7. Browser fires 'online' event
8. WebSocketProvider detects online status
9. WebSocket auto-reconnects with exponential backoff
10. Auto-rejoins all project rooms
11. "Connection restored" banner shows briefly (3s)
12. All real-time features resume normal operation
```

## Best Practices

### 1. Always Use WebSocketProvider

```tsx
// ✅ Good: Wrap entire app
<WebSocketProvider>
  <App />
</WebSocketProvider>

// ❌ Bad: Missing provider
<App />  // Connection state unavailable
```

### 2. Join Project Rooms

```tsx
// ✅ Good: Join room for real-time updates
useProjectRoom(projectId);

// ❌ Bad: Not joining room
// Will not receive project-specific events
```

### 3. Clean Up Side Effects

```tsx
// ✅ Good: Hooks handle cleanup automatically
useRealtimeChatSync(projectId, chatId);

// ❌ Bad: Manual event listeners without cleanup
useEffect(() => {
  wsClient.onProjectUpdate(handleUpdate);
  // Missing cleanup!
}, []);
```

### 4. Handle Loading and Error States

```tsx
// ✅ Good: Complete state handling
<DocumentProcessingStatus
  onComplete={handleComplete}
  onError={(id, error) => {
    notify.error('Processing Failed', error);
    logError(id, error);
  }}
/>

// ❌ Bad: No error handling
<DocumentProcessingStatus />
```

### 5. Use OfflineGuard for Critical Features

```tsx
// ✅ Good: Guard online-only features
<OfflineGuard fallback={<OfflineMessage />}>
  <ChatInterface />
</OfflineGuard>

// ❌ Bad: No offline handling
<ChatInterface />  // Breaks when offline
```

### 6. Invalidate React Query Caches

```tsx
// ✅ Good: Let RealtimeChatUpdates handle invalidation
<RealtimeChatUpdates projectId={projectId} />

// ❌ Bad: Manual polling
useEffect(() => {
  const interval = setInterval(() => {
    queryClient.invalidateQueries(['chats']);
  }, 5000);
  return () => clearInterval(interval);
}, []);
```

## Troubleshooting

### Notifications Not Appearing

**Problem:** NotificationCenter bell icon shows but notifications don't appear

**Solutions:**
1. Verify `NotificationCenter` is mounted in your layout
2. Check WebSocket connection status using `useWebSocket()`
3. Ensure you've joined the correct project room with `useProjectRoom()`
4. Check browser console for WebSocket errors
5. Verify backend is emitting notification events

### Document Progress Not Updating

**Problem:** Progress bar stays at 0% or doesn't move

**Solutions:**
1. Check WebSocket connection is active: `const { isConnected } = useWebSocket()`
2. Verify `document_id` matches between upload and status component
3. Check backend logs to ensure progress events are being emitted
4. Ensure `DocumentProcessingStatus` component is mounted
5. Test with browser Network tab WebSocket frames

### Real-time Chat Sync Not Working

**Problem:** Chat messages don't appear automatically

**Solutions:**
1. Verify `RealtimeChatUpdates` component is mounted
2. Check React Query configuration is correct
3. Ensure WebSocket connection is active
4. Verify project room is joined: `useProjectRoom(projectId)`
5. Check query keys match between `RealtimeChatUpdates` and your queries

### Offline Detection Not Working

**Problem:** Offline banner doesn't appear when disconnecting

**Solutions:**
1. Test by disabling network in Chrome DevTools (Network tab → Offline)
2. Check browser console for online/offline events
3. Verify `WebSocketProvider` is wrapping your app
4. Ensure `showOfflineAlert` prop is `true` (default)
5. Test auto-reconnect by re-enabling network

### Connection Not Auto-Reconnecting

**Problem:** WebSocket stays disconnected after network returns

**Solutions:**
1. Check if maximum reconnection attempts (5) were exceeded
2. Verify `autoConnect` prop is `true` on `WebSocketProvider`
3. Check browser console for `reconnect_failed` events
4. Manually reconnect using `connect()` from `useWebSocket()`
5. Verify backend is accessible and WebSocket endpoint is available

### Performance Issues with Many Notifications

**Problem:** UI lags with hundreds of notifications

**Solutions:**
1. Clear old notifications regularly: "Clear all" button
2. Implement notification limits in NotificationCenter
3. Use virtualized list for notification dropdown
4. Filter notifications by type or date range
5. Consider persisting to localStorage and lazy loading

## TypeScript API Reference

### Component Props

```typescript
// DocumentProcessingStatus
interface DocumentProcessingStatusProps {
  documentId?: number;
  onComplete?: (documentId: number) => void;
  onError?: (documentId: number, error: string) => void;
}

// DocumentStatusBadge
interface DocumentStatusBadgeProps {
  documentId: number;
  showProgress?: boolean;
}

// RealtimeChatUpdates
interface RealtimeChatUpdatesProps {
  projectId: number;
  onNewMessage?: (chatId: number) => void;
  onChatUpdated?: (chatId: number) => void;
  onChatDeleted?: (chatId: number) => void;
}

// WebSocketProvider
interface WebSocketProviderProps {
  children: ReactNode;
  showOfflineAlert?: boolean;
  autoConnect?: boolean;
}

// OfflineGuard
interface OfflineGuardProps {
  children: ReactNode;
  fallback?: ReactNode;
}
```

### Hook Returns

```typescript
// useWebSocket
interface UseWebSocketReturn {
  status: ConnectionStatus;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
}

type ConnectionStatus =
  | 'connected'
  | 'disconnected'
  | 'connecting'
  | 'reconnecting'
  | 'error';

// useNotifications
interface UseNotificationsReturn {
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
}

// useOnlineStatus
function useOnlineStatus(): boolean;

// useRealtimeChatSync
function useRealtimeChatSync(projectId: number, chatId?: number): void;
```

### Event Types

```typescript
// Document status event
interface DocumentStatusEvent {
  document_id: number;
  status: 'processing' | 'completed' | 'failed';
  progress?: number;  // 0-100
  error?: string;
}

// Notification event
interface NotificationEvent {
  id: string;
  type: 'document' | 'project' | 'system';
  title: string;
  message?: string;
  timestamp: string;
  read: boolean;
}

// Project update event
interface ProjectUpdateEvent {
  type: string;
  data: Record<string, any>;
}
```

## Additional Resources

- [WebSocket Integration Documentation](./WEBSOCKET_INTEGRATION.md) - Low-level WebSocket API
- [Components Documentation](./COMPONENTS_README.md) - UI component library
- [State Management](./STATE_MANAGEMENT.md) - React Query and Zustand patterns
- [Socket.IO Client Documentation](https://socket.io/docs/v4/client-api/)
- [React Query Documentation](https://tanstack.com/query/latest/docs/react/overview)
