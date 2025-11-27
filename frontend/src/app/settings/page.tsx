'use client';

import React, { useState, useEffect } from 'react';
import { Loader2, Github, Settings as SettingsIcon } from 'lucide-react';
import MainLayout from '@/components/layout/MainLayout';
import ModelSelector from '@/components/settings/ModelSelector';
import ModelInstaller from '@/components/settings/ModelInstaller';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { systemApi } from '@/lib/api';
import type { UserSettings, InstalledModels, PopularModel } from '@/types';

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [installedModels, setInstalledModels] = useState<InstalledModels | null>(null);
  const [popularModels, setPopularModels] = useState<{
    llm_models: PopularModel[];
    embedding_models: PopularModel[];
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [settingsData, installedData, popularData] = await Promise.all([
        systemApi.getSettings(),
        systemApi.getInstalledModels(),
        systemApi.getPopularModels(),
      ]);

      setSettings(settingsData);
      setInstalledModels(installedData);
      setPopularModels(popularData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleLLMChange = async (modelName: string) => {
    await systemApi.updateModels({ llm_model: modelName });
    await fetchData();
  };

  const handleEmbeddingChange = async (modelName: string) => {
    await systemApi.updateModels({ embedding_model: modelName });
    await fetchData();
  };

  const handleModelInstalled = async () => {
    // Refresh installed models and popular models after installation
    await fetchData();
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-sm text-muted-foreground">Loading settings...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
            <p className="text-muted-foreground mt-2">
              Configure your chatbot models and preferences
            </p>
          </div>
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <div className="flex items-center gap-2">
            <SettingsIcon className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          </div>
          <p className="text-muted-foreground mt-2">
            Configure your chatbot models and preferences
          </p>
        </div>

        {/* Current Models Card */}
        <Card>
          <CardHeader>
            <CardTitle>Model Configuration</CardTitle>
            <CardDescription>
              Select which models to use for chat and embeddings. Changes take effect immediately.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {settings && installedModels && (
              <>
                <ModelSelector
                  type="llm"
                  label="Language Model"
                  currentModel={settings.default_llm_model}
                  installedModels={installedModels.llm_models}
                  onModelChange={handleLLMChange}
                />

                <ModelSelector
                  type="embedding"
                  label="Embedding Model"
                  currentModel={settings.default_embedding_model}
                  installedModels={installedModels.embedding_models}
                  onModelChange={handleEmbeddingChange}
                />
              </>
            )}
          </CardContent>
        </Card>

        {/* Install Models Card */}
        <Card>
          <CardHeader>
            <CardTitle>Install Popular Models</CardTitle>
            <CardDescription>
              Download recommended models from Ollama library. Installation may take several
              minutes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ModelInstaller popularModels={popularModels} onModelInstalled={handleModelInstalled} />
          </CardContent>
        </Card>

        {/* About Card */}
        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                DAA Chatbot - Local RAG System v0.1.0
              </p>
              <p className="text-sm text-muted-foreground">
                A fully-local, privacy-focused RAG chatbot system. All data processing, storage,
                and inference happens locally using Ollama.
              </p>
              <a
                href="https://github.com/DouglasC2627/DAA-Chatbot"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
              >
                <Github className="h-4 w-4" />
                View on GitHub
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
