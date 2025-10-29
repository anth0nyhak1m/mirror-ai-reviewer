import { ClaimSubstantiatorStateOutput, DocumentChunkOutput, SeverityEnum } from './generated-api';

export function getSeverity(results: ClaimSubstantiatorStateOutput, chunk: DocumentChunkOutput) {
  const issues = results.rankedIssues?.filter((issue) => issue.chunkIndex === chunk.chunkIndex) || [];

  const severities = issues.map((issue) => issue.severity);
  if (severities.includes(SeverityEnum.High)) {
    return SeverityEnum.High;
  }
  if (severities.includes(SeverityEnum.Medium)) {
    return SeverityEnum.Medium;
  }
  if (severities.includes(SeverityEnum.Low)) {
    return SeverityEnum.Low;
  }
  return SeverityEnum.None;
}

export const severityColors: Record<SeverityEnum, 'none' | 'yellow' | 'red' | 'green' | 'blue'> = {
  [SeverityEnum.None]: 'none',
  [SeverityEnum.Low]: 'blue',
  [SeverityEnum.Medium]: 'yellow',
  [SeverityEnum.High]: 'red',
};
