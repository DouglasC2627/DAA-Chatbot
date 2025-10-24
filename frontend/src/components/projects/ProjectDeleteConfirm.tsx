'use client';

import { useState } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import type { Project } from '@/types';
import { AlertTriangle } from 'lucide-react';
import { projectApi } from '@/lib/api';

interface ProjectDeleteConfirmProps {
  project: Project;
  open: boolean;
  onClose: () => void;
}

export default function ProjectDeleteConfirm({
  project,
  open,
  onClose,
}: ProjectDeleteConfirmProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const deleteProject = useProjectStore((state) => state.deleteProject);
  const { toast } = useToast();

  const handleDelete = async () => {
    setIsDeleting(true);

    try {
      // Call the backend API to delete the project
      await projectApi.delete(project.id);

      // Update local store after successful API call
      deleteProject(project.id);

      toast({
        title: 'Project Deleted',
        description: `Project "${project.name}" has been permanently deleted`,
      });

      onClose();
    } catch (error: any) {
      // If project doesn't exist in backend (404), remove it from frontend anyway
      if (error?.response?.status === 404) {
        deleteProject(project.id);

        toast({
          title: 'Project Removed',
          description: `Project "${project.name}" was not found in the database and has been removed from the list`,
        });

        onClose();
      } else {
        // Other errors - show error message
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to delete project',
          variant: 'destructive',
        });
      }
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            <DialogTitle>Delete Project</DialogTitle>
          </div>
          <DialogDescription className="pt-3">
            Are you sure you want to delete <span className="font-semibold">{project.name}</span>?
            This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-3">
          <p className="text-sm text-muted-foreground">
            Deleting this project will permanently remove:
          </p>
          <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground pl-2">
            <li>{project.document_count || 0} document(s)</li>
            <li>{project.chat_count || 0} chat conversation(s)</li>
            <li>All associated vector embeddings</li>
            <li>All project settings and metadata</li>
          </ul>
          <p className="text-sm font-semibold text-destructive pt-2">
            This action is irreversible!
          </p>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={isDeleting}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={handleDelete} disabled={isDeleting}>
            {isDeleting ? 'Deleting...' : 'Delete Project'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
