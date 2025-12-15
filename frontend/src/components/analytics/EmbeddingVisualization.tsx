'use client';

import { useState } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { InfoTooltip } from '@/components/ui/info-tooltip';
import analyticsApi from '@/lib/analytics-api';
import type { DimReductionResponse, ReductionMethod } from '@/types/analytics';
import ScatterPlot2D from './ScatterPlot2D';
import ScatterPlot3D from './ScatterPlot3D';

interface EmbeddingVisualizationProps {
  projectId: number;
}

export default function EmbeddingVisualization({ projectId }: EmbeddingVisualizationProps) {
  const [method, setMethod] = useState<ReductionMethod>('pca');
  const [dimensions, setDimensions] = useState<2 | 3>(2);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DimReductionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVisualize = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await analyticsApi.getDimensionalityReduction(projectId, {
        method,
        dimensions,
        n_samples: 500,
        perplexity: 30,
        n_neighbors: 15,
      });

      setData(response);
    } catch (err) {
      console.error('Error fetching visualization:', err);
      setError('Failed to generate visualization. Make sure you have documents with embeddings.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center">
          <CardTitle>Embeddings Visualization</CardTitle>
          <InfoTooltip content={
            <div>
              <p className="mb-2"><strong>Dimensionality Reduction</strong> transforms high-dimensional embeddings (e.g., 768 dimensions) into 2D or 3D space for visualization.</p>
              <p>This makes it possible to see patterns, clusters, and relationships between your document chunks that would be impossible to visualize in the original high-dimensional space.</p>
            </div>
          } />
        </div>
        <CardDescription>
          Visualize document embeddings in reduced dimensional space
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex flex-wrap gap-4 items-center">
          {/* Method Selection */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Method:</label>
            <div className="flex gap-1">
              <Button
                variant={method === 'pca' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMethod('pca')}
                disabled={loading}
              >
                PCA
              </Button>
              <Button
                variant={method === 'tsne' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMethod('tsne')}
                disabled={loading}
              >
                t-SNE
              </Button>
              <Button
                variant={method === 'umap' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMethod('umap')}
                disabled={loading}
                title="UMAP requires additional backend setup"
              >
                UMAP
                <Badge variant="secondary" className="ml-1 text-xs">
                  Beta
                </Badge>
              </Button>
            </div>
          </div>

          {/* Dimensions Selection */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Dimensions:</label>
            <div className="flex gap-1">
              <Button
                variant={dimensions === 2 ? 'default' : 'outline'}
                size="sm"
                onClick={() => setDimensions(2)}
                disabled={loading}
              >
                2D
              </Button>
              <Button
                variant={dimensions === 3 ? 'default' : 'outline'}
                size="sm"
                onClick={() => setDimensions(3)}
                disabled={loading}
              >
                3D
              </Button>
            </div>
          </div>

          {/* Visualize Button */}
          <Button onClick={handleVisualize} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Computing...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Visualize
              </>
            )}
          </Button>

          {/* Info */}
          {data && (
            <span className="text-sm text-muted-foreground">
              {data.total_points} points • {data.method.toUpperCase()}
            </span>
          )}
        </div>

        {/* Method Description */}
        <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded">
          {method === 'pca' && (
            <p>
              <strong>PCA (Principal Component Analysis):</strong> Fast linear dimensionality reduction.
              Good for initial exploration and understanding overall structure.
            </p>
          )}
          {method === 'tsne' && (
            <p>
              <strong>t-SNE:</strong> Non-linear reduction that preserves local structure.
              Great for identifying clusters but can take longer to compute.
            </p>
          )}
          {method === 'umap' && (
            <p>
              <strong>UMAP:</strong> Fast non-linear reduction preserving both local and global structure.
              Requires additional backend setup (umap-learn package).
            </p>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="text-sm text-destructive bg-destructive/10 p-3 rounded">
            {error}
          </div>
        )}

        {/* Visualization */}
        {data && !loading && (
          <div className="border rounded-lg p-4">
            {dimensions === 2 ? (
              <ScatterPlot2D data={data} />
            ) : (
              <ScatterPlot3D data={data} />
            )}
          </div>
        )}

        {/* Empty State */}
        {!data && !loading && !error && (
          <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
            <RefreshCw className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium">Click "Visualize" to generate embeddings visualization</p>
            <p className="text-sm mt-1">
              Select your preferred method and dimensions, then click the button above
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
