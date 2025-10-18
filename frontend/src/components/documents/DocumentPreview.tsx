'use client';

import { Document, DocumentStatus } from '@/types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Download, FileText, ExternalLink } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';

interface DocumentPreviewProps {
  document: Document;
  open: boolean;
  onClose: () => void;
}

const getStatusBadge = (status: DocumentStatus) => {
  switch (status) {
    case DocumentStatus.COMPLETED:
      return (
        <Badge variant="default" className="bg-green-500">
          Processed
        </Badge>
      );
    case DocumentStatus.PROCESSING:
      return (
        <Badge variant="default" className="bg-blue-500">
          Processing
        </Badge>
      );
    case DocumentStatus.FAILED:
      return <Badge variant="destructive">Failed</Badge>;
    case DocumentStatus.PENDING:
      return <Badge variant="secondary">Pending</Badge>;
    default:
      return null;
  }
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export default function DocumentPreview({ document, open, onClose }: DocumentPreviewProps) {
  const handleDownload = () => {
    // TODO: Implement actual download
    console.log('Download document:', document.id);
  };

  const handleOpenExternal = () => {
    // TODO: Implement opening in external viewer
    console.log('Open document externally:', document.id);
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <DialogTitle className="text-xl">{document.filename}</DialogTitle>
              <DialogDescription className="mt-2">Document details and metadata</DialogDescription>
            </div>
            <div>{getStatusBadge(document.processing_status)}</div>
          </div>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Document Icon */}
          <div className="flex justify-center py-8 bg-muted rounded-lg">
            <FileText className="h-24 w-24 text-muted-foreground" />
          </div>

          {/* Document Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">File Type</p>
              <p className="text-sm mt-1">{document.file_type.toUpperCase()}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">File Size</p>
              <p className="text-sm mt-1">{formatFileSize(document.file_size)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Uploaded</p>
              <p className="text-sm mt-1">
                {formatDistanceToNow(new Date(document.upload_date), { addSuffix: true })}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Status</p>
              <p className="text-sm mt-1 capitalize">{document.processing_status}</p>
            </div>
          </div>

          {/* Processing Details */}
          {document.processing_status === DocumentStatus.COMPLETED && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium mb-3">Processing Details</h4>
              <div className="grid grid-cols-3 gap-4">
                {document.page_count !== undefined && (
                  <div>
                    <p className="text-sm text-muted-foreground">Pages</p>
                    <p className="text-2xl font-bold">{document.page_count}</p>
                  </div>
                )}
                {document.word_count !== undefined && (
                  <div>
                    <p className="text-sm text-muted-foreground">Words</p>
                    <p className="text-2xl font-bold">{document.word_count.toLocaleString()}</p>
                  </div>
                )}
                {document.chunk_count !== undefined && (
                  <div>
                    <p className="text-sm text-muted-foreground">Chunks</p>
                    <p className="text-2xl font-bold">{document.chunk_count}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error Message */}
          {document.processing_status === DocumentStatus.FAILED && document.error_message && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium mb-2 text-destructive">Error Details</h4>
              <p className="text-sm text-muted-foreground bg-destructive/10 p-3 rounded">
                {document.error_message}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4 border-t">
            <Button onClick={handleDownload} className="flex-1">
              <Download className="mr-2 h-4 w-4" />
              Download
            </Button>
            <Button variant="outline" onClick={handleOpenExternal} className="flex-1">
              <ExternalLink className="mr-2 h-4 w-4" />
              Open External
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
