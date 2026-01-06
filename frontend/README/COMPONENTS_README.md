# Components Documentation

This document provides comprehensive documentation for all React components in the DAA Chatbot frontend application.

## Table of Contents

- [Overview](#overview)
- [Component Architecture](#component-architecture)
- [Component Categories](#component-categories)
  - [UI Components (shadcn/ui)](#ui-components-shadcnui)
  - [Chat Components](#chat-components)
  - [Document Components](#document-components)
  - [Project Components](#project-components)
  - [Analytics Components](#analytics-components)
  - [Layout Components](#layout-components)
  - [Provider Components](#provider-components)
- [Component Patterns](#component-patterns)
- [Best Practices](#best-practices)

## Overview

The frontend uses a component-based architecture built with **React 18**, **Next.js 14 App Router**, and **TypeScript**. Components are organized by feature and responsibility, following atomic design principles.

```
frontend/src/components/
├── ui/                    # shadcn/ui primitives (buttons, dialogs, etc.)
├── chat/                  # Chat interface components
├── documents/             # Document management components
├── projects/              # Project management components
├── analytics/             # Analytics and visualization components
├── layout/                # Layout and navigation components
├── settings/              # Settings and configuration components
├── notifications/         # Notification system components
└── providers/             # Context providers and wrappers
```

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Pages                              │
│            (App Router - app/ directory)                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 Feature Components                      │
│     (Chat, Documents, Projects, Analytics)              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Layout Components                          │
│         (Header, Sidebar, Navigation)                    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               UI Primitives                             │
│      (shadcn/ui - Button, Card, Dialog, etc.)           │
└─────────────────────────────────────────────────────────┘

                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              State & Data Layer                         │
│      (Zustand Stores, React Query, WebSocket)           │
└─────────────────────────────────────────────────────────┘
```

## Component Categories

### UI Components (shadcn/ui)

**Location:** `src/components/ui/`

Unstyled, accessible UI primitives built on Radix UI, customized with Tailwind CSS.

#### Core Primitives

##### Button

**File:** `ui/button.tsx`

Versatile button component with multiple variants.

**Props:**
```typescript
interface ButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  asChild?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}
```

**Usage:**
```tsx
import { Button } from '@/components/ui/button';

// Default button
<Button onClick={() => console.log('clicked')}>
  Click me
</Button>

// Variants
<Button variant="destructive">Delete</Button>
<Button variant="outline">Cancel</Button>
<Button variant="ghost">Menu</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
<Button size="icon"><IconComponent /></Button>

// With icon
<Button>
  <PlusIcon className="mr-2 h-4 w-4" />
  Add Item
</Button>
```

##### Card

**File:** `ui/card.tsx`

Container component for content grouping.

**Components:**
- `Card`: Main container
- `CardHeader`: Header section
- `CardTitle`: Title text
- `CardDescription`: Description text
- `CardContent`: Main content area
- `CardFooter`: Footer section

**Usage:**
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Project Name</CardTitle>
    <CardDescription>Project description goes here</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Main content</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

##### Dialog

**File:** `ui/dialog.tsx`

Modal dialog component.

**Usage:**
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
    </DialogHeader>
    <p>Dialog content here</p>
  </DialogContent>
</Dialog>
```

##### Input

**File:** `ui/input.tsx`

Text input component.

**Usage:**
```tsx
import { Input } from '@/components/ui/input';

<Input
  type="text"
  placeholder="Enter text..."
  value={value}
  onChange={(e) => setValue(e.target.value)}
/>
```

##### Select

**File:** `ui/select.tsx`

Dropdown select component.

**Usage:**
```tsx
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

<Select value={value} onValueChange={setValue}>
  <SelectTrigger>
    <SelectValue placeholder="Select option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

##### InfoTooltip

**File:** `ui/info-tooltip.tsx`

Educational tooltip with help icon for explaining technical concepts.

**Props:**
```typescript
interface InfoTooltipProps {
  content: string;
  side?: 'top' | 'right' | 'bottom' | 'left';
}
```

**Usage:**
```tsx
import { InfoTooltip } from '@/components/ui/info-tooltip';

<div className="flex items-center gap-2">
  <span>Vector Norm</span>
  <InfoTooltip content="The length of the embedding vector, indicating magnitude in the vector space" />
</div>
```

---

### Chat Components

**Location:** `src/components/chat/`

Components for the chat interface and messaging functionality.

#### ChatInterface

**File:** `chat/ChatInterface.tsx`

Main chat interface component combining message display and input.

**Props:**
```typescript
interface ChatInterfaceProps {
  chatId: number;
  projectId: number;
}
```

**Features:**
- Real-time message streaming
- Source reference display
- Typing indicators
- Auto-scroll to latest message
- Markdown rendering

**Usage:**
```tsx
import { ChatInterface } from '@/components/chat/ChatInterface';

<ChatInterface chatId={1} projectId={1} />
```

#### MessageList

**File:** `chat/MessageList.tsx`

Displays chat message history with virtualization for performance.

**Props:**
```typescript
interface MessageListProps {
  chatId: number;
  messages: Message[];
  isLoading?: boolean;
}
```

**Usage:**
```tsx
import { MessageList } from '@/components/chat/MessageList';

<MessageList
  chatId={1}
  messages={messages}
  isLoading={false}
/>
```

#### Message

**File:** `chat/Message.tsx`

Individual message component with role-based styling.

**Props:**
```typescript
interface MessageProps {
  message: Message;
  showSources?: boolean;
}

interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  metadata?: {
    sources?: SourceReference[];
  };
}
```

**Features:**
- Markdown rendering with syntax highlighting
- Code block copy functionality
- Source citations
- Timestamp display

**Usage:**
```tsx
import { Message } from '@/components/chat/Message';

<Message
  message={{
    id: 1,
    role: 'assistant',
    content: 'Response text with **markdown**',
    created_at: '2025-01-07T12:00:00Z'
  }}
  showSources={true}
/>
```

#### MessageInput

**File:** `chat/MessageInput.tsx`

Message input with auto-resize and keyboard shortcuts.

**Props:**
```typescript
interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

**Features:**
- Auto-resizing textarea
- Enter to send (Shift+Enter for new line)
- Character count
- Send button with loading state

**Usage:**
```tsx
import { MessageInput } from '@/components/chat/MessageInput';

<MessageInput
  onSend={(text) => sendMessage(text)}
  disabled={isSending}
  placeholder="Ask a question..."
/>
```

#### SourceReferences

**File:** `chat/SourceReferences.tsx`

Displays source citations from RAG retrieval.

**Props:**
```typescript
interface SourceReferencesProps {
  sources: SourceReference[];
}

interface SourceReference {
  document_id: number;
  document_name: string;
  chunk_text: string;
  page?: number;
  similarity: number;
}
```

**Usage:**
```tsx
import { SourceReferences } from '@/components/chat/SourceReferences';

<SourceReferences sources={[
  {
    document_id: 1,
    document_name: 'research.pdf',
    chunk_text: 'Relevant excerpt...',
    page: 5,
    similarity: 0.92
  }
]} />
```

#### ChatHistoryPanel

**File:** `chat/ChatHistoryPanel.tsx`

Sidebar panel showing all chats in a project.

**Features:**
- Create new chat
- Rename chat
- Delete chat
- Switch between chats
- Search chats

**Usage:**
```tsx
import { ChatHistoryPanel } from '@/components/chat/ChatHistoryPanel';

<ChatHistoryPanel projectId={1} currentChatId={5} />
```

---

### Document Components

**Location:** `src/components/documents/`

Components for document upload and management.

#### DocumentUpload

**File:** `documents/DocumentUpload.tsx`

Drag-and-drop file upload component.

**Props:**
```typescript
interface DocumentUploadProps {
  projectId: number;
  onUploadComplete?: () => void;
}
```

**Features:**
- Drag-and-drop support
- Multiple file upload
- File type validation
- Upload progress tracking
- Preview before upload

**Supported Formats:**
- PDF (.pdf)
- Word (.docx)
- Text (.txt, .md)
- CSV (.csv)
- Excel (.xlsx)

**Usage:**
```tsx
import { DocumentUpload } from '@/components/documents/DocumentUpload';

<DocumentUpload
  projectId={1}
  onUploadComplete={() => refetch()}
/>
```

#### DocumentList

**File:** `documents/DocumentList.tsx`

Grid or list view of project documents.

**Props:**
```typescript
interface DocumentListProps {
  projectId: number;
  view?: 'grid' | 'list';
}
```

**Features:**
- Grid/list toggle
- Sort by name, date, size
- Filter by file type
- Delete documents
- View document details

**Usage:**
```tsx
import { DocumentList } from '@/components/documents/DocumentList';

<DocumentList projectId={1} view="grid" />
```

#### DocumentCard

**File:** `documents/DocumentCard.tsx`

Card display for a single document.

**Props:**
```typescript
interface DocumentCardProps {
  document: Document;
  onDelete?: (id: number) => void;
}
```

**Usage:**
```tsx
import { DocumentCard } from '@/components/documents/DocumentCard';

<DocumentCard
  document={doc}
  onDelete={(id) => handleDelete(id)}
/>
```

#### DocumentProcessingStatus

**File:** `documents/DocumentProcessingStatus.tsx`

Real-time document processing status indicator.

**Props:**
```typescript
interface DocumentProcessingStatusProps {
  status: 'processing' | 'completed' | 'failed';
  progress?: number;
  error?: string;
}
```

**Usage:**
```tsx
import { DocumentProcessingStatus } from '@/components/documents/DocumentProcessingStatus';

<DocumentProcessingStatus
  status="processing"
  progress={65}
/>
```

---

### Project Components

**Location:** `src/components/projects/`

Components for project management.

#### ProjectCard

**File:** `projects/ProjectCard.tsx`

Card display for a project.

**Props:**
```typescript
interface ProjectCardProps {
  project: Project;
  onClick?: () => void;
  onDelete?: (id: number) => void;
}
```

**Usage:**
```tsx
import { ProjectCard } from '@/components/projects/ProjectCard';

<ProjectCard
  project={project}
  onClick={() => router.push(`/projects/${project.id}`)}
  onDelete={handleDelete}
/>
```

#### ProjectCreate

**File:** `projects/ProjectCreate.tsx`

Dialog for creating new projects.

**Features:**
- Form validation
- Auto-focus on name field
- Create and redirect

**Usage:**
```tsx
import { ProjectCreate } from '@/components/projects/ProjectCreate';

<ProjectCreate
  onSuccess={(project) => router.push(`/projects/${project.id}`)}
/>
```

#### ProjectList

**File:** `projects/ProjectList.tsx`

Grid of all projects.

**Usage:**
```tsx
import { ProjectList } from '@/components/projects/ProjectList';

<ProjectList />
```

---

### Analytics Components

**Location:** `src/components/analytics/`

Components for embedding visualization and analysis.

#### EmbeddingVisualization

**File:** `analytics/EmbeddingVisualization.tsx`

Main visualization component with controls.

**Features:**
- 2D/3D toggle
- Method selection (PCA, t-SNE, UMAP)
- Interactive scatter plots
- Color coding by document
- Hover tooltips with chunk text

**Usage:**
```tsx
import { EmbeddingVisualization } from '@/components/analytics/EmbeddingVisualization';

<EmbeddingVisualization projectId={1} />
```

#### ScatterPlot2D

**File:** `analytics/ScatterPlot2D.tsx`

2D scatter plot using Recharts.

**Props:**
```typescript
interface ScatterPlot2DProps {
  data: EmbeddingPoint[];
  width?: number;
  height?: number;
}
```

#### ScatterPlot3D

**File:** `analytics/ScatterPlot3D.tsx`

3D scatter plot using Plotly.js.

**Props:**
```typescript
interface ScatterPlot3DProps {
  data: EmbeddingPoint[];
}
```

#### SimilarityHeatmap

**File:** `analytics/SimilarityHeatmap.tsx`

Heatmap showing document/chunk similarity matrix.

**Usage:**
```tsx
import { SimilarityHeatmap } from '@/components/analytics/SimilarityHeatmap';

<SimilarityHeatmap projectId={1} level="document" />
```

#### EmbeddingTable

**File:** `analytics/EmbeddingTable.tsx`

Data table with search and CSV export.

**Features:**
- Search by document name or chunk text
- Sort by any column
- CSV export
- Pagination

**Usage:**
```tsx
import { EmbeddingTable } from '@/components/analytics/EmbeddingTable';

<EmbeddingTable data={embeddings} />
```

#### EmbeddingStats

**File:** `analytics/EmbeddingStats.tsx`

Statistics cards showing embedding metrics.

**Usage:**
```tsx
import { EmbeddingStats } from '@/components/analytics/EmbeddingStats';

<EmbeddingStats projectId={1} />
```

#### RetrievalTester

**File:** `analytics/RetrievalTester.tsx`

Interface for testing RAG retrieval quality.

**Features:**
- Query input
- Adjustable k value
- Retrieval results with similarity scores
- Timing metrics

**Usage:**
```tsx
import { RetrievalTester } from '@/components/analytics/RetrievalTester';

<RetrievalTester projectId={1} />
```

---

### Layout Components

**Location:** `src/components/layout/`

Application layout and navigation components.

#### AppLayout

**File:** `layout/AppLayout.tsx`

Main application layout wrapper.

**Usage:**
```tsx
import { AppLayout } from '@/components/layout/AppLayout';

<AppLayout>
  <YourPageContent />
</AppLayout>
```

#### Header

**File:** `layout/Header.tsx`

Top navigation bar.

**Features:**
- Logo and branding
- Navigation links
- User menu
- Theme toggle
- Mobile menu trigger

#### Sidebar

**File:** `layout/Sidebar.tsx`

Side navigation panel.

**Features:**
- Project selector
- Navigation menu
- Chat history
- Collapsible sections

#### ProjectSelector

**File:** `layout/ProjectSelector.tsx`

Dropdown for switching between projects.

**Usage:**
```tsx
import { ProjectSelector } from '@/components/layout/ProjectSelector';

<ProjectSelector
  currentProjectId={1}
  onProjectChange={(id) => setProjectId(id)}
/>
```

---

### Provider Components

**Location:** `src/components/providers/`

Context providers and app wrappers.

#### QueryProvider

**File:** `providers/QueryProvider.tsx`

React Query provider with default configuration.

**Usage:**
```tsx
import { QueryProvider } from '@/components/providers/QueryProvider';

<QueryProvider>
  <App />
</QueryProvider>
```

#### WebSocketProvider

**File:** `providers/WebSocketProvider.tsx`

WebSocket connection provider for real-time features.

**Usage:**
```tsx
import { WebSocketProvider } from '@/components/providers/WebSocketProvider';

<WebSocketProvider>
  <ChatInterface />
</WebSocketProvider>
```

---

## Component Patterns

### Compound Components

Used for related component groups:

```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

### Render Props

For flexible content rendering:

```tsx
<DataTable
  data={data}
  renderRow={(item) => <CustomRow item={item} />}
/>
```

### Controlled vs Uncontrolled

```tsx
// Controlled
<Input value={value} onChange={setValue} />

// Uncontrolled
<Input defaultValue="initial" ref={inputRef} />
```

### Composition

```tsx
<Button asChild>
  <Link href="/page">Navigate</Link>
</Button>
```

---

## Best Practices

### 1. Component Organization

```tsx
// ✅ Good: Clear, single responsibility
function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map(msg => (
        <Message key={msg.id} message={msg} />
      ))}
    </div>
  );
}

// ❌ Bad: Too many responsibilities
function ChatPage() {
  // 200 lines of mixed logic
}
```

### 2. Props Interface

```tsx
// ✅ Good: Explicit interface
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  children: React.ReactNode;
}

// ❌ Bad: Any or implicit types
function Button(props: any) { ... }
```

### 3. Event Handlers

```tsx
// ✅ Good: Memoized handlers
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);

// ❌ Bad: Inline function in JSX
<Button onClick={() => doSomething(id)} />
```

### 4. Conditional Rendering

```tsx
// ✅ Good: Early return
if (!data) return <Loading />;
return <Content data={data} />;

// ❌ Bad: Nested ternaries
{data ? data.length ? data.map(...) : <Empty /> : <Loading />}
```

### 5. State Management

```tsx
// ✅ Good: Zustand for global state
const useStore = create<State>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 }))
}));

// ✅ Good: React Query for server state
const { data } = useQuery(['projects'], fetchProjects);

// ✅ Good: useState for local UI state
const [isOpen, setIsOpen] = useState(false);
```

### 6. Performance Optimization

```tsx
// ✅ Good: Memoization for expensive calculations
const sortedData = useMemo(
  () => data.sort((a, b) => a.date - b.date),
  [data]
);

// ✅ Good: React.memo for pure components
export const Message = React.memo(MessageComponent);
```

### 7. Accessibility

```tsx
// ✅ Good: Semantic HTML and ARIA
<button
  aria-label="Close dialog"
  aria-expanded={isOpen}
  onClick={onClose}
>
  <XIcon />
</button>

// ❌ Bad: Click handler on div
<div onClick={onClose}>Close</div>
```

---

## Component Testing

### Unit Testing

```tsx
import { render, screen } from '@testing-library/react';
import { Button } from '@/components/ui/button';

test('renders button with text', () => {
  render(<Button>Click me</Button>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});
```

### Integration Testing

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MessageInput } from '@/components/chat/MessageInput';

test('sends message on submit', async () => {
  const handleSend = jest.fn();
  render(<MessageInput onSend={handleSend} />);

  await userEvent.type(screen.getByRole('textbox'), 'Hello');
  await userEvent.click(screen.getByRole('button', { name: /send/i }));

  await waitFor(() => {
    expect(handleSend).toHaveBeenCalledWith('Hello');
  });
});
```

---

## Additional Resources

- [React Documentation](https://react.dev/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Radix UI Primitives](https://www.radix-ui.com/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
