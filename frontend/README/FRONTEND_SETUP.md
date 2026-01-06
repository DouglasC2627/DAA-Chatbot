# Frontend Setup Documentation

This document provides comprehensive setup instructions for the DAA Chatbot frontend application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [UI Component Library](#ui-component-library)
- [Theming System](#theming-system)
- [Layout Components](#layout-components)
- [Development Workflow](#development-workflow)
- [Testing Setup](#testing-setup)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

The DAA Chatbot frontend is built with modern web technologies providing a responsive, accessible, and performant user interface.

**Technology Stack:**
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5+
- **Styling**: Tailwind CSS 3.4+ with custom theme
- **UI Library**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Forms**: React Hook Form + Zod validation

## Prerequisites

Before setting up the frontend, ensure you have:

- **Node.js**: Version 18.0 or higher
- **npm**: Version 9.0 or higher (comes with Node.js)
- **Git**: For version control
- **Code Editor**: VS Code recommended with extensions:
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
  - TypeScript and JavaScript Language Features

**Verify Installation:**
```bash
node --version  # Should show v18.0.0 or higher
npm --version   # Should show v9.0.0 or higher
```

## Initial Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd daa-chatbot/frontend

# Install dependencies
npm install
```

### 2. Environment Configuration

Create `.env.local` file in the frontend root:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Optional: Environment indicator
NEXT_PUBLIC_ENV=development
```

**Important Notes:**
- Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser
- Never commit `.env.local` to version control
- Create `.env.production` for production builds

### 3. Start Development Server

```bash
# Start the dev server
npm run dev

# Server will start at http://localhost:3000
```

**First-time startup:**
- Initial compilation takes 5-10 seconds
- Subsequent hot reloads are much faster
- Open http://localhost:3000 in your browser

## Development Environment

### Available Scripts

```bash
# Development
npm run dev          # Start dev server with hot reload
npm run build        # Create production build
npm run start        # Start production server
npm run lint         # Run ESLint
npm run lint:fix     # Auto-fix ESLint issues

# Type checking
npm run type-check   # Run TypeScript compiler check
```

### IDE Configuration

**VS Code Settings** (`.vscode/settings.json`):
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"],
    ["cn\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ]
}
```

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next",
    "styled-components.vscode-styled-components"
  ]
}
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx           # Home page
│   │   ├── layout.tsx         # Root layout
│   │   ├── globals.css        # Global styles
│   │   ├── projects/          # Project pages
│   │   ├── chat/              # Chat pages
│   │   ├── documents/         # Document pages
│   │   └── analytics/         # Analytics pages
│   │
│   ├── components/            # React components
│   │   ├── ui/               # shadcn/ui primitives
│   │   ├── chat/             # Chat components
│   │   ├── documents/        # Document components
│   │   ├── projects/         # Project components
│   │   ├── analytics/        # Analytics components
│   │   ├── layout/           # Layout components
│   │   └── providers/        # Context providers
│   │
│   ├── lib/                  # Utilities
│   │   ├── api.ts           # API client
│   │   ├── utils.ts         # Helper functions
│   │   └── websocket.ts     # WebSocket client
│   │
│   ├── stores/              # Zustand stores
│   │   ├── chatStore.ts
│   │   ├── projectStore.ts
│   │   └── documentStore.ts
│   │
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   │
│   └── hooks/               # Custom hooks
│       └── useWebSocket.ts
│
├── public/                  # Static assets
│   ├── favicon.ico
│   └── images/
│
├── .env.local              # Environment variables (not in git)
├── .env.example            # Example environment file
├── components.json         # shadcn/ui configuration
├── next.config.mjs         # Next.js configuration
├── tailwind.config.ts      # Tailwind configuration
├── tsconfig.json           # TypeScript configuration
├── package.json            # Dependencies and scripts
└── README.md              # Main documentation
```

## UI Component Library

### shadcn/ui Setup

The project uses shadcn/ui, a collection of re-usable components built with Radix UI and Tailwind CSS.

**Configuration** (`components.json`):
```json
{
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

### Adding New Components

```bash
# Add a single component
npx shadcn-ui@latest add button

# Add multiple components
npx shadcn-ui@latest add card dialog input

# List available components
npx shadcn-ui@latest add
```

### Installed Components

The following shadcn/ui components are pre-installed:

**Form Components:**
- `button` - Versatile button with variants
- `input` - Text input field
- `textarea` - Multi-line text input
- `select` - Dropdown select
- `label` - Form label
- `form` - Form wrapper with validation

**Layout Components:**
- `card` - Content container
- `dialog` - Modal dialog
- `sheet` - Slide-out panel
- `scroll-area` - Custom scrollbar
- `collapsible` - Expandable section

**Feedback Components:**
- `toast` - Toast notifications
- `alert` - Alert messages
- `progress` - Progress bar
- `badge` - Status badge

**Utility Components:**
- `tooltip` - Hover tooltips
- `dropdown-menu` - Dropdown menu
- `alert-dialog` - Confirmation dialog
- `slider` - Range slider
- `switch` - Toggle switch

## Theming System

### CSS Variables Setup

**File:** `src/app/globals.css`

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    /* ... more variables */
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    /* ... more variables */
  }
}
```

### Theme Provider Setup

**File:** `src/components/theme-provider.tsx`

```tsx
'use client';

import { ThemeProvider as NextThemesProvider } from 'next-themes';

export function ThemeProvider({ children, ...props }) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
```

**Integration in Root Layout:**

```tsx
// app/layout.tsx
import { ThemeProvider } from '@/components/theme-provider';

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

### Dark Mode Toggle

```tsx
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
    >
      <Sun className="rotate-0 scale-100 dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute rotate-90 scale-0 dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
```

## Layout Components

### Header Component

**File:** `src/components/layout/Header.tsx`

Features:
- Sticky positioning with backdrop blur
- Logo and navigation links
- Theme toggle
- Mobile menu trigger
- Project selector

### Sidebar Component

**File:** `src/components/layout/Sidebar.tsx`

Features:
- Fixed position navigation
- Active route highlighting
- Icon-based menu items
- Collapsible on mobile

### Main Layout Wrapper

```tsx
// src/components/layout/MainLayout.tsx
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';

export function MainLayout({ children }) {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
      <Footer />
    </div>
  );
}
```

## Development Workflow

### Creating a New Page

```bash
# 1. Create page file
mkdir -p src/app/new-feature
touch src/app/new-feature/page.tsx

# 2. Add page component
# src/app/new-feature/page.tsx
export default function NewFeaturePage() {
  return <div>New Feature</div>;
}

# 3. Add to navigation in Header/Sidebar
```

### Creating a New Component

```bash
# 1. Create component file
mkdir -p src/components/feature-name
touch src/components/feature-name/ComponentName.tsx

# 2. Define component with TypeScript
export interface ComponentNameProps {
  // props
}

export function ComponentName({ ...props }: ComponentNameProps) {
  return <div>Component</div>;
}

# 3. Export from index if needed
# src/components/feature-name/index.ts
export { ComponentName } from './ComponentName';
```

### Styling Guidelines

```tsx
// Use Tailwind classes
<div className="flex items-center gap-4 p-6">

// Combine with cn() utility for conditional classes
import { cn } from '@/lib/utils';

<div className={cn(
  'base-classes',
  isActive && 'active-classes',
  className // Allow prop override
)}>

// Use CSS variables for theme colors
<div className="bg-primary text-primary-foreground">
```

## Testing Setup

### Component Testing

Install testing dependencies:

```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom
```

**Jest Configuration** (`jest.config.js`):

```javascript
const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};

module.exports = createJestConfig(customJestConfig);
```

### Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

## Troubleshooting

### Port Already in Use

```bash
# Use different port
PORT=3001 npm run dev

# Or kill process using port 3000
lsof -ti:3000 | xargs kill -9
```

### Module Not Found Errors

```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
```

### TypeScript Errors

```bash
# Clear TypeScript cache
rm -rf .next tsconfig.tsbuildinfo

# Restart dev server
npm run dev
```

### Styling Issues

```bash
# Rebuild Tailwind
npm run build

# Check globals.css is imported in layout.tsx
```

### WebSocket Connection Issues

Check `.env.local` has correct URLs:
```bash
NEXT_PUBLIC_WS_URL=ws://localhost:8000  # Not http://
```

Ensure backend is running on port 8000.

## Best Practices

### 1. File Organization

```tsx
// ✅ Good: Organized by feature
src/components/
  chat/
    MessageList.tsx
    MessageInput.tsx
  documents/
    DocumentUpload.tsx
    DocumentList.tsx

// ❌ Bad: Flat structure
src/components/
  MessageList.tsx
  MessageInput.tsx
  DocumentUpload.tsx
  DocumentList.tsx
```

### 2. Component Structure

```tsx
// ✅ Good: Clean component structure
interface Props {
  title: string;
}

export function MyComponent({ title }: Props) {
  const [state, setState] = useState();

  useEffect(() => {
    // side effects
  }, []);

  return <div>{title}</div>;
}
```

### 3. Import Organization

```tsx
// 1. React imports
import { useState, useEffect } from 'react';

// 2. External libraries
import { useQuery } from '@tanstack/react-query';

// 3. Internal components
import { Button } from '@/components/ui/button';

// 4. Utilities
import { cn } from '@/lib/utils';

// 5. Types
import type { Project } from '@/types';

// 6. Styles (if any)
import './styles.css';
```

### 4. Type Safety

```tsx
// ✅ Good: Explicit types
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  onClick: () => void;
  children: React.ReactNode;
}

// ❌ Bad: Any types
function Button(props: any) { }
```

### 5. Environment Variables

```tsx
// ✅ Good: Type-safe config
const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL!,
  wsUrl: process.env.NEXT_PUBLIC_WS_URL!,
} as const;

// ❌ Bad: Direct access everywhere
fetch(process.env.NEXT_PUBLIC_API_URL + '/api');
```

## Additional Resources

### Documentation
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Radix UI](https://www.radix-ui.com/)

### Learning Resources
- [Next.js Learn](https://nextjs.org/learn)
- [TypeScript for React](https://react-typescript-cheatsheet.netlify.app/)
- [Tailwind CSS Tutorial](https://tailwindcss.com/docs/utility-first)

### Community
- [Next.js GitHub](https://github.com/vercel/next.js)
- [shadcn/ui GitHub](https://github.com/shadcn/ui)
- [React Community Discord](https://discord.gg/react)

---

**Setup Complete!** You now have a fully configured Next.js frontend with modern tooling, component library, and development environment.
