// Document Store - Zustand state management for document functionality
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Document, DocumentStatus } from '@/types';

// ============================================================================
// Document Store State Interface
// ============================================================================

interface DocumentState {
  // Current state
  documents: Record<number, Document[]>; // projectId -> documents
  selectedDocumentIds: number[];
  uploadProgress: Record<number, number>; // documentId -> progress (0-100)
  processingDocuments: Set<number>; // documentIds being processed
  isLoading: boolean;
  error: string | null;

  // Actions - Document management
  addDocument: (projectId: number, document: Document) => void;
  updateDocument: (projectId: number, documentId: number, updates: Partial<Document>) => void;
  deleteDocument: (projectId: number, documentId: number) => void;
  setDocuments: (projectId: number, documents: Document[]) => void;
  clearDocuments: (projectId: number) => void;

  // Actions - Selection
  selectDocument: (documentId: number) => void;
  unselectDocument: (documentId: number) => void;
  selectAllDocuments: (projectId: number) => void;
  clearSelection: () => void;
  toggleDocumentSelection: (documentId: number) => void;

  // Actions - Upload progress
  setUploadProgress: (documentId: number, progress: number) => void;
  clearUploadProgress: (documentId: number) => void;
  resetUploadProgress: () => void;

  // Actions - Processing status
  addProcessingDocument: (documentId: number) => void;
  removeProcessingDocument: (documentId: number) => void;
  clearProcessingDocuments: () => void;

  // Actions - Loading state
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;

  // Actions - Utility
  reset: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState = {
  documents: {},
  selectedDocumentIds: [],
  uploadProgress: {},
  processingDocuments: new Set<number>(),
  isLoading: false,
  error: null,
};

// ============================================================================
// Document Store
// ============================================================================

export const useDocumentStore = create<DocumentState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // ============================================================================
        // Document Management Actions
        // ============================================================================

        addDocument: (projectId, document) => {
          set(
            (state) => {
              const projectDocuments = state.documents[projectId] || [];
              return {
                documents: {
                  ...state.documents,
                  [projectId]: [document, ...projectDocuments],
                },
                error: null,
              };
            },
            false,
            'addDocument'
          );
        },

        updateDocument: (projectId, documentId, updates) => {
          set(
            (state) => {
              const projectDocuments = state.documents[projectId] || [];
              return {
                documents: {
                  ...state.documents,
                  [projectId]: projectDocuments.map((doc) =>
                    doc.id === documentId ? { ...doc, ...updates } : doc
                  ),
                },
                error: null,
              };
            },
            false,
            'updateDocument'
          );
        },

        deleteDocument: (projectId, documentId) => {
          set(
            (state) => {
              const projectDocuments = state.documents[projectId] || [];
              return {
                documents: {
                  ...state.documents,
                  [projectId]: projectDocuments.filter((doc) => doc.id !== documentId),
                },
                selectedDocumentIds: state.selectedDocumentIds.filter((id) => id !== documentId),
                error: null,
              };
            },
            false,
            'deleteDocument'
          );

          // Clean up upload progress and processing status
          get().clearUploadProgress(documentId);
          get().removeProcessingDocument(documentId);
        },

        setDocuments: (projectId, documents) => {
          set(
            (state) => ({
              documents: {
                ...state.documents,
                [projectId]: documents,
              },
              error: null,
            }),
            false,
            'setDocuments'
          );
        },

        clearDocuments: (projectId) => {
          set(
            (state) => {
              const newDocuments = { ...state.documents };
              delete newDocuments[projectId];
              return {
                documents: newDocuments,
                error: null,
              };
            },
            false,
            'clearDocuments'
          );
        },

        // ============================================================================
        // Selection Actions
        // ============================================================================

        selectDocument: (documentId) => {
          set(
            (state) => ({
              selectedDocumentIds: state.selectedDocumentIds.includes(documentId)
                ? state.selectedDocumentIds
                : [...state.selectedDocumentIds, documentId],
            }),
            false,
            'selectDocument'
          );
        },

        unselectDocument: (documentId) => {
          set(
            (state) => ({
              selectedDocumentIds: state.selectedDocumentIds.filter((id) => id !== documentId),
            }),
            false,
            'unselectDocument'
          );
        },

        selectAllDocuments: (projectId) => {
          const projectDocuments = get().documents[projectId] || [];
          set(
            {
              selectedDocumentIds: projectDocuments.map((doc) => doc.id),
            },
            false,
            'selectAllDocuments'
          );
        },

        clearSelection: () => {
          set({ selectedDocumentIds: [] }, false, 'clearSelection');
        },

        toggleDocumentSelection: (documentId) => {
          const { selectedDocumentIds } = get();
          if (selectedDocumentIds.includes(documentId)) {
            get().unselectDocument(documentId);
          } else {
            get().selectDocument(documentId);
          }
        },

        // ============================================================================
        // Upload Progress Actions
        // ============================================================================

        setUploadProgress: (documentId, progress) => {
          set(
            (state) => ({
              uploadProgress: {
                ...state.uploadProgress,
                [documentId]: Math.min(100, Math.max(0, progress)),
              },
            }),
            false,
            'setUploadProgress'
          );
        },

        clearUploadProgress: (documentId) => {
          set(
            (state) => {
              const newProgress = { ...state.uploadProgress };
              delete newProgress[documentId];
              return { uploadProgress: newProgress };
            },
            false,
            'clearUploadProgress'
          );
        },

        resetUploadProgress: () => {
          set({ uploadProgress: {} }, false, 'resetUploadProgress');
        },

        // ============================================================================
        // Processing Status Actions
        // ============================================================================

        addProcessingDocument: (documentId) => {
          set(
            (state) => ({
              processingDocuments: new Set(state.processingDocuments).add(documentId),
            }),
            false,
            'addProcessingDocument'
          );
        },

        removeProcessingDocument: (documentId) => {
          set(
            (state) => {
              const newProcessing = new Set(state.processingDocuments);
              newProcessing.delete(documentId);
              return { processingDocuments: newProcessing };
            },
            false,
            'removeProcessingDocument'
          );
        },

        clearProcessingDocuments: () => {
          set({ processingDocuments: new Set() }, false, 'clearProcessingDocuments');
        },

        // ============================================================================
        // Loading State Actions
        // ============================================================================

        setLoading: (isLoading) => {
          set({ isLoading }, false, 'setLoading');
        },

        setError: (error) => {
          set({ error, isLoading: false }, false, 'setError');
        },

        // ============================================================================
        // Utility Actions
        // ============================================================================

        reset: () => {
          set(initialState, false, 'reset');
        },
      }),
      {
        name: 'document-storage',
        partialize: (state) => ({
          // Only persist these fields
          documents: state.documents,
          // Don't persist selection, upload progress, processing state, loading/error
        }),
      }
    ),
    { name: 'DocumentStore' }
  )
);

// ============================================================================
// Selectors (for optimized component re-renders)
// ============================================================================

export const selectProjectDocuments = (projectId: number) => (state: DocumentState) =>
  state.documents[projectId] || [];

export const selectDocumentById =
  (projectId: number, documentId: number) => (state: DocumentState) => {
    const projectDocuments = state.documents[projectId] || [];
    return projectDocuments.find((doc) => doc.id === documentId);
  };

export const selectSelectedDocuments = (projectId: number) => (state: DocumentState) => {
  const projectDocuments = state.documents[projectId] || [];
  return projectDocuments.filter((doc) => state.selectedDocumentIds.includes(doc.id));
};

export const selectIsDocumentSelected = (documentId: number) => (state: DocumentState) =>
  state.selectedDocumentIds.includes(documentId);

export const selectUploadProgress = (documentId: number) => (state: DocumentState) =>
  state.uploadProgress[documentId] || 0;

export const selectIsProcessing = (documentId: number) => (state: DocumentState) =>
  state.processingDocuments.has(documentId);

export const selectProcessingDocumentsCount = (state: DocumentState) =>
  state.processingDocuments.size;

export const selectDocumentsByStatus =
  (projectId: number, status: DocumentStatus) => (state: DocumentState) => {
    const projectDocuments = state.documents[projectId] || [];
    return projectDocuments.filter((doc) => doc.processing_status === status);
  };

export const selectIsLoading = (state: DocumentState) => state.isLoading;

export const selectError = (state: DocumentState) => state.error;
