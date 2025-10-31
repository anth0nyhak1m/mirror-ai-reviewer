'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Separator } from '@/components/ui/separator';
import { Filter, X } from 'lucide-react';
import {
  AddendumSeverity,
  EvidenceWeighterRecommendedAction,
  ReferenceAlignmentLevel,
  AddendumItem,
} from '@/lib/generated-api';
import { FilterGroup } from '../literature-review-tab/filter-group';

export interface AddendumFilterState {
  severity: AddendumSeverity | 'all';
  recommendedAction: EvidenceWeighterRecommendedAction | 'all';
  evidenceAlignment: ReferenceAlignmentLevel | 'all';
}

/**
 * Humanize enum values for display
 */
function humanizeLabel(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Create filter options from enum values
 */
function createFilterOptions<T extends string>(
  enumObject: Record<string, T>,
): Array<{ value: T | 'all'; label: string }> {
  return [
    { value: 'all' as const, label: 'All' },
    ...Object.values(enumObject).map((v) => ({
      value: v,
      label: humanizeLabel(v),
    })),
  ];
}

const FILTER_CONFIGS = [
  {
    key: 'severity' as const,
    label: 'Severity',
    options: createFilterOptions(AddendumSeverity),
  },
  {
    key: 'recommendedAction' as const,
    label: 'Recommended Action',
    options: createFilterOptions(EvidenceWeighterRecommendedAction),
  },
  {
    key: 'evidenceAlignment' as const,
    label: 'Evidence Alignment',
    options: createFilterOptions(ReferenceAlignmentLevel),
  },
];

interface AddendumFiltersProps {
  filters: AddendumFilterState;
  onFiltersChange: (filters: AddendumFilterState) => void;
  totalCount: number;
  filteredCount: number;
}

export function AddendumFilters({ filters, onFiltersChange, totalCount, filteredCount }: AddendumFiltersProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const hasActiveFilters =
    filters.severity !== 'all' || filters.recommendedAction !== 'all' || filters.evidenceAlignment !== 'all';

  const handleClearAll = () => {
    onFiltersChange({
      severity: 'all',
      recommendedAction: 'all',
      evidenceAlignment: 'all',
    });
  };

  const getActiveFilterBadges = () => {
    return FILTER_CONFIGS.filter(({ key }) => filters[key] !== 'all').map(({ key, options }) => {
      const option = options.find((o) => o.value === filters[key]);
      return {
        label: option?.label || '',
        onRemove: () => onFiltersChange({ ...filters, [key]: 'all' }),
      };
    });
  };

  const activeBadges = getActiveFilterBadges();

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <Filter className="h-4 w-4" />
            Filters
            {hasActiveFilters && (
              <Badge variant="secondary" className="ml-0.5 px-1.5 h-5 text-xs">
                {activeBadges.length}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="start">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-sm">Filter Items</h4>
              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={handleClearAll} className="h-8 gap-1 text-xs">
                  <X className="h-3 w-3" />
                  Clear All
                </Button>
              )}
            </div>

            <Separator />

            <div className="space-y-4">
              {FILTER_CONFIGS.map(({ key, label, options }) => (
                <FilterGroup
                  key={key}
                  label={label}
                  options={options}
                  value={filters[key]}
                  onChange={(value) => onFiltersChange({ ...filters, [key]: value })}
                />
              ))}
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {activeBadges.map((badge, index) => (
        <Badge key={index} variant="secondary" className="gap-1 pl-2.5 pr-1">
          {badge.label}
          <button onClick={badge.onRemove} className="ml-0.5 rounded-sm hover:bg-muted-foreground/20 p-0.5">
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}

      {filteredCount !== totalCount && (
        <span className="text-xs text-muted-foreground ml-auto">
          Showing {filteredCount} of {totalCount}
        </span>
      )}
    </div>
  );
}

export function filterAddendumItems(items: AddendumItem[], filters: AddendumFilterState): AddendumItem[] {
  return items.filter((item) => {
    if (filters.severity !== 'all' && item.severity !== filters.severity) return false;
    if (filters.recommendedAction !== 'all' && item.recommendedAction !== filters.recommendedAction) return false;
    if (filters.evidenceAlignment !== 'all' && item.evidenceAlignment !== filters.evidenceAlignment) return false;
    return true;
  });
}
