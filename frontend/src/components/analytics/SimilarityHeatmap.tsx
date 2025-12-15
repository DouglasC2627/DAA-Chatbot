'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Loader2, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { InfoTooltip } from '@/components/ui/info-tooltip';
import analyticsApi from '@/lib/analytics-api';
import type { SimilarityMatrixResponse } from '@/types/analytics';

// Dynamically import Plot to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface SimilarityHeatmapProps {
  projectId: number;
  documents?: Array<{ id: number; filename: string }>;
}

export default function SimilarityHeatmap({ projectId, documents = [] }: SimilarityHeatmapProps) {
  const [scope, setScope] = useState<'document' | 'chunk'>('document');
  const [selectedDocs, setSelectedDocs] = useState<number[]>([]);
  const [maxItems, setMaxItems] = useState(20);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SimilarityMatrixResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await analyticsApi.getSimilarityMatrix(projectId, {
        scope,
        document_ids: selectedDocs.length > 0 ? selectedDocs : undefined,
        max_items: maxItems,
      });

      setData(response);
    } catch (err) {
      console.error('Error fetching similarity matrix:', err);
      setError('Failed to generate heatmap. Make sure you have documents with embeddings.');
    } finally {
      setLoading(false);
    }
  };

  const toggleDocument = (docId: number) => {
    setSelectedDocs((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center">
          <CardTitle>Similarity Heatmap</CardTitle>
          <InfoTooltip content="Cosine similarity measures how similar two text chunks are based on their embeddings, ranging from 0 (completely different) to 1 (identical). The heatmap visualizes this similarity between all pairs of documents or chunks, with warmer colors indicating higher similarity." />
        </div>
        <CardDescription>
          Visualize cosine similarity between documents or chunks
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="space-y-4">
          {/* Scope Selection */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Scope:</label>
            <div className="flex gap-1">
              <Button
                variant={scope === 'document' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setScope('document')}
                disabled={loading}
              >
                Document Level
              </Button>
              <Button
                variant={scope === 'chunk' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setScope('chunk')}
                disabled={loading}
              >
                Chunk Level
              </Button>
            </div>
          </div>

          {/* Max Items Selection */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Max Items:</label>
            <select
              value={maxItems}
              onChange={(e) => setMaxItems(Number(e.target.value))}
              disabled={loading}
              className="border rounded px-3 py-1 text-sm"
            >
              {[10, 20, 30, 50].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
            <span className="text-xs text-muted-foreground">
              (Smaller = faster computation)
            </span>
          </div>

          {/* Document Selection for Chunk Level */}
          {scope === 'chunk' && documents.length > 0 && (
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Select Documents (optional, max 5 for performance):
              </label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto border rounded p-2">
                {documents.slice(0, 10).map((doc) => (
                  <Button
                    key={doc.id}
                    variant={selectedDocs.includes(doc.id) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => toggleDocument(doc.id)}
                    disabled={
                      loading ||
                      (!selectedDocs.includes(doc.id) && selectedDocs.length >= 5)
                    }
                  >
                    {doc.filename}
                  </Button>
                ))}
              </div>
              {selectedDocs.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedDocs([])}
                  disabled={loading}
                >
                  Clear Selection
                </Button>
              )}
            </div>
          )}

          {/* Generate Button */}
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Computing...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Generate Heatmap
              </>
            )}
          </Button>
        </div>

        {/* Description */}
        <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded">
          {scope === 'document' ? (
            <p>
              <strong>Document Level:</strong> Shows average similarity between entire documents.
              Each cell shows how similar two documents are based on their content.
            </p>
          ) : (
            <p>
              <strong>Chunk Level:</strong> Shows similarity between individual chunks.
              Useful for finding specific sections that are semantically related.
            </p>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="text-sm text-destructive bg-destructive/10 p-3 rounded">
            {error}
          </div>
        )}

        {/* Heatmap */}
        {data && !loading && (
          <div className="border rounded-lg p-4">
            <Plot
              data={[
                {
                  type: 'heatmap',
                  z: data.matrix,
                  x: data.items.map((item) => item.label),
                  y: data.items.map((item) => item.label),
                  colorscale: 'RdYlGn',
                  hovertemplate:
                    '<b>%{y}</b> vs <b>%{x}</b><br>' +
                    'Similarity: %{z:.3f}<br>' +
                    '<extra></extra>',
                  colorbar: {
                    title: 'Similarity',
                    titleside: 'right',
                  },
                },
              ]}
              layout={{
                autosize: true,
                height: Math.min(600, data.items.length * 30 + 100),
                xaxis: {
                  tickangle: -45,
                  side: 'bottom',
                },
                yaxis: {
                  autorange: 'reversed',
                },
                margin: {
                  l: 150,
                  r: 50,
                  b: 150,
                  t: 50,
                },
              }}
              config={{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
              }}
              style={{ width: '100%' }}
            />

            {/* Stats */}
            <div className="mt-4 text-sm text-muted-foreground text-center">
              {data.items.length}x{data.items.length} similarity matrix •
              Scope: {data.scope}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!data && !loading && !error && (
          <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
            <RefreshCw className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium">Click "Generate Heatmap" to visualize similarity</p>
            <p className="text-sm mt-1">
              Select your preferences above, then click the button
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
