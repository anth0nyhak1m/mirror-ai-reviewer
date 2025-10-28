from __future__ import annotations

from enum import Enum
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from lib.config.llm_models import gpt_5_model
from lib.models.agent import DEFAULT_LLM_TIMEOUT, AgentProtocol
from pydantic import BaseModel, Field

# Required types used in the Addendum models
from lib.agents.claim_categorizer import ClaimCategory
from lib.agents.evidence_weighter import (
    EvidenceWeighterRecommendedAction,
    ReferenceAlignmentLevel,
)
from lib.agents.literature_review import QualityLevel


class AddendumSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AddendumItem(BaseModel):
    chunk_index: int
    claim_index: int
    original_claim: str
    rewritten_claim: str
    claim_category: ClaimCategory
    evidence_alignment: ReferenceAlignmentLevel
    recommended_action: EvidenceWeighterRecommendedAction
    action_summary: str = Field(
        description="Two sentences max; actionable guidance on what to change in the claim"
    )
    confidence: QualityLevel
    rationale: str
    severity: AddendumSeverity


class AddendumSections(BaseModel):
    background: list[AddendumItem] = []
    methodology: list[AddendumItem] = []
    results: list[AddendumItem] = []
    interpretation: list[AddendumItem] = []


class Addendum(BaseModel):
    summary: str = Field(
        description="2–3 sentence executive summary of salient updates"
    )
    sections: AddendumSections


_addendum_prompt = ChatPromptTemplate.from_template(
    """
You are an expert research editor. Aggregate live report updates across claims and produce a concise addendum with:
- A 2–3 sentence executive summary of the most salient high-severity updates
- Sectioned bullet points under Background, Methodology, Results, Interpretation

Severity rubric:
- High: The issue changes the validity/soundness of the overall argument (foundational to thesis)
- Medium: Significant change to background that affects results but is not foundational
- Low: Minor change not related to thesis or argument soundness

Instructions:
1) For each input item, assign a severity using the rubric above.
2) Create an action_summary for each item (max two sentences) that tells the editor what to do to the claim (e.g., update wording to reflect X; add citations Y and Z; qualify scope to ...).
3) Populate sections by claim category: established_reported_knowledge → Background; methodology_procedural → Methodology; empirical_analytical_results → Results; inferential_interpretive_claims → Interpretation; others may be omitted from sections.
4) In top_items, include all High severity items, then Medium if needed for context. Sort by severity then by highest impact.
5) Keep the output concise; avoid repeating full evidence details already present in live reports.

Document context:
Domain: {domain_context}
Audience: {audience_context}
Title: {document_title}
Summary (optional): {document_summary}

Input records (JSON):
```
{records_json}
```

Return one JSON object matching the required schema exactly.
    """
)


class AddendumGeneratorAgent(AgentProtocol):
    name: str = "Addendum Generator"
    description: str = (
        "Aggregate live reports and produce a structured addendum with severities and actions"
    )

    def __init__(self):
        self.llm = init_chat_model(
            gpt_5_model.model_name, temperature=0.2, timeout=DEFAULT_LLM_TIMEOUT
        ).with_structured_output(Addendum)

    async def ainvoke(
        self, prompt_kwargs: dict, config: RunnableConfig = None
    ) -> Addendum:
        messages = _addendum_prompt.format_messages(**prompt_kwargs)
        return await self.llm.ainvoke(messages, config=config)


addendum_generator_agent = AddendumGeneratorAgent()
