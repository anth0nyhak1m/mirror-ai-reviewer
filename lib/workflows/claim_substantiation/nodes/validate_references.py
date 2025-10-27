import logging

from lib.agents.reference_validator import reference_validator_agent
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def validate_references(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info(f"validate_references ({state.config.session_id}): starting")

    if not state.config.run_literature_review:
        logger.info(
            f"literature_review ({state.config.session_id}): skipping literature review (run_literature_review is False)"
        )
        return {}

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "validate_references" not in agents_to_run:
        logger.info(
            f"validate_references ({state.config.session_id}): Skipping validate references (not in agents_to_run)"
        )
        return {}

    validate_references_response = await reference_validator_agent.ainvoke(
        {
            "domain_context": state.config.domain or "",
            "audience_context": state.config.target_audience or "",
            "references": state.references,
        }
    )

    logger.info(f"validate_references ({state.config.session_id}): done")

    return {
        "references_validated": validate_references_response.bibliography_item_validations
    }
