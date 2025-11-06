'use client';

import { ClaimSubstantiatorStateSummary, AddendumSeverity, AddendumItem } from '@/lib/generated-api';
import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';
import { TabWithLoadingStates } from '../tab-with-loading-states';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { AddendumFilters, AddendumFilterState, filterAddendumItems } from './addendum-filters';

interface LiveReportsTabProps {
  results: ClaimSubstantiatorStateSummary;
  isProcessing?: boolean;
}

const severityColorMap: Record<
  AddendumSeverity,
  {
    badgeClassName: string;
  }
> = {
  [AddendumSeverity.Low]: {
    badgeClassName: 'bg-blue-500 text-white',
  },
  [AddendumSeverity.Medium]: {
    badgeClassName: 'bg-yellow-500 text-white',
  },
  [AddendumSeverity.High]: {
    badgeClassName: 'bg-red-500 text-white',
  },
};

function AddendumItemCard({ item }: { item: AddendumItem }) {
  const { badgeClassName } = severityColorMap[item.severity];

  return (
    <Card className="mb-4">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Claim Update</CardTitle>
          <Badge variant="secondary" className={cn(badgeClassName)}>
            {item.severity.charAt(0).toUpperCase() + item.severity.slice(1)}
          </Badge>
        </div>
        <CardDescription>
          Chunk {item.chunkIndex} · Claim {item.claimIndex + 1}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="text-sm font-medium mb-2">Original Claim:</h4>
          <p className="text-sm text-muted-foreground">{item.originalClaim}</p>
        </div>
        <div>
          <h4 className="text-sm font-medium mb-2">Rewritten Claim:</h4>
          <p className="text-sm">{item.rewrittenClaim}</p>
        </div>
        <div>
          <h4 className="text-sm font-medium mb-2">Recommended Action:</h4>
          <p className="text-sm">{item.actionSummary}</p>
        </div>
        <div>
          <h4 className="text-sm font-medium mb-2">Rationale:</h4>
          <p className="text-sm text-muted-foreground">{item.rationale}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Badge variant="outline">Category: {item.claimCategory}</Badge>
          <Badge variant="outline">Alignment: {item.evidenceAlignment}</Badge>
          <Badge variant="outline">Action: {item.recommendedAction}</Badge>
          <Badge variant="outline">Confidence: {item.confidence}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}

export function LiveReportsTab({ results, isProcessing = false }: LiveReportsTabProps) {
  const shouldShowLoading = isProcessing && results.config.runLiveReports === true;
  const [filters, setFilters] = React.useState<AddendumFilterState>({
    severity: 'all',
    recommendedAction: 'all',
    evidenceAlignment: 'all',
  });

  return (
    <TabWithLoadingStates
      title="Live Reports"
      data={results.addendum}
      isProcessing={shouldShowLoading}
      hasData={(addendum) => !!addendum}
      loadingMessage={{
        title: 'Generating live reports...',
        description: 'Analyzing claims and generating addendum updates',
      }}
      emptyMessage={{
        icon: <AlertCircle className="h-12 w-12 text-muted-foreground" />,
        title: 'No live reports available',
        description: 'The live reports agent was not enabled for this analysis',
      }}
      emptyStateChildren={
        <div className="text-sm text-muted-foreground text-left max-w-md">
          <p className="mb-2">This may be because:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>The live reports option was not selected during upload</li>
            <li>An error occurred during the live reports process</li>
          </ul>
        </div>
      }
      skeletonType="paragraphs"
      skeletonCount={6}
    >
      {(addendum) => {
        if (!addendum) {
          return null;
        }

        // Collect all items from all sections
        const allItems: AddendumItem[] = [
          ...(addendum.sections.background || []),
          ...(addendum.sections.methodology || []),
          ...(addendum.sections.results || []),
          ...(addendum.sections.interpretation || []),
        ];

        // Filter items
        const filteredItems = filterAddendumItems(allItems, filters);

        // Group filtered items back by section for display
        const getSectionItems = (sectionItems: AddendumItem[]): AddendumItem[] => {
          return filteredItems.filter((item) =>
            sectionItems.some(
              (sectionItem) => sectionItem.chunkIndex === item.chunkIndex && sectionItem.claimIndex === item.claimIndex,
            ),
          );
        };

        const sections = [
          {
            name: 'Background',
            items: getSectionItems(addendum.sections.background || []),
          },
          {
            name: 'Methodology',
            items: getSectionItems(addendum.sections.methodology || []),
          },
          {
            name: 'Results',
            items: getSectionItems(addendum.sections.results || []),
          },
          {
            name: 'Interpretation',
            items: getSectionItems(addendum.sections.interpretation || []),
          },
        ];

        const hasAnyItems = allItems.length > 0;
        const hasFilteredItems = filteredItems.length > 0;

        return (
          <div className="space-y-6">
            {addendum.summary && (
              <Card className="bg-blue-50/50 border-blue-200">
                <CardHeader>
                  <CardTitle className="text-base">Executive Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed">{addendum.summary}</p>
                </CardContent>
              </Card>
            )}

            {hasAnyItems && (
              <AddendumFilters
                filters={filters}
                onFiltersChange={setFilters}
                totalCount={allItems.length}
                filteredCount={filteredItems.length}
              />
            )}

            {hasFilteredItems ? (
              <div className="space-y-6">
                {sections.map(
                  (section) =>
                    section.items.length > 0 && (
                      <div key={section.name} className="space-y-2">
                        <h3 className="text-lg font-semibold">{section.name}</h3>
                        {section.items.map((item, index) => (
                          <AddendumItemCard key={`${item.chunkIndex}-${item.claimIndex}-${index}`} item={item} />
                        ))}
                      </div>
                    ),
                )}
              </div>
            ) : hasAnyItems ? (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <div className="text-center space-y-2">
                    <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto" />
                    <p className="text-sm text-muted-foreground">No items match the selected filters</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <div className="text-center space-y-2">
                    <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto" />
                    <p className="text-sm text-muted-foreground">No addendum items available</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        );
      }}
    </TabWithLoadingStates>
  );
}
