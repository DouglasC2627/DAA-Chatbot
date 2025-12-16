# DAA Chatbot - Frontend

Modern, responsive frontend for the DAA Chatbot built with Next.js 14, TypeScript, and Tailwind CSS.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand for global state
- **Server State**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod validation
- **Real-time**: Socket.IO client for WebSocket streaming
- **HTTP Client**: Axios
- **Visualization**: Plotly.js (3D scatter plots), Recharts (2D charts)
- **Icons**: Lucide React
- **Animations**: Framer Motion

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend server running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000" > .env.local

# Run development server
npm run dev
```

The app will be available at http://localhost:3000

## Available Scripts

```bash
npm run dev          # Start development server with hot reload
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

## Project Structure

```
frontend/src/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Home/landing page
│   ├── layout.tsx         # Root layout with providers
│   ├── globals.css        # Global styles and Tailwind imports
│   ├── chat/              # Chat interface pages
│   ├── projects/          # Project management pages
│   ├── documents/         # Document management pages
│   └── analytics/         # Embedding analytics dashboard
├── components/            # React components
│   ├── ui/               # shadcn/ui primitives (Button, Card, Dialog, Tooltip, etc.)
│   │   ├── tooltip.tsx            # Tooltip primitive wrapper
│   │   └── info-tooltip.tsx       # Educational tooltip component
│   ├── chat/             # Chat-specific components
│   │   ├── MessageList.tsx        # Chat message display
│   │   ├── MessageInput.tsx       # Message input form
│   │   └── SourceReferences.tsx   # RAG source citations
│   ├── documents/        # Document management components
│   │   ├── DocumentUpload.tsx     # File upload with drag-and-drop
│   │   └── DocumentList.tsx       # Document listing and management
│   ├── projects/         # Project components
│   │   ├── ProjectCard.tsx        # Project display card
│   │   └── CreateProject.tsx      # Project creation form
│   ├── analytics/        # Analytics visualizations
│   │   ├── EmbeddingVisualization.tsx  # 2D/3D scatter plots
│   │   ├── ScatterPlot2D.tsx          # 2D chart (Recharts)
│   │   ├── ScatterPlot3D.tsx          # 3D chart (Plotly.js)
│   │   ├── SimilarityHeatmap.tsx      # Similarity matrix heatmap
│   │   ├── EmbeddingTable.tsx         # Data table with search/export
│   │   ├── EmbeddingStats.tsx         # Statistics cards
│   │   └── RetrievalTester.tsx        # Query testing interface
│   ├── layout/           # Layout components (Header, Sidebar, etc.)
│   └── providers/        # React context providers
├── lib/                  # Utilities and configurations
│   ├── api.ts           # Axios client and API functions
│   ├── analytics-api.ts # Analytics API client
│   ├── websocket.ts     # Socket.IO client setup
│   └── utils.ts         # Helper functions
├── stores/              # Zustand state stores
│   ├── chatStore.ts     # Chat messages and state
│   ├── projectStore.ts  # Project data
│   └── documentStore.ts # Document management
├── types/               # TypeScript type definitions
│   ├── index.ts         # Shared types
│   └── analytics.ts     # Analytics type definitions
└── hooks/               # Custom React hooks
    └── useWebSocket.ts  # WebSocket connection hook
```

## Key Features

### 1. Project Management
- Create and manage multiple isolated projects
- Each project has its own document collection and chat history
- Project switching preserves state

### 2. Document Upload
- Drag-and-drop file upload
- Multi-file selection support
- Supported formats: PDF, DOCX, TXT, MD, CSV, XLSX
- Real-time upload progress
- File validation and error handling

### 3. Real-time Chat
- WebSocket-based streaming responses
- Markdown formatting support
- Source attribution with document references
- Chat history persistence
- Auto-scroll to latest messages

### 4. Responsive Design
- Mobile-first approach
- Adaptive layouts for all screen sizes
- Touch-friendly interactions
- Accessible UI components

### 5. Embedding Analytics Dashboard
- **Visualization:** Interactive 2D/3D scatter plots with PCA, t-SNE, and UMAP dimensionality reduction
- **Similarity Analysis:** Heatmaps showing cosine similarity between documents and chunks
- **Data Exploration:** Searchable table with pagination, CSV export, and embedding statistics
- **Retrieval Testing:** Test query interface to evaluate RAG performance with similarity scores
- **Educational UI:** Hover tooltips explaining technical concepts (embedding dimensions, vector norms, cosine similarity, etc.)
- **Performance:** Optimized for datasets with 1000+ embeddings using sampling and caching

## State Management

### Zustand Stores

The app uses Zustand for global state management:

```typescript
// Chat Store
- messages: Array of chat messages
- currentChatId: Active chat session
- isStreaming: WebSocket streaming status
- addMessage(): Add new message
- updateMessage(): Update existing message
- clearMessages(): Clear chat history

// Project Store
- projects: List of all projects
- currentProject: Active project
- setCurrentProject(): Switch projects
- addProject(): Create new project
- deleteProject(): Remove project

// Document Store
- documents: List of documents in current project
- uploadProgress: Upload status tracking
- addDocument(): Add new document
- removeDocument(): Delete document
```

### TanStack Query (React Query)

Server state is managed with React Query for:
- Automatic caching and invalidation
- Background refetching
- Optimistic updates
- Loading and error states

## WebSocket Integration

Real-time chat uses Socket.IO:

```typescript
// Connection established on chat page mount
const socket = io(NEXT_PUBLIC_WS_URL)

// Events
socket.emit('send_message', { message, projectId })
socket.on('message_chunk', (chunk) => {
  // Append to current message
})
socket.on('message_complete', (message) => {
  // Finalize message with sources
})
```

## Styling

### Tailwind CSS

Utility-first CSS framework with custom configuration:
- Custom color palette for dark/light themes
- Responsive breakpoints
- Custom animations

### shadcn/ui Components

Pre-built, accessible components:
- Button, Card, Dialog, Form, Input, Select
- Toast notifications
- Progress indicators
- Dropdown menus
- Alert dialogs

To add new components:
```bash
npx shadcn-ui@latest add [component-name]
```

## Environment Variables

Create a `.env.local` file:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Development Guidelines

### Adding a New Page

1. Create a new directory in `src/app/`
2. Add `page.tsx` for the route component
3. Add `layout.tsx` if needed for nested layouts
4. Update navigation in layout components

### Adding a New Feature Component

1. Create component in appropriate directory under `src/components/`
2. Use TypeScript for type safety
3. Leverage shadcn/ui primitives
4. Add to Zustand store if state management needed
5. Use React Query for server data

### Code Quality

- ESLint configuration enforces code standards
- Prettier for consistent formatting
- TypeScript strict mode enabled
- Components should be functional with hooks
- Use proper React patterns (memo, useCallback, useMemo)

## Common Tasks

### Adding API Endpoints

Update `src/lib/api.ts`:

```typescript
export const myNewEndpoint = async (params) => {
  const response = await apiClient.get('/endpoint', { params })
  return response.data
}
```

### Creating Forms

Use React Hook Form + Zod:

```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  field: z.string().min(1, 'Required')
})

const form = useForm({
  resolver: zodResolver(schema)
})
```

### Adding Animations

Use Framer Motion:

```typescript
import { motion } from 'framer-motion'

<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  exit={{ opacity: 0 }}
>
  Content
</motion.div>
```

## Analytics Components

### Analytics API Client

The `analytics-api.ts` module provides methods for analytics endpoints:

```typescript
import analyticsApi from '@/lib/analytics-api'

// Get embeddings data
const data = await analyticsApi.getEmbeddings(projectId, {
  limit: 500,
  include_text: true
})

// Compute dimensionality reduction
const result = await analyticsApi.getDimensionalityReduction(projectId, {
  method: 'pca',
  dimensions: 2,
  n_samples: 500
})

// Get similarity matrix
const matrix = await analyticsApi.getSimilarityMatrix(projectId, {
  scope: 'document',
  max_items: 20
})

// Test retrieval
const results = await analyticsApi.testRetrieval(projectId, {
  query: 'test query',
  top_k: 10
})
```

### Visualization Components

#### EmbeddingVisualization
Interactive scatter plot with method selection (PCA, t-SNE, UMAP) and dimension toggle (2D/3D):

```typescript
<EmbeddingVisualization projectId={projectId} />
```

#### SimilarityHeatmap
Heatmap showing cosine similarity between documents or chunks:

```typescript
<SimilarityHeatmap
  projectId={projectId}
  documents={documents}
/>
```

#### EmbeddingTable
Searchable data table with pagination and CSV export:

```typescript
<EmbeddingTable projectId={projectId} />
```

#### RetrievalTester
Query testing interface for evaluating RAG retrieval:

```typescript
<RetrievalTester projectId={projectId} />
```

### Educational Tooltips

Use `InfoTooltip` component to explain technical terms:

```typescript
import { InfoTooltip } from '@/components/ui/info-tooltip'

<div className="flex items-center">
  <label>Embedding Dimension</label>
  <InfoTooltip content="The size of the vector representation for each text chunk. Higher dimensions can capture more nuanced semantic meaning." />
</div>
```

## Testing

```bash
# Run tests (when configured)
npm test

# Run in watch mode
npm run test:watch

# E2E tests with Playwright (when configured)
npm run test:e2e
```

## Build and Deployment

```bash
# Create production build
npm run build

# Preview production build locally
npm run start
```

The build output will be in `.next/` directory.

### Deployment Options

- **Vercel**: Native Next.js deployment platform (recommended)
- **Docker**: Use included Dockerfile for containerization
- **Static Export**: Configure for static site generation if needed

## Troubleshooting

### Port Already in Use
```bash
# Use different port
PORT=3001 npm run dev
```

### WebSocket Connection Issues
- Ensure backend is running
- Check NEXT_PUBLIC_WS_URL in .env.local
- Verify CORS settings in backend

### Build Errors
```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

## Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Zustand](https://github.com/pmndrs/zustand)
- [TanStack Query](https://tanstack.com/query/latest)
- [Socket.IO Client](https://socket.io/docs/v4/client-api/)
