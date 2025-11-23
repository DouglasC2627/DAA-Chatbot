'use client';

import { FileText } from 'lucide-react';

interface PdfViewerProps {
  url: string | null;
  onLoadSuccess?: (data: { numPages: number }) => void;
  onLoadError?: (error: Error) => void;
}

export default function PdfViewer({ url }: PdfViewerProps) {
  if (!url) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] bg-muted">
        <FileText className="h-24 w-24 text-muted-foreground mb-4 animate-pulse" />
        <p className="text-sm text-muted-foreground">Loading PDF...</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[500px]">
      <iframe
        src={url}
        className="w-full h-full border-0"
        title="PDF Preview"
      />
    </div>
  );
}
