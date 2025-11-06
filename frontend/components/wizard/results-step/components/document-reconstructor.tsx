import { Markdown } from '@/components/markdown';
import type { ClaimSubstantiatorStateOutput, DocumentChunkOutput } from '@/lib/generated-api';
import { getSeverity } from '@/lib/severity';
import { cn } from '@/lib/utils';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useEffect, useMemo, useRef } from 'react';
import rehypeRaw from 'rehype-raw';

interface DocumentReconstructorProps {
  results: ClaimSubstantiatorStateOutput;
  selectedChunkIndex: number | null;
  onChunkSelect: (chunkIndex: number | null) => void;
}

export function DocumentReconstructor({ results, selectedChunkIndex, onChunkSelect }: DocumentReconstructorProps) {
  const parentRef = useRef<HTMLDivElement>(null);
  const chunks = results.chunks || [];

  // Group chunks by paragraph
  const chunksGroupedByParagraphIndex = useMemo(() => {
    return chunks.reduce(
      (acc, chunk) => {
        acc[chunk.paragraphIndex] = acc[chunk.paragraphIndex] || [];
        acc[chunk.paragraphIndex].push(chunk);
        return acc;
      },
      {} as Record<number, DocumentChunkOutput[]>,
    );
  }, [chunks]);

  // Create ordered array of paragraph entries for virtual list
  const paragraphEntries = useMemo(() => {
    return Object.entries(chunksGroupedByParagraphIndex).sort(([aIndex], [bIndex]) => Number(aIndex) - Number(bIndex));
  }, [chunksGroupedByParagraphIndex]);

  // Calculate overscan based on viewport height for better UX
  // More items will be rendered to fill the viewport + buffer
  const estimatedParagraphHeight = 150;
  const viewportBasedOverscan = useMemo(() => {
    if (typeof window !== 'undefined') {
      const viewportHeight = window.innerHeight;
      // Render enough to fill 2x viewport (1x above + 1x below visible area)
      return Math.ceil(viewportHeight / estimatedParagraphHeight);
    }
    return 10; // Default fallback
  }, []);

  // Create virtualizer for paragraphs
  const rowVirtualizer = useVirtualizer({
    count: paragraphEntries.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimatedParagraphHeight,
    overscan: viewportBasedOverscan,
  });

  // Scroll to selected chunk when selection changes
  useEffect(() => {
    if (selectedChunkIndex !== null) {
      // Find which paragraph contains the selected chunk
      const chunk = chunks.find((c) => c.chunkIndex === selectedChunkIndex);
      if (chunk) {
        const paragraphRowIndex = paragraphEntries.findIndex(([pIndex]) => Number(pIndex) === chunk.paragraphIndex);
        if (paragraphRowIndex !== -1) {
          rowVirtualizer.scrollToIndex(paragraphRowIndex, {
            align: 'center',
            behavior: 'smooth',
          });
        }
      }
    }
  }, [selectedChunkIndex, chunks, paragraphEntries, rowVirtualizer]);

  return (
    <div ref={parentRef} className="h-full overflow-y-auto">
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
          paddingTop: '1rem',
          paddingBottom: '4rem',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const [paragraphIndex, paragraphChunks] = paragraphEntries[virtualRow.index];

          return (
            <div
              key={virtualRow.key}
              data-index={virtualRow.index}
              ref={rowVirtualizer.measureElement}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <div className="pb-2">
                <DocumentReconstructorChunkGroup
                  chunks={paragraphChunks}
                  results={results}
                  selectedChunkIndex={selectedChunkIndex}
                  onChunkSelect={onChunkSelect}
                />
              </div>
            </div>
          );
        })}
      </div>
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
