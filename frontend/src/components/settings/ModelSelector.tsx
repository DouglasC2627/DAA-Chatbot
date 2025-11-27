'use client';

import React, { useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import type { ModelInfo } from '@/types';

interface ModelSelectorProps {
  type: 'llm' | 'embedding';
  label: string;
  currentModel: string;
  installedModels: ModelInfo[];
  onModelChange: (modelName: string) => Promise<void>;
  disabled?: boolean;
}

export default function ModelSelector({
  type,
  label,
  currentModel,
  installedModels,
  onModelChange,
  disabled = false,
}: ModelSelectorProps) {
  const [isChanging, setIsChanging] = useState(false);
  const { toast } = useToast();

  const handleModelChange = async (modelName: string) => {
    if (modelName === currentModel) return;

    setIsChanging(true);

    try {
      await onModelChange(modelName);

      toast({
        title: 'Model updated',
        description: `Successfully switched to ${modelName}`,
      });
    } catch (error) {
      toast({
        title: 'Failed to update model',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      setIsChanging(false);
    }
  };

  const formatSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-2">
      <Label htmlFor={`${type}-model`}>{label}</Label>
      <div className="flex items-center gap-2">
        <Select
          value={currentModel}
          onValueChange={handleModelChange}
          disabled={disabled || isChanging || installedModels.length === 0}
        >
          <SelectTrigger id={`${type}-model`} className="w-full">
            <SelectValue placeholder={`Select ${type} model`} />
          </SelectTrigger>
          <SelectContent>
            {installedModels.map((model) => (
              <SelectItem key={model.name} value={model.name}>
                <div className="flex items-center justify-between w-full">
                  <span className="flex items-center gap-2">
                    {model.name}
                    {model.name === currentModel && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </span>
                  <span className="text-xs text-muted-foreground ml-4">
                    {formatSize(model.size)}
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {isChanging && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
      </div>
      {installedModels.length === 0 && (
        <p className="text-sm text-muted-foreground">No {type} models installed</p>
      )}
      <p className="text-xs text-muted-foreground">
        Current: <span className="font-medium">{currentModel}</span>
      </p>
    </div>
  );
}
