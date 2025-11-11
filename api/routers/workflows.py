"""
Workflow run management endpoints
"""

from fastapi import APIRouter, Depends

from api.auth import get_current_user
from lib.models.user import User
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
async def list_workflow_runs(current_user: User = Depends(get_current_user)):
    """List all workflow runs"""
    return await get_workflow_runs(user=current_user)


@router.get("/api/workflow-run/{workflow_run_id}", response_model=WorkflowRunDetailed)
async def get_workflow_run(
    workflow_run_id: str, current_user: User = Depends(get_current_user)
):
    """Get detailed workflow run information including state"""
    return await get_workflow_run_detailed(workflow_run_id, user=current_user)


@router.patch("/api/workflow-run/{workflow_run_id}", response_model=WorkflowRun)
async def update_workflow_run_endpoint(
    workflow_run_id: str,
    request: UpdateWorkflowRunRequest,
    current_user: User = Depends(get_current_user),
):
    """Update a workflow run with the provided fields"""
    return await update_workflow_run(workflow_run_id, request, user=current_user)


@router.get(
    "/api/workflow-run/{workflow_run_id}/chunk/{chunk_index}",
    response_model=DocumentChunk,
)
async def get_chunk_details_endpoint(workflow_run_id: str, chunk_index: int):
    """Get detailed analysis for a specific chunk (lazy loading)"""
    return await get_chunk_details(workflow_run_id, chunk_index)


@router.delete("/api/workflow-run/{workflow_run_id}")
async def delete_workflow_run_endpoint(
    workflow_run_id: str, current_user: User = Depends(get_current_user)
):
    """Delete a workflow run and its associated checkpoint data"""
    await delete_workflow_run(workflow_run_id, user=current_user)
    return {"message": "Workflow run deleted successfully", "id": workflow_run_id}
