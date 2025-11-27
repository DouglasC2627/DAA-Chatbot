'use client';

import React, { useState } from 'react';
import { Download, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { systemApi } from '@/lib/api';
import type { PopularModel } from '@/types';

interface ModelInstallerProps {
  popularModels: { llm_models: PopularModel[]; embedding_models: PopularModel[] } | null;
  onModelInstalled: () => void;
}

export default function ModelInstaller({ popularModels, onModelInstalled }: ModelInstallerProps) {
  const [installingModel, setInstallingModel] = useState<string | null>(null);
  const { toast } = useToast();

  const handleInstall = async (modelName: string) => {
    setInstallingModel(modelName);

    try {
      await systemApi.pullModel(modelName);

      toast({
        title: 'Model installed',
        description: `Successfully installed ${modelName}`,
      });

      // Refresh installed models list
      onModelInstalled();
    } catch (error) {
      toast({
        title: 'Installation failed',
        description: error instanceof Error ? error.message : 'Failed to install model',
        variant: 'destructive',
      });
    } finally {
      setInstallingModel(null);
    }
  };

  const renderModelCard = (model: PopularModel) => (
    <Card key={model.name} className="border">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <h4 className="font-medium">{model.name}</h4>
              {model.installed && (
                <Badge variant="secondary" className="text-xs">
                  <Check className="h-3 w-3 mr-1" />
                  Installed
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{model.description}</p>
            <p className="text-xs text-muted-foreground">Size: {model.size}</p>
          </div>
          <div>
            {model.installed ? (
              <Button variant="outline" size="sm" disabled>
                <Check className="h-4 w-4 mr-2" />
                Installed
              </Button>
            ) : (
              <Button
                variant="default"
                size="sm"
                onClick={() => handleInstall(model.name)}
                disabled={installingModel !== null}
              >
                {installingModel === model.name ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Installing...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Install
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (!popularModels) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* LLM Models Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Language Models
        </h3>
        <div className="space-y-2">
          {popularModels.llm_models.map((model) => renderModelCard(model))}
        </div>
      </div>

      {/* Embedding Models Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Embedding Models
        </h3>
        <div className="space-y-2">
          {popularModels.embedding_models.map((model) => renderModelCard(model))}
        </div>
      </div>

      {installingModel && (
        <div className="bg-muted/50 border rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <div className="flex-1">
              <p className="text-sm font-medium">Installing {installingModel}</p>
              <p className="text-xs text-muted-foreground">
                This may take several minutes depending on model size and network speed...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
