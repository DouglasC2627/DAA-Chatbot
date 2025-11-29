'use client';

import React, { useState } from 'react';
import { Download, Check, Loader2, ExternalLink, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { systemApi } from '@/lib/api';
import type { PopularModel } from '@/types';

interface ModelInstallerProps {
  popularModels: { llm_models: PopularModel[]; embedding_models: PopularModel[] } | null;
  onModelInstalled: () => void;
}

export default function ModelInstaller({ popularModels, onModelInstalled }: ModelInstallerProps) {
  const [installingModel, setInstallingModel] = useState<string | null>(null);
  const [llmSearchQuery, setLlmSearchQuery] = useState('');
  const [embeddingSearchQuery, setEmbeddingSearchQuery] = useState('');
  const [customLlmModels, setCustomLlmModels] = useState<PopularModel[]>([]);
  const [customEmbeddingModels, setCustomEmbeddingModels] = useState<PopularModel[]>([]);
  const { toast } = useToast();

  const getOllamaLibraryUrl = (modelName: string): string => {
    return `https://ollama.com/library/${modelName.split(':')[0]}`;
  };

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

  const handleAddLlmModel = () => {
    if (!llmSearchQuery.trim()) {
      toast({
        title: 'Invalid input',
        description: 'Please enter a model name',
        variant: 'destructive',
      });
      return;
    }

    // Check if model already exists in popular or custom lists
    const allLlmModels = [
      ...(popularModels?.llm_models || []),
      ...customLlmModels,
    ];

    if (allLlmModels.some(m => m.name === llmSearchQuery.trim())) {
      toast({
        title: 'Model already listed',
        description: `${llmSearchQuery} is already in the list`,
        variant: 'destructive',
      });
      return;
    }

    // Add to custom models list
    const newModel: PopularModel = {
      name: llmSearchQuery.trim(),
      size: 'Unknown',
      description: 'Custom model from Ollama library',
      installed: false,
    };

    setCustomLlmModels([...customLlmModels, newModel]);
    setLlmSearchQuery('');
  };

  const handleAddEmbeddingModel = () => {
    if (!embeddingSearchQuery.trim()) {
      toast({
        title: 'Invalid input',
        description: 'Please enter a model name',
        variant: 'destructive',
      });
      return;
    }

    // Check if model already exists in popular or custom lists
    const allEmbeddingModels = [
      ...(popularModels?.embedding_models || []),
      ...customEmbeddingModels,
    ];

    if (allEmbeddingModels.some(m => m.name === embeddingSearchQuery.trim())) {
      toast({
        title: 'Model already listed',
        description: `${embeddingSearchQuery} is already in the list`,
        variant: 'destructive',
      });
      return;
    }

    // Add to custom models list
    const newModel: PopularModel = {
      name: embeddingSearchQuery.trim(),
      size: 'Unknown',
      description: 'Custom embedding model from Ollama library',
      installed: false,
    };

    setCustomEmbeddingModels([...customEmbeddingModels, newModel]);
    setEmbeddingSearchQuery('');
  };

  const renderModelCard = (model: PopularModel) => (
    <Card key={model.name} className="border">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="font-medium">{model.name}</h4>
              <a
                href={getOllamaLibraryUrl(model.name)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/80 transition-colors"
                title="View on Ollama Library"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
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

        {/* Search for LLM Models */}
        <div className="flex gap-2">
          <Input
            placeholder="Search Ollama library (e.g., codellama, gemma2)"
            value={llmSearchQuery}
            onChange={(e) => setLlmSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleAddLlmModel();
              }
            }}
            className="flex-1"
          />
          <Button
            variant="secondary"
            size="default"
            onClick={handleAddLlmModel}
            disabled={!llmSearchQuery.trim()}
          >
            <Search className="h-4 w-4 mr-2" />
            Add
          </Button>
        </div>

        <div className="space-y-2">
          {popularModels.llm_models.map((model) => renderModelCard(model))}
          {customLlmModels.map((model) => renderModelCard(model))}
        </div>
      </div>

      {/* Embedding Models Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Embedding Models
        </h3>

        {/* Search for Embedding Models */}
        <div className="flex gap-2">
          <Input
            placeholder="Search Ollama library (e.g., bge-large, snowflake-arctic-embed)"
            value={embeddingSearchQuery}
            onChange={(e) => setEmbeddingSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleAddEmbeddingModel();
              }
            }}
            className="flex-1"
          />
          <Button
            variant="secondary"
            size="default"
            onClick={handleAddEmbeddingModel}
            disabled={!embeddingSearchQuery.trim()}
          >
            <Search className="h-4 w-4 mr-2" />
            Add
          </Button>
        </div>

        <div className="space-y-2">
          {popularModels.embedding_models.map((model) => renderModelCard(model))}
          {customEmbeddingModels.map((model) => renderModelCard(model))}
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
