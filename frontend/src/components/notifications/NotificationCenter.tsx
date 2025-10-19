'use client';

import React, { useState, useEffect } from 'react';
import {
  useDocumentUpdates,
  useProjectUpdates,
  DocumentStatusEvent,
  ProjectUpdateEvent,
} from '@/lib/websocket';
import { useToast } from '@/hooks/use-toast';
import { Bell, X, FileCheck, FileX, FilePlus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface Notification {
  id: string;
  type: 'document' | 'project' | 'system';
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
  icon?: React.ReactNode;
  variant?: 'default' | 'success' | 'error' | 'info';
}

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const { toast } = useToast();

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: Date.now(),
      read: false,
    };

    setNotifications((prev) => [newNotification, ...prev]);

    // Show toast for important notifications
    if (notification.variant === 'error' || notification.variant === 'success') {
      toast({
        title: notification.title,
        description: notification.message,
        variant: notification.variant === 'error' ? 'destructive' : 'default',
      });
    }
  };

  // Listen to document updates
  useDocumentUpdates((data: DocumentStatusEvent) => {
    if (data.status === 'completed') {
      addNotification({
        type: 'document',
        title: 'Document Processed',
        message: `Document #${data.document_id} has been processed successfully`,
        icon: <FileCheck className="h-4 w-4" />,
        variant: 'success',
      });
    } else if (data.status === 'failed') {
      addNotification({
        type: 'document',
        title: 'Processing Failed',
        message: `Document #${data.document_id} failed to process`,
        icon: <FileX className="h-4 w-4" />,
        variant: 'error',
      });
    }
  });

  // Listen to project updates
  useProjectUpdates((data: ProjectUpdateEvent) => {
    const notificationMap: Record<
      string,
      {
        title: string;
        message: (data: any) => string;
        icon: React.ReactNode;
        variant: 'default' | 'success' | 'error' | 'info';
      }
    > = {
      document_added: {
        title: 'Document Added',
        message: (d) => `${d.filename} has been added to the project`,
        icon: <FilePlus className="h-4 w-4" />,
        variant: 'info',
      },
      document_deleted: {
        title: 'Document Removed',
        message: (d) => `Document #${d.document_id} has been removed`,
        icon: <Trash2 className="h-4 w-4" />,
        variant: 'info',
      },
    };

    const config = notificationMap[data.type];
    if (config) {
      addNotification({
        type: 'project',
        title: config.title,
        message: config.message(data.data),
        icon: config.icon,
        variant: config.variant,
      });
    }
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAsRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const removeNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between px-4 py-2">
          <h3 className="font-semibold">Notifications</h3>
          {notifications.length > 0 && (
            <div className="flex gap-2">
              {unreadCount > 0 && (
                <Button variant="ghost" size="sm" onClick={markAllAsRead} className="h-7 text-xs">
                  Mark all read
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={clearAll} className="h-7 text-xs">
                Clear all
              </Button>
            </div>
          )}
        </div>

        <DropdownMenuSeparator />

        <ScrollArea className="h-[400px]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Bell className="h-8 w-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">No notifications</p>
            </div>
          ) : (
            <div className="space-y-1 p-2">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onRead={markAsRead}
                  onRemove={removeNotification}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

interface NotificationItemProps {
  notification: Notification;
  onRead: (id: string) => void;
  onRemove: (id: string) => void;
}

function NotificationItem({ notification, onRead, onRemove }: NotificationItemProps) {
  const variantStyles = {
    default: 'border-gray-200 dark:border-gray-700',
    success: 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950',
    error: 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950',
    info: 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950',
  };

  const getTimeAgo = (timestamp: number) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div
      className={cn(
        'p-3 rounded-lg border transition-colors cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800',
        !notification.read && 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800',
        notification.read && variantStyles[notification.variant || 'default']
      )}
      onClick={() => !notification.read && onRead(notification.id)}
    >
      <div className="flex items-start gap-3">
        {notification.icon && (
          <div className="mt-0.5 text-gray-600 dark:text-gray-400">{notification.icon}</div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-medium truncate">{notification.title}</h4>
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 -mt-1 -mr-1 shrink-0"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(notification.id);
              }}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{notification.message}</p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            {getTimeAgo(notification.timestamp)}
          </p>
        </div>
        {!notification.read && <div className="h-2 w-2 rounded-full bg-blue-500 shrink-0 mt-2" />}
      </div>
    </div>
  );
}

/**
 * Simple toast notification hook for one-off notifications
 */
export function useNotifications() {
  const { toast } = useToast();

  const notify = {
    success: (title: string, message?: string) => {
      toast({
        title,
        description: message,
        variant: 'default',
      });
    },
    error: (title: string, message?: string) => {
      toast({
        title,
        description: message,
        variant: 'destructive',
      });
    },
    info: (title: string, message?: string) => {
      toast({
        title,
        description: message,
      });
    },
  };

  return notify;
}
