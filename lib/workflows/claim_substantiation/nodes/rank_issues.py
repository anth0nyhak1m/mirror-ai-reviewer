from typing import List


from lib.agents.claim_verifier import EvidenceAlignmentLevel
from lib.agents.evidence_weighter import EvidenceWeighterRecommendedAction
from lib.agents.models import ClaimCategory
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
    DocumentIssue,
    SeverityEnum,
)


def rank_issues(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    """Rank issues based on analysis results from various workflow stages."""
    issues: List[DocumentIssue] = []

    # 1. Extract References: References without matching supporting documents
    for reference in state.references:
        if not reference.has_associated_supporting_document:
            issue = DocumentIssue(
                title="Missing supporting document for reference",
                description=f'Reference does not have an associated supporting document: "{reference.text}"',
                severity=SeverityEnum.LOW,
                additional_context="This reference was mentioned in the document but no corresponding supporting document was provided. It was excluded from the analysis.",
                chunk_index=None,  # TODO: include the chunk index that contains the reference
            )
            issues.append(issue)

    # 2. Claim Categorization: Claims needing external verification without citations
    for chunk in state.chunks:
        if not chunk.claim_categories:
            continue

        # Check if chunk has citations
        has_citations = (
            chunk.citations
            and chunk.citations.citations
            and len(chunk.citations.citations) > 0
        )

        for category in chunk.claim_categories:
            if category.needs_external_verification and not has_citations:
                issue = DocumentIssue(
                    title="Unsupported claim",
                    description=f"Claim '{category.claim}' requires external verification but no citations were found.",
                    severity=SeverityEnum.MEDIUM,
                    additional_context=f"Rationale: {category.rationale}",
                    chunk_index=category.chunk_index,
                    claim_index=category.claim_index,
                    claim_category=category.claim_category,
                )
                issues.append(issue)

    # 3. Claim Verification: Unsupported and partially supported claims
    for chunk in state.chunks:
        if not chunk.substantiations:
            continue

        for substantiation in chunk.substantiations:
            if substantiation.evidence_alignment == EvidenceAlignmentLevel.UNSUPPORTED:
                issue = DocumentIssue(
                    title="Unsupported Claim",
                    description=substantiation.rationale,
                    severity=SeverityEnum.HIGH,
                    additional_context=f"Feedback: {substantiation.feedback}",
                    chunk_index=substantiation.chunk_index,
                    claim_index=substantiation.claim_index,
                    claim_category=_find_claim_category(
                        chunk, substantiation.claim_index
                    ),
                )
                issues.append(issue)
            elif (
                substantiation.evidence_alignment
                == EvidenceAlignmentLevel.PARTIALLY_SUPPORTED
            ):
                issue = DocumentIssue(
                    title="Partially Supported Claim",
                    description=substantiation.rationale,
                    severity=SeverityEnum.MEDIUM,
                    additional_context=f"Feedback: {substantiation.feedback}",
                    chunk_index=substantiation.chunk_index,
                    claim_index=substantiation.claim_index,
                    claim_category=_find_claim_category(
                        chunk, substantiation.claim_index
                    ),
                )
                issues.append(issue)

    # 4. Live Reports Analysis: Add citation and update claim actions
    for live_report in state.live_reports_analysis:
        if (
            live_report.claim_update_action
            == EvidenceWeighterRecommendedAction.ADD_CITATION
        ):
            issue = DocumentIssue(
                title="Additional Citation Recommended",
                description=live_report.rationale,
                severity=SeverityEnum.MEDIUM,
                additional_context=f"Newer references alignment: {live_report.newer_references_alignment.value}. Confidence: {live_report.confidence_level.value}.",
                chunk_index=live_report.chunk_index,
                claim_index=live_report.claim_index,
                claim_category=_find_claim_category(chunk, live_report.claim_index),
            )
            issues.append(issue)
        elif (
            live_report.claim_update_action
            == EvidenceWeighterRecommendedAction.UPDATE_CLAIM
        ):
            issue = DocumentIssue(
                title="Claim Update Recommended",
                description=live_report.rationale,
                severity=SeverityEnum.MEDIUM,
                additional_context=f"Newer references alignment: {live_report.newer_references_alignment.value}. Confidence: {live_report.confidence_level.value}. Rewritten claim: {live_report.rewritten_claim}",
                chunk_index=live_report.chunk_index,
                claim_index=live_report.claim_index,
                claim_category=_find_claim_category(chunk, live_report.claim_index),
            )
            issues.append(issue)

    issues.sort(key=lambda x: x.severity.sort_index(), reverse=True)

    return {"ranked_issues": issues}


def _find_claim_category(chunk: DocumentChunk, claim_index: int) -> ClaimCategory:
    for category in chunk.claim_categories:
        if category.claim_index == claim_index:
            return category.claim_category

    return None
