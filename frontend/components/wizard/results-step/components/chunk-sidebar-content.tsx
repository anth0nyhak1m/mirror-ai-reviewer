import { Badge } from '@/components/ui/badge';
import { ChunkReevaluationResponse, ClaimSubstantiatorStateOutput, DocumentIssue } from '@/lib/generated-api';
import { X } from 'lucide-react';
import { ChunkAnalysisCard } from './chunk-analysis-card';
import { ChunkEvalGenerator } from './chunk-eval-generator';
import { ChunkReevaluateControl } from './chunk-reevaluate-control';
import { ChunkStatusBadge, useShouldShowStatusBadge } from './chunk-status-badge';
import { ClaimAnalysisCard } from './claim-analysis-card';
import { DocumentIssuesList } from './document-issues-list';
import { ErrorsCard } from './errors-card';

export interface ChunkSidebarContentProps {
  results: ClaimSubstantiatorStateOutput;
  chunkIndex: number | null;
  isWorkflowRunning: boolean;
  onSelectIssue: (issue: DocumentIssue) => void;
  onChunkReevaluation: (response: ChunkReevaluationResponse) => void;
  onClearChunkSelection: () => void;
}

export function ChunkSidebarContent({
  results,
  chunkIndex,
  isWorkflowRunning,
  onSelectIssue,
  onChunkReevaluation,
  onClearChunkSelection,
}: ChunkSidebarContentProps) {
  const chunkErrors = results.errors?.filter((error) => error.chunkIndex === chunkIndex) || [];
  const references = results.references || [];
  const chunk = results.chunks?.find((chunk) => chunk.chunkIndex === chunkIndex);
  const claims = chunk?.claims?.claims || [];
  const claimCommonKnowledgeResults = chunk?.claimCommonKnowledgeResults || [];
  const substantiations = chunk?.substantiations || [];
  const supportingFiles = results.supportingFiles || [];
  const shouldShowStatusBadge = useShouldShowStatusBadge(isWorkflowRunning);
  const citationSuggestions = chunk?.citationSuggestions || [];
  const liveReportsAnalysis = chunk?.liveReportsAnalysis || [];
  const claimCategories = chunk?.claimCategories || [];
  const issues = results.rankedIssues?.filter((issue) => issue.chunkIndex === chunkIndex) || [];

  if (!chunk) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        {shouldShowStatusBadge && <ChunkStatusBadge chunk={chunk} isWorkflowRunning={isWorkflowRunning} />}

        <Badge variant="secondary" className="gap-1 pl-2.5 pr-1">
          Chunk #{chunk.chunkIndex}
          <button
            onClick={onClearChunkSelection}
            className="ml-0.5 rounded-sm hover:bg-muted-foreground/20 p-0.5 cursor-pointer"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      </div>

      {chunkErrors.length > 0 && <ErrorsCard errors={chunkErrors} />}

      <div className="space-y-2">
        <DocumentIssuesList issues={issues} onSelect={onSelectIssue} />

        {claims.map((claim, index) => (
          <ClaimAnalysisCard
            key={index}
            claim={claim}
            claimCategory={claimCategories.find((c) => c.claimIndex === index)}
            commonKnowledgeResult={claimCommonKnowledgeResults.find((c) => c.claimIndex === index)}
            substantiation={substantiations.find((s) => s.claimIndex === index)}
            citationSuggestion={citationSuggestions.find((c) => c.claimIndex === index)}
            liveReportsAnalysis={liveReportsAnalysis.find((l) => l.claimIndex === index)}
            claimIndex={index}
            totalClaims={claims.length}
            references={references}
            supportingFiles={results.supportingFiles || []}
            workflowRunId={results.workflowRunId ?? undefined}
            chunkIndex={chunkIndex ?? undefined}
          />
        ))}
      </div>

      <ChunkAnalysisCard chunk={chunk} references={references} supportingFiles={supportingFiles} />

      <ChunkReevaluateControl
        chunkIndex={chunk.chunkIndex}
        originalState={results}
        onReevaluation={onChunkReevaluation}
        sessionId={results.config.sessionId}
      />

      <ChunkEvalGenerator chunkIndex={chunk.chunkIndex} originalState={results} />
    </div>
  );
}
