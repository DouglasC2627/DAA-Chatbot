'use client';

import { useCallback } from 'react';
import { useProjectUpdates, ProjectUpdateEvent } from '@/lib/websocket';
import { useQueryClient } from '@tanstack/react-query';
import { useNotifications } from '@/components/notifications/NotificationCenter';

interface RealtimeChatUpdatesProps {
  projectId: number;
  onNewMessage?: (chatId: number) => void;
  onChatUpdated?: (chatId: number) => void;
  onChatDeleted?: (chatId: number) => void;
}

/**
 * Component that listens to real-time chat updates and keeps the UI in sync
 */
export function RealtimeChatUpdates({
  projectId,
  onNewMessage,
  onChatUpdated,
  onChatDeleted,
}: RealtimeChatUpdatesProps) {
  const queryClient = useQueryClient();
  const notify = useNotifications();

  // Memoized callback to prevent infinite loops
  const handleProjectUpdate = useCallback(
    (data: ProjectUpdateEvent) => {
      // Handle different update types
      switch (data.type) {
        case 'chat_message_added':
          // Invalidate chat messages query to refetch
          if (data.data.chat_id) {
            queryClient.invalidateQueries({
              queryKey: ['chat', 'messages', data.data.chat_id],
            });
            onNewMessage?.(data.data.chat_id);
          }
          break;

        case 'chat_created':
          // Invalidate chats list
          queryClient.invalidateQueries({
            queryKey: ['chats', projectId],
          });
          break;

        case 'chat_updated':
          // Invalidate specific chat and chats list
          if (data.data.chat_id) {
            queryClient.invalidateQueries({
              queryKey: ['chat', data.data.chat_id],
            });
            queryClient.invalidateQueries({
              queryKey: ['chats', projectId],
            });
            onChatUpdated?.(data.data.chat_id);
          }
          break;

        case 'chat_deleted':
          // Invalidate chats list
          queryClient.invalidateQueries({
            queryKey: ['chats', projectId],
          });
          if (data.data.chat_id) {
            // Remove specific chat from cache
            queryClient.removeQueries({
              queryKey: ['chat', data.data.chat_id],
            });
            onChatDeleted?.(data.data.chat_id);
          }
          notify.info('Chat Deleted', 'A chat has been removed from this project');
          break;

        case 'document_added':
          // Invalidate documents list
          queryClient.invalidateQueries({
            queryKey: ['documents', projectId],
          });
          break;

        case 'document_deleted':
          // Invalidate documents list
          queryClient.invalidateQueries({
            queryKey: ['documents', projectId],
          });
          break;

        default:
          // Handle unknown update types
          console.log('[RealtimeChatUpdates] Unknown update type:', data.type);
      }
    },
    [queryClient, projectId, onNewMessage, onChatUpdated, onChatDeleted, notify]
  );

  useProjectUpdates(handleProjectUpdate);

  return null; // This is a logic-only component
}

/**
 * Hook for real-time chat synchronization
 */
export function useRealtimeChatSync(projectId: number, chatId?: number) {
  const queryClient = useQueryClient();

  // Memoized callback to prevent infinite loops
  const handleProjectUpdate = useCallback(
    (data: ProjectUpdateEvent) => {
      if (chatId && data.type === 'chat_message_added' && data.data.chat_id === chatId) {
        // Invalidate messages for the active chat
        queryClient.invalidateQueries({
          queryKey: ['chat', 'messages', chatId],
        });
      }

      if (data.type === 'document_added' || data.type === 'document_deleted') {
        // Invalidate documents list when documents change
        queryClient.invalidateQueries({
          queryKey: ['documents', projectId],
        });
      }
    },
    [queryClient, chatId, projectId]
  );

  useProjectUpdates(handleProjectUpdate);
}
