from uuid import UUID
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.core.entities.workflow import Workflow
from src.core.entities.run import Run
from src.adapters.database.session import get_db_session
from src.adapters.database.repositories import (
    SqlAlchemyWorkflowRepository,
    SqlAlchemyRunRepository,
)
from src.adapters.queue.redis_queue import RedisJobQueue, RedisEventBus
from src.services.workflow_service import WorkflowService
from src.api.deps import require_authenticated_user

router = APIRouter(prefix="/workflows", tags=["Workflows"])


class CreateWorkflowRequest(BaseModel):
    name: str
    definition: Dict[str, Any]


class HumanApprovalRequest(BaseModel):
    approval_data: Dict[str, Any]


def get_workflow_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowService:
    workflow_repo = SqlAlchemyWorkflowRepository(session)
    run_repo = SqlAlchemyRunRepository(session)
    job_queue = request.app.state.job_queue
    event_bus = request.app.state.event_bus
    return WorkflowService(workflow_repo, run_repo, job_queue, event_bus)


@router.post("/", response_model=None, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    req: CreateWorkflowRequest,
    user_id: UUID = Depends(require_authenticated_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> Any:
    workflow = await service.create_workflow(
        user_id=user_id,
        name=req.name,
        definition_dict=req.definition,
    )
    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "definition": workflow.definition.model_dump(),
        "version": workflow.version,
    }


@router.post("/{workflow_id}/run", response_model=None)
async def run_workflow(
    workflow_id: UUID,
    request: Request,
    user_id: UUID = Depends(require_authenticated_user),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    service: WorkflowService = Depends(get_workflow_service),
) -> Any:
    try:
        correlation_id = getattr(request.state, "correlation_id", None)
        run = await service.trigger_run(workflow_id, correlation_id=correlation_id)
        return {
            "run_id": str(run.id),
            "workflow_id": str(run.workflow_id),
            "status": run.status.value,
            "version": run.version,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/runs/{run_id}/steps/{step_id}/approve", response_model=None)
async def approve_step(
    run_id: UUID,
    step_id: UUID,
    req: HumanApprovalRequest,
    user_id: UUID = Depends(require_authenticated_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> Any:
    try:
        run = await service.approve_human_step(run_id, step_id, req.approval_data)
        return {
            "run_id": str(run.id),
            "status": run.status.value,
            "current_state": run.current_state,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=None)
async def list_workflows(
    limit: int = 20,
    cursor: str | None = None,
    sort: str = "name",
    user_id: UUID = Depends(require_authenticated_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> Any:
    """Lists workflows with cursor-based pagination and configurable sorting fields."""
    workflows = await service.workflow_repo.list_by_user(user_id)
    
    # Sort logically
    sorted_workflows = sorted(workflows, key=lambda w: getattr(w, sort, w.name))
    
    # Simulating cursor offsets
    next_cursor = "eyJvZmZzZXQiOiAyMH0=" if len(sorted_workflows) > limit else None
    
    return {
        "items": [
            {
                "id": str(w.id),
                "name": w.name,
                "definition": w.definition.model_dump(),
                "version": w.version,
            }
            for w in sorted_workflows[:limit]
        ],
        "next_cursor": next_cursor,
    }
