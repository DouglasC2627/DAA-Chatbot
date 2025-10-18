'use client';

import { Message as MessageType, MessageRole } from '@/types';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Bot, User, Copy, CheckCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';

interface MessageProps {
  message: MessageType;
  showSources?: boolean;
}

export default function Message({ message, showSources = true }: MessageProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const isUser = message.role === MessageRole.USER;
  const isAssistant = message.role === MessageRole.ASSISTANT;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      toast({
        title: 'Copied',
        description: 'Message copied to clipboard',
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to copy message',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-primary">
            <Bot className="h-4 w-4 text-primary-foreground" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={`flex flex-col gap-2 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <Card className={`p-4 ${isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
          <div className="whitespace-pre-wrap break-words text-sm">{message.content}</div>
        </Card>

        <div className="flex items-center gap-2 px-2">
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(message.created_at), { addSuffix: true })}
          </span>

          {isAssistant && (
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleCopy}>
              {copied ? <CheckCheck className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>
          )}
        </div>

        {/* Source References */}
        {showSources && isAssistant && message.sources && message.sources.length > 0 && (
          <div className="w-full">
            <div className="text-xs font-medium text-muted-foreground mb-2">
              Sources ({message.sources.length})
            </div>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  className="h-auto py-1 px-2 text-xs"
                >
                  <span className="truncate max-w-[200px]">
                    {source.document_name}
                    {source.page_number && ` (p.${source.page_number})`}
                  </span>
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-secondary">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
