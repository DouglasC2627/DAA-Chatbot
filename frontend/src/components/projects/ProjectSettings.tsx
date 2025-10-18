'use client';

import { useState, useEffect } from 'react';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import type { Project, UpdateProjectRequest } from '@/types';

interface ProjectSettingsProps {
  project: Project;
  open: boolean;
  onClose: () => void;
}

export default function ProjectSettings({ project, open, onClose }: ProjectSettingsProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<UpdateProjectRequest>({
    name: project.name,
    description: project.description || '',
  });

  const updateProject = useProjectStore((state) => state.updateProject);
  const { toast } = useToast();

  // Update form when project changes
  useEffect(() => {
    setFormData({
      name: project.name,
      description: project.description || '',
    });
  }, [project]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name?.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Project name is required',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      // TODO: Replace with actual API call
      // const response = await api.put(`/api/projects/${project.id}`, formData);

      updateProject(project.id, formData);

      toast({
        title: 'Success',
        description: `Project "${formData.name}" updated successfully`,
      });

      onClose();
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update project',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof UpdateProjectRequest, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Project Settings</DialogTitle>
            <DialogDescription>Update your project details and configuration.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="edit-name">Project Name *</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-description">Description (optional)</Label>
              <Textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={4}
              />
            </div>
            <div className="grid gap-2 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                <p className="font-medium mb-1">Project Statistics</p>
                <div className="grid grid-cols-2 gap-2">
                  <div>Documents: {project.document_count || 0}</div>
                  <div>Chats: {project.chat_count || 0}</div>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
