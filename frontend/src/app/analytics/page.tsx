'use client';

import { BarChart3, Sparkles } from 'lucide-react';
import MainLayout from '@/components/layout/MainLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function AnalyticsPage() {
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

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Chunks
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">
                Across all documents
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Documents
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">
                In current project
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Embedding Dimension
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">
                Vector size
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Avg Similarity
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">
                Between chunks
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Feature Overview Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <CardTitle>Embeddings Analytics Dashboard</CardTitle>
            </div>
            <CardDescription>
              Powerful visualization and analysis tools for your document embeddings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Feature List */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    📊 2D/3D Scatter Plots
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Visualize embeddings in reduced dimensional space using t-SNE, UMAP, or PCA. See how your documents cluster and relate to each other.
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
                    🔍 Retrieval Testing
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Test queries in real-time to see which chunks are retrieved and their relevance scores. Perfect for RAG optimization.
                  </p>
                </div>
              </div>

              {/* Status */}
              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground">
                  <strong>Status:</strong> Backend API is ready and functional. Frontend visualizations are under development.
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  <strong>Available:</strong> PCA and t-SNE dimensionality reduction (UMAP requires additional setup)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
