'use client';

import * as React from 'react';
import { ChunkDisplay, ChunkItem } from '../components/chunk-display';
import { ClaimSubstantiatorStateSummary } from '@/lib/generated-api';
import { BookOpen } from 'lucide-react';
import { TabWithLoadingStates } from './tab-with-loading-states';

interface CitationsTabProps {
  results: ClaimSubstantiatorStateSummary;
  isProcessing?: boolean;
}

export function CitationsTab({ results, isProcessing = false }: CitationsTabProps) {
  return (
    <TabWithLoadingStates
      title="Citations Analysis"
      data={results.chunks}
      isProcessing={isProcessing}
      hasData={(chunks) => chunks?.some((c) => c.hasCitations) || false}
      loadingMessage={{
        title: 'Detecting citations...',
        description: 'Analyzing document for citation patterns',
      }}
      emptyMessage={{
        icon: <BookOpen className="h-12 w-12 text-muted-foreground" />,
        title: 'No citations found',
        description: "This document doesn't contain formal citations or references",
      }}
      skeletonType="list"
      skeletonCount={3}
    >
      {(chunks) => {
        const chunksWithCitations = chunks.filter((chunk) => chunk.hasCitations);
        const totalCitations = chunks.reduce((sum, chunk) => sum + (chunk.citationsCount || 0), 0);
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-900">
                <strong>Summary:</strong> Found {totalCitations} citation{totalCitations !== 1 ? 's' : ''} across{' '}
                {chunksWithCitations.length} chunk{chunksWithCitations.length !== 1 ? 's' : ''}.
              </p>
              <p className="text-xs text-blue-700 mt-2">
                Click on a chunk in the <strong>Document Explorer</strong> tab and expand "Show full analysis results"
                to see detailed citation information.
              </p>
            </div>
            {chunksWithCitations.map((chunk) => (
              <ChunkDisplay key={chunk.chunkIndex} chunkIndex={chunk.chunkIndex}>
                <ChunkItem>
                  <p className="text-sm">
                    <strong>{chunk.citationsCount || 0}</strong> citation{chunk.citationsCount !== 1 ? 's' : ''} found
                    in this chunk
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">Click to view in Document Explorer</p>
                </ChunkItem>
              </ChunkDisplay>
            ))}
          </div>
        );
      }}
    </TabWithLoadingStates>
  );
}
