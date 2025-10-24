'use client';

import { Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t bg-background md:ml-64">
      <div className="container flex flex-col items-center justify-between gap-4 py-4 px-4 md:h-16 md:flex-row md:py-0 md:px-6">
        <div className="flex flex-col items-center gap-2 md:flex-row md:gap-2">
          <p className="text-center text-xs leading-loose text-muted-foreground md:text-left md:text-sm">
            Built with <Heart className="inline h-3 w-3 text-red-500" fill="currentColor" /> and
            curiosity
          </p>
        </div>

        <div className="flex items-center gap-4">
          <p className="text-xs text-muted-foreground">v0.1.0 • Local RAG</p>
        </div>
      </div>
    </footer>
  );
}
