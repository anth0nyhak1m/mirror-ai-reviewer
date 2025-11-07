import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useChunkDetails } from '@/lib/hooks/use-chunk-details';
import type { ChunkReevaluationResponse, ClaimSubstantiatorStateSummary, DocumentIssue } from '@/lib/generated-api';
import { ChevronDown, ChevronRight, Loader2, X } from 'lucide-react';
import { useState } from 'react';
import { ChunkAnalysisCard } from './chunk-analysis-card';
import { ChunkEvalGenerator } from './chunk-eval-generator';
import { ChunkReevaluateControl } from './chunk-reevaluate-control';
import { ChunkStatusBadge, useShouldShowStatusBadge } from './chunk-status-badge';
import { ClaimAnalysisCard } from './claim-analysis-card';
import { DocumentIssuesList } from './document-issues-list';
import { ErrorsCard } from './errors-card';

export interface ChunkSidebarContentProps {
  results: ClaimSubstantiatorStateSummary;
  chunkIndex: number | null;
  workflowRunId?: string;
  isWorkflowRunning: boolean;
  onSelectIssue: (issue: DocumentIssue) => void;
  onChunkReevaluation: (response: ChunkReevaluationResponse) => void;
  onClearChunkSelection: () => void;
}

export function ChunkSidebarContent({
  results,
  chunkIndex,
  workflowRunId,
  isWorkflowRunning,
  onSelectIssue,
  onChunkReevaluation,
  onClearChunkSelection,
}: ChunkSidebarContentProps) {
  const [showAdvancedAnalysis, setShowAdvancedAnalysis] = useState(false);

  const { data: chunkDetails, isLoading: isLoadingDetails } = useChunkDetails(
    workflowRunId || '',
    chunkIndex,
    showAdvancedAnalysis && !!workflowRunId,
  );

  const chunkErrors = results.errors?.filter((error) => error.chunkIndex === chunkIndex) ?? [];
  const references = results.references ?? [];
  const issues = results.rankedIssues?.filter((issue) => issue.chunkIndex === chunkIndex) ?? [];
  const supportingFiles = results.supportingFiles ?? [];

  const lightweightChunk = results.chunks?.find((chunk) => chunk.chunkIndex === chunkIndex);
  const shouldShowStatusBadge = useShouldShowStatusBadge(isWorkflowRunning);

  const claims = chunkDetails?.claims?.claims ?? [];

  if (!lightweightChunk) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        {shouldShowStatusBadge && chunkDetails && (
          <ChunkStatusBadge chunk={chunkDetails} isWorkflowRunning={isWorkflowRunning} />
        )}

        <Badge variant="secondary" className="gap-1 pl-2.5 pr-1">
          Chunk #{lightweightChunk.chunkIndex}
          <button
            onClick={onClearChunkSelection}
            className="ml-0.5 rounded-sm hover:bg-muted-foreground/20 p-0.5"
            aria-label="Clear chunk selection"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      </div>

      {chunkErrors.length > 0 && <ErrorsCard errors={chunkErrors} />}

      <DocumentIssuesList issues={issues} onSelect={onSelectIssue} />

      {issues.length === 0 && <p className="text-sm text-muted-foreground italic">No issues found in this chunk.</p>}

      <div className="flex items-center gap-2 justify-end">
        <Button variant="outline" size="xs" onClick={() => setShowAdvancedAnalysis(!showAdvancedAnalysis)}>
          {showAdvancedAnalysis ? (
            <>
              <ChevronDown />
              Hide full analysis results
            </>
          ) : (
            <>
              <ChevronRight />
              Show full analysis results
            </>
          )}
        </Button>
      </div>

      {showAdvancedAnalysis && (
        <>
          {isLoadingDetails && (
            <div className="flex items-center justify-center py-8">
              <div className="text-center space-y-3">
                <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto" />
                <p className="text-sm text-muted-foreground">Loading detailed analysis...</p>
              </div>
            </div>
          )}

          {!isLoadingDetails && (
            <>
              {claims.map((claim, index) => (
                <ClaimAnalysisCard
                  key={index}
                  claim={claim}
                  claimCategory={chunkDetails?.claimCategories?.find((c) => c.claimIndex === index)}
                  commonKnowledgeResult={chunkDetails?.claimCommonKnowledgeResults?.find((c) => c.claimIndex === index)}
                  substantiation={chunkDetails?.substantiations?.find((s) => s.claimIndex === index)}
                  citationSuggestion={chunkDetails?.citationSuggestions?.find((c) => c.claimIndex === index)}
                  liveReportsAnalysis={chunkDetails?.liveReportsAnalysis?.find((l) => l.claimIndex === index)}
                  inferenceValidation={chunkDetails?.inferenceValidations?.find((i) => i.claimIndex === index)}
                  claimIndex={index}
                  totalClaims={claims.length}
                  references={references}
                  supportingFiles={supportingFiles}
                  workflowRunId={results.workflowRunId ?? undefined}
                  chunkIndex={chunkIndex ?? undefined}
                />
              ))}

              {chunkDetails && (
                <ChunkAnalysisCard chunk={chunkDetails} references={references} supportingFiles={supportingFiles} />
              )}

              <ChunkReevaluateControl
                chunkIndex={lightweightChunk.chunkIndex}
                originalState={results}
                onReevaluation={onChunkReevaluation}
                sessionId={results.config?.sessionId}
              />

              <ChunkEvalGenerator chunkIndex={lightweightChunk.chunkIndex} originalState={results} />
            </>
          )}
        </>
      )}
    </div>
  );
}
