'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Download, Check, Loader2, ExternalLink, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
  const [llmSearchResults, setLlmSearchResults] = useState<PopularModel[]>([]);
  const [embeddingSearchResults, setEmbeddingSearchResults] = useState<PopularModel[]>([]);
  const [showLlmResults, setShowLlmResults] = useState(false);
  const [showEmbeddingResults, setShowEmbeddingResults] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [confirmModel, setConfirmModel] = useState<PopularModel | null>(null);
  const llmSearchRef = useRef<HTMLDivElement>(null);
  const embeddingSearchRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const getOllamaLibraryUrl = (modelName: string): string => {
    return `https://ollama.com/library/${modelName.split(':')[0]}`;
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (llmSearchRef.current && !llmSearchRef.current.contains(event.target as Node)) {
        setShowLlmResults(false);
      }
      if (embeddingSearchRef.current && !embeddingSearchRef.current.contains(event.target as Node)) {
        setShowEmbeddingResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = async (query: string, type: 'llm' | 'embedding') => {
    if (!query.trim() || query.length < 2) {
      if (type === 'llm') {
        setLlmSearchResults([]);
        setShowLlmResults(false);
      } else {
        setEmbeddingSearchResults([]);
        setShowEmbeddingResults(false);
      }
      return;
    }

    setIsSearching(true);

    try {
      const results = await systemApi.searchModels(query, type);

      if (type === 'llm') {
        setLlmSearchResults(results);
        setShowLlmResults(true);
      } else {
        setEmbeddingSearchResults(results);
        setShowEmbeddingResults(true);
      }
    } catch (error) {
      toast({
        title: 'Search failed',
        description: error instanceof Error ? error.message : 'Failed to search models',
        variant: 'destructive',
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectModel = (model: PopularModel) => {
    setConfirmModel(model);
    setShowLlmResults(false);
    setShowEmbeddingResults(false);
  };

  const handleManualAdd = (modelName: string, type: 'llm' | 'embedding') => {
    // Create a custom model entry for manual installation
    const customModel: PopularModel = {
      name: modelName.trim(),
      size: 'Unknown',
      description: `Custom ${type === 'llm' ? 'language' : 'embedding'} model from Ollama library`,
      installed: false,
    };

    setConfirmModel(customModel);
    setShowLlmResults(false);
    setShowEmbeddingResults(false);
  };

  const handleConfirmInstall = async () => {
    if (!confirmModel) return;

    setInstallingModel(confirmModel.name);
    setConfirmModel(null);

    try {
      await systemApi.pullModel(confirmModel.name);

      toast({
        title: 'Model installed',
        description: `Successfully installed ${confirmModel.name}`,
      });

      // Refresh installed models list
      onModelInstalled();

      // Clear search
      setLlmSearchQuery('');
      setEmbeddingSearchQuery('');
      setLlmSearchResults([]);
      setEmbeddingSearchResults([]);
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

  const renderSearchResult = (model: PopularModel, onClick: () => void) => (
    <div
      key={model.name}
      className="flex items-start justify-between gap-3 p-3 hover:bg-accent rounded-md cursor-pointer transition-colors"
      onClick={onClick}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className="font-medium text-sm">{model.name}</p>
          {model.installed && (
            <Badge variant="secondary" className="text-xs h-5">
              Installed
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground line-clamp-2">{model.description}</p>
        <p className="text-xs text-muted-foreground mt-1">Size: {model.size}</p>
      </div>
      <ExternalLink className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-1" />
    </div>
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
        <div className="relative" ref={llmSearchRef}>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search Ollama library (e.g., codellama, gemma2)"
                value={llmSearchQuery}
                onChange={(e) => {
                  setLlmSearchQuery(e.target.value);
                  handleSearch(e.target.value, 'llm');
                }}
                onFocus={() => {
                  if (llmSearchResults.length > 0) {
                    setShowLlmResults(true);
                  }
                }}
                className="pl-9"
              />
              {llmSearchQuery && (
                <button
                  onClick={() => {
                    setLlmSearchQuery('');
                    setLlmSearchResults([]);
                    setShowLlmResults(false);
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Search Results Dropdown */}
          {showLlmResults && llmSearchResults.length > 0 && (
            <Card className="absolute z-50 w-full mt-2 max-h-80 overflow-y-auto shadow-lg">
              <CardContent className="p-2">
                <div className="space-y-1">
                  {llmSearchResults.map((model) =>
                    renderSearchResult(model, () => handleSelectModel(model))
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {showLlmResults && llmSearchResults.length === 0 && llmSearchQuery.length >= 2 && !isSearching && (
            <Card className="absolute z-50 w-full mt-2 shadow-lg">
              <CardContent className="p-4 space-y-3">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground mb-1">
                    No models found for <span className="font-medium">"{llmSearchQuery}"</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Model not in our curated list? You can add it manually.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => handleManualAdd(llmSearchQuery, 'llm')}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Add "{llmSearchQuery}" manually
                </Button>
                <p className="text-xs text-muted-foreground text-center">
                  This will attempt to pull the model from Ollama's library
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-2">
          {popularModels.llm_models.map((model) => renderModelCard(model))}
        </div>
      </div>

      {/* Embedding Models Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Embedding Models
        </h3>

        {/* Search for Embedding Models */}
        <div className="relative" ref={embeddingSearchRef}>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search Ollama library (e.g., bge-large, snowflake-arctic-embed)"
                value={embeddingSearchQuery}
                onChange={(e) => {
                  setEmbeddingSearchQuery(e.target.value);
                  handleSearch(e.target.value, 'embedding');
                }}
                onFocus={() => {
                  if (embeddingSearchResults.length > 0) {
                    setShowEmbeddingResults(true);
                  }
                }}
                className="pl-9"
              />
              {embeddingSearchQuery && (
                <button
                  onClick={() => {
                    setEmbeddingSearchQuery('');
                    setEmbeddingSearchResults([]);
                    setShowEmbeddingResults(false);
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Search Results Dropdown */}
          {showEmbeddingResults && embeddingSearchResults.length > 0 && (
            <Card className="absolute z-50 w-full mt-2 max-h-80 overflow-y-auto shadow-lg">
              <CardContent className="p-2">
                <div className="space-y-1">
                  {embeddingSearchResults.map((model) =>
                    renderSearchResult(model, () => handleSelectModel(model))
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {showEmbeddingResults && embeddingSearchResults.length === 0 && embeddingSearchQuery.length >= 2 && !isSearching && (
            <Card className="absolute z-50 w-full mt-2 shadow-lg">
              <CardContent className="p-4 space-y-3">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground mb-1">
                    No models found for <span className="font-medium">"{embeddingSearchQuery}"</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Model not in our curated list? You can add it manually.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => handleManualAdd(embeddingSearchQuery, 'embedding')}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Add "{embeddingSearchQuery}" manually
                </Button>
                <p className="text-xs text-muted-foreground text-center">
                  This will attempt to pull the model from Ollama's library
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-2">
          {popularModels.embedding_models.map((model) => renderModelCard(model))}
        </div>
      </div>

      {/* Installation Progress */}
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

      {/* Confirmation Dialog */}
      <Dialog open={!!confirmModel} onOpenChange={(open) => !open && setConfirmModel(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Install Model: {confirmModel?.name}</DialogTitle>
            <DialogDescription className="space-y-3 pt-2">
              <div>
                <p className="text-sm">{confirmModel?.description}</p>
                <p className="text-sm text-muted-foreground mt-2">
                  <span className="font-medium">Size:</span> {confirmModel?.size}
                </p>
              </div>

              {/* Warning for manually added models */}
              {confirmModel && confirmModel.size === 'Unknown' && (
                <div className="bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800 rounded-md p-3">
                  <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100 mb-1">
                    ⚠️ Manual Installation
                  </p>
                  <p className="text-xs text-yellow-800 dark:text-yellow-200">
                    This model is not in our curated list. We'll attempt to pull it from Ollama's library.
                    If the model doesn't exist, the installation will fail.
                  </p>
                </div>
              )}

              {confirmModel?.installed && (
                <div className="bg-muted/50 border rounded-md p-3">
                  <p className="text-sm font-medium flex items-center gap-2">
                    <Check className="h-4 w-4" />
                    This model is already installed
                  </p>
                </div>
              )}
              <a
                href={confirmModel ? getOllamaLibraryUrl(confirmModel.name) : '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
              >
                <ExternalLink className="h-4 w-4" />
                View on Ollama Library
              </a>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmModel(null)}>
              Cancel
            </Button>
            {!confirmModel?.installed && (
              <Button onClick={handleConfirmInstall}>
                <Download className="h-4 w-4 mr-2" />
                Install Model
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
