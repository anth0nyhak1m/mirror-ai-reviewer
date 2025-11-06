import { Markdown } from '@/components/markdown';
import { ClaimSubstantiatorStateOutput, DocumentChunkOutput } from '@/lib/generated-api';
import { getSeverity } from '@/lib/severity';
import { cn } from '@/lib/utils';
import { useEffect, useMemo, useRef } from 'react';
import rehypeRaw from 'rehype-raw';

interface DocumentReconstructorProps {
  results: ClaimSubstantiatorStateOutput;
  selectedChunkIndex: number | null;
  onChunkSelect: (chunkIndex: number | null) => void;
}

export function DocumentReconstructor({ results, selectedChunkIndex, onChunkSelect }: DocumentReconstructorProps) {
  // Scroll to selected chunk when selection changes
  useEffect(() => {
    if (selectedChunkIndex !== null) {
      const element = document.querySelector(`[data-chunk-index="${selectedChunkIndex}"]`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedChunkIndex]);

  const chunks = useMemo(() => results.chunks || [], [results.chunks]);

  const chunksGroupedByParagraphIndex = useMemo(
    () =>
      chunks.reduce(
        (acc, chunk) => {
          acc[chunk.paragraphIndex] = acc[chunk.paragraphIndex] || [];
          acc[chunk.paragraphIndex].push(chunk);
          return acc;
        },
        {} as Record<number, DocumentChunkOutput[]>,
      ),
    [chunks],
  );

  return (
    <div className="space-y-2">
      {Object.entries(chunksGroupedByParagraphIndex).map(([paragraphIndex, chunks]) => (
        <div key={paragraphIndex} className="space-y-2">
          <DocumentReconstructorChunkGroup
            chunks={chunks}
            results={results}
            selectedChunkIndex={selectedChunkIndex}
            onChunkSelect={onChunkSelect}
          />
        </div>
      ))}
    </div>
  );
}

export function DocumentReconstructorChunkGroup({
  chunks,
  results,
  selectedChunkIndex,
  onChunkSelect,
}: {
  chunks: DocumentChunkOutput[];
  results: ClaimSubstantiatorStateOutput;
  selectedChunkIndex: number | null;
  onChunkSelect: (chunkIndex: number | null) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const combinedContent = useMemo(() => {
    if (chunks.length === 0) {
      return null;
    }

    // Detect block-level syntax from the first chunk
    const firstChunk = chunks[0];
    const blockPrefix = detectBlockSyntax(firstChunk.content);

    // Extract content from all chunks and wrap in spans
    const wrappedChunks = chunks
      .map((chunk) => {
        const content = extractChunkContent(chunk.content, blockPrefix);
        const severity = getSeverity(results, chunk);
        return `<span data-chunk-index="${chunk.chunkIndex}" data-severity="${severity}">${content}</span>`;
      })
      .join(' ');

    // Reconstruct markdown with block-level syntax from first chunk
    return blockPrefix ? `${blockPrefix}${wrappedChunks}` : wrappedChunks;
  }, [chunks, results]);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const targets = containerRef.current.querySelectorAll('[data-chunk-index]');
    targets.forEach((target: Element) => {
      if (selectedChunkIndex !== null) {
        target.setAttribute(
          'data-chunk-selected',
          selectedChunkIndex === parseInt(target.getAttribute('data-chunk-index') || '0') ? 'true' : 'false',
        );
      } else {
        target.removeAttribute('data-chunk-selected');
      }
    });
  }, [selectedChunkIndex]);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const handleClick = (event: Event) => {
      const target = event.target as HTMLElement;
      const chunkIndex = target.getAttribute('data-chunk-index');
      if (chunkIndex && onChunkSelect) {
        onChunkSelect(parseInt(chunkIndex));
      }
    };

    const targets = containerRef.current.querySelectorAll('[data-chunk-index]');
    targets.forEach((target: Element) => {
      target.addEventListener('click', handleClick);
    });
    return () => {
      targets.forEach((target: Element) => {
        target.removeEventListener('click', handleClick);
      });
    };
  }, [combinedContent, onChunkSelect]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "[&_[data-severity='high']]:bg-red-100",
        "[&_[data-severity='medium']]:bg-yellow-100",
        "[&_[data-severity='low']]:bg-blue-100",
        '[&_[data-severity]]:hover:bg-gray-300/50 [&_[data-severity]]:cursor-pointer',
        '[&_[data-chunk-selected="true"]]:shadow-lg',
        '[&_[data-chunk-selected="false"]]:opacity-50',
      )}
    >
      <Markdown rehypePlugins={[rehypeRaw]}>{combinedContent}</Markdown>
    </div>
  );
}

/**
 * Detects block-level markdown syntax from a chunk.
 * Returns the block prefix (e.g., "# ", "- ", "> ") or null for paragraphs.
 */
function detectBlockSyntax(chunk: string): string | null {
  if (!chunk || !chunk.trim()) {
    return null;
  }

  const trimmed = chunk.trimStart();

  // Headings: #, ##, ###, etc. (1-6 # characters followed by space)
  const headingMatch = trimmed.match(/^(#{1,6})\s/);
  if (headingMatch) {
    return headingMatch[0];
  }

  // Unordered lists: -, *, + followed by space
  if (/^[-*+]\s/.test(trimmed)) {
    return trimmed.match(/^[-*+]\s/)?.[0] || null;
  }

  // Ordered lists: digits followed by . and space
  const orderedListMatch = trimmed.match(/^\d+\.\s/);
  if (orderedListMatch) {
    return orderedListMatch[0];
  }

  // Blockquotes: > followed by space
  if (/^>\s/.test(trimmed)) {
    return '> ';
  }

  // Paragraphs: no block-level syntax
  return null;
}

/**
 * Extracts content from a chunk by removing block-level syntax.
 * Preserves inline markdown and returns the content without the block prefix.
 */
function extractChunkContent(chunk: string, blockPrefix: string | null): string {
  if (!chunk) {
    return '';
  }

  if (!blockPrefix) {
    return chunk.trim();
  }

  // Remove the block prefix from the start of the chunk
  const trimmed = chunk.trimStart();
  if (trimmed.startsWith(blockPrefix)) {
    return trimmed.slice(blockPrefix.length).trim();
  }

  // If the prefix doesn't match (shouldn't happen, but handle gracefully)
  return chunk.trim();
}
