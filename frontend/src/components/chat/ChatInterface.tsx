'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useProjectStore, selectProjects } from '@/stores/projectStore';
import { useChatStore, selectCurrentChat, selectCurrentMessages } from '@/stores/chatStore';
import { MessageRole } from '@/types';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare, Settings, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface ChatInterfaceProps {
  projectId: number;
}

export default function ChatInterface({ projectId }: ChatInterfaceProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState(false);

  // Get project details - use stable selector
  const projects = useProjectStore(selectProjects);
  const project = useMemo(() => projects.find((p) => p.id === projectId), [projects, projectId]);

  // Chat store state - use stable selectors
  const messages = useChatStore(selectCurrentMessages);
  const currentChatId = useChatStore((state) => state.currentChatId);
  const setCurrentChat = useChatStore((state) => state.setCurrentChat);
  const addChat = useChatStore((state) => state.addChat);
  const addMessage = useChatStore((state) => state.addMessage);
  const chats = useChatStore((state) => state.chats);

  // Initialize or find chat for this project
  useEffect(() => {
    if (!project) return;

    // Find existing chat for this project
    const projectChat = chats.find((chat) => chat.project_id === projectId);

    if (projectChat) {
      setCurrentChat(projectChat.id);
    } else {
      // Create a new chat for this project (mock - will be replaced with API call)
      const newChat = {
        id: Date.now(), // Use timestamp as numeric ID
        project_id: projectId,
        title: `Chat with ${project.name}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        message_count: 0,
      };

      addChat(newChat);
      setCurrentChat(newChat.id);

      toast({
        title: 'Chat Started',
        description: `Started new chat for ${project.name}`,
      });
    }
  }, [projectId, project, chats, setCurrentChat, addChat, toast]);

  const handleSendMessage = async (content: string) => {
    if (!currentChatId || !project) {
      toast({
        title: 'Error',
        description: 'No active chat session',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Add user message (mock - will be replaced with API call)
      const userMessage = {
        id: Date.now(), // Use timestamp as numeric ID
        chat_id: currentChatId,
        role: MessageRole.USER,
        content,
        created_at: new Date().toISOString(),
      };

      addMessage(currentChatId, userMessage);

      // Set generating state
      setIsGenerating(true);

      // Simulate assistant response (will be replaced with actual API call)
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const assistantMessage = {
        id: Date.now() + 1, // Ensure unique ID by adding 1
        chat_id: currentChatId,
        role: MessageRole.ASSISTANT,
        content: `I received your message: "${content}". This is a mock response. Once the backend is connected, I'll provide real AI-powered responses based on your documents.`,
        sources: [
          {
            document_id: 1, // Use numeric ID
            document_name: 'Sample Document.pdf',
            chunk_index: 0,
            page_number: 1,
            content: 'Sample content from document',
            similarity_score: 0.95,
            section: 'Introduction',
          },
        ],
        created_at: new Date().toISOString(),
      };

      addMessage(currentChatId, assistantMessage);
    } catch (error) {
      console.error('Error sending message:', error);
      toast({
        title: 'Error',
        description: 'Failed to send message. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsGenerating(false);
    }
  };

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
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Header */}
      <div className="border-b bg-background px-4 py-2">
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

      {/* Messages Area */}
      <MessageList messages={messages} isLoading={isGenerating} />

      {/* Input Area */}
      <MessageInput
        onSend={handleSendMessage}
        disabled={!currentChatId}
        isLoading={isGenerating}
        placeholder={`Ask questions about ${project.name}...`}
      />
    </div>
  );
}
