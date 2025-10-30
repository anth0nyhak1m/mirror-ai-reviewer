import asyncio
import logging

from lib.services.converters.base import convert_to_markdown as convert_to_markdown_fn
from lib.services.file import FileDocument
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.workflows.decorators import requires_agent

logger = logging.getLogger(__name__)


@requires_agent("convert_to_markdown")
async def convert_to_markdown(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info(f"convert_to_markdown ({state.config.session_id}): starting")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "convert_to_markdown" not in agents_to_run:
        logger.info(
            f"convert_to_markdown ({state.config.session_id}): Skipping convert_to_markdown (not in agents_to_run)"
        )
        return {}

    tasks = [
        _convert_to_markdown_task(state.file),
        *[_convert_to_markdown_task(file) for file in state.supporting_files or []],
    ]
    results = await asyncio.gather(*tasks)
    [file, *supporting_files] = results

    logger.info(f"convert_to_markdown ({state.config.session_id}): done")

    return {"file": file, "supporting_files": supporting_files}


async def _convert_to_markdown_task(file_document: FileDocument) -> FileDocument:
    markdown = await convert_to_markdown_fn(file_document.file_path)

    return FileDocument(
        file_path=file_document.file_path,
        file_name=file_document.file_name,
        file_type=file_document.file_type,
        markdown=markdown,
    )
