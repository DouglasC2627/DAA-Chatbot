'use client';

import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { InfoTooltip } from '@/components/ui/info-tooltip';
import analyticsApi from '@/lib/analytics-api';
import type { TestRetrievalResponse } from '@/types/analytics';

interface RetrievalTesterProps {
  projectId: number;
}

export default function RetrievalTester({ projectId }: RetrievalTesterProps) {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<TestRetrievalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTest = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await analyticsApi.testRetrieval(projectId, {
        query: query.trim(),
        top_k: topK,
        return_embeddings: false,
      });
      setResults(data);
    } catch (err) {
      console.error('Error testing retrieval:', err);
      setError('Failed to test query. Make sure you have documents uploaded.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleTest();
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center">
          <CardTitle>Retrieval Testing</CardTitle>
          <InfoTooltip content={
            <div>
              <p className="mb-2"><strong>Retrieval Testing</strong> lets you test how well your RAG system finds relevant chunks for a given query.</p>
              <p className="mb-2">The system converts your query to an embedding and finds the most similar chunks using cosine similarity.</p>
              <p>Higher scores (closer to 100%) indicate better semantic matches between your query and the retrieved chunks.</p>
            </div>
          } />
        </div>
        <CardDescription>
          Test queries to see which chunks are retrieved and their relevance scores
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Query Input */}
        <div className="flex gap-2">
          <Input
            placeholder="Enter your test query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <Button onClick={handleTest} disabled={loading || !query.trim()}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Test
              </>
            )}
          </Button>
        </div>

        {/* Top K Selector */}
        <div className="flex items-center gap-2">
          <div className="flex items-center">
            <label className="text-sm font-medium">Top K:</label>
            <InfoTooltip content="The number of most relevant chunks to retrieve. For example, Top K = 10 means the system will return the 10 chunks with the highest similarity scores to your query. Higher values give more context but may include less relevant results." />
          </div>
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            disabled={loading}
            className="border rounded px-2 py-1 text-sm"
          >
            {[5, 10, 15, 20].map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
          <span className="text-sm text-muted-foreground">results</span>
        </div>

        {/* Error Message */}
        {error && (
          <div className="text-sm text-destructive bg-destructive/10 p-3 rounded">
            {error}
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="space-y-4">
            {/* Stats */}
            <div className="flex gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Results: </span>
                <span className="font-medium">{results.results.length}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Avg Score: </span>
                <span className="font-medium">
                  {(results.stats.avg_score * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Max Score: </span>
                <span className="font-medium">
                  {(results.stats.max_score * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Results List */}
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {results.results.map((result, index) => (
                <div
                  key={result.chunk_id}
                  className="border rounded-lg p-4 space-y-2 hover:bg-muted/50 transition-colors"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">#{index + 1}</Badge>
                        <span className="text-sm font-medium truncate">
                          {result.document_name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          Chunk {result.chunk_index}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Badge
                        variant={result.score > 0.7 ? 'default' : 'secondary'}
                      >
                        {(result.score * 100).toFixed(1)}%
                      </Badge>
                    </div>
                  </div>

                  {/* Text Content */}
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {result.text}
                  </p>

                  {/* Metadata */}
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    <span>Score: {result.score.toFixed(4)}</span>
                    <span>Distance: {result.distance.toFixed(4)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!results && !error && !loading && (
          <div className="text-center py-8 text-muted-foreground">
            <Search className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Enter a query above to test retrieval</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
