# State Management Guide

This document provides comprehensive guidance on using the state management setup in the DAA Chatbot frontend.

## Table of Contents

1. [Overview](#overview)
2. [Zustand Stores](#zustand-stores)
3. [React Query](#react-query)
4. [API Client](#api-client)
5. [WebSocket Client](#websocket-client)
6. [Usage Examples](#usage-examples)

## Overview

The DAA Chatbot frontend uses a hybrid state management approach:

- **Zustand**: For client-side UI state (current selections, temporary data, streaming state)
- **React Query (TanStack Query)**: For server state (data fetching, caching, synchronization)
- **Axios**: For HTTP API calls
- **Socket.io**: For real-time WebSocket communication

## Zustand Stores

### Chat Store (`stores/chatStore.ts`)

Manages chat sessions, messages, and streaming state.

#### State Structure
```typescript
{
  currentChatId: string | null;
  chats: Chat[];
  messages: Record<string, Message[]>;
  activeStreaming: boolean;
  streamingMessageId: string | null;
  streamingContent: string;
}
```

#### Usage Example
```typescript
import { useChatStore } from '@/stores/chatStore';

function ChatComponent() {
  // Select entire store
  const chatStore = useChatStore();

  // Select specific values (recommended for performance)
  const currentChatId = useChatStore((state) => state.currentChatId);
  const chats = useChatStore((state) => state.chats);

  // Use actions
  const setCurrentChat = useChatStore((state) => state.setCurrentChat);
  const addMessage = useChatStore((state) => state.addMessage);

  // Use selectors
  const currentChat = useChatStore(selectCurrentChat);
  const messages = useChatStore(selectCurrentMessages);

  return (
    <div>
      {/* Your component */}
    </div>
  );
}
```

#### Key Actions
- `setCurrentChat(chatId)`: Set the active chat
- `addMessage(chatId, message)`: Add a message to a chat
- `startStreaming(messageId)`: Begin streaming a response
- `appendStreamChunk(chunk)`: Add text to streaming response
- `endStreaming()`: Finalize streaming response

### Project Store (`stores/projectStore.ts`)

Manages projects and current project selection.

#### State Structure
```typescript
{
  currentProjectId: string | null;
  projects: Project[];
  isLoading: boolean;
  error: string | null;
}
```

#### Usage Example
```typescript
import { useProjectStore, selectCurrentProject } from '@/stores/projectStore';

function ProjectSelector() {
  const currentProject = useProjectStore(selectCurrentProject);
  const setCurrentProject = useProjectStore((state) => state.setCurrentProject);
  const projects = useProjectStore((state) => state.projects);

  return (
    <select onChange={(e) => setCurrentProject(e.target.value)}>
      {projects.map(project => (
        <option key={project.id} value={project.id}>
          {project.name}
        </option>
      ))}
    </select>
  );
}
```

#### Key Actions
- `setCurrentProject(projectId)`: Set active project
- `addProject(project)`: Add a new project
- `updateProject(projectId, updates)`: Update project details
- `deleteProject(projectId)`: Remove a project

### Document Store (`stores/documentStore.ts`)

Manages documents, selections, upload progress, and processing status.

#### State Structure
```typescript
{
  documents: Record<string, Document[]>; // projectId -> documents
  selectedDocumentIds: string[];
  uploadProgress: Record<string, number>;
  processingDocuments: Set<string>;
  isLoading: boolean;
  error: string | null;
}
```

#### Usage Example
```typescript
import {
  useDocumentStore,
  selectProjectDocuments,
  selectUploadProgress
} from '@/stores/documentStore';

function DocumentList({ projectId }: { projectId: string }) {
  const documents = useDocumentStore(selectProjectDocuments(projectId));
  const selectDocument = useDocumentStore((state) => state.selectDocument);
  const selectedIds = useDocumentStore((state) => state.selectedDocumentIds);

  return (
    <div>
      {documents.map(doc => (
        <div key={doc.id}>
          <input
            type="checkbox"
            checked={selectedIds.includes(doc.id)}
            onChange={() => selectDocument(doc.id)}
          />
          {doc.filename}
        </div>
      ))}
    </div>
  );
}
```

#### Key Actions
- `addDocument(projectId, document)`: Add a document
- `updateDocument(projectId, documentId, updates)`: Update document
- `selectDocument(documentId)`: Select a document
- `setUploadProgress(documentId, progress)`: Update upload progress
- `addProcessingDocument(documentId)`: Mark document as processing

## React Query

React Query is configured globally in `components/providers/QueryProvider.tsx`.

### Configuration
- **Stale Time**: 5 minutes
- **Cache Time**: 10 minutes
- **Refetch on Window Focus**: Disabled
- **Retry**: 1 attempt

### Creating Query Hooks

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Query hook
export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => api.projects.list(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// Mutation hook with optimistic update
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProjectRequest) => api.projects.create(data),
    onMutate: async (newProject) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['projects'] });

      // Snapshot previous value
      const previousProjects = queryClient.getQueryData(['projects']);

      // Optimistically update
      queryClient.setQueryData(['projects'], (old: Project[]) => [
        ...old,
        { ...newProject, id: 'temp-id', created_at: new Date().toISOString() }
      ]);

      return { previousProjects };
    },
    onError: (err, newProject, context) => {
      // Rollback on error
      queryClient.setQueryData(['projects'], context?.previousProjects);
    },
    onSettled: () => {
      // Refetch after error or success
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
```

### Usage in Components

```typescript
function ProjectList() {
  const { data: projects, isLoading, error } = useProjects();
  const createProject = useCreateProject();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {projects?.map(project => (
        <div key={project.id}>{project.name}</div>
      ))}
      <button
        onClick={() => createProject.mutate({ name: 'New Project' })}
        disabled={createProject.isPending}
      >
        Create Project
      </button>
    </div>
  );
}
```

## API Client

The API client (`lib/api.ts`) provides typed methods for all backend endpoints.

### Structure
```typescript
import { api } from '@/lib/api';

// All API modules
api.projects.*    // Project endpoints
api.documents.*   // Document endpoints
api.chats.*       // Chat endpoints
api.integrations.*// Integration endpoints
api.system.*      // System endpoints
```

### Usage Examples

```typescript
// Projects
const projects = await api.projects.list();
const project = await api.projects.get(id);
const newProject = await api.projects.create({ name: 'My Project' });
await api.projects.update(id, { name: 'Updated' });
await api.projects.delete(id);

// Documents
const documents = await api.documents.list(projectId);
const uploadResult = await api.documents.upload(projectId, files);
await api.documents.delete(documentId);

// Chats
const chats = await api.chats.list(projectId);
const chat = await api.chats.create(projectId, 'Chat Title');
const messages = await api.chats.getHistory(chatId);
await api.chats.sendMessage(chatId, { content: 'Hello' });
```

### Error Handling

The API client automatically handles:
- Authentication (adds JWT token from localStorage)
- 401 errors (clears token and redirects)
- Response unwrapping (extracts `data` field)

```typescript
try {
  const projects = await api.projects.list();
} catch (error) {
  if (error.response?.status === 404) {
    console.log('Not found');
  } else if (error.response?.status === 500) {
    console.log('Server error');
  }
}
```

## WebSocket Client

The WebSocket client (`lib/websocket.ts`) handles real-time communication.

### Direct Usage

```typescript
import wsClient from '@/lib/websocket';
import { WSMessageType } from '@/types';

// Connect
await wsClient.connect(chatId);

// Send message
wsClient.sendMessage(chatId, 'Hello');

// Listen for messages
const unsubscribe = wsClient.on(WSMessageType.MESSAGE_CHUNK, (data) => {
  console.log('Received chunk:', data);
});

// Cleanup
unsubscribe();
wsClient.disconnect();
```

### React Hook Usage

```typescript
import { useWebSocket } from '@/lib/websocket';
import { WSMessageType } from '@/types';

function ChatInterface({ chatId }: { chatId: string }) {
  const { send, sendMessage, isConnected } = useWebSocket({
    chatId,
    autoConnect: true,
    onMessage: (type, data) => {
      if (type === WSMessageType.MESSAGE_CHUNK) {
        // Handle chunk
        const chunk = data as MessageChunkData;
        chatStore.appendStreamChunk(chunk.chunk);
      }
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  const handleSend = () => {
    sendMessage(chatId, 'Hello from user');
  };

  return (
    <div>
      <div>Status: {isConnected() ? 'Connected' : 'Disconnected'}</div>
      <button onClick={handleSend}>Send Message</button>
    </div>
  );
}
```

## Usage Examples

### Complete Chat Flow

```typescript
import { useChatStore, selectCurrentMessages } from '@/stores/chatStore';
import { useWebSocket } from '@/lib/websocket';
import { WSMessageType, MessageRole } from '@/types';
import { v4 as uuidv4 } from 'uuid';

function ChatInterface() {
  const chatId = useChatStore((state) => state.currentChatId);
  const messages = useChatStore(selectCurrentMessages);
  const addMessage = useChatStore((state) => state.addMessage);
  const startStreaming = useChatStore((state) => state.startStreaming);
  const appendStreamChunk = useChatStore((state) => state.appendStreamChunk);
  const endStreaming = useChatStore((state) => state.endStreaming);
  const streamingContent = useChatStore((state) => state.streamingContent);
  const isStreaming = useChatStore((state) => state.activeStreaming);

  const { sendMessage } = useWebSocket({
    chatId: chatId || undefined,
    onMessage: (type, data) => {
      switch (type) {
        case WSMessageType.MESSAGE_START:
          const messageId = uuidv4();
          startStreaming(messageId);
          break;
        case WSMessageType.MESSAGE_CHUNK:
          const chunk = data as MessageChunkData;
          appendStreamChunk(chunk.chunk);
          break;
        case WSMessageType.MESSAGE_END:
          endStreaming();
          break;
      }
    },
  });

  const handleSend = (content: string) => {
    if (!chatId) return;

    // Add user message
    addMessage(chatId, {
      id: uuidv4(),
      chat_id: chatId,
      role: MessageRole.USER,
      content,
      created_at: new Date().toISOString(),
    });

    // Send to server
    sendMessage(chatId, content);
  };

  return (
    <div>
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id}>{msg.content}</div>
        ))}
        {isStreaming && <div>{streamingContent}</div>}
      </div>
      <input
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            handleSend(e.currentTarget.value);
            e.currentTarget.value = '';
          }
        }}
      />
    </div>
  );
}
```

### Document Upload with Progress

```typescript
import { useDocumentStore, selectUploadProgress } from '@/stores/documentStore';
import { api } from '@/lib/api';

function DocumentUpload({ projectId }: { projectId: string }) {
  const addDocument = useDocumentStore((state) => state.addDocument);
  const setUploadProgress = useDocumentStore((state) => state.setUploadProgress);

  const handleUpload = async (files: File[]) => {
    try {
      const result = await api.documents.upload(projectId, files);

      result.documents.forEach(doc => {
        addDocument(projectId, {
          id: doc.document_id,
          filename: doc.filename,
          processing_status: doc.status,
          // ... other fields
        });
      });
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  return (
    <input
      type="file"
      multiple
      onChange={(e) => {
        if (e.target.files) {
          handleUpload(Array.from(e.target.files));
        }
      }}
    />
  );
}
```

## Best Practices

1. **Use Selectors**: Always use selectors for better performance
   ```typescript
   // Good
   const currentChat = useChatStore(selectCurrentChat);

   // Avoid (causes unnecessary re-renders)
   const { chats, currentChatId } = useChatStore();
   const currentChat = chats.find(c => c.id === currentChatId);
   ```

2. **Combine Zustand + React Query**: Use Zustand for UI state, React Query for server state
   ```typescript
   // UI state in Zustand
   const selectedId = useProjectStore(state => state.currentProjectId);

   // Server state in React Query
   const { data: project } = useQuery({
     queryKey: ['project', selectedId],
     queryFn: () => api.projects.get(selectedId),
     enabled: !!selectedId,
   });
   ```

3. **Handle Loading States**: Always handle loading, error, and empty states
   ```typescript
   const { data, isLoading, error } = useProjects();

   if (isLoading) return <Spinner />;
   if (error) return <ErrorMessage error={error} />;
   if (!data?.length) return <EmptyState />;

   return <ProjectList projects={data} />;
   ```

4. **Cleanup WebSocket Listeners**: Always cleanup subscriptions
   ```typescript
   useEffect(() => {
     const unsubscribe = wsClient.on(WSMessageType.MESSAGE_CHUNK, handler);
     return () => unsubscribe();
   }, []);
   ```

5. **Optimistic Updates**: Use for better UX
   ```typescript
   const deleteMutation = useMutation({
     mutationFn: api.documents.delete,
     onMutate: async (docId) => {
       // Remove from UI immediately
       documentStore.deleteDocument(projectId, docId);
     },
     onError: (err, docId, context) => {
       // Restore on error
       documentStore.addDocument(projectId, context.previousDoc);
     },
   });
   ```

## Debugging

### Zustand DevTools
Zustand stores are configured with devtools. Use Redux DevTools extension to inspect state.

### React Query DevTools
React Query DevTools are enabled in development mode. Access via the floating icon in the bottom-right corner.

### WebSocket Debugging
Enable WebSocket logging:
```typescript
// In browser console
localStorage.debug = '*';
```

## Migration Guide

If you need to migrate existing components:

1. Replace direct API calls with React Query hooks
2. Move UI state to appropriate Zustand store
3. Use WebSocket hook for real-time features
4. Remove local state that duplicates server state

Example:
```typescript
// Before
const [projects, setProjects] = useState<Project[]>([]);
useEffect(() => {
  fetch('/api/projects')
    .then(res => res.json())
    .then(setProjects);
}, []);

// After
const { data: projects } = useQuery({
  queryKey: ['projects'],
  queryFn: () => api.projects.list(),
});
```
