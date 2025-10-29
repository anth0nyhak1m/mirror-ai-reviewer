import { Markdown } from '@/components/markdown';
import { ClaimSubstantiatorStateOutput, DocumentChunkOutput } from '@/lib/generated-api';
import { getSeverity, severityColors } from '@/lib/severity';
import { cn } from '@/lib/utils';
import { useEffect } from 'react';

interface DocumentReconstructorProps {
  results: ClaimSubstantiatorStateOutput;
  selectedChunkIndex: number | null;
  onChunkSelect: (chunkIndex: number | null) => void;
}

export function DocumentReconstructor({ results, selectedChunkIndex, onChunkSelect }: DocumentReconstructorProps) {
  // Scroll to selected chunk when selection changes
  useEffect(() => {
    if (selectedChunkIndex !== null) {
      const element = document.getElementById(`chunk-${selectedChunkIndex}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedChunkIndex]);
  const chunks = results.chunks || [];

  const chunksGroupedByParagraphIndex = chunks.reduce(
    (acc, chunk) => {
      acc[chunk.paragraphIndex] = acc[chunk.paragraphIndex] || [];
      acc[chunk.paragraphIndex].push(chunk);
      return acc;
    },
    {} as Record<number, DocumentChunkOutput[]>,
  );

  return (
    <div className="space-y-2">
      {Object.entries(chunksGroupedByParagraphIndex).map(([paragraphIndex, chunks]) => (
        <div key={paragraphIndex} className="space-y-2">
          {chunks.map((chunk) => {
            const severity = getSeverity(results, chunk);
            const isSelected = selectedChunkIndex === chunk.chunkIndex;
            return (
              <div
                key={chunk.chunkIndex}
                id={`chunk-${chunk.chunkIndex}`}
                className={cn(
                  'cursor-pointer rounded relative',
                  !isSelected && 'hover:bg-gray-200/50',
                  selectedChunkIndex && !isSelected && 'opacity-60',
                )}
                onClick={() => onChunkSelect(isSelected ? null : chunk.chunkIndex)}
              >
                {isSelected && (
                  <div className="absolute top-[-0.5rem] bottom-[-0.5rem] left-[-1rem] right-[-0.5rem] rounded-md shadow-lg border" />
                )}
                <Markdown highlight={severityColors[severity]}>{chunk.content}</Markdown>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
