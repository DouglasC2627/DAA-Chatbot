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
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Plus, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { CreateProjectRequest } from '@/types';

interface ProjectCreateProps {
  trigger?: React.ReactNode;
  onProjectCreated?: (projectId: number) => void;
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

export default function ProjectCreate({ trigger, onProjectCreated }: ProjectCreateProps) {
  const [open, setOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<CreateProjectRequest>({
    name: '',
    description: '',
  });
  const [nameValidation, setNameValidation] = useState<{
    isValid: boolean;
    invalidChars: string[];
  }>({ isValid: true, invalidChars: [] });

  const addProject = useProjectStore((state) => state.addProject);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
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
      // Call the actual API to create the project
      const { projectApi } = await import('@/lib/api');
      const newProject = await projectApi.create(formData);

      addProject(newProject);

      toast({
        title: 'Success',
        description: `Project "${formData.name}" created successfully`,
      });

      // Reset form and close dialog
      setFormData({ name: '', description: '' });
      setNameValidation({ isValid: true, invalidChars: [] });
      setOpen(false);

      // Notify parent component
      onProjectCreated?.(newProject.id);
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create project',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof CreateProjectRequest, value: string) => {
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
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Create a new project to organize your documents and conversations.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Project Name *</Label>
              <Input
                id="name"
                placeholder="e.g., Research Papers 2024"
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
              <Label htmlFor="description">Description (optional)</Label>
              <Textarea
                id="description"
                placeholder="Brief description of your project..."
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !nameValidation.isValid}
            >
              {isSubmitting ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
