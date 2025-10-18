'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useProjectStore, selectProjects } from '@/stores/projectStore';
import ProjectCard from './ProjectCard';
import ProjectSettings from './ProjectSettings';
import ProjectDeleteConfirm from './ProjectDeleteConfirm';
import { Project } from '@/types';
import { Folder } from 'lucide-react';

export default function ProjectList() {
  const router = useRouter();
  const projects = useProjectStore(selectProjects);
  const setCurrentProject = useProjectStore((state) => state.setCurrentProject);

  const [selectedProjectForEdit, setSelectedProjectForEdit] = useState<Project | null>(null);
  const [selectedProjectForDelete, setSelectedProjectForDelete] = useState<Project | null>(null);

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
