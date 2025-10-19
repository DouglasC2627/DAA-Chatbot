# Live Updates Implementation Guide

## Overview

Task 8.3 adds comprehensive real-time features to the DAA Chatbot, including live document processing status, notifications, progress tracking, and offline/online handling.

## Features Implemented

### 1. Live Document Processing Status

Real-time updates for document processing with progress tracking.

**Components:**
- `DocumentProcessingStatus` - Full status cards with progress bars
- `DocumentStatusBadge` - Compact inline badge for individual documents

**Usage:**

```typescript
import { DocumentProcessingStatus, DocumentStatusBadge } from '@/components/documents/DocumentProcessingStatus';

// Show all processing documents
<DocumentProcessingStatus
  onComplete={(docId) => console.log('Document completed:', docId)}
  onError={(docId, error) => console.error('Document failed:', docId, error)}
/>

// Show status for a specific document
<DocumentProcessingStatus documentId={123} />

// Inline badge in document list
<DocumentStatusBadge documentId={123} showProgress={true} />
```

**Features:**
- ✅ Real-time progress updates (0-100%)
- ✅ Status indicators (Processing, Completed, Failed)
- ✅ Auto-removal of completed documents after 3 seconds
- ✅ Progress bars with percentage
- ✅ Callback support for completion and errors

### 2. Notification Center

Centralized notification system with toast integration.

**Component:** `NotificationCenter`

**Usage:**

```typescript
import { NotificationCenter, useNotifications } from '@/components/notifications/NotificationCenter';

// Add to header/layout
<NotificationCenter />

// Use programmatically
const notify = useNotifications();

notify.success('Document Processed', 'Your document is ready');
notify.error('Processing Failed', 'Please try again');
notify.info('New Update', 'A new document was added');
```

**Features:**
- ✅ Bell icon with unread count badge
- ✅ Dropdown with notification history
- ✅ Real-time notifications for:
  - Document processing completion
  - Document processing failures
  - Documents added/removed from project
  - Custom project updates
- ✅ Mark as read/Mark all as read
- ✅ Clear all notifications
- ✅ Time ago formatting
- ✅ Toast integration for important notifications
- ✅ Categorized by type (document, project, system)

### 3. Real-time Chat Updates

Automatic UI synchronization when chat data changes.

**Component:** `RealtimeChatUpdates`

**Usage:**

```typescript
import { RealtimeChatUpdates, useRealtimeChatSync } from '@/components/chat/RealtimeChatUpdates';

// As a component (automatically invalidates React Query caches)
<RealtimeChatUpdates
  projectId={projectId}
  onNewMessage={(chatId) => console.log('New message in chat:', chatId)}
  onChatUpdated={(chatId) => console.log('Chat updated:', chatId)}
  onChatDeleted={(chatId) => console.log('Chat deleted:', chatId)}
/>

// As a hook
function ChatPage({ projectId, chatId }) {
  useRealtimeChatSync(projectId, chatId);
  // Chat messages will auto-refresh when new messages arrive
}
```

**Features:**
- ✅ Automatically invalidates React Query caches
- ✅ Syncs on:
  - New messages added
  - Chats created/updated/deleted
  - Documents added/removed
- ✅ Callback support for custom actions
- ✅ No polling required

### 4. WebSocket Provider & Offline Handling

Complete connection management with offline/online detection.

**Component:** `WebSocketProvider`

**Usage:**

```typescript
import { WebSocketProvider, useWebSocket, OfflineGuard, useOnlineStatus } from '@/components/providers/WebSocketProvider';

// Wrap your app
<WebSocketProvider showOfflineAlert={true} autoConnect={true}>
  <App />
</WebSocketProvider>

// Use in components
function MyComponent() {
  const { status, isConnected, connect, disconnect } = useWebSocket();

  return <div>Status: {status}</div>;
}

// Guard features that require connection
<OfflineGuard fallback={<div>This feature requires internet</div>}>
  <ChatFeature />
</OfflineGuard>

// Check online status
const isOnline = useOnlineStatus();
```

**Features:**
- ✅ Auto-detection of browser online/offline status
- ✅ Banner notifications for:
  - Offline mode
  - WebSocket disconnected
  - Connection restored (temporary, auto-hides after 3s)
- ✅ Manual reconnect button when disconnected
- ✅ Auto-reconnect when coming back online
- ✅ OfflineGuard component for conditional rendering
- ✅ Context API for connection state sharing

### 5. Application Layout Integration

Complete layout with all real-time features integrated.

**Component:** `AppLayout`

**Usage:**

```typescript
import { AppLayout } from '@/components/layout/AppLayout';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <AppLayout>
          {children}
        </AppLayout>
      </body>
    </html>
  );
}
```

**Features:**
- ✅ WebSocket provider wrapping entire app
- ✅ Connection status indicator in header
- ✅ Notification center in header
- ✅ Conditional rendering on auth pages
- ✅ Responsive header and footer

## Component API Reference

### DocumentProcessingStatus

```typescript
interface DocumentProcessingStatusProps {
  documentId?: number;           // Filter to specific document
  onComplete?: (documentId: number) => void;
  onError?: (documentId: number, error: string) => void;
}
```

### DocumentStatusBadge

```typescript
interface DocumentStatusBadgeProps {
  documentId: number;            // Document to show status for
  showProgress?: boolean;        // Show progress percentage (default: false)
}
```

### NotificationCenter

No props. Add to layout/header.

### useNotifications Hook

```typescript
const notify = useNotifications();

notify.success(title: string, message?: string);
notify.error(title: string, message?: string);
notify.info(title: string, message?: string);
```

### RealtimeChatUpdates

```typescript
interface RealtimeChatUpdatesProps {
  projectId: number;
  onNewMessage?: (chatId: number) => void;
  onChatUpdated?: (chatId: number) => void;
  onChatDeleted?: (chatId: number) => void;
}
```

### useRealtimeChatSync Hook

```typescript
useRealtimeChatSync(projectId: number, chatId?: number);
```

### WebSocketProvider

```typescript
interface WebSocketProviderProps {
  children: ReactNode;
  showOfflineAlert?: boolean;    // Show connection banners (default: true)
  autoConnect?: boolean;         // Auto-connect on mount (default: true)
}
```

### useWebSocket Hook

```typescript
const {
  status,        // 'connected' | 'disconnected' | 'connecting' | 'reconnecting' | 'error'
  isConnected,   // boolean
  connect,       // () => Promise<void>
  disconnect     // () => void
} = useWebSocket();
```

### useOnlineStatus Hook

```typescript
const isOnline = useOnlineStatus();  // boolean
```

### OfflineGuard Component

```typescript
<OfflineGuard fallback={<CustomOfflineUI />}>
  <OnlineOnlyFeature />
</OfflineGuard>
```

## Integration Examples

### Example 1: Document Upload with Live Status

```typescript
'use client';

import { useState } from 'react';
import { DocumentUpload } from '@/components/documents/DocumentUpload';
import { DocumentProcessingStatus } from '@/components/documents/DocumentProcessingStatus';

export default function DocumentsPage({ projectId }) {
  const [uploadedDocs, setUploadedDocs] = useState<number[]>([]);

  return (
    <div>
      <DocumentUpload
        projectId={projectId}
        onUploadComplete={(docIds) => setUploadedDocs(docIds)}
      />

      {/* Show processing status for uploaded documents */}
      <DocumentProcessingStatus
        onComplete={(docId) => {
          // Remove from processing list
          setUploadedDocs(prev => prev.filter(id => id !== docId));
          // Refresh documents list
          queryClient.invalidateQueries(['documents', projectId]);
        }}
      />
    </div>
  );
}
```

### Example 2: Chat with Real-time Updates

```typescript
'use client';

import { useChatStream, useProjectRoom } from '@/lib/websocket';
import { useRealtimeChatSync } from '@/components/chat/RealtimeChatUpdates';
import { OfflineGuard } from '@/components/providers/WebSocketProvider';

export default function ChatPage({ projectId, chatId }) {
  // Join project room for real-time updates
  useProjectRoom(projectId);

  // Sync chat data automatically
  useRealtimeChatSync(projectId, chatId);

  // Stream messages
  const { sendMessage } = useChatStream(chatId, {
    onToken: (token) => appendToMessage(token),
    onComplete: () => console.log('Message complete')
  });

  return (
    <OfflineGuard>
      <ChatInterface onSend={sendMessage} />
    </OfflineGuard>
  );
}
```

### Example 3: Complete App with All Features

```typescript
// app/layout.tsx
import { AppLayout } from '@/components/layout/AppLayout';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

export default function RootLayout({ children }) {
  return (
    <html>
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

// app/projects/[id]/page.tsx
import { RealtimeChatUpdates } from '@/components/chat/RealtimeChatUpdates';
import { useProjectRoom } from '@/lib/websocket';

export default function ProjectPage({ params }) {
  const projectId = parseInt(params.id);

  // Join project room
  useProjectRoom(projectId);

  return (
    <div>
      {/* Listen to real-time updates */}
      <RealtimeChatUpdates projectId={projectId} />

      {/* Rest of your page */}
      <ProjectDashboard projectId={projectId} />
    </div>
  );
}
```

## Event Flow

### Document Processing

```
1. User uploads document
2. Backend starts processing
3. Backend emits: document_status { document_id, status: 'processing', progress: 0 }
4. Frontend shows DocumentProcessingStatus card
5. Backend emits progress updates: progress: 25, 50, 75...
6. Frontend updates progress bar
7. Backend emits: status: 'completed', progress: 100
8. Frontend shows success, triggers onComplete callback
9. NotificationCenter shows "Document Processed" notification
10. Card auto-removes after 3 seconds
```

### Chat Message

```
1. User sends message via WebSocket
2. Backend processes with RAG pipeline
3. Backend emits: message_sources
4. Frontend updates sources
5. Backend streams: message_token, message_token, message_token...
6. Frontend appends tokens in real-time
7. Backend emits: message_complete
8. Backend emits: project_update { type: 'chat_message_added', data: {...} }
9. RealtimeChatUpdates invalidates React Query cache
10. Chat list auto-refreshes
```

### Offline/Online

```
1. User goes offline (network disconnected)
2. Browser fires 'offline' event
3. WebSocketProvider detects offline status
4. "You are offline" banner appears
5. WebSocket automatically disconnects
6. User comes back online
7. Browser fires 'online' event
8. WebSocketProvider auto-reconnects WebSocket
9. Rejoins project rooms
10. "Connection restored" banner shows for 3s
11. All real-time features resume
```

## Styling & Customization

All components use Tailwind CSS and support dark mode:

```typescript
// Custom progress bar color
<Progress value={50} className="h-2 [&>div]:bg-blue-500" />

// Custom notification colors
notify.success('Title', 'Message'); // Green
notify.error('Title', 'Message');   // Red
notify.info('Title', 'Message');    // Blue

// Custom offline fallback
<OfflineGuard fallback={<CustomOfflineComponent />}>
  <YourComponent />
</OfflineGuard>
```

## Performance Considerations

- **React Query Integration:** Uses query invalidation instead of manual refetches
- **Auto-cleanup:** Notifications and status cards auto-remove
- **Event Throttling:** WebSocket events are batched where appropriate
- **Memory Management:** Unsubscribes from all events on component unmount
- **Smart Reconnection:** Exponential backoff, max 5 attempts

## Troubleshooting

### Notifications Not Showing

1. Ensure `NotificationCenter` is in your layout
2. Check WebSocket connection status
3. Verify you're in the correct project room
4. Check browser console for errors

### Progress Not Updating

1. Verify WebSocket is connected
2. Check that document_id matches
3. Ensure backend is emitting progress events
4. Check DocumentProcessingStatus is mounted

### Real-time Updates Not Working

1. Check `RealtimeChatUpdates` is mounted
2. Verify React Query is configured
3. Ensure WebSocket connection is active
4. Check project room is joined

### Offline Detection Not Working

1. Test by disabling network in DevTools
2. Check browser console for online/offline events
3. Verify WebSocketProvider is wrapping app
4. Test auto-reconnect manually

## Files Created

- `frontend/src/components/documents/DocumentProcessingStatus.tsx`
- `frontend/src/components/notifications/NotificationCenter.tsx`
- `frontend/src/components/chat/RealtimeChatUpdates.tsx`
- `frontend/src/components/providers/WebSocketProvider.tsx`
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/ui/alert.tsx`
- `frontend/LIVE_UPDATES_GUIDE.md`

## Testing

### Manual Testing Checklist

- [ ] Upload document and watch progress update in real-time
- [ ] Verify notification appears when document completes
- [ ] Send chat message and see it appear instantly
- [ ] Disconnect network and verify offline banner
- [ ] Reconnect network and verify "Connection restored" message
- [ ] Click reconnect button when WebSocket disconnects
- [ ] Mark notifications as read
- [ ] Clear all notifications
- [ ] Join different projects and verify room switching

### Automated Testing

```typescript
// Example test for DocumentProcessingStatus
import { render } from '@testing-library/react';
import { DocumentProcessingStatus } from '@/components/documents/DocumentProcessingStatus';

test('shows processing status', () => {
  const { getByText } = render(<DocumentProcessingStatus documentId={1} />);
  // Trigger WebSocket event
  wsClient.onDocumentStatus({ document_id: 1, status: 'processing', progress: 50 });
  expect(getByText('50% complete')).toBeInTheDocument();
});
```

## Next Steps

With Task 8.3 complete, you can:

1. **Integrate into existing pages:** Add components to your project/chat pages
2. **Customize styling:** Match your brand colors and theme
3. **Add more notification types:** Extend NotificationCenter for custom events
4. **Implement persistence:** Save notification history to localStorage
5. **Add filters:** Filter notifications by type or date
6. **Analytics:** Track notification engagement

## Summary

Task 8.3 provides a complete real-time update system:

- ✅ Live document processing with progress bars
- ✅ Centralized notification center
- ✅ Automatic chat synchronization
- ✅ Offline/online handling
- ✅ Connection status indicators
- ✅ WebSocket provider for app-wide state
- ✅ Comprehensive error handling
- ✅ Dark mode support
- ✅ Fully typed TypeScript API

All features work seamlessly with the WebSocket implementation from Tasks 8.1 and 8.2!
