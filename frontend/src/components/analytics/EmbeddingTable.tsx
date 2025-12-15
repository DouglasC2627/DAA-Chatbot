'use client';

import { useState, useEffect, useMemo } from 'react';
import { Loader2, Download, Search } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { InfoTooltip } from '@/components/ui/info-tooltip';
import analyticsApi from '@/lib/analytics-api';
import type { EmbeddingData } from '@/types/analytics';

interface EmbeddingTableProps {
  projectId: number;
}

export default function EmbeddingTable({ projectId }: EmbeddingTableProps) {
  const [embeddings, setEmbeddings] = useState<EmbeddingData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  useEffect(() => {
    async function fetchEmbeddings() {
      try {
        setLoading(true);
        setError(null);

        const response = await analyticsApi.getEmbeddings(projectId, {
          limit: 500,
          include_text: true,
        });

        setEmbeddings(response.embeddings);
      } catch (err) {
        console.error('Error fetching embeddings:', err);
        setError('Failed to load embeddings data');
      } finally {
        setLoading(false);
      }
    }

    if (projectId) {
      fetchEmbeddings();
    }
  }, [projectId]);

  // Filter embeddings based on search term
  const filteredEmbeddings = useMemo(() => {
    if (!searchTerm) return embeddings;

    const term = searchTerm.toLowerCase();
    return embeddings.filter(
      (emb) =>
        emb.document_name.toLowerCase().includes(term) ||
        emb.text?.toLowerCase().includes(term) ||
        emb.chunk_id.toLowerCase().includes(term)
    );
  }, [embeddings, searchTerm]);

  // Paginate filtered results
  const paginatedEmbeddings = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredEmbeddings.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredEmbeddings, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredEmbeddings.length / itemsPerPage);

  // Calculate embedding norm
  const calculateNorm = (embedding: number[]) => {
    const sum = embedding.reduce((acc, val) => acc + val * val, 0);
    return Math.sqrt(sum);
  };

  // Export to CSV
  const handleExport = () => {
    const headers = ['Chunk ID', 'Document', 'Chunk Index', 'Text Preview', 'Embedding Dimension', 'Embedding Norm'];
    const rows = filteredEmbeddings.map((emb) => [
      emb.chunk_id,
      emb.document_name,
      emb.chunk_index.toString(),
      (emb.text || '').replace(/"/g, '""').substring(0, 200),
      emb.embedding.length.toString(),
      calculateNorm(emb.embedding).toFixed(4),
    ]);

    const csv = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `embeddings_${projectId}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-sm text-destructive bg-destructive/10 p-3 rounded text-center">
            {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Embeddings Data Table</CardTitle>
        <CardDescription>
          Browse all document chunks with their embeddings and metadata
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex gap-2 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by document name, chunk ID, or text..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="pl-9"
            />
          </div>
          <Button variant="outline" onClick={handleExport} disabled={embeddings.length === 0}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>

        {/* Stats */}
        <div className="text-sm text-muted-foreground">
          Showing {paginatedEmbeddings.length} of {filteredEmbeddings.length} chunks
          {searchTerm && ` (filtered from ${embeddings.length} total)`}
        </div>

        {/* Table */}
        <div className="border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3 font-medium">Chunk ID</th>
                  <th className="text-left p-3 font-medium">Document</th>
                  <th className="text-left p-3 font-medium">Index</th>
                  <th className="text-left p-3 font-medium">Text Preview</th>
                  <th className="text-left p-3 font-medium">
                    <div className="flex items-center">
                      Dim
                      <InfoTooltip content="Embedding dimension - the length of the vector representing this chunk. All chunks have the same dimension based on the embedding model used." />
                    </div>
                  </th>
                  <th className="text-left p-3 font-medium">
                    <div className="flex items-center">
                      Norm
                      <InfoTooltip content="Vector norm (magnitude) - calculated as the square root of the sum of squared values in the embedding. It represents the 'length' of the vector in high-dimensional space. Embeddings are typically normalized to have similar norms for better comparison." />
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedEmbeddings.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center p-8 text-muted-foreground">
                      {searchTerm ? 'No chunks match your search' : 'No embeddings found'}
                    </td>
                  </tr>
                ) : (
                  paginatedEmbeddings.map((emb) => (
                    <tr key={emb.chunk_id} className="border-t hover:bg-muted/50">
                      <td className="p-3">
                        <code className="text-xs bg-muted px-2 py-1 rounded">
                          {emb.chunk_id}
                        </code>
                      </td>
                      <td className="p-3">
                        <div className="max-w-xs truncate">{emb.document_name}</div>
                      </td>
                      <td className="p-3">
                        <Badge variant="outline">{emb.chunk_index}</Badge>
                      </td>
                      <td className="p-3">
                        <div className="max-w-md line-clamp-2 text-xs text-muted-foreground">
                          {emb.text || 'No text available'}
                        </div>
                      </td>
                      <td className="p-3 text-muted-foreground">{emb.embedding.length}</td>
                      <td className="p-3 text-muted-foreground">
                        {calculateNorm(emb.embedding).toFixed(3)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
