import pytest

from lib.agents.addendum_generator import (
    Addendum,
    AddendumItem,
    AddendumSections,
    AddendumSeverity,
)
from lib.agents.claim_categorizer import (
    ClaimCategorizationResponseWithClaimIndex,
    ClaimCategory,
)
from lib.agents.claim_extractor import Claim, ClaimResponse
from lib.agents.evidence_weighter import (
    EvidenceWeighterResponseWithClaimIndex,
    EvidenceWeighterRecommendedAction,
    ReferenceAlignmentLevel,
)
from lib.agents.literature_review import QualityLevel
from lib.services.file import FileDocument
from lib.workflows.claim_substantiation.nodes.generate_addendum import (
    generate_addendum,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
    SubstantiationWorkflowConfig,
)


@pytest.mark.asyncio
async def test_generate_addendum_smoke(monkeypatch):
    # Minimal state with one chunk and one claim
    file = FileDocument(
        file_name="test.md",
        file_path="/tmp/test.md",
        file_type="text/markdown",
        markdown="# Title\n\nTest paragraph with a claim.",
    )

    claim_text = "X causes Y"
    chunk = DocumentChunk(
        content="X causes Y.",
        chunk_index=0,
        paragraph_index=0,
        claims=ClaimResponse(
            claims=[
                Claim(text="X causes Y.", claim=claim_text, rationale="test rationale"),
            ],
            rationale="rationale",
        ),
        claim_categories=[
            ClaimCategorizationResponseWithClaimIndex(
                chunk_index=0,
                claim_index=0,
                claim=claim_text,
                claim_category=ClaimCategory.ESTABLISHED,
                rationale="cat rationale",
                needs_external_verification=True,
            )
        ],
        live_reports_analysis=[
            EvidenceWeighterResponseWithClaimIndex(
                chunk_index=0,
                claim_index=0,
                newer_references=[],
                newer_references_alignment=ReferenceAlignmentLevel.UNSUPPORTED,
                claim_update_action=EvidenceWeighterRecommendedAction.UPDATE_CLAIM,
                rationale="evidence rationale",
                confidence_level=QualityLevel.HIGH,
                rewritten_claim="X does not consistently cause Y",
            )
        ],
    )

    state = ClaimSubstantiatorState(
        file=file,
        config=SubstantiationWorkflowConfig(run_live_reports=True),
        chunks=[chunk],
    )

    # Mock agent to return a deterministic Addendum
    from lib.workflows.claim_substantiation import nodes as _nodes_pkg  # noqa: F401
    from lib.agents import addendum_generator as addendum_module

    async def _fake_ainvoke(prompt_kwargs, config=None):
        item = AddendumItem(
            chunk_index=0,
            claim_index=0,
            original_claim=claim_text,
            rewritten_claim="X does not consistently cause Y",
            claim_category=ClaimCategory.ESTABLISHED,
            evidence_alignment=ReferenceAlignmentLevel.UNSUPPORTED,
            recommended_action=EvidenceWeighterRecommendedAction.UPDATE_CLAIM,
            action_summary="Revise claim to qualify causality and add updated citations.",
            confidence=QualityLevel.HIGH,
            rationale="High-impact contradiction to thesis.",
            severity=AddendumSeverity.HIGH,
        )
        return Addendum(
            summary="Recent evidence undermines a foundational claim.",
            top_items=[item],
            sections=AddendumSections(background=[item]),
        )

    monkeypatch.setattr(
        addendum_module.addendum_generator_agent, "ainvoke", _fake_ainvoke
    )

    # Execute node
    result_delta = await generate_addendum(state)

    # Validate
    assert "addendum" in result_delta
    addendum = result_delta["addendum"]
    assert isinstance(addendum, Addendum)
    assert addendum.summary
    assert (
        addendum.top_items and addendum.top_items[0].severity == AddendumSeverity.HIGH
    )
