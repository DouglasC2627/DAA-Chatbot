'use client';

import { useState, useEffect, useCallback } from 'react';
import { Document as DocumentModel, DocumentStatus } from '@/types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Download, FileText, ExternalLink } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';
import { documentApi } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import PdfViewer from './PdfViewer';

interface DocumentPreviewProps {
  document: DocumentModel;
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
  const { toast } = useToast();
  const [showDownloadConfirm, setShowDownloadConfirm] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  const isPdf = document.file_type.toLowerCase() === 'pdf';

  const loadPdf = useCallback(async () => {
    try {
      const blob = await documentApi.download(document.id);
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
    } catch (error) {
      toast({
        title: 'Failed to Load PDF',
        description: error instanceof Error ? error.message : 'Failed to load PDF preview',
        variant: 'destructive',
      });
    }
  }, [document.id, toast]);

  // Load PDF when dialog opens
  useEffect(() => {
    if (open && isPdf && document.processing_status === DocumentStatus.COMPLETED) {
      loadPdf();
    }
  }, [open, isPdf, document.processing_status, loadPdf]);

  // Clean up blob URL when dialog closes
  useEffect(() => {
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [pdfUrl]);

  const handleDownload = () => {
    setShowDownloadConfirm(true);
  };

  const performDownload = async () => {
    setShowDownloadConfirm(false);
    try {
      toast({
        title: 'Download Started',
        description: `Downloading "${document.filename}"`,
      });

      const blob = await documentApi.download(document.id);

      // Create a download link and trigger it
      const url = window.URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = document.filename;
      window.document.body.appendChild(link);
      link.click();
      window.document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Download Complete',
        description: `"${document.filename}" has been downloaded`,
      });
    } catch (error) {
      toast({
        title: 'Download Failed',
        description: error instanceof Error ? error.message : 'Failed to download document',
        variant: 'destructive',
      });
    }
  };

  const handleOpenExternal = async () => {
    if (!isPdf) {
      // For non-PDF files, download instead of opening
      toast({
        title: 'Downloading Document',
        description: `Non-PDF files cannot be opened in browser. Downloading "${document.filename}" instead.`,
      });
      await performDownload();
      return;
    }

    // For PDF files, open in new tab
    try {
      const blob = await documentApi.download(document.id);
      const url = window.URL.createObjectURL(blob);

      // Open in new tab
      window.open(url, '_blank');

      // Clean up after a delay to ensure the file loads
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 1000);

      toast({
        title: 'Opening Document',
        description: `Opening "${document.filename}" in new tab`,
      });
    } catch (error) {
      toast({
        title: 'Failed to Open',
        description: error instanceof Error ? error.message : 'Failed to open document',
        variant: 'destructive',
      });
    }
  };


  return (
    <>
      <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
        <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-y-auto">
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
            {/* Document Preview Viewer */}
            <div className="rounded-lg border overflow-hidden" style={{ minHeight: '500px' }}>
              {document.processing_status === DocumentStatus.COMPLETED ? (
                isPdf ? (
                  <PdfViewer url={pdfUrl} />
                ) : (
                  <div className="flex flex-col items-center justify-center h-[500px] bg-muted">
                    <FileText className="h-24 w-24 text-muted-foreground mb-4" />
                    <p className="text-sm text-muted-foreground mb-2">
                      Preview not available for {document.file_type.toUpperCase()} files
                    </p>
                    <Button onClick={handleDownload} variant="outline" size="sm">
                      <Download className="mr-2 h-4 w-4" />
                      Download to View
                    </Button>
                  </div>
                )
              ) : (
                <div className="flex flex-col items-center justify-center h-[500px] bg-muted">
                  <FileText className="h-24 w-24 text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground">
                    {document.processing_status === DocumentStatus.PROCESSING && 'Document is being processed...'}
                    {document.processing_status === DocumentStatus.PENDING && 'Document is pending processing...'}
                    {document.processing_status === DocumentStatus.FAILED && 'Document processing failed'}
                  </p>
                </div>
              )}
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
                {isPdf ? 'Open External' : 'Download'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Download Confirmation Dialog */}
      <AlertDialog open={showDownloadConfirm} onOpenChange={setShowDownloadConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm Download</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to download "{document.filename}"?
              <br />
              <span className="text-sm text-muted-foreground">
                Size: {formatFileSize(document.file_size)}
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={performDownload}>Download</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
