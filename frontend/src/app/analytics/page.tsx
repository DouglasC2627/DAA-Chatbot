'use client';

import { useState } from 'react';
import { AlertCircle, BarChart3, Sparkles, Grid3X3, Table, Search } from 'lucide-react';
import MainLayout from '@/components/layout/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useProjectStore } from '@/stores/projectStore';
import EmbeddingStats from '@/components/analytics/EmbeddingStats';
import RetrievalTester from '@/components/analytics/RetrievalTester';
import EmbeddingVisualization from '@/components/analytics/EmbeddingVisualization';
import SimilarityHeatmap from '@/components/analytics/SimilarityHeatmap';
import EmbeddingTable from '@/components/analytics/EmbeddingTable';

type TabType = 'overview' | 'visualization' | 'heatmap' | 'table' | 'retrieval';

export default function AnalyticsPage() {
  const currentProjectId = useProjectStore((state) => state.currentProjectId);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: BarChart3 },
    { id: 'visualization' as TabType, label: 'Visualization', icon: Sparkles },
    { id: 'heatmap' as TabType, label: 'Heatmap', icon: Grid3X3 },
    { id: 'table' as TabType, label: 'Table', icon: Table },
    { id: 'retrieval' as TabType, label: 'Retrieval', icon: Search },
  ];

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Header Section */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Embeddings Analytics</h1>
          <p className="text-muted-foreground mt-2">
            Visualize and analyze document embeddings for better understanding of your knowledge base
          </p>
        </div>

        {/* No Project Selected Warning */}
        {!currentProjectId && (
          <Card className="border-yellow-500/50 bg-yellow-500/10">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div>
                  <p className="font-medium">No Project Selected</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Please select a project from the sidebar to view analytics.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs Navigation */}
        {currentProjectId && (
          <div className="border-b">
            <div className="flex gap-2 overflow-x-auto pb-px">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <Button
                    key={tab.id}
                    variant={activeTab === tab.id ? 'default' : 'ghost'}
                    onClick={() => setActiveTab(tab.id)}
                    className="gap-2"
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </Button>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab Content */}
        {currentProjectId && (
          <div>
            {activeTab === 'overview' && (
              <div className="space-y-8">
                <EmbeddingStats projectId={currentProjectId} />
              </div>
            )}

            {activeTab === 'visualization' && (
              <EmbeddingVisualization projectId={currentProjectId} />
            )}

            {activeTab === 'heatmap' && (
              <SimilarityHeatmap projectId={currentProjectId} />
            )}

            {activeTab === 'table' && (
              <EmbeddingTable projectId={currentProjectId} />
            )}

            {activeTab === 'retrieval' && (
              <RetrievalTester projectId={currentProjectId} />
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
