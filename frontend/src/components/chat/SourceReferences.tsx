'use client';

import { useState } from 'react';
import { SourceReference } from '@/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, ExternalLink, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface SourceReferencesProps {
  sources: SourceReference[];
  compact?: boolean;
  showPreview?: boolean;
}

export default function SourceReferences({
  sources,
  compact = false,
  showPreview = true,
}: SourceReferencesProps) {
  const [selectedSource, setSelectedSource] = useState<SourceReference | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  const handleSourceClick = (source: SourceReference) => {
    if (showPreview) {
      setSelectedSource(source);
      setPreviewOpen(true);
    }
  };

  const handleJumpToDocument = (documentId: number) => {
    // Navigate to document view/details page
    window.open(`/documents/${documentId}`, '_blank');
  };

  const getRelevanceColor = (score: number): string => {
    if (score >= 0.8) return 'bg-green-500/10 text-green-700 dark:text-green-400';
    if (score >= 0.6) return 'bg-blue-500/10 text-blue-700 dark:text-blue-400';
    if (score >= 0.4) return 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400';
    return 'bg-gray-500/10 text-gray-700 dark:text-gray-400';
  };

  const getRelevanceLabel = (score: number): string => {
    if (score >= 0.8) return 'Highly Relevant';
    if (score >= 0.6) return 'Relevant';
    if (score >= 0.4) return 'Somewhat Relevant';
    return 'Low Relevance';
  };

  // Compact view - simple badges
  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        {sources.map((source, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            className="h-auto py-1 px-2 text-xs"
            onClick={() => handleSourceClick(source)}
          >
            <FileText className="h-3 w-3 mr-1" />
            <span className="truncate max-w-[150px]">
              {source.document_name}
              {source.page_number && ` (p.${source.page_number})`}
            </span>
          </Button>
        ))}
      </div>
    );
  }

  // Full view with detailed information
  return (
    <>
      <div className="w-full">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold">Source References ({sources.length})</h4>
        </div>

        <div className="space-y-2">
          {sources.map((source, index) => (
            <Card
              key={index}
              className="cursor-pointer hover:bg-accent/50 transition-colors"
              onClick={() => handleSourceClick(source)}
            >
              <CardContent className="p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="font-medium text-sm truncate">{source.document_name}</span>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      {source.page_number && (
                        <Badge variant="outline" className="text-xs">
                          Page {source.page_number}
                        </Badge>
                      )}
                      {source.chunk_index !== undefined && (
                        <Badge variant="outline" className="text-xs">
                          Chunk {source.chunk_index}
                        </Badge>
                      )}
                      <Badge className={`text-xs ${getRelevanceColor(source.similarity_score)}`}>
                        {getRelevanceLabel(source.similarity_score)} (
                        {(source.similarity_score * 100).toFixed(0)}%)
                      </Badge>
                    </div>

                    {source.content && (
                      <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                        {source.content}
                      </p>
                    )}
                  </div>

                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 flex-shrink-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleJumpToDocument(source.document_id);
                    }}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Source Preview Modal */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Source Preview
            </DialogTitle>
            <DialogDescription>
              View the source content that was used to generate the response
            </DialogDescription>
          </DialogHeader>

          {selectedSource && (
            <ScrollArea className="max-h-[60vh] pr-4">
              <div className="space-y-4">
                {/* Source Metadata */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">{selectedSource.document_name}</CardTitle>
                    <CardDescription className="flex items-center gap-2 flex-wrap">
                      {selectedSource.page_number && (
                        <Badge variant="outline">Page {selectedSource.page_number}</Badge>
                      )}
                      {selectedSource.chunk_index !== undefined && (
                        <Badge variant="outline">Chunk {selectedSource.chunk_index}</Badge>
                      )}
                      {selectedSource.section && (
                        <Badge variant="outline">{selectedSource.section}</Badge>
                      )}
                      <Badge className={getRelevanceColor(selectedSource.similarity_score)}>
                        Relevance: {(selectedSource.similarity_score * 100).toFixed(1)}%
                      </Badge>
                    </CardDescription>
                  </CardHeader>
                </Card>

                {/* Source Content */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Content</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown>{selectedSource.content}</ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleJumpToDocument(selectedSource.document_id)}
                    className="w-full"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open Full Document
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      navigator.clipboard.writeText(selectedSource.content);
                    }}
                    className="w-full"
                  >
                    Copy Content
                  </Button>
                </div>
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
