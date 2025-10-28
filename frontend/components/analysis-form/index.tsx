'use client';

import { uploadOrchestrator } from '@/lib/services/upload-orchestrator';
import { useRouter } from 'next/navigation';
import { useForm } from '@tanstack/react-form';
import { useMutation } from '@tanstack/react-query';
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { UploadSection } from './upload-section';
import { CheckboxWithDescription } from '../ui/checkbox-with-description';
import { Play, Loader2, AlertCircle } from 'lucide-react';
import { Progress } from '../ui/progress';
import { AnalysisConfig } from '../wizard/types';
import { StartAnalysisResponse } from '@/lib/generated-api';

export function AnalysisForm() {
  const router = useRouter();
  const [mainDocument, setMainDocument] = React.useState<File | null>(null);
  const [supportingDocuments, setSupportingDocuments] = React.useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = React.useState(0);
  const [processingStage, setProcessingStage] = React.useState<'idle' | 'uploading' | 'complete'>('idle');

  const form = useForm({
    defaultValues: {
      domain: '',
      targetAudience: '',
      documentPublicationDate: '',
      runLiteratureReview: false,
      runSuggestCitations: false,
      runLiveReports: false,
    },
    validators: {
      onChange: ({ value }) => {
        if (value.runLiteratureReview || value.runLiveReports) {
          if (!value.documentPublicationDate) {
            return {
              fields: {
                documentPublicationDate: 'Document publication date is required',
              },
            };
          }
        }
        return undefined;
      },
    },
    onSubmit: ({ value }) => {
      if (!mainDocument) {
        return;
      }

      const allFiles = [mainDocument, ...supportingDocuments];
      const validation = uploadOrchestrator.validateFiles(allFiles);

      if (!validation.valid && validation.errors) {
        // Show validation errors
        return;
      }

      analysisMutation.mutate({
        mainDocument,
        supportingDocuments,
        config: value,
      });
    },
  });

  const analysisMutation = useMutation<
    StartAnalysisResponse,
    Error,
    {
      mainDocument: File;
      supportingDocuments: File[];
      config: AnalysisConfig;
    }
  >({
    mutationFn: async (data) => {
      return uploadOrchestrator.startAnalysisWithProgress(
        {
          mainDocument: data.mainDocument,
          supportingDocuments: data.supportingDocuments,
          config: {
            useToulmin: true,
            runLiteratureReview: data.config.runLiteratureReview,
            runSuggestCitations: data.config.runSuggestCitations,
            runLiveReports: data.config.runLiveReports,
            domain: data.config.domain || undefined,
            targetAudience: data.config.targetAudience || undefined,
            documentPublicationDate: data.config.documentPublicationDate
              ? new Date(data.config.documentPublicationDate)
              : undefined,
            sessionId: undefined,
          },
        },
        {
          onProgress: (progress) => {
            setUploadProgress(progress);
          },
          onStageChange: (stage) => {
            setProcessingStage(stage);
          },
        },
      );
    },
    onSuccess: (response) => {
      router.push(`/results/${response.workflowRunId}`);
    },
  });

  const removeFile = (type: 'main' | 'supporting', index?: number) => {
    if (type === 'main') {
      setMainDocument(null);
    } else if (typeof index === 'number') {
      const newFiles = supportingDocuments.filter((_, i) => i !== index);
      setSupportingDocuments(newFiles);
    }
  };

  const getStageInfo = () => {
    switch (processingStage) {
      case 'uploading':
        return {
          title: 'Uploading Documents',
          description: 'Uploading and converting your files...',
          detail: 'This may take a moment for large PDF files',
        };
      case 'complete':
        return {
          title: 'Upload Complete',
          description: 'Documents uploaded successfully',
          detail: 'Redirecting to analysis...',
        };
      default:
        return {
          title: 'Preparing Upload',
          description: 'Getting ready to upload your documents...',
          detail: 'Please wait',
        };
    }
  };

  if (analysisMutation.isPending) {
    const stageInfo = getStageInfo();

    return (
      <div className="space-y-6">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 mx-auto animate-spin text-primary" />
          <h2 className="text-2xl font-bold">{stageInfo.title}</h2>
          <p className="text-muted-foreground max-w-md mx-auto">{stageInfo.description}</p>
        </div>
        <Card className="max-w-xl mx-auto">
          <CardContent className="py-8">
            <div className="space-y-4">
              <Progress value={uploadProgress} className="w-full" />
              <p className="text-sm text-center text-muted-foreground">{stageInfo.detail}</p>

              {processingStage === 'uploading' && uploadProgress > 0 && (
                <div className="text-center">
                  <p className="text-2xl font-semibold text-primary">{Math.round(uploadProgress)}%</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Uploading {mainDocument?.name}
                    {supportingDocuments.length > 0 &&
                      ` and ${supportingDocuments.length} supporting file${supportingDocuments.length > 1 ? 's' : ''}`}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (analysisMutation.isError) {
    return (
      <Card className="max-w-4xl mx-auto border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Analysis Failed
          </CardTitle>
          <CardDescription>There was an error processing your files</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
            <p className="text-sm text-destructive whitespace-pre-line">
              {analysisMutation.error?.message || 'Failed to start analysis'}
            </p>
          </div>

          <Button
            onClick={() => {
              analysisMutation.reset();
              setUploadProgress(0);
              setProcessingStage('idle');
            }}
            variant="outline"
            className="w-full"
          >
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <form
      className="space-y-8"
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        form.handleSubmit();
      }}
    >
      <div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <UploadSection
            title="Main Document"
            description="Primary document for analysis"
            badgeText="Required"
            badgeClass="bg-primary/10 text-primary border border-primary/20"
            onFilesChange={(files) => setMainDocument(files[0] || null)}
            multiple={false}
            files={mainDocument ? [mainDocument] : []}
            fileType="main"
            onRemoveFile={() => removeFile('main')}
          />

          <UploadSection
            title="Supporting Documents"
            description="Documents used as references for the main document"
            badgeText="Optional"
            badgeClass="bg-muted/60 text-muted-foreground border border-muted"
            onFilesChange={setSupportingDocuments}
            multiple={true}
            files={supportingDocuments}
            fileType="supporting"
            onRemoveFile={(index) => removeFile('supporting', index)}
          />
        </div>
      </div>

      {/* Analysis Options Section */}
      <div className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold">Analysis Options</h2>
          <p className="text-sm text-muted-foreground">Select which analysis features to run</p>
        </div>
        <div className="space-y-3">
          <form.Field name="runLiteratureReview">
            {(field) => (
              <CheckboxWithDescription
                id="run-literature-review"
                checked={field.state.value}
                onCheckedChange={(checked) => field.handleChange(checked === true)}
                label="Run literature review"
                description="Analyzes the document and bibliography to identify high-quality references that should be cited. Suggests both existing bibliography entries that should be cited in different places and new, high-quality references found via web research."
                disabled={analysisMutation.isPending}
              />
            )}
          </form.Field>
          <form.Field name="runSuggestCitations">
            {(field) => (
              <CheckboxWithDescription
                id="run-suggest-citations"
                checked={field.state.value}
                onCheckedChange={(checked) => field.handleChange(checked === true)}
                label="Run suggest citations"
                description="Analyzes each claim to identify missing citations based on RAND's Three Rules of Attribution. Suggests where ideas, facts, statistics, or exact words require attribution to support the document's claims."
                disabled={analysisMutation.isPending}
              />
            )}
          </form.Field>
          <form.Field name="runLiveReports">
            {(field) => (
              <CheckboxWithDescription
                id="run-live-reports"
                checked={field.state.value}
                onCheckedChange={(checked) => field.handleChange(checked === true)}
                label="Run live reports"
                description="Analyzes whether claims remain accurate given newer literature published after the document's publication date. Evaluates evidence strength and direction of newer research to assess if conclusions still hold."
                disabled={analysisMutation.isPending}
              />
            )}
          </form.Field>
        </div>
        <form.Subscribe selector={(state) => [state.values.runLiteratureReview, state.values.runLiveReports]}>
          {(showWhenTrue) =>
            showWhenTrue.some((value) => !!value) && (
              <form.Field name="documentPublicationDate">
                {(field) => (
                  <div className="space-y-2 pt-2">
                    <Label htmlFor="publication-date">
                      Document Publication Date
                      <span className="text-destructive ml-1">*</span>
                    </Label>
                    <Input
                      id="publication-date"
                      type="date"
                      value={field.state.value}
                      onChange={(e) => field.handleChange(e.target.value)}
                      className={field.state.meta.errors.length > 0 ? 'border-destructive' : ''}
                      disabled={analysisMutation.isPending}
                    />
                    {!field.state.meta.isValid && (
                      <p className="text-sm text-destructive">{field.state.meta.errors.join(', ')}</p>
                    )}
                  </div>
                )}
              </form.Field>
            )
          }
        </form.Subscribe>
      </div>

      {/* Additional Context Section */}
      <div className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold">Additional Context</h2>
          <p className="text-sm text-muted-foreground">Provide context for more accurate analysis</p>
        </div>
        <div className="space-y-4">
          <form.Field name="domain">
            {(field) => (
              <div className="space-y-2">
                <Label htmlFor="domain">
                  Domain <span className="text-muted-foreground text-xs font-normal">(Optional)</span>
                </Label>
                <Input
                  id="domain"
                  placeholder="e.g., Healthcare, Technology, Finance..."
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  disabled={analysisMutation.isPending}
                />
                <p className="text-sm text-muted-foreground">
                  The subject area or field of expertise to contextualize the analysis. This helps tailor the evaluation
                  to domain-specific standards and terminology.
                </p>
              </div>
            )}
          </form.Field>
          <form.Field name="targetAudience">
            {(field) => (
              <div className="space-y-2">
                <Label htmlFor="target-audience">
                  Target Audience <span className="text-muted-foreground text-xs font-normal">(Optional)</span>
                </Label>
                <Input
                  id="target-audience"
                  placeholder="e.g., General public, Experts, Students..."
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  disabled={analysisMutation.isPending}
                />
                <p className="text-sm text-muted-foreground">
                  The intended readers of the document. Specifying the audience helps adjust the analysis to match
                  appropriate complexity level and expectations.
                </p>
              </div>
            )}
          </form.Field>
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-center">
        <form.Subscribe selector={(state) => [state.canSubmit, state.isSubmitting]}>
          {([canSubmit]) => (
            <Button
              type="submit"
              disabled={!mainDocument || !canSubmit || analysisMutation.isPending}
              size="lg"
              className="min-w-48 gap-2 font-semibold"
            >
              {analysisMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Start Analysis
                </>
              )}
            </Button>
          )}
        </form.Subscribe>
      </div>
    </form>
  );
}
