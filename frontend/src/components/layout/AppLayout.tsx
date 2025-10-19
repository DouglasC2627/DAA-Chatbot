'use client';

import React, { ReactNode } from 'react';
import { WebSocketProvider } from '@/components/providers/WebSocketProvider';
import { NotificationCenter } from '@/components/notifications/NotificationCenter';
import { ConnectionStatus } from '@/components/chat/ConnectionStatus';
import { usePathname } from 'next/navigation';

interface AppLayoutProps {
  children: ReactNode;
}

/**
 * Main application layout with WebSocket integration, notifications, and connection status
 */
export function AppLayout({ children }: AppLayoutProps) {
  const pathname = usePathname();

  // Don't show WebSocket features on auth/public pages
  const isAuthPage = pathname?.startsWith('/auth') || pathname === '/';

  return (
    <WebSocketProvider showOfflineAlert={!isAuthPage} autoConnect={!isAuthPage}>
      <div className="min-h-screen flex flex-col">
        {/* Header */}
        {!isAuthPage && <AppHeader />}

        {/* Main Content */}
        <main className="flex-1">{children}</main>

        {/* Footer (optional) */}
        {!isAuthPage && <AppFooter />}
      </div>
    </WebSocketProvider>
  );
}

/**
 * Application header with navigation and status indicators
 */
function AppHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold">DAA Chatbot</h1>
          {/* Add navigation links here */}
        </div>

        <div className="flex items-center gap-2">
          {/* Connection Status Indicator */}
          <ConnectionStatus showLabel={false} />

          {/* Notification Center */}
          <NotificationCenter />

          {/* User menu, settings, etc */}
        </div>
      </div>
    </header>
  );
}

/**
 * Application footer
 */
function AppFooter() {
  return (
    <footer className="border-t py-4">
      <div className="container px-4">
        <p className="text-xs text-center text-gray-600 dark:text-gray-400">
          DAA Chatbot - Local RAG System
        </p>
      </div>
    </footer>
  );
}
