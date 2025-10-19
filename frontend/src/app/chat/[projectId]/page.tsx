'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useProjectStore } from '@/stores/projectStore';
import ChatInterface from '@/components/chat/ChatInterface';
import { Loader2 } from 'lucide-react';

interface ChatPageProps {
  params: {
    projectId: string;
  };
}

export default function ChatPage({ params }: ChatPageProps) {
  const router = useRouter();
  const projects = useProjectStore((state) => state.projects);
  const setCurrentProject = useProjectStore((state) => state.setCurrentProject);
  const currentProjectId = useProjectStore((state) => state.currentProjectId);

  // Convert URL param to number for comparison
  const projectIdNum = Number(params.projectId);
  const project = projects.find((p) => p.id === projectIdNum);

  useEffect(() => {
    // Set the current project if it exists
    if (project && currentProjectId !== projectIdNum) {
      setCurrentProject(projectIdNum);
    }

    // Redirect to projects page if project doesn't exist
    if (!project && projects.length > 0) {
      router.push('/projects');
    }
  }, [projectIdNum, project, projects, currentProjectId, setCurrentProject, router]);

  // Show loading state while checking project
  if (!project) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading chat...</p>
        </div>
      </div>
    );
  }

  return <ChatInterface projectId={projectIdNum} />;
}
