"""
Workflow run management endpoints
"""

from fastapi import APIRouter

from lib.models.workflow_run import WorkflowRun
from lib.services.workflow_runs import (
    UpdateWorkflowRunRequest,
    WorkflowRunDetailed,
    delete_workflow_run,
    get_chunk_details,
    get_workflow_run_detailed,
    get_workflow_runs,
    update_workflow_run,
)
from lib.workflows.claim_substantiation.state import DocumentChunk

router = APIRouter(tags=["workflows"])


@router.get("/api/workflow-runs", response_model=list[WorkflowRun])
async def list_workflow_runs():
    """List all workflow runs"""
    return await get_workflow_runs()


@router.get("/api/workflow-run/{workflow_run_id}", response_model=WorkflowRunDetailed)
async def get_workflow_run(workflow_run_id: str):
    """Get detailed workflow run information including state"""
    return await get_workflow_run_detailed(workflow_run_id)


@router.patch("/api/workflow-run/{workflow_run_id}", response_model=WorkflowRun)
async def update_workflow_run_endpoint(
    workflow_run_id: str, request: UpdateWorkflowRunRequest
):
    """Update a workflow run with the provided fields"""
    return await update_workflow_run(workflow_run_id, request)


@router.get(
    "/api/workflow-run/{workflow_run_id}/chunk/{chunk_index}",
    response_model=DocumentChunk,
)
async def get_chunk_details_endpoint(workflow_run_id: str, chunk_index: int):
    """Get detailed analysis for a specific chunk (lazy loading)"""
    return await get_chunk_details(workflow_run_id, chunk_index)


@router.delete("/api/workflow-run/{workflow_run_id}")
async def delete_workflow_run_endpoint(workflow_run_id: str):
    """Delete a workflow run and its associated checkpoint data"""
    await delete_workflow_run(workflow_run_id)
    return {"message": "Workflow run deleted successfully", "id": workflow_run_id}
