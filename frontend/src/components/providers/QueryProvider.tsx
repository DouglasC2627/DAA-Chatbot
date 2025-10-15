'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState, type ReactNode } from 'react';

// ============================================================================
// Query Client Configuration
// ============================================================================

const createQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Default options for all queries
        staleTime: 1000 * 60 * 5, // 5 minutes
        gcTime: 1000 * 60 * 10, // 10 minutes (formerly cacheTime)
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        retry: 1,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      },
      mutations: {
        // Default options for all mutations
        retry: 0,
        onError: (error) => {
          // Global error handling for mutations
          console.error('Mutation error:', error);
        },
      },
    },
  });
};

// ============================================================================
// Query Provider Component
// ============================================================================

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  // Create a stable QueryClient instance
  const [queryClient] = useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Only show devtools in development */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom" />
      )}
    </QueryClientProvider>
  );
}
