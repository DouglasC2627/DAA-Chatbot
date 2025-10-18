'use client';

import { Document, DocumentStatus } from '@/types';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  FileText,
  Download,
  Trash2,
  MoreVertical,
  FileIcon,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface DocumentCardProps {
  document: Document;
  uploadProgress?: number;
  onDelete?: (document: Document) => void;
  onDownload?: (document: Document) => void;
  onPreview?: (document: Document) => void;
}

const getFileIcon = (fileType: string) => {
  const type = fileType.toLowerCase();
  if (type.includes('pdf')) return <FileText className="h-8 w-8 text-red-500" />;
  if (type.includes('doc')) return <FileText className="h-8 w-8 text-blue-500" />;
  if (type.includes('xls') || type.includes('csv'))
    return <FileText className="h-8 w-8 text-green-500" />;
  if (type.includes('txt') || type.includes('md'))
    return <FileText className="h-8 w-8 text-gray-500" />;
  return <FileIcon className="h-8 w-8 text-gray-400" />;
};

const getStatusBadge = (status: DocumentStatus) => {
  switch (status) {
    case DocumentStatus.COMPLETED:
      return (
        <Badge variant="default" className="bg-green-500">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Processed
        </Badge>
      );
    case DocumentStatus.PROCESSING:
      return (
        <Badge variant="default" className="bg-blue-500">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          Processing
        </Badge>
      );
    case DocumentStatus.FAILED:
      return (
        <Badge variant="destructive">
          <XCircle className="mr-1 h-3 w-3" />
          Failed
        </Badge>
      );
    case DocumentStatus.PENDING:
      return (
        <Badge variant="secondary">
          <Clock className="mr-1 h-3 w-3" />
          Pending
        </Badge>
      );
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

export default function DocumentCard({
  document,
  uploadProgress,
  onDelete,
  onDownload,
  onPreview,
}: DocumentCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.(document);
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDownload?.(document);
  };

  const handlePreview = () => {
    onPreview?.(document);
  };

  const isProcessing = document.processing_status === DocumentStatus.PROCESSING;
  const showProgress = isProcessing && uploadProgress !== undefined;

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={handlePreview}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="flex-shrink-0">{getFileIcon(document.file_type)}</div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-sm truncate" title={document.filename}>
                {document.filename}
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                {formatFileSize(document.file_size)}
              </p>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
                <MoreVertical className="h-4 w-4" />
                <span className="sr-only">Document actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleDownload}>
                <Download className="mr-2 h-4 w-4" />
                Download
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleDelete} className="text-destructive">
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="pb-3 space-y-3">
        <div className="flex items-center justify-between">
          {getStatusBadge(document.processing_status)}
          <span className="text-xs text-muted-foreground">{document.file_type.toUpperCase()}</span>
        </div>

        {showProgress && (
          <div className="space-y-1">
            <Progress value={uploadProgress} className="h-2" />
            <p className="text-xs text-muted-foreground text-center">{uploadProgress}%</p>
          </div>
        )}

        {document.processing_status === DocumentStatus.COMPLETED && (
          <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
            {document.page_count !== undefined && <div>Pages: {document.page_count}</div>}
            {document.chunk_count !== undefined && <div>Chunks: {document.chunk_count}</div>}
          </div>
        )}

        {document.processing_status === DocumentStatus.FAILED && document.error_message && (
          <p className="text-xs text-destructive">{document.error_message}</p>
        )}
      </CardContent>

      <CardFooter className="pt-3 border-t">
        <p className="text-xs text-muted-foreground">
          Uploaded {formatDistanceToNow(new Date(document.upload_date), { addSuffix: true })}
        </p>
      </CardFooter>
    </Card>
  );
}
