'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useDocumentUpdates, DocumentStatusEvent } from '@/lib/websocket';
import { Progress } from '@/components/ui/progress';
import { Card } from '@/components/ui/card';
import { CheckCircle2, XCircle, Loader2, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DocumentProcessingStatusProps {
  documentId?: number;
  onComplete?: (documentId: number) => void;
  onError?: (documentId: number, error: string) => void;
}

interface ProcessingDocument {
  id: number;
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  timestamp: number;
}

export function DocumentProcessingStatus({
  documentId,
  onComplete,
  onError,
}: DocumentProcessingStatusProps) {
  const [processingDocs, setProcessingDocs] = useState<Map<number, ProcessingDocument>>(new Map());

  // Listen to document status updates - memoized callback to prevent infinite loops
  const handleDocumentUpdate = useCallback(
    (data: DocumentStatusEvent) => {
      const doc: ProcessingDocument = {
        id: data.document_id,
        status: data.status,
        progress: data.progress || 0,
        timestamp: Date.now(),
      };

      setProcessingDocs((prev) => {
        const updated = new Map(prev);
        updated.set(data.document_id, doc);
        return updated;
      });

      // Trigger callbacks
      if (data.status === 'completed' && onComplete) {
        onComplete(data.document_id);
        // Auto-remove after 3 seconds
        setTimeout(() => {
          setProcessingDocs((prev) => {
            const updated = new Map(prev);
            updated.delete(data.document_id);
            return updated;
          });
        }, 3000);
      } else if (data.status === 'failed' && onError) {
        onError(data.document_id, 'Processing failed');
      }
    },
    [onComplete, onError]
  );

  useDocumentUpdates(handleDocumentUpdate);

  // Filter to specific document if provided
  const docs = documentId
    ? Array.from(processingDocs.values()).filter((doc) => doc.id === documentId)
    : Array.from(processingDocs.values());

  if (docs.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {docs.map((doc) => (
        <DocumentStatusCard key={doc.id} document={doc} />
      ))}
    </div>
  );
}

interface DocumentStatusCardProps {
  document: ProcessingDocument;
}

function DocumentStatusCard({ document }: DocumentStatusCardProps) {
  const statusConfig = {
    processing: {
      icon: <Loader2 className="h-5 w-5 animate-spin text-blue-500" />,
      label: 'Processing',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-950',
    },
    completed: {
      icon: <CheckCircle2 className="h-5 w-5 text-green-500" />,
      label: 'Completed',
      color: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-950',
    },
    failed: {
      icon: <XCircle className="h-5 w-5 text-red-500" />,
      label: 'Failed',
      color: 'text-red-600',
      bgColor: 'bg-red-50 dark:bg-red-950',
    },
  };

  const config = statusConfig[document.status];

  return (
    <Card className={cn('p-4', config.bgColor)}>
      <div className="flex items-start gap-3">
        <FileText className="h-5 w-5 text-gray-500 mt-0.5" />
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Document #{document.id}</span>
            <div className="flex items-center gap-2">
              {config.icon}
              <span className={cn('text-sm font-medium', config.color)}>{config.label}</span>
            </div>
          </div>

          {document.status === 'processing' && (
            <div className="space-y-1">
              <Progress value={document.progress} className="h-2" />
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {document.progress}% complete
              </p>
            </div>
          )}

          {document.status === 'completed' && (
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Document processed successfully
            </p>
          )}

          {document.status === 'failed' && (
            <p className="text-xs text-red-600 dark:text-red-400">
              Failed to process document. Please try again.
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}

/**
 * Compact inline status indicator for individual documents
 */
export function DocumentStatusBadge({
  documentId,
  showProgress = false,
}: {
  documentId: number;
  showProgress?: boolean;
}) {
  const [status, setStatus] = useState<DocumentStatusEvent | null>(null);

  // Memoized callback to prevent infinite loops
  const handleDocumentUpdate = useCallback(
    (data: DocumentStatusEvent) => {
      if (data.document_id === documentId) {
        setStatus(data);
      }
    },
    [documentId]
  );

  useDocumentUpdates(handleDocumentUpdate);

  if (!status || status.status === 'completed') {
    return null;
  }

  const statusConfig = {
    processing: {
      icon: <Loader2 className="h-3 w-3 animate-spin" />,
      label: 'Processing',
      color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    },
    failed: {
      icon: <XCircle className="h-3 w-3" />,
      label: 'Failed',
      color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    },
  };

  const config = statusConfig[status.status as 'processing' | 'failed'];
  if (!config) return null;

  return (
    <div className="space-y-1">
      <span
        className={cn(
          'inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium',
          config.color
        )}
      >
        {config.icon}
        {config.label}
        {showProgress && status.progress !== undefined && ` ${status.progress}%`}
      </span>
      {showProgress && status.status === 'processing' && status.progress !== undefined && (
        <Progress value={status.progress} className="h-1" />
      )}
    </div>
  );
}
