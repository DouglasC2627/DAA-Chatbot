'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useWebSocketConnection, ConnectionStatus as WSConnectionStatus } from '@/lib/websocket';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { WifiOff, Wifi } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WebSocketContextValue {
  status: WSConnectionStatus;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
}

interface WebSocketProviderProps {
  children: React.ReactNode;
  showOfflineAlert?: boolean;
  autoConnect?: boolean;
}

export function WebSocketProvider({
  children,
  showOfflineAlert = true,
  autoConnect = true,
}: WebSocketProviderProps) {
  const { status, isConnected, connect, disconnect } = useWebSocketConnection({ autoConnect });
  const [isOnline, setIsOnline] = useState(true);
  const [showReconnectBanner, setShowReconnectBanner] = useState(false);

  // Detect browser online/offline status
  useEffect(() => {
    const handleOnline = () => {
      console.log('[WebSocketProvider] Browser is online');
      setIsOnline(true);
      // Auto-reconnect WebSocket when coming back online
      if (!isConnected) {
        connect().catch(console.error);
      }
    };

    const handleOffline = () => {
      console.log('[WebSocketProvider] Browser is offline');
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check initial state
    setIsOnline(navigator.onLine);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [connect, isConnected]);

  // Show reconnect banner when connection is lost but browser is online
  useEffect(() => {
    if (isOnline && (status === 'disconnected' || status === 'error')) {
      setShowReconnectBanner(true);
    } else {
      setShowReconnectBanner(false);
    }
  }, [status, isOnline]);

  const handleReconnect = async () => {
    try {
      await connect();
    } catch (error) {
      console.error('[WebSocketProvider] Failed to reconnect:', error);
    }
  };

  return (
    <WebSocketContext.Provider value={{ status, isConnected, connect, disconnect }}>
      {/* Offline Alert */}
      {showOfflineAlert && !isOnline && (
        <Alert className="rounded-none border-x-0 border-t-0 bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
          <WifiOff className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>You are currently offline. Some features may not be available.</span>
          </AlertDescription>
        </Alert>
      )}

      {/* WebSocket Disconnected Banner */}
      {showOfflineAlert && showReconnectBanner && (
        <Alert className="rounded-none border-x-0 border-t-0 bg-orange-50 dark:bg-orange-950 border-orange-200 dark:border-orange-800">
          <WifiOff className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>
              Real-time updates disconnected.{' '}
              {status === 'reconnecting' ? 'Attempting to reconnect...' : 'Click to reconnect.'}
            </span>
            {status !== 'reconnecting' && (
              <Button size="sm" variant="outline" onClick={handleReconnect}>
                Reconnect
              </Button>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Connection Restored Banner */}
      {isOnline && status === 'connected' && showReconnectBanner === false && (
        <ConnectionRestoredBanner />
      )}

      {children}
    </WebSocketContext.Provider>
  );
}

/**
 * Shows a temporary banner when connection is restored
 */
function ConnectionRestoredBanner() {
  const [show, setShow] = useState(false);
  const [justConnected, setJustConnected] = useState(false);

  useEffect(() => {
    // Only show if we just connected (not on initial mount)
    if (!justConnected) {
      setJustConnected(true);
      return;
    }

    setShow(true);
    const timer = setTimeout(() => {
      setShow(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, [justConnected]);

  if (!show) return null;

  return (
    <Alert className="rounded-none border-x-0 border-t-0 bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
      <Wifi className="h-4 w-4" />
      <AlertDescription>
        <span>Connection restored. Real-time updates are now active.</span>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Hook to detect if user is offline
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    setIsOnline(navigator.onLine);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

/**
 * Component that shows when a feature is unavailable offline
 */
export function OfflineGuard({
  children,
  fallback,
}: {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const isOnline = useOnlineStatus();
  const { isConnected } = useWebSocket();

  if (!isOnline || !isConnected) {
    return (
      fallback || (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <WifiOff className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold mb-2">Offline</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            This feature requires an active connection. Please check your internet connection and
            try again.
          </p>
        </div>
      )
    );
  }

  return <>{children}</>;
}
