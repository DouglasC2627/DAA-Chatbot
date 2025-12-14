'use client';

import { Sparkles, AlertCircle } from 'lucide-react';
import MainLayout from '@/components/layout/MainLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useProjectStore } from '@/stores/projectStore';
import EmbeddingStats from '@/components/analytics/EmbeddingStats';
import RetrievalTester from '@/components/analytics/RetrievalTester';

export default function AnalyticsPage() {
  const currentProjectId = useProjectStore((state) => state.currentProjectId);

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

        {/* Stats Grid */}
        {currentProjectId && (
          <EmbeddingStats projectId={currentProjectId} />
        )}

        {/* Retrieval Tester */}
        {currentProjectId && (
          <RetrievalTester projectId={currentProjectId} />
        )}

        {/* Feature Overview Card */}
        {currentProjectId && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <CardTitle>More Features Coming Soon</CardTitle>
              </div>
              <CardDescription>
                Additional visualization tools being developed
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    📊 2D/3D Scatter Plots
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Visualize embeddings in reduced dimensional space using t-SNE or PCA. See how your documents cluster and relate to each other.
                  </p>
                </div>

                <div className="space-y-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    🔥 Similarity Heatmaps
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Interactive heatmaps showing cosine similarity between documents and chunks. Understand relationships at a glance.
                  </p>
                </div>

                <div className="space-y-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    📋 Data Table View
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Browse all chunks with full text, metadata, and embedding statistics. Search, filter, and export data.
                  </p>
                </div>

                <div className="space-y-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    ✅ Working Now
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    <strong>Embedding Statistics:</strong> View real-time stats above<br />
                    <strong>Retrieval Testing:</strong> Test queries and see results above
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </MainLayout>
  );
}
