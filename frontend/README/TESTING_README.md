# Frontend Testing Documentation

This document provides comprehensive documentation for testing the DAA Chatbot frontend application.

## Table of Contents

- [Overview](#overview)
- [Testing Stack](#testing-stack)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Testing Patterns](#testing-patterns)
- [Component Testing](#component-testing)
- [Integration Testing](#integration-testing)
- [E2E Testing](#e2e-testing)
- [Best Practices](#best-practices)

## Overview

The frontend uses **Jest** and **React Testing Library** for unit and integration tests, and **Playwright** for end-to-end testing.

## Testing Stack

- **Jest** (29+): Test framework
- **React Testing Library** (14+): Component testing
- **@testing-library/user-event** (14+): User interaction simulation
- **MSW** (Mock Service Worker): API mocking
- **Playwright** (optional): E2E testing

## Test Structure

```
frontend/
├── __tests__/
│   ├── components/
│   │   ├── ui/
│   │   │   └── button.test.tsx
│   │   ├── chat/
│   │   │   ├── MessageList.test.tsx
│   │   │   └── MessageInput.test.tsx
│   │   └── projects/
│   │       └── ProjectCard.test.tsx
│   ├── hooks/
│   │   └── useWebSocket.test.ts
│   ├── lib/
│   │   └── api.test.ts
│   └── integration/
│       └── chat-flow.test.tsx
├── e2e/
│   ├── projects.spec.ts
│   ├── chat.spec.ts
│   └── documents.spec.ts
└── jest.config.js
```

## Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Specific file
npm test -- MessageList

# E2E tests
npx playwright test

# E2E UI mode
npx playwright test --ui
```

## Testing Patterns

### Component Testing

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/components/ui/button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    await userEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders different variants', () => {
    const { container } = render(<Button variant="destructive">Delete</Button>);
    expect(container.firstChild).toHaveClass('bg-destructive');
  });
});
```

### Testing with React Query

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { ProjectList } from '@/components/projects/ProjectList';
import { server } from '../mocks/server';
import { rest } from 'msw';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('ProjectList', () => {
  it('displays projects', async () => {
    render(<ProjectList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Project 1')).toBeInTheDocument();
    });
  });

  it('handles error state', async () => {
    server.use(
      rest.get('/api/projects', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    render(<ProjectList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

### Testing Async Operations

```tsx
describe('MessageInput', () => {
  it('sends message on submit', async () => {
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} />);

    const input = screen.getByRole('textbox');
    await userEvent.type(input, 'Hello world');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith('Hello world');
    });
  });
});
```

## Component Testing

### UI Components

```tsx
// button.test.tsx
import { render } from '@testing-library/react';
import { Button } from '@/components/ui/button';

describe('Button', () => {
  it('supports all variants', () => {
    const variants = ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'];

    variants.forEach((variant) => {
      const { container } = render(<Button variant={variant as any}>Test</Button>);
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
```

### Chat Components

```tsx
// MessageList.test.tsx
import { render, screen } from '@testing-library/react';
import { MessageList } from '@/components/chat/MessageList';

const mockMessages = [
  { id: 1, role: 'user', content: 'Hello', created_at: '2025-01-07' },
  { id: 2, role: 'assistant', content: 'Hi!', created_at: '2025-01-07' },
];

describe('MessageList', () => {
  it('renders messages', () => {
    render(<MessageList chatId={1} messages={mockMessages} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi!')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<MessageList chatId={1} messages={[]} isLoading />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
```

## Integration Testing

```tsx
// chat-flow.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '@/components/chat/ChatInterface';

describe('Chat Flow', () => {
  it('completes full chat interaction', async () => {
    render(<ChatInterface chatId={1} projectId={1} />);

    // Type message
    const input = screen.getByRole('textbox');
    await userEvent.type(input, 'What is machine learning?');

    // Send message
    await userEvent.click(screen.getByRole('button', { name: /send/i }));

    // Wait for response
    await waitFor(
      () => {
        expect(screen.getByText(/machine learning/i)).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });
});
```

## E2E Testing

### Playwright Configuration

**File:** `playwright.config.ts`

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### E2E Test Example

**File:** `e2e/projects.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Projects', () => {
  test('create and delete project', async ({ page }) => {
    await page.goto('/projects');

    // Create project
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="name"]', 'Test Project');
    await page.click('button:has-text("Create")');

    // Verify created
    await expect(page.locator('text=Test Project')).toBeVisible();

    // Delete project
    await page.click('[data-testid="project-menu"]');
    await page.click('text=Delete');
    await page.click('button:has-text("Confirm")');

    // Verify deleted
    await expect(page.locator('text=Test Project')).not.toBeVisible();
  });
});
```

## Best Practices

### 1. Test User Behavior

```tsx
// ✅ Good: Test user perspective
it('allows user to send message', async () => {
  render(<ChatInterface />);
  await userEvent.type(screen.getByRole('textbox'), 'Hello');
  await userEvent.click(screen.getByRole('button', { name: /send/i }));
  expect(screen.getByText('Hello')).toBeInTheDocument();
});

// ❌ Bad: Test implementation
it('calls sendMessage function', () => {
  const { result } = renderHook(() => useSendMessage());
  result.current.sendMessage('Hello');
  expect(mockSocket.emit).toHaveBeenCalled();
});
```

### 2. Use Semantic Queries

```tsx
// ✅ Good: Accessible queries
screen.getByRole('button', { name: /submit/i });
screen.getByLabelText('Email');
screen.getByText('Welcome');

// ❌ Bad: Implementation details
screen.getByClassName('submit-btn');
screen.getByTestId('email-input');
```

### 3. Test Error States

```tsx
it('shows error when API fails', async () => {
  server.use(
    rest.post('/api/messages', (req, res, ctx) => {
      return res(ctx.status(500));
    })
  );

  render(<MessageInput />);
  await userEvent.click(screen.getByRole('button'));

  expect(await screen.findByText(/error/i)).toBeInTheDocument();
});
```

### 4. Clean Up

```tsx
afterEach(() => {
  cleanup();
  jest.clearAllMocks();
});
```

### 5. Mock External Dependencies

```tsx
// __mocks__/socket.io-client.ts
export const io = jest.fn(() => ({
  on: jest.fn(),
  emit: jest.fn(),
  disconnect: jest.fn(),
}));
```

## Additional Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
