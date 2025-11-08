'use client';

import { useState, KeyboardEvent } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, Loader2, MessageSquarePlus } from 'lucide-react';
import { chatApi } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface ProjectChatInputProps {
  projectId: number;
  projectName: string;
}

export default function ProjectChatInput({ projectId, projectName }: ProjectChatInputProps) {
  const [query, setQuery] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const handleCreateChat = async () => {
    if (!query.trim() || isCreating) return;

    const userQuery = query.trim();
    setIsCreating(true);

    try {
      // Create new chat with auto-generated title from query
      const newChat = await chatApi.create(projectId, userQuery.substring(0, 50));

      // Navigate to the chat page - the chat interface will handle sending the message
      // We'll pass the initial query via URL state
      router.push(`/chat/${newChat.id}?initialMessage=${encodeURIComponent(userQuery)}`);
    } catch (error) {
      console.error('Failed to create chat:', error);
      toast({
        title: 'Error',
        description: 'Failed to create new chat. Please try again.',
        variant: 'destructive',
      });
      setIsCreating(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleCreateChat();
    }
  };

  return (
    <div className="sticky top-0 z-10 bg-background border-b shadow-sm">
      <div className="max-w-5xl mx-auto px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <MessageSquarePlus className="h-5 w-5 text-primary" />
            </div>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Start a new conversation..."
                disabled={isCreating}
                className="h-10 text-sm"
              />

              <Button
                onClick={handleCreateChat}
                disabled={!query.trim() || isCreating}
                size="sm"
                className="h-10 px-4"
              >
                {isCreating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Start Chat
                  </>
                )}
              </Button>
            </div>

            <p className="mt-1 text-xs text-muted-foreground">
              Ask a question about your documents in {projectName}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
