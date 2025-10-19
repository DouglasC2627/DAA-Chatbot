'use client';

import React from 'react';
import { Wifi, WifiOff, Loader2, AlertCircle } from 'lucide-react';
import { useWebSocketConnection, ConnectionStatus as WSConnectionStatus } from '@/lib/websocket';
import { cn } from '@/lib/utils';

interface ConnectionStatusProps {
  className?: string;
  showLabel?: boolean;
}

const statusConfig: Record<
  WSConnectionStatus,
  {
    icon: React.ReactNode;
    label: string;
    color: string;
    bgColor: string;
  }
> = {
  connected: {
    icon: <Wifi className="h-4 w-4" />,
    label: 'Connected',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  disconnected: {
    icon: <WifiOff className="h-4 w-4" />,
    label: 'Disconnected',
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
  },
  connecting: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    label: 'Connecting...',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  reconnecting: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    label: 'Reconnecting...',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
  },
  error: {
    icon: <AlertCircle className="h-4 w-4" />,
    label: 'Connection Error',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
};

export function ConnectionStatus({ className, showLabel = true }: ConnectionStatusProps) {
  const { status } = useWebSocketConnection();
  const config = statusConfig[status];

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 rounded-full transition-colors',
        config.bgColor,
        className
      )}
    >
      <span className={cn(config.color)}>{config.icon}</span>
      {showLabel && <span className={cn('text-sm font-medium', config.color)}>{config.label}</span>}
    </div>
  );
}

export function ConnectionStatusDot({ className }: { className?: string }) {
  const { status } = useWebSocketConnection();

  const dotColor = {
    connected: 'bg-green-500',
    disconnected: 'bg-gray-400',
    connecting: 'bg-blue-500 animate-pulse',
    reconnecting: 'bg-yellow-500 animate-pulse',
    error: 'bg-red-500',
  }[status];

  return (
    <div
      className={cn('h-2 w-2 rounded-full', dotColor, className)}
      title={statusConfig[status].label}
    />
  );
}
