'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useProjectStore, selectProjects } from '@/stores/projectStore';
import ProjectCard from './ProjectCard';
import ProjectSettings from './ProjectSettings';
import ProjectDeleteConfirm from './ProjectDeleteConfirm';
import { Project } from '@/types';
import { Folder, Loader2 } from 'lucide-react';
import { projectApi } from '@/lib/api';

export default function ProjectList() {
  const router = useRouter();
  const projects = useProjectStore(selectProjects);
  const setCurrentProject = useProjectStore((state) => state.setCurrentProject);
  const setProjects = useProjectStore((state) => state.setProjects);

  const [selectedProjectForEdit, setSelectedProjectForEdit] = useState<Project | null>(null);
  const [selectedProjectForDelete, setSelectedProjectForDelete] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch projects from the API on mount
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const fetchedProjects = await projectApi.list();
        setProjects(fetchedProjects);
      } catch (err) {
        console.error('Failed to fetch projects:', err);
        setError('Failed to load projects. Please try refreshing the page.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  const handleSelectProject = (project: Project) => {
    setCurrentProject(project.id);
    router.push(`/chat/${project.id}`);
  };

  const handleEditProject = (project: Project) => {
    setSelectedProjectForEdit(project);
  };

  const handleDeleteProject = (project: Project) => {
    setSelectedProjectForDelete(project);
  };

  const handleEditClose = () => {
    setSelectedProjectForEdit(null);
  };

  const handleDeleteClose = () => {
    setSelectedProjectForDelete(null);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <Loader2 className="h-16 w-16 text-muted-foreground mb-4 animate-spin" />
        <h3 className="text-lg font-semibold mb-2">Loading projects...</h3>
        <p className="text-sm text-muted-foreground">Please wait while we fetch your projects</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <div className="text-destructive mb-4">⚠️</div>
        <h3 className="text-lg font-semibold mb-2">Error loading projects</h3>
        <p className="text-sm text-muted-foreground text-center max-w-md mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          Reload Page
        </button>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <Folder className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">No projects yet</h3>
        <p className="text-sm text-muted-foreground text-center max-w-md">
          Get started by creating your first project. Projects help you organize your documents and
          conversations.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <ProjectCard
            key={project.id}
            project={project}
            onSelect={handleSelectProject}
            onEdit={handleEditProject}
            onDelete={handleDeleteProject}
          />
        ))}
      </div>

      {/* Project Settings Modal */}
      {selectedProjectForEdit && (
        <ProjectSettings
          project={selectedProjectForEdit}
          open={!!selectedProjectForEdit}
          onClose={handleEditClose}
        />
      )}

      {/* Project Delete Confirmation */}
      {selectedProjectForDelete && (
        <ProjectDeleteConfirm
          project={selectedProjectForDelete}
          open={!!selectedProjectForDelete}
          onClose={handleDeleteClose}
        />
      )}
    </>
  );
}
