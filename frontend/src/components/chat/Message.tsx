'use client';

import { Message as MessageType, MessageRole } from '@/types';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Bot, User, Copy, CheckCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import SourceReferences from './SourceReferences';
import ReactMarkdown from 'react-markdown';
import { useChatSettingsStore } from '@/stores/chatSettingsStore';

interface MessageProps {
  message: MessageType;
  showSources?: boolean;
  useMarkdown?: boolean;
}

export default function Message({ message, showSources = true, useMarkdown = true }: MessageProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();
  const { uiPreferences } = useChatSettingsStore();

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
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to copy message',
        variant: 'destructive',
      });
    }
  };

  // Highlight source citations in text (e.g., [Source 1], [1], etc.)
  const highlightCitations = (text: string): string => {
    // Match patterns like [Source 1], [1], (Source 1), etc.
    return text.replace(
      /\[(Source\s+\d+|[Ss]ource\s+\d+|\d+)\]|\((Source\s+\d+|[Ss]ource\s+\d+)\)/g,
      (match) => `**${match}**`
    );
  };

  const processedContent =
    isAssistant && useMarkdown ? highlightCitations(message.content) : message.content;

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-primary">
            <Bot className="h-4 w-4 text-primary-foreground" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={`flex flex-col gap-3 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <Card className={`p-4 ${isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
          {isAssistant && useMarkdown ? (
            <div
              className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed"
              style={{ fontSize: `${uiPreferences.fontSize}px` }}
            >
              <ReactMarkdown>{processedContent}</ReactMarkdown>
            </div>
          ) : (
            <div
              className="whitespace-pre-wrap break-words"
              style={{ fontSize: `${uiPreferences.fontSize}px` }}
            >
              {message.content}
            </div>
          )}
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

        {/* Enhanced Source References */}
        {showSources && isAssistant && message.sources && message.sources.length > 0 && (
          <div className="w-full">
            <SourceReferences sources={message.sources} />
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
