'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import MainLayout from '@/components/layout/MainLayout';
import ProjectChatInput from '@/components/projects/ProjectChatInput';
import ChatHistoryPanel from '@/components/chat/ChatHistoryPanel';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, FileText, MessageSquare, Loader2, FolderOpen } from 'lucide-react';
import { projectApi } from '@/lib/api';
import { Project } from '@/types';
import { useToast } from '@/hooks/use-toast';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const projectId = parseInt(params.projectId as string, 10);

  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load project details
  useEffect(() => {
    const loadProject = async () => {
      setIsLoading(true);
      try {
        const projectData = await projectApi.get(projectId);
        setProject(projectData);
      } catch (error) {
        console.error('Failed to load project:', error);
        toast({
          title: 'Error',
          description: 'Failed to load project details',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (projectId) {
      loadProject();
    }
  }, [projectId, toast]);

  // Handle chat selection
  const handleChatSelect = (chatId: number) => {
    router.push(`/chat/${chatId}`);
  };

  // Handle new chat (called from ChatHistoryPanel "New Chat" button)
  const handleNewChat = () => {
    // Scroll to top to show the input
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-[calc(100vh-200px)]">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading project...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (!project) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)] gap-4">
          <FolderOpen className="h-16 w-16 text-muted-foreground/50" />
          <div className="text-center">
            <h2 className="text-2xl font-semibold mb-2">Project Not Found</h2>
            <p className="text-muted-foreground mb-4">
              The project you're looking for doesn't exist or has been deleted.
            </p>
            <Button onClick={() => router.push('/projects')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Projects
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push('/projects')}
              title="Back to projects"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
              {project.description && (
                <p className="text-muted-foreground mt-1">{project.description}</p>
              )}
            </div>
          </div>

          <Button variant="outline" onClick={() => router.push(`/projects/${projectId}/documents`)}>
            <FileText className="h-4 w-4 mr-2" />
            Manage Documents
          </Button>
        </div>

        {/* Project Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-blue-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Documents</p>
                  <div className="flex items-center gap-2">
                    <p className="text-2xl font-bold">{project.document_count || 0}</p>
                    {project.document_count === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        No documents yet
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-green-500/10 flex items-center justify-center">
                  <MessageSquare className="h-6 w-6 text-green-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Conversations</p>
                  <div className="flex items-center gap-2">
                    <p className="text-2xl font-bold">{project.chat_count || 0}</p>
                    {project.chat_count === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Start chatting
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* New Chat Input - Sticky Section */}
        <ProjectChatInput projectId={projectId} projectName={project.name} />

        {/* Chat History */}
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold">Chat History</h2>
            <p className="text-sm text-muted-foreground mt-1">
              View and manage your conversations in this project
            </p>
          </div>

          <Card className="h-[600px]">
            <ChatHistoryPanel
              projectId={projectId}
              onChatSelect={handleChatSelect}
              onNewChat={handleNewChat}
            />
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}
