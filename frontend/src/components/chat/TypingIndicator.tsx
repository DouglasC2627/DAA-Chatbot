'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface TypingIndicatorProps {
  className?: string;
  label?: string;
}

export function TypingIndicator({ className, label = 'AI is thinking' }: TypingIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-2 p-4', className)}>
      <div className="flex space-x-1.5">
        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" />
      </div>
      {label && <span className="text-sm text-gray-500">{label}</span>}
    </div>
  );
}

interface StreamingIndicatorProps {
  content: string;
  className?: string;
}

export function StreamingIndicator({ content, className }: StreamingIndicatorProps) {
  return (
    <div className={cn('relative', className)}>
      <div className="whitespace-pre-wrap">{content}</div>
      <span className="inline-block w-1.5 h-4 bg-gray-900 dark:bg-gray-100 animate-pulse ml-0.5" />
    </div>
  );
}
