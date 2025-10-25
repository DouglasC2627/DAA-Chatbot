'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Loader2, Paperclip } from 'lucide-react';

interface MessageInputProps {
  onSend: (message: string) => void | Promise<void>;
  disabled?: boolean;
  placeholder?: string;
  isLoading?: boolean;
}

export default function MessageInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about your documents...',
  isLoading = false,
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = async () => {
    if (!message.trim() || disabled || isLoading) return;

    const messageToSend = message.trim();
    setMessage('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    await onSend(messageToSend);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter, new line on Shift+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);

    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
  };

  return (
    <div className="px-4 py-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-2">
          {/* Attach Files Button (Future Enhancement) */}
          <Button
            variant="ghost"
            size="icon"
            className="flex-shrink-0 h-9 w-9"
            disabled
            title="Attach files (coming soon)"
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          {/* Message Textarea */}
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled || isLoading}
              className="min-h-[36px] max-h-[100px] resize-none pr-16 py-1.5 text-sm"
              rows={1}
            />
            {message.length > 0 && (
              <div className="absolute bottom-1.5 right-2 text-xs text-muted-foreground/70">
                {message.length}
              </div>
            )}
          </div>

          {/* Send Button */}
          <Button
            onClick={handleSend}
            disabled={!message.trim() || disabled || isLoading}
            size="icon"
            className="flex-shrink-0 h-9 w-9"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Helper Text - Only show when loading */}
        {isLoading && (
          <div className="mt-1 text-xs text-primary text-center">Generating response...</div>
        )}
      </div>
    </div>
  );
}
