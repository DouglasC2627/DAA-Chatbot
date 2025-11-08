'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useProjectStore } from '@/stores/projectStore';
import { useChatStore } from '@/stores/chatStore';
import ChatInterface from '@/components/chat/ChatInterface';
import { chatApi, projectApi } from '@/lib/api';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ChatPageProps {
  params: {
    chatId: string;
  };
}

export default function ChatPage({ params }: ChatPageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<number | null>(null);

  const setCurrentProject = useProjectStore((state) => state.setCurrentProject);
  const setCurrentChat = useChatStore((state) => state.setCurrentChat);
  const addChat = useChatStore((state) => state.addChat);

  // Convert URL param to number
  const chatIdNum = Number(params.chatId);

  // Get initial message from URL query params (if navigating from ProjectChatInput)
  const initialMessage = searchParams.get('initialMessage');

  useEffect(() => {
    const loadChatAndProject = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Fetch chat details to get the project ID
        const chat = await chatApi.get(chatIdNum);

        if (!chat) {
          setError('Chat not found');
          setTimeout(() => router.push('/projects'), 2000);
          return;
        }

        // Set the project ID
        setProjectId(chat.project_id);

        // Update stores
        setCurrentProject(chat.project_id);
        setCurrentChat(chatIdNum);
        addChat(chat);

        // Load project details to ensure it's in the store
        try {
          const project = await projectApi.get(chat.project_id);
          useProjectStore.getState().updateProject(project.id, project);
        } catch (err) {
          console.error('Failed to load project details:', err);
          // Non-fatal error, continue anyway
        }

        setIsLoading(false);
      } catch (err) {
        console.error('Failed to load chat:', err);
        setError('Failed to load chat. Redirecting to projects...');
        toast({
          title: 'Error',
          description: 'Failed to load chat',
          variant: 'destructive',
        });
        setTimeout(() => router.push('/projects'), 2000);
      }
    };

    if (chatIdNum) {
      loadChatAndProject();
    }
  }, [chatIdNum, router, setCurrentProject, setCurrentChat, addChat, toast]);

  // Show loading state while fetching chat details
  if (isLoading || projectId === null) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading chat...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <ChatInterface
      projectId={projectId}
      chatId={chatIdNum}
      initialMessage={initialMessage || undefined}
    />
  );
}
