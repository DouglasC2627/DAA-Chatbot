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
import { AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { Project, UpdateProjectRequest } from '@/types';
import { projectApi } from '@/lib/api';

interface ProjectSettingsProps {
  project: Project;
  open: boolean;
  onClose: () => void;
}

/**
 * Validate project name for filesystem safety
 * Allows: alphanumeric, spaces, hyphens, underscores
 * Returns array of invalid characters found
 */
function validateProjectName(name: string): string[] {
  const invalidChars: string[] = [];
  const allowedPattern = /^[a-zA-Z0-9\s\-_]+$/;

  if (!allowedPattern.test(name)) {
    // Find specific invalid characters
    for (const char of name) {
      if (!/[a-zA-Z0-9\s\-_]/.test(char) && !invalidChars.includes(char)) {
        invalidChars.push(char);
      }
    }
  }

  return invalidChars;
}

export default function ProjectSettings({ project, open, onClose }: ProjectSettingsProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<UpdateProjectRequest>({
    name: project.name,
    description: project.description || '',
  });
  const [nameValidation, setNameValidation] = useState<{
    isValid: boolean;
    invalidChars: string[];
  }>({ isValid: true, invalidChars: [] });

  const updateProject = useProjectStore((state) => state.updateProject);
  const { toast } = useToast();

  // Update form when project changes
  useEffect(() => {
    setFormData({
      name: project.name,
      description: project.description || '',
    });
    // Validate initial name
    const invalidChars = validateProjectName(project.name);
    setNameValidation({
      isValid: invalidChars.length === 0,
      invalidChars,
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

    // Check for invalid characters
    if (!nameValidation.isValid) {
      toast({
        title: 'Validation Error',
        description: `Project name contains invalid characters: ${nameValidation.invalidChars.join(', ')}`,
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      // Call the backend API to update the project
      const updatedProject = await projectApi.update(project.id, formData);

      // Update local store after successful API call
      updateProject(project.id, updatedProject);

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

    // Validate project name
    if (field === 'name') {
      const invalidChars = validateProjectName(value);
      setNameValidation({
        isValid: invalidChars.length === 0,
        invalidChars,
      });
    }
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
                className={!nameValidation.isValid && formData.name ? 'border-red-500' : ''}
              />
              {!nameValidation.isValid && formData.name && (
                <div className="flex items-start gap-2 text-sm text-red-500">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium">Invalid characters detected</p>
                    <p className="text-xs mt-1">
                      Found: {nameValidation.invalidChars.map(c => `"${c}"`).join(', ')}
                    </p>
                  </div>
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                Allowed: letters, numbers, spaces, hyphens, and underscores
              </p>
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
            <Button
              type="submit"
              disabled={isSubmitting || !nameValidation.isValid}
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
