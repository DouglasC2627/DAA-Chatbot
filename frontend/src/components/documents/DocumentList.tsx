'use client';

import { useState } from 'react';
import { useDocumentStore, selectProjectDocuments } from '@/stores/documentStore';
import { useProjectStore, selectCurrentProject } from '@/stores/projectStore';
import DocumentCard from './DocumentCard';
import DocumentPreview from './DocumentPreview';
import { Document } from '@/types';
import { FileText } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function DocumentList() {
  const currentProject = useProjectStore(selectCurrentProject);
  const allDocuments = useDocumentStore((state) => state.documents);
  const deleteDocument = useDocumentStore((state) => state.deleteDocument);
  const { toast } = useToast();

  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  // Get documents for current project
  const projectDocuments = currentProject ? allDocuments[currentProject.id] || [] : [];

  const handleDelete = (document: Document) => {
    if (confirm(`Are you sure you want to delete "${document.filename}"?`)) {
      // TODO: Replace with actual API call
      // await api.delete(`/api/documents/${document.id}`);

      if (currentProject) {
        deleteDocument(currentProject.id, document.id);
      }

      toast({
        title: 'Document Deleted',
        description: `"${document.filename}" has been deleted`,
      });
    }
  };

  const handleDownload = (document: Document) => {
    // TODO: Implement actual download
    toast({
      title: 'Download Started',
      description: `Downloading "${document.filename}"`,
    });
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
    </>
  );
}
