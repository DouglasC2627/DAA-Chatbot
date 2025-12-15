'use client';

import { HelpCircle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface InfoTooltipProps {
  content: string | React.ReactNode;
  className?: string;
  iconSize?: number;
}

export function InfoTooltip({ content, className = '', iconSize = 14 }: InfoTooltipProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className={`inline-flex items-center justify-center ml-1 text-muted-foreground hover:text-foreground transition-colors ${className}`}
            onClick={(e) => e.preventDefault()}
          >
            <HelpCircle className="h-4 w-4" style={{ width: iconSize, height: iconSize }} />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs" side="top">
          <div className="text-sm">{content}</div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
