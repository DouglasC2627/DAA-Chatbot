# Pages and Routing Documentation

This document provides comprehensive documentation for the Next.js App Router, page structure, and navigation in the DAA Chatbot frontend.

## Table of Contents

- [Overview](#overview)
- [App Router Architecture](#app-router-architecture)
- [Route Structure](#route-structure)
- [Pages](#pages)
  - [Home Page](#home-page)
  - [Projects Pages](#projects-pages)
  - [Chat Pages](#chat-pages)
  - [Documents Pages](#documents-pages)
  - [Analytics Page](#analytics-page)
  - [Settings Page](#settings-page)
- [Layouts](#layouts)
- [Navigation](#navigation)
- [Dynamic Routes](#dynamic-routes)
- [Route Groups](#route-groups)
- [Loading and Error States](#loading-and-error-states)
- [Best Practices](#best-practices)

## Overview

The DAA Chatbot frontend uses **Next.js 14 App Router** with the `app/` directory structure. This provides file-system based routing, layouts, server components, and enhanced navigation features.

**Key Features:**
- File-system based routing
- Nested layouts
- Server and Client Components
- Parallel routes
- Intercepting routes
- Loading and error states
- Metadata API for SEO

## App Router Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      app/                               │
│                   (Root Layout)                          │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
    ┌────▼────┐                 ┌───▼──────┐
    │  page.tsx │               │ Projects │
    │  (Home)  │               │  Routes  │
    └──────────┘               └────┬─────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐   ┌────▼────┐    ┌────▼────┐
              │ Documents │   │  Chat   │    │Analytics│
              └───────────┘   └─────────┘    └─────────┘
```

## Route Structure

```
app/
├── layout.tsx                  # Root layout (wraps all pages)
├── page.tsx                    # Home page (/)
├── globals.css                 # Global styles
│
├── projects/
│   ├── page.tsx               # Projects list (/projects)
│   └── [projectId]/
│       ├── page.tsx           # Project detail (/projects/:id)
│       └── documents/
│           └── page.tsx       # Project documents (/projects/:id/documents)
│
├── chat/
│   └── [chatId]/
│       └── page.tsx           # Chat interface (/chat/:id)
│
├── documents/
│   └── page.tsx               # All documents (/documents)
│
├── analytics/
│   └── page.tsx               # Analytics dashboard (/analytics)
│
└── settings/
    └── page.tsx               # Settings (/settings)
```

## Pages

### Home Page

**File:** `app/page.tsx`

**Route:** `/`

Landing page with quick actions and project overview.

```tsx
export default function HomePage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-4xl font-bold mb-8">
        Welcome to DAA Chatbot
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Create Project</CardTitle>
          </CardHeader>
          <CardContent>
            <ProjectCreate />
          </CardContent>
        </Card>

        {/* Recent Projects */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <ProjectList limit={5} />
          </CardContent>
        </Card>

        {/* Stats */}
        <Card>
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <StatsOverview />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

**Metadata:**
```tsx
export const metadata: Metadata = {
  title: 'DAA Chatbot - Local RAG Application',
  description: 'Privacy-focused chatbot with document understanding',
};
```

---

### Projects Pages

#### Projects List

**File:** `app/projects/page.tsx`

**Route:** `/projects`

Grid view of all projects with create/delete actions.

```tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { getProjects } from '@/lib/api';
import { ProjectList } from '@/components/projects/ProjectList';
import { ProjectCreate } from '@/components/projects/ProjectCreate';

export default function ProjectsPage() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="container py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Projects</h1>
        <ProjectCreate />
      </div>

      <ProjectList projects={projects} />
    </div>
  );
}
```

#### Project Detail

**File:** `app/projects/[projectId]/page.tsx`

**Route:** `/projects/:projectId`

Project dashboard with documents and chats.

```tsx
'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getProject } from '@/lib/api';

export default function ProjectPage() {
  const params = useParams();
  const projectId = parseInt(params.projectId as string);

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
  });

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-8">{project?.name}</h1>

      <Tabs defaultValue="chat">
        <TabsList>
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="chat">
          <ChatHistoryPanel projectId={projectId} />
        </TabsContent>

        <TabsContent value="documents">
          <DocumentList projectId={projectId} />
        </TabsContent>

        <TabsContent value="analytics">
          <EmbeddingVisualization projectId={projectId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

**Dynamic Params:**
```tsx
// Generate static params (optional for SSG)
export async function generateStaticParams() {
  const projects = await getProjects();

  return projects.map((project) => ({
    projectId: project.id.toString(),
  }));
}
```

#### Project Documents

**File:** `app/projects/[projectId]/documents/page.tsx`

**Route:** `/projects/:projectId/documents`

Document management for a specific project.

```tsx
export default function ProjectDocumentsPage() {
  const params = useParams();
  const projectId = parseInt(params.projectId as string);

  return (
    <div className="container py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Documents</h1>
        <DocumentUpload projectId={projectId} />
      </div>

      <DocumentList projectId={projectId} />
    </div>
  );
}
```

---

### Chat Pages

#### Chat Interface

**File:** `app/chat/[chatId]/page.tsx`

**Route:** `/chat/:chatId`

Full-screen chat interface with message history.

```tsx
'use client';

import { useParams } from 'next/navigation';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { useChatStore } from '@/stores/chatStore';

export default function ChatPage() {
  const params = useParams();
  const chatId = parseInt(params.chatId as string);

  const { currentChat } = useChatStore();

  return (
    <div className="h-screen flex flex-col">
      {/* Chat Header */}
      <div className="border-b px-6 py-4">
        <h1 className="text-xl font-semibold">
          {currentChat?.title || 'Chat'}
        </h1>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface chatId={chatId} projectId={currentChat?.project_id} />
      </div>
    </div>
  );
}
```

**Client Component:**
```tsx
// Mark as client component for real-time features
'use client';
```

---

### Documents Pages

#### All Documents

**File:** `app/documents/page.tsx`

**Route:** `/documents`

View all documents across all projects.

```tsx
export default function DocumentsPage() {
  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: getAllDocuments,
  });

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-8">All Documents</h1>

      <div className="mb-6 flex gap-4">
        {/* Filters */}
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Filter by project" />
          </SelectTrigger>
          <SelectContent>
            {/* Project options */}
          </SelectContent>
        </Select>

        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="pdf">PDF</SelectItem>
            <SelectItem value="docx">Word</SelectItem>
            <SelectItem value="txt">Text</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DocumentGrid documents={documents} />
    </div>
  );
}
```

---

### Analytics Page

**File:** `app/analytics/page.tsx`

**Route:** `/analytics`

Embedding visualization and analysis dashboard.

```tsx
'use client';

import { useState } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { EmbeddingVisualization } from '@/components/analytics/EmbeddingVisualization';
import { SimilarityHeatmap } from '@/components/analytics/SimilarityHeatmap';
import { EmbeddingStats } from '@/components/analytics/EmbeddingStats';
import { RetrievalTester } from '@/components/analytics/RetrievalTester';

export default function AnalyticsPage() {
  const { currentProject } = useProjectStore();
  const [activeTab, setActiveTab] = useState('embeddings');

  if (!currentProject) {
    return (
      <div className="container py-8">
        <p>Please select a project to view analytics.</p>
      </div>
    );
  }

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-8">Analytics Dashboard</h1>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="embeddings">Embeddings</TabsTrigger>
          <TabsTrigger value="similarity">Similarity</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
          <TabsTrigger value="retrieval">Retrieval Test</TabsTrigger>
        </TabsList>

        <TabsContent value="embeddings">
          <EmbeddingVisualization projectId={currentProject.id} />
        </TabsContent>

        <TabsContent value="similarity">
          <SimilarityHeatmap projectId={currentProject.id} />
        </TabsContent>

        <TabsContent value="stats">
          <EmbeddingStats projectId={currentProject.id} />
        </TabsContent>

        <TabsContent value="retrieval">
          <RetrievalTester projectId={currentProject.id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

---

### Settings Page

**File:** `app/settings/page.tsx`

**Route:** `/settings`

Application settings and configuration.

```tsx
export default function SettingsPage() {
  return (
    <div className="container max-w-4xl py-8">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="space-y-8">
        {/* LLM Settings */}
        <Card>
          <CardHeader>
            <CardTitle>LLM Configuration</CardTitle>
            <CardDescription>
              Configure language model settings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ModelSelector />
            <TemperatureSlider />
          </CardContent>
        </Card>

        {/* RAG Settings */}
        <Card>
          <CardHeader>
            <CardTitle>RAG Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <ChunkSizeInput />
            <RetrievalKInput />
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
          </CardHeader>
          <CardContent>
            <ThemeToggle />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

## Layouts

### Root Layout

**File:** `app/layout.tsx`

**Route:** All pages

Main application layout wrapping all pages.

```tsx
import { Inter } from 'next/font/google';
import { Toaster } from '@/components/ui/toaster';
import { QueryProvider } from '@/components/providers/QueryProvider';
import { ThemeProvider } from '@/components/theme-provider';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
        >
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

**Metadata:**
```tsx
export const metadata: Metadata = {
  title: {
    default: 'DAA Chatbot',
    template: '%s | DAA Chatbot',
  },
  description: 'Local RAG chatbot for document Q&A',
  icons: {
    icon: '/favicon.ico',
  },
};
```

### Nested Layouts

Create layouts for route segments:

```tsx
// app/projects/layout.tsx
export default function ProjectsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex">
      <ProjectSidebar />
      <main className="flex-1">{children}</main>
    </div>
  );
}
```

---

## Navigation

### Link Component

Use Next.js `Link` for client-side navigation:

```tsx
import Link from 'next/link';

<Link href="/projects">
  View Projects
</Link>

// With dynamic route
<Link href={`/projects/${project.id}`}>
  {project.name}
</Link>
```

### useRouter Hook

Programmatic navigation:

```tsx
'use client';

import { useRouter } from 'next/navigation';

function MyComponent() {
  const router = useRouter();

  const handleClick = () => {
    router.push('/projects');
    // or
    router.replace('/projects'); // No history entry
    // or
    router.back(); // Go back
  };

  return <button onClick={handleClick}>Navigate</button>;
}
```

### usePathname Hook

Get current path:

```tsx
'use client';

import { usePathname } from 'next/navigation';

function NavItem({ href, children }) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={isActive ? 'active' : ''}
    >
      {children}
    </Link>
  );
}
```

### useParams Hook

Access route parameters:

```tsx
'use client';

import { useParams } from 'next/navigation';

function ProjectPage() {
  const params = useParams();
  const projectId = params.projectId; // From /projects/[projectId]

  return <div>Project ID: {projectId}</div>;
}
```

---

## Dynamic Routes

### Single Dynamic Segment

**Route:** `/projects/[projectId]/page.tsx`

**Matches:** `/projects/1`, `/projects/abc`, etc.

```tsx
export default function ProjectPage({ params }: { params: { projectId: string } }) {
  return <div>Project: {params.projectId}</div>;
}
```

### Multiple Dynamic Segments

**Route:** `/projects/[projectId]/chat/[chatId]/page.tsx`

**Matches:** `/projects/1/chat/5`

```tsx
export default function ChatPage({
  params,
}: {
  params: { projectId: string; chatId: string };
}) {
  return (
    <div>
      Project: {params.projectId}, Chat: {params.chatId}
    </div>
  );
}
```

### Catch-all Routes

**Route:** `/docs/[...slug]/page.tsx`

**Matches:** `/docs/a`, `/docs/a/b`, `/docs/a/b/c`

```tsx
export default function DocsPage({
  params,
}: {
  params: { slug: string[] };
}) {
  return <div>Path: {params.slug.join('/')}</div>;
}
```

---

## Route Groups

Organize routes without affecting URL structure:

```
app/
├── (marketing)/
│   ├── page.tsx           # /
│   └── about/
│       └── page.tsx       # /about
│
└── (app)/
    ├── layout.tsx         # Shared layout for app routes
    ├── projects/
    │   └── page.tsx       # /projects
    └── chat/
        └── page.tsx       # /chat
```

Group pages share layout but don't add to URL.

---

## Loading and Error States

### Loading UI

**File:** `app/projects/loading.tsx`

Automatically shown while page loads:

```tsx
export default function Loading() {
  return (
    <div className="flex justify-center items-center h-screen">
      <Spinner className="h-12 w-12" />
    </div>
  );
}
```

### Error UI

**File:** `app/projects/error.tsx`

Handles errors in page:

```tsx
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
      <p className="text-muted-foreground mb-4">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

### Not Found

**File:** `app/not-found.tsx`

404 page:

```tsx
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h2 className="text-4xl font-bold mb-4">404</h2>
      <p className="text-xl mb-8">Page not found</p>
      <Link href="/">
        <Button>Go home</Button>
      </Link>
    </div>
  );
}
```

---

## Best Practices

### 1. Server vs Client Components

```tsx
// ✅ Good: Server component by default (faster)
export default function ProjectsPage() {
  const projects = await getProjects(); // Can use async/await
  return <ProjectList projects={projects} />;
}

// ✅ Good: Client component when needed
'use client';

export default function InteractivePage() {
  const [state, setState] = useState(0);
  return <div onClick={() => setState(s => s + 1)}>{state}</div>;
}
```

### 2. Data Fetching

```tsx
// ✅ Good: Use React Query for client components
'use client';

export default function ClientPage() {
  const { data } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  return <div>{/* ... */}</div>;
}

// ✅ Good: Direct fetch in server components
export default async function ServerPage() {
  const projects = await getProjects();
  return <div>{/* ... */}</div>;
}
```

### 3. Metadata

```tsx
// Static metadata
export const metadata: Metadata = {
  title: 'Projects',
  description: 'Manage your projects',
};

// Dynamic metadata
export async function generateMetadata({ params }): Promise<Metadata> {
  const project = await getProject(params.id);

  return {
    title: project.name,
    description: project.description,
  };
}
```

### 4. Route Organization

```tsx
// ✅ Good: Clear, nested structure
app/
├── projects/
│   ├── page.tsx                    # /projects
│   └── [projectId]/
│       ├── page.tsx                # /projects/:id
│       └── documents/
│           └── page.tsx            # /projects/:id/documents

// ❌ Bad: Flat structure with complex routes
app/
├── projects.tsx
├── project-detail.tsx
├── project-documents.tsx
```

### 5. Loading States

```tsx
// ✅ Good: Use loading.tsx for automatic loading UI
// app/projects/loading.tsx
export default function Loading() {
  return <Skeleton />;
}

// ✅ Good: Suspense for granular control
<Suspense fallback={<Spinner />}>
  <ProjectList />
</Suspense>
```

### 6. Type-Safe Routing

```tsx
// Define route types
type ProjectParams = { projectId: string };
type ChatParams = { projectId: string; chatId: string };

// Use in components
export default function ProjectPage({ params }: { params: ProjectParams }) {
  const id = parseInt(params.projectId);
  // ...
}
```

---

## Additional Resources

- [Next.js App Router Documentation](https://nextjs.org/docs/app)
- [Next.js Routing](https://nextjs.org/docs/app/building-your-application/routing)
- [Next.js Data Fetching](https://nextjs.org/docs/app/building-your-application/data-fetching)
- [Next.js Metadata](https://nextjs.org/docs/app/building-your-application/optimizing/metadata)
