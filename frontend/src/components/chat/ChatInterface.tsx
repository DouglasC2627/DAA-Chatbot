'use client';

import { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useProjectStore, selectProjects } from '@/stores/projectStore';
import { useChatStore, selectCurrentChat, selectCurrentMessages } from '@/stores/chatStore';
import { MessageRole, Message } from '@/types';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare, Settings, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { useWebSocketConnection, useProjectRoom, useChatStream } from '@/lib/websocket';
import { chatApi } from '@/lib/api';
import type { SourceDocument } from '@/lib/websocket';

interface ChatInterfaceProps {
  projectId: number;
}

export default function ChatInterface({ projectId }: ChatInterfaceProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingSources, setStreamingSources] = useState<SourceDocument[]>([]);
  const assistantMessageIdRef = useRef<number | null>(null);

  // Get project details - use stable selector
  const projects = useProjectStore(selectProjects);
  const project = useMemo(() => projects.find((p) => p.id === projectId), [projects, projectId]);

  // Chat store state - use stable selectors
  const messages = useChatStore(selectCurrentMessages);
  const currentChatId = useChatStore((state) => state.currentChatId);
  const setCurrentChat = useChatStore((state) => state.setCurrentChat);
  const addChat = useChatStore((state) => state.addChat);
  const addMessage = useChatStore((state) => state.addMessage);
  const updateMessage = useChatStore((state) => state.updateMessage);

  // WebSocket connection
  const { isConnected } = useWebSocketConnection({ autoConnect: true });

  // Join project room when connected
  useProjectRoom(isConnected ? projectId : null);

  // Initialize or find chat for this project
  useEffect(() => {
    // Use ref to prevent double execution in React StrictMode
    let isInitializing = false;

    const initChat = async () => {
      if (!project || isInitializing) return;

      // Check if we already have a chat for this project in the store
      if (currentChatId) {
        console.log('Chat already initialized:', currentChatId);
        return;
      }

      isInitializing = true;

      try {
        // Fetch existing chats from backend for this project
        const existingChats = await chatApi.list(projectId);

        if (existingChats && existingChats.length > 0) {
          // Use the most recent chat
          const mostRecentChat = existingChats[0];

          // Update store with backend chat
          addChat(mostRecentChat);
          setCurrentChat(mostRecentChat.id);

          // Load existing messages for this chat
          try {
            const existingMessages = await chatApi.getHistory(mostRecentChat.id);
            // Add messages to store
            existingMessages.forEach((msg: Message) => {
              addMessage(mostRecentChat.id, msg);
            });
            console.log(
              `Loaded ${existingMessages.length} existing messages for chat:`,
              mostRecentChat.id
            );
          } catch (msgError) {
            console.error('Failed to load messages:', msgError);
            // Continue even if messages fail to load
          }

          console.log('Using existing chat:', mostRecentChat.id);
        } else {
          // No existing chats, create a new one via API
          const newChat = await chatApi.create(projectId, `Chat with ${project.name}`);
          addChat(newChat);
          setCurrentChat(newChat.id);

          toast({
            title: 'Chat Started',
            description: `Started new chat for ${project.name}`,
          });

          console.log('Created new chat:', newChat.id);
        }
      } catch (error) {
        console.error('Failed to initialize chat:', error);
        toast({
          title: 'Error',
          description: 'Failed to initialize chat session. Please refresh and try again.',
          variant: 'destructive',
        });
      } finally {
        isInitializing = false;
      }
    };

    initChat();
    // Only depend on projectId to run once when project changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  // Chat stream handlers
  const handleToken = useCallback((token: string) => {
    setStreamingContent((prev) => prev + token);
  }, []);

  const handleSources = useCallback((sources: SourceDocument[]) => {
    setStreamingSources(sources);
  }, []);

  const handleComplete = useCallback(() => {
    // Finalize the assistant message with complete content
    if (assistantMessageIdRef.current && currentChatId) {
      updateMessage(currentChatId, assistantMessageIdRef.current, {
        content: streamingContent,
        sources: streamingSources.map((src) => ({
          id: src.id,
          content: src.content,
          metadata: src.metadata,
          score: src.score,
          document_id: src.metadata.document_id,
          document_name: src.metadata.filename || 'Unknown',
          chunk_index: src.metadata.chunk_index,
          page_number: src.metadata.page,
          similarity_score: src.score,
        })),
      });
    }

    // Reset streaming state
    setIsGenerating(false);
    setStreamingContent('');
    setStreamingSources([]);
    assistantMessageIdRef.current = null;
  }, [currentChatId, streamingContent, streamingSources, updateMessage]);

  const handleError = useCallback(
    (error: string) => {
      console.error('Chat stream error:', error);
      toast({
        title: 'Error',
        description: error || 'Failed to generate response',
        variant: 'destructive',
      });
      setIsGenerating(false);
      setStreamingContent('');
      setStreamingSources([]);
      assistantMessageIdRef.current = null;
    },
    [toast]
  );

  // Use chat stream hook
  const { sendMessage: sendWSMessage } = useChatStream(currentChatId || 0, {
    onToken: handleToken,
    onSources: handleSources,
    onComplete: handleComplete,
    onError: handleError,
  });

  const handleSendMessage = async (content: string) => {
    if (!currentChatId || !project) {
      toast({
        title: 'Error',
        description: 'No active chat session',
        variant: 'destructive',
      });
      return;
    }

    if (!isConnected) {
      toast({
        title: 'Connection Error',
        description: 'WebSocket not connected. Please wait and try again.',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Add user message
      const userMessage = {
        id: Date.now(),
        chat_id: currentChatId,
        role: MessageRole.USER,
        content,
        created_at: new Date().toISOString(),
      };

      addMessage(currentChatId, userMessage);

      // Create placeholder assistant message for streaming
      const assistantMessageId = Date.now() + 1;
      assistantMessageIdRef.current = assistantMessageId;

      const assistantMessage = {
        id: assistantMessageId,
        chat_id: currentChatId,
        role: MessageRole.ASSISTANT,
        content: '',
        created_at: new Date().toISOString(),
      };

      addMessage(currentChatId, assistantMessage);

      // Set generating state
      setIsGenerating(true);
      setStreamingContent('');
      setStreamingSources([]);

      // Send message via WebSocket
      sendWSMessage(content, {
        include_history: true,
        temperature: 0.7,
      });
    } catch (error) {
      console.error('Error sending message:', error);
      toast({
        title: 'Error',
        description: 'Failed to send message. Please try again.',
        variant: 'destructive',
      });
      setIsGenerating(false);
    }
  };

  // Update streaming message in real-time
  useEffect(() => {
    if (isGenerating && assistantMessageIdRef.current && currentChatId && streamingContent) {
      updateMessage(currentChatId, assistantMessageIdRef.current, {
        content: streamingContent,
      });
    }
  }, [streamingContent, isGenerating, currentChatId, updateMessage]);

  if (!project) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-center">Project Not Found</CardTitle>
            <p className="text-sm text-muted-foreground text-center">
              The requested project could not be found. Please select a valid project.
            </p>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      {/* Chat Header - Fixed at top */}
      <div className="flex-shrink-0 border-b bg-background px-4 py-2 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
              title="Go back"
              className="h-8 w-8"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div className="rounded-full bg-primary/10 p-1.5">
              <MessageSquare className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-base">{project.name}</h2>
              {project.description && (
                <p className="text-xs text-muted-foreground line-clamp-1">{project.description}</p>
              )}
            </div>
          </div>

          <Button variant="ghost" size="icon" title="Chat Settings" className="h-8 w-8">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Messages Area - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} isLoading={isGenerating} />
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="flex-shrink-0 border-t bg-background z-10">
        <MessageInput
          onSend={handleSendMessage}
          disabled={!currentChatId}
          isLoading={isGenerating}
          placeholder={`Ask questions about ${project.name}...`}
        />
      </div>
    </div>
  );
}
