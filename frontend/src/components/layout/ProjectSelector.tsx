'use client';

import { useProjectStore, selectCurrentProject, selectProjects } from '@/stores/projectStore';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Folder } from 'lucide-react';

export default function ProjectSelector() {
  const currentProject = useProjectStore(selectCurrentProject);
  const projects = useProjectStore(selectProjects);
  const setCurrentProject = useProjectStore((state) => state.setCurrentProject);

  if (projects.length === 0) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
        <Folder className="h-4 w-4" />
        <span>No projects yet</span>
      </div>
    );
  }

  return (
    <Select
      value={currentProject?.id || ''}
      onValueChange={(value) => setCurrentProject(value)}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select a project">
          {currentProject ? (
            <div className="flex items-center gap-2">
              <Folder className="h-4 w-4" />
              <span className="truncate">{currentProject.name}</span>
            </div>
          ) : (
            <span className="text-muted-foreground">Select a project</span>
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {projects.map((project) => (
          <SelectItem key={project.id} value={project.id}>
            <div className="flex items-center gap-2">
              <Folder className="h-4 w-4" />
              <div className="flex flex-col">
                <span className="font-medium">{project.name}</span>
                {project.description && (
                  <span className="text-xs text-muted-foreground line-clamp-1">
                    {project.description}
                  </span>
                )}
              </div>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
