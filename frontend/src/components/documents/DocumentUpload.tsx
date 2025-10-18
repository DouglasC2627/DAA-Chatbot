'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useDocumentStore } from '@/stores/documentStore';
import { useProjectStore, selectCurrentProject } from '@/stores/projectStore';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, File, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Progress } from '@/components/ui/progress';
import { DocumentStatus } from '@/types';

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
  'text/csv': ['.csv'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function DocumentUpload() {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const currentProject = useProjectStore(selectCurrentProject);
  const addDocument = useDocumentStore((state) => state.addDocument);
  const { toast } = useToast();

  const onDrop = useCallback(
    async (acceptedFiles: File[], rejectedFiles: any[]) => {
      if (!currentProject) {
        toast({
          title: 'No Project Selected',
          description: 'Please select a project before uploading documents',
          variant: 'destructive',
        });
        return;
      }

      // Handle rejected files
      if (rejectedFiles.length > 0) {
        rejectedFiles.forEach((rejection) => {
          const errors = rejection.errors.map((e: any) => e.message).join(', ');
          toast({
            title: 'File Rejected',
            description: `${rejection.file.name}: ${errors}`,
            variant: 'destructive',
          });
        });
      }

      if (acceptedFiles.length === 0) return;

      setIsUploading(true);

      // Initialize uploading files
      const initialFiles: UploadingFile[] = acceptedFiles.map((file) => ({
        file,
        progress: 0,
        status: 'uploading' as const,
      }));
      setUploadingFiles(initialFiles);

      // Upload files one by one (or in parallel if desired)
      for (let i = 0; i < acceptedFiles.length; i++) {
        const file = acceptedFiles[i];

        try {
          // Simulate upload progress (replace with actual API call)
          await simulateUpload(file, (progress) => {
            setUploadingFiles((prev) => prev.map((f, idx) => (idx === i ? { ...f, progress } : f)));
          });

          // Create mock document object (replace with actual API response)
          const newDocument = {
            id: `doc-${Date.now()}-${i}`,
            project_id: currentProject.id,
            filename: file.name,
            file_type: file.type || 'application/octet-stream',
            file_size: file.size,
            upload_date: new Date().toISOString(),
            processing_status: DocumentStatus.PROCESSING,
            page_count: 0,
            chunk_count: 0,
          };

          addDocument(currentProject.id, newDocument);

          // Update file status
          setUploadingFiles((prev) =>
            prev.map((f, idx) => (idx === i ? { ...f, status: 'success' as const } : f))
          );
        } catch (error) {
          setUploadingFiles((prev) =>
            prev.map((f, idx) =>
              idx === i
                ? {
                    ...f,
                    status: 'error' as const,
                    error: error instanceof Error ? error.message : 'Upload failed',
                  }
                : f
            )
          );
        }
      }

      setIsUploading(false);

      // Clear uploaded files after a delay
      setTimeout(() => {
        setUploadingFiles([]);
      }, 3000);

      toast({
        title: 'Upload Complete',
        description: `${acceptedFiles.length} file(s) uploaded successfully`,
      });
    },
    [currentProject, addDocument, toast]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
  });

  const removeUploadingFile = (index: number) => {
    setUploadingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <Card
        {...getRootProps()}
        className={`border-2 border-dashed transition-colors cursor-pointer ${
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
        }`}
      >
        <CardContent className="flex flex-col items-center justify-center p-12 text-center">
          <input {...getInputProps()} />
          <div className="mb-4 rounded-full bg-primary/10 p-4">
            <Upload className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {isDragActive ? 'Drop files here' : 'Upload Documents'}
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            Drag and drop files here, or click to browse
          </p>
          <p className="text-xs text-muted-foreground">
            Supported: PDF, DOCX, TXT, MD, CSV, XLSX (Max 10MB per file)
          </p>
          <Button type="button" variant="outline" className="mt-4" disabled={isUploading}>
            {isUploading ? 'Uploading...' : 'Select Files'}
          </Button>
        </CardContent>
      </Card>

      {/* Uploading Files List */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Uploading Files</h4>
          {uploadingFiles.map((uploadFile, index) => (
            <Card key={index}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <File className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{uploadFile.file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(uploadFile.file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {uploadFile.status === 'uploading' && (
                      <>
                        <Progress value={uploadFile.progress} className="w-24 h-2" />
                        <span className="text-xs text-muted-foreground w-10 text-right">
                          {uploadFile.progress}%
                        </span>
                      </>
                    )}
                    {uploadFile.status === 'success' && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                    {uploadFile.status === 'error' && (
                      <AlertCircle className="h-5 w-5 text-destructive" />
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => removeUploadingFile(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                {uploadFile.status === 'error' && uploadFile.error && (
                  <p className="text-xs text-destructive mt-2">{uploadFile.error}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// Simulate upload progress (replace with actual API call)
function simulateUpload(_file: File, onProgress: (progress: number) => void): Promise<void> {
  return new Promise((resolve) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      onProgress(Math.min(progress, 100));
      if (progress >= 100) {
        clearInterval(interval);
        setTimeout(resolve, 500);
      }
    }, 200);
  });
}
