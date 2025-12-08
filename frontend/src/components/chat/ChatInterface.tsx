'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useShallow } from 'zustand/react/shallow';
import { useProjectStore } from '@/stores/projectStore';
import { useChatStore } from '@/stores/chatStore';
import { useChatSettingsStore } from '@/stores/chatSettingsStore';
import { MessageRole } from '@/types';
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
  chatId?: number;
  initialMessage?: string;
}

export default function ChatInterface({ projectId, chatId, initialMessage }: ChatInterfaceProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingSources, setStreamingSources] = useState<SourceDocument[]>([]);
  const [messagesLoaded, setMessagesLoaded] = useState(false);
  const assistantMessageIdRef = useRef<number | null>(null);

  // Get chat settings
  const { chatSettings } = useChatSettingsStore();

  // Get project details - use useShallow to prevent infinite loops
  const project = useProjectStore(
    useShallow((state) => state.projects.find((p) => p.id === projectId))
  );

  // Chat store state - use useShallow for array comparisons
  const currentChatId = useChatStore((state) => state.currentChatId);
  const messages = useChatStore(
    useShallow((state) => (state.currentChatId ? state.messages[state.currentChatId] || [] : []))
  );

  // WebSocket connection
  const { isConnected } = useWebSocketConnection({ autoConnect: true });

  // Join project room when connected
  useProjectRoom(isConnected ? projectId : null);

  // Use ref to track initialization status per project
  const initializingRef = useRef<number | null>(null);
  const initializedProjects = useRef<Set<number>>(new Set());
  const loadedMessagesRef = useRef<Set<number>>(new Set());

  // Helper function to transform sources from backend format to frontend format
  const transformSources = (sources: any[] | null | undefined) => {
    if (!sources || !Array.isArray(sources)) return undefined;

    return sources.map((src: any) => ({
      id: src.id,
      content: src.content || '',
      metadata: src.metadata || {},
      score: src.score || 0,
      document_id: src.metadata?.document_id || src.document_id || 0,
      document_name: src.metadata?.filename || src.document_name || 'Unknown Document',
      chunk_index: src.metadata?.chunk_index ?? src.chunk_index ?? 0,
      page_number: src.metadata?.page || src.page_number,
      similarity_score: src.score ?? src.similarity_score ?? 0,
    }));
  };

  // Initialize chat session for the project (fetch or create chat)
  useEffect(() => {
    // Don't initialize if project not found
    if (!project) {
      console.log(`[ChatInterface] Project ${projectId} not found in store, waiting...`);
      return;
    }

    // If chatId is provided externally, use it directly and skip initialization
    if (chatId) {
      console.log(`[ChatInterface] Using provided chatId ${chatId}, skipping initialization`);
      const { setCurrentChat } = useChatStore.getState();
      setCurrentChat(chatId);
      initializedProjects.current.add(projectId);
      return;
    }

    // Prevent re-initialization BEFORE starting async work
    if (initializingRef.current === projectId || initializedProjects.current.has(projectId)) {
      console.log(
        `[ChatInterface] Project ${projectId} already initializing or initialized, skipping`
      );
      return;
    }

    // Mark as initializing immediately to prevent duplicate runs
    initializingRef.current = projectId;
    console.log(`[ChatInterface] Set initializingRef to ${projectId}`);

    const initChat = async () => {
      // Get fresh store state inside the effect
      const store = useChatStore.getState();
      const { syncWithProject, setCurrentChat, addChat, chats: storeChats } = store;

      try {
        console.log(`[ChatInterface] Initializing chat for project ${projectId}`);

        // sync store with current project (removes chats from other projects)
        syncWithProject(projectId);
        console.log(`[ChatInterface] Store synced with project ${projectId}`);

        // Fetch existing chats from backend for this project
        console.log(`[ChatInterface] Fetching chats for project ${projectId}...`);
        const existingChats = await chatApi.list(projectId);
        console.log(`[ChatInterface] Received chats:`, existingChats);

        if (existingChats && existingChats.length > 0) {
          // Use the most recent chat
          const chatToUse = existingChats[0];
          console.log(`[ChatInterface] Will use existing chat:`, chatToUse);

          // Only add if not already in store
          const chatExistsInStore = storeChats.some((c) => c.id === chatToUse.id);
          console.log(`[ChatInterface] Chat exists in store: ${chatExistsInStore}`);
          if (!chatExistsInStore) {
            addChat(chatToUse);
            console.log(`[ChatInterface] Added chat ${chatToUse.id} to store`);
          }

          setCurrentChat(chatToUse.id);
          console.log(`[ChatInterface] Using existing chat: ${chatToUse.id}, currentChatId set`);
        } else {
          // No existing chats, create a new one via API
          console.log(`[ChatInterface] No existing chats, creating new one...`);
          const newChat = await chatApi.create(projectId, `Chat with ${project.name}`);
          console.log(`[ChatInterface] Created chat:`, newChat);

          addChat(newChat);
          console.log(`[ChatInterface] Added new chat ${newChat.id} to store`);

          setCurrentChat(newChat.id);
          console.log(`[ChatInterface] Set currentChatId to ${newChat.id}`);

          toast({
            title: 'Chat Started',
            description: `Started new chat for ${project.name}`,
          });

          console.log(`[ChatInterface] Created new chat: ${newChat.id}`);
        }

        // Mark project as initialized
        initializedProjects.current.add(projectId);
        console.log(`[ChatInterface] Project ${projectId} initialized successfully`);
      } catch (error) {
        console.error('[ChatInterface] Failed to initialize chat:', error);
        console.error('[ChatInterface] Error details:', {
          message: error instanceof Error ? error.message : 'Unknown error',
          stack: error instanceof Error ? error.stack : undefined,
          error: error,
        });

        toast({
          title: 'Error',
          description: 'Failed to initialize chat session. Please refresh and try again.',
          variant: 'destructive',
        });
      } finally {
        initializingRef.current = null;
      }
    };

    initChat();

    return () => {
      console.log(`[ChatInterface] Cleanup called for project ${projectId}`);
      // No cleanup needed - initialization will complete and update Zustand store
      // which persists across component mounts
    };
    // Only depend on projectId and chatId - toast is stable and shouldn't cause re-initialization
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, chatId]);

  // Load messages when current chat changes
  useEffect(() => {
    if (!currentChatId) {
      setMessagesLoaded(false);
      return;
    }

    // Skip if already loaded
    if (loadedMessagesRef.current.has(currentChatId)) {
      setMessagesLoaded(true);
      return;
    }

    let isMounted = true;
    setMessagesLoaded(false);

    const loadMessages = async () => {
      try {
        console.log(`[ChatInterface] Loading messages for chat ${currentChatId}`);
        const existingMessages = await chatApi.getHistory(currentChatId);

        if (!isMounted) return;

        // Transform sources in messages to frontend format
        const transformedMessages = existingMessages.map((msg) => ({
          ...msg,
          sources: msg.sources ? transformSources(msg.sources) : undefined,
        }));

        const { setMessages } = useChatStore.getState();
        setMessages(currentChatId, transformedMessages);
        loadedMessagesRef.current.add(currentChatId);
        setMessagesLoaded(true);

        console.log(
          `[ChatInterface] Loaded ${existingMessages.length} messages for chat ${currentChatId}`
        );
      } catch (error) {
        console.error('[ChatInterface] Failed to load messages:', error);
        setMessagesLoaded(true); // Still mark as loaded even on error to prevent infinite waiting
      }
    };

    loadMessages();

    return () => {
      isMounted = false;
    };
  }, [currentChatId]);

  // Chat stream handlers
  const handleToken = useCallback((token: string) => {
    setStreamingContent((prev) => prev + token);
  }, []);

  const handleSources = useCallback((sources: SourceDocument[]) => {
    setStreamingSources(sources);
  }, []);

  const handleComplete = useCallback(() => {
    // Finalize the assistant message with complete content
    const { updateMessage: storeUpdateMessage } = useChatStore.getState();

    if (assistantMessageIdRef.current && currentChatId) {
      storeUpdateMessage(currentChatId, assistantMessageIdRef.current, {
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
  }, [currentChatId, streamingContent, streamingSources]);

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

  const handleSendMessage = useCallback(
    async (content: string) => {
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
        // Get store actions
        const { addMessage: storeAddMessage } = useChatStore.getState();

        // Add user message
        const userMessage = {
          id: Date.now(),
          chat_id: currentChatId,
          role: MessageRole.USER,
          content,
          created_at: new Date().toISOString(),
        };

        storeAddMessage(currentChatId, userMessage);

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

        storeAddMessage(currentChatId, assistantMessage);

        // Set generating state
        setIsGenerating(true);
        setStreamingContent('');
        setStreamingSources([]);

        // Send message via WebSocket with settings from store
        sendWSMessage(content, {
          include_history: true,
          temperature: chatSettings.temperature,
          top_k: chatSettings.topK,
          max_tokens: chatSettings.maxTokens,
          history_length: chatSettings.historyLength,
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
    },
    [currentChatId, project, isConnected, sendWSMessage, toast]
  );

  // Handle initial message if provided (for new chat creation from project page)
  const initialMessageSentRef = useRef(false);

  // Reset the sent flag when chat changes
  useEffect(() => {
    initialMessageSentRef.current = false;
  }, [currentChatId]);

  useEffect(() => {
    // Only send if we have all required data and haven't sent yet
    if (
      initialMessage &&
      currentChatId &&
      isConnected &&
      messagesLoaded &&
      !initialMessageSentRef.current
    ) {
      console.log(`[ChatInterface] Sending initial message: ${initialMessage}`);
      initialMessageSentRef.current = true;

      // Use setTimeout to ensure the UI is fully initialized
      setTimeout(() => {
        handleSendMessage(initialMessage);
      }, 500);
    }
  }, [initialMessage, currentChatId, isConnected, messagesLoaded, handleSendMessage]);

  // Update streaming message in real-time
  useEffect(() => {
    if (isGenerating && assistantMessageIdRef.current && currentChatId && streamingContent) {
      const { updateMessage: storeUpdateMessage } = useChatStore.getState();
      storeUpdateMessage(currentChatId, assistantMessageIdRef.current, {
        content: streamingContent,
      });
    }
  }, [streamingContent, isGenerating, currentChatId]);

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

          <div className="flex items-center gap-2">
            {/* Debug info */}
            <div className="text-xs text-muted-foreground">
              Chat ID: {currentChatId || 'none'} | WS: {isConnected ? '✓' : '✗'}
            </div>
          </div>
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
