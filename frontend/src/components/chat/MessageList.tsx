'use client';

import { useEffect, useRef } from 'react';
import { Message as MessageType } from '@/types';
import Message from './Message';
import { MessageSquare } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

interface MessageListProps {
  messages: MessageType[];
  isLoading?: boolean;
}

export default function MessageList({ messages, isLoading = false }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="mb-4 flex justify-center">
            <div className="rounded-full bg-primary/10 p-6">
              <MessageSquare className="h-12 w-12 text-primary" />
            </div>
          </div>
          <h3 className="text-lg font-semibold mb-2">Start a Conversation</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Ask questions about your documents and get AI-powered responses with source citations.
          </p>
          <div className="space-y-2 text-left bg-muted/50 rounded-lg p-4">
            <p className="text-xs font-medium text-muted-foreground">Example questions:</p>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>• "Summarize the main points from my documents"</li>
              <li>• "What are the key findings in the research?"</li>
              <li>• "Explain the methodology used in the study"</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 px-4 py-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-3">
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
              <MessageSquare className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="bg-muted rounded-lg p-4 max-w-[80%]">
              <div className="flex items-center gap-2">
                <div
                  className="h-2 w-2 bg-primary rounded-full animate-bounce"
                  style={{ animationDelay: '0ms' }}
                />
                <div
                  className="h-2 w-2 bg-primary rounded-full animate-bounce"
                  style={{ animationDelay: '150ms' }}
                />
                <div
                  className="h-2 w-2 bg-primary rounded-full animate-bounce"
                  style={{ animationDelay: '300ms' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
