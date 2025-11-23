'use client';

import { useState, useEffect, useCallback } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useDocumentStore } from '@/stores/documentStore';
import { useProjectStore } from '@/stores/projectStore';
import DocumentCard from './DocumentCard';
import dynamic from 'next/dynamic';
import { Document, DocumentStatus } from '@/types';
import { FileText } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useDocumentUpdates, useWebSocketConnection, useProjectRoom } from '@/lib/websocket';
import { documentApi } from '@/lib/api';
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

// Dynamically import DocumentPreview to avoid SSR issues with PDF.js
const DocumentPreview = dynamic(() => import('./DocumentPreview'), {
  ssr: false,
  loading: () => null,
});

export default function DocumentList() {
  const currentProject = useProjectStore(
    useShallow((state) => state.projects.find((project) => project.id === state.currentProjectId))
  );
  const allDocuments = useDocumentStore((state) => state.documents);
  const setDocuments = useDocumentStore((state) => state.setDocuments);
  const updateDocument = useDocumentStore((state) => state.updateDocument);
  const deleteDocument = useDocumentStore((state) => state.deleteDocument);
  const { toast } = useToast();

  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [downloadDocument, setDownloadDocument] = useState<Document | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Connect to WebSocket and join project room
  useWebSocketConnection({ autoConnect: true });
  useProjectRoom(currentProject?.id || null);

  // Get documents for current project
  const projectDocuments = currentProject ? allDocuments[currentProject.id] || [] : [];

  // Fetch documents when project changes
  useEffect(() => {
    if (!currentProject) return;

    const fetchDocuments = async () => {
      setIsLoading(true);
      try {
        const docs = await documentApi.list(currentProject.id);
        const formattedDocs = docs.map((doc) => ({
          id: doc.id,
          project_id: currentProject.id,
          filename: doc.filename,
          file_type: doc.file_type,
          file_size: doc.file_size,
          upload_date: doc.created_at,
          processing_status: doc.status as DocumentStatus,
          page_count: doc.page_count || 0,
          chunk_count: doc.chunk_count || 0,
        }));
        setDocuments(currentProject.id, formattedDocs);
      } catch (error) {
        toast({
          title: 'Failed to Load Documents',
          description: error instanceof Error ? error.message : 'Unknown error',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, [currentProject, setDocuments, toast]);

  // Listen for WebSocket document status updates
  const handleDocumentStatusUpdate = useCallback(
    (event: { document_id: number; status: string; progress?: number }) => {
      if (!currentProject) return;

      // Update the document status in the store
      updateDocument(currentProject.id, event.document_id, {
        processing_status: event.status as DocumentStatus,
      });

      // If completed, refresh the document to get updated metadata
      if (event.status === 'completed') {
        documentApi
          .get(event.document_id)
          .then((doc) => {
            updateDocument(currentProject.id, event.document_id, {
              processing_status: doc.status as DocumentStatus,
              page_count: doc.page_count || 0,
              chunk_count: doc.chunk_count || 0,
              word_count: doc.word_count || 0,
            });
          })
          .catch(console.error);
      }
    },
    [currentProject, updateDocument]
  );

  useDocumentUpdates(handleDocumentStatusUpdate);

  const handleDelete = async (document: Document) => {
    if (confirm(`Are you sure you want to delete "${document.filename}"?`)) {
      try {
        await documentApi.delete(document.id);

        if (currentProject) {
          deleteDocument(currentProject.id, document.id);
        }

        toast({
          title: 'Document Deleted',
          description: `"${document.filename}" has been deleted`,
        });
      } catch (error) {
        toast({
          title: 'Delete Failed',
          description: error instanceof Error ? error.message : 'Failed to delete document',
          variant: 'destructive',
        });
      }
    }
  };

  const handleDownload = (document: Document) => {
    setDownloadDocument(document);
  };

  const performDownload = async () => {
    if (!downloadDocument) return;

    setDownloadDocument(null);
    try {
      toast({
        title: 'Download Started',
        description: `Downloading "${downloadDocument.filename}"`,
      });

      const blob = await documentApi.download(downloadDocument.id);

      // Create a download link and trigger it
      const url = window.URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = downloadDocument.filename;
      window.document.body.appendChild(link);
      link.click();
      window.document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Download Complete',
        description: `"${downloadDocument.filename}" has been downloaded`,
      });
    } catch (error) {
      toast({
        title: 'Download Failed',
        description: error instanceof Error ? error.message : 'Failed to download document',
        variant: 'destructive',
      });
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const handlePreview = (document: Document) => {
    setSelectedDocument(document);
  };

  if (!currentProject) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <FileText className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Project Selected</h3>
        <p className="text-sm text-muted-foreground text-center max-w-md">
          Please select a project from the sidebar to view and manage its documents.
        </p>
      </div>
    );
  }

  if (projectDocuments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <FileText className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Documents</h3>
        <p className="text-sm text-muted-foreground text-center max-w-md">
          Upload documents to this project to get started with RAG-powered conversations.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {projectDocuments.map((document) => (
          <DocumentCard
            key={document.id}
            document={document}
            onDelete={handleDelete}
            onDownload={handleDownload}
            onPreview={handlePreview}
          />
        ))}
      </div>

      {/* Document Preview Modal */}
      {selectedDocument && (
        <DocumentPreview
          document={selectedDocument}
          open={!!selectedDocument}
          onClose={() => setSelectedDocument(null)}
        />
      )}

      {/* Download Confirmation Dialog */}
      <AlertDialog
        open={!!downloadDocument}
        onOpenChange={(open: boolean) => !open && setDownloadDocument(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm Download</AlertDialogTitle>
            <AlertDialogDescription>
              {downloadDocument && (
                <>
                  Are you sure you want to download "{downloadDocument.filename}"?
                  <br />
                  <span className="text-sm text-muted-foreground">
                    Size: {formatFileSize(downloadDocument.file_size)}
                  </span>
                </>
              )}
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
