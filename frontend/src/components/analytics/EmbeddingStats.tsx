'use client';

import { useEffect, useState } from 'react';
import { BarChart3, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import analyticsApi from '@/lib/analytics-api';
import type { EmbeddingStatsResponse } from '@/types/analytics';

interface EmbeddingStatsProps {
  projectId: number;
}

export default function EmbeddingStats({ projectId }: EmbeddingStatsProps) {
  const [stats, setStats] = useState<EmbeddingStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true);
        setError(null);
        const data = await analyticsApi.getEmbeddingStats(projectId);
        setStats(data);
      } catch (err) {
        console.error('Error fetching embedding stats:', err);
        setError('Failed to load statistics');
      } finally {
        setLoading(false);
      }
    }

    if (projectId) {
      fetchStats();
    }
  }, [projectId]);

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Please wait</p>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="md:col-span-2 lg:col-span-4">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground text-center">
              {error || 'No data available. Upload documents to see statistics.'}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Total Chunks */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Chunks</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_chunks.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">Across all documents</p>
        </CardContent>
      </Card>

      {/* Documents */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Documents</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_documents.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">In current project</p>
        </CardContent>
      </Card>

      {/* Embedding Dimension */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Embedding Dimension</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.embedding_dimension}</div>
          <p className="text-xs text-muted-foreground">{stats.embedding_model}</p>
        </CardContent>
      </Card>

      {/* Average Similarity */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Similarity</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(stats.stats.avg_similarity * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">Between chunks</p>
        </CardContent>
      </Card>
    </div>
  );
}
