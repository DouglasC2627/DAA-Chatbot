'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useProjectStore } from '@/stores/projectStore';
import MainLayout from '@/components/layout/MainLayout';
import DocumentUpload from '@/components/documents/DocumentUpload';
import DocumentList from '@/components/documents/DocumentList';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { projectApi } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export default function ProjectDocumentsPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const projectId = parseInt(params.projectId as string, 10);

  const currentProjectId = useProjectStore((state) => state.currentProjectId);
  const setCurrentProject = useProjectStore((state) => state.setCurrentProject);
  const projects = useProjectStore((state) => state.projects);
  const currentProject = projects.find((p) => p.id === projectId);

  // Set current project when page loads
  useEffect(() => {
    if (projectId && currentProjectId !== projectId) {
      // Verify project exists before setting
      projectApi
        .get(projectId)
        .then(() => {
          setCurrentProject(projectId);
        })
        .catch((error) => {
          console.error('Failed to load project:', error);
          toast({
            title: 'Error',
            description: 'Project not found',
            variant: 'destructive',
          });
          router.push('/projects');
        });
    }
  }, [projectId, currentProjectId, setCurrentProject, router, toast]);

  // Show loading while setting up the project
  if (!currentProject || currentProjectId !== projectId) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-[calc(100vh-200px)]">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading documents...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Header Section */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/projects/${projectId}`)}
            title="Back to project"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Documents - {currentProject.name}
            </h1>
            <p className="text-muted-foreground mt-2">
              Upload and manage documents for RAG-powered conversations
            </p>
          </div>
        </div>

        {/* Upload Section */}
        <DocumentUpload />

        {/* Documents List Section */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Your Documents</h2>
          <DocumentList />
        </div>
      </div>
    </MainLayout>
  );
}
