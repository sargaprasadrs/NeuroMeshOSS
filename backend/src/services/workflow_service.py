import logging
from uuid import UUID, uuid4
from typing import Sequence
from src.core.entities.workflow import Workflow, WorkflowDefinition
from src.core.entities.run import Run, RunStep, RunStatus
from src.core.ports.repositories import IWorkflowRepository, IRunRepository
from src.core.ports.queue import IJobQueue, IEventBus

logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(
        self,
        workflow_repo: IWorkflowRepository,
        run_repo: IRunRepository,
        job_queue: IJobQueue,
        event_bus: IEventBus,
    ) -> None:
        self.workflow_repo = workflow_repo
        self.run_repo = run_repo
        self.job_queue = job_queue
        self.event_bus = event_bus

    async def create_workflow(
        self, user_id: UUID, name: str, definition_dict: dict
    ) -> Workflow:
        """Validates, creates and persists a new workflow."""
        definition = WorkflowDefinition.model_validate(definition_dict)
        # Verify DAG properties (cycles, orphan nodes) can be implemented here
        workflow = Workflow(
            id=uuid4(),
            user_id=user_id,
            name=name,
            definition=definition,
            is_active=True,
            version=1,
        )
        saved = await self.workflow_repo.save(workflow)
        logger.info(f"Workflow {saved.id} created successfully.")
        return saved

    async def trigger_run(self, workflow_id: UUID, correlation_id: str | None = None) -> Run:
        """Triggers a new execution run of a workflow and enqueues the execution command."""
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow or not workflow.is_active:
            raise ValueError(f"Workflow {workflow_id} not found or inactive.")

        run = Run(
            id=uuid4(),
            workflow_id=workflow_id,
            status=RunStatus.PENDING,
            current_state={},
            version=1,
        )
        saved_run = await self.run_repo.save(run)

        # Enqueue the run execution command
        await self.job_queue.enqueue(
            queue_name="workflow_jobs",
            payload={
                "run_id": str(saved_run.id),
                "workflow_id": str(workflow_id),
                "action": "START",
                "correlation_id": correlation_id,
            },
        )

        # Publish state event
        await self.event_bus.publish(
            topic=str(saved_run.id),
            event_type="RUN_STARTED",
            payload={"run_id": str(saved_run.id), "status": saved_run.status.value},
        )
        logger.info(f"Workflow Run {saved_run.id} triggered.")
        return saved_run

    async def approve_human_step(self, run_id: UUID, step_id: UUID, approval_data: dict) -> Run:
        """Handles human approval nodes, resuming execution runs."""
        run = await self.run_repo.get_by_id(run_id)
        if not run or run.status != RunStatus.PAUSED:
            raise ValueError("Run is not in a paused state awaiting approval.")

        # Update run variables with approval data
        updated_state = run.current_state.copy()
        updated_state[f"approval_{step_id}"] = approval_data
        
        # Increment OCC version and update status
        updated_run = Run(
            id=run.id,
            workflow_id=run.workflow_id,
            status=RunStatus.RUNNING,
            current_state=updated_state,
            version=run.version,
            created_at=run.created_at,
        )
        saved_run = await self.run_repo.save(updated_run)

        # Resume the worker run command
        await self.job_queue.enqueue(
            queue_name="workflow_jobs",
            payload={
                "run_id": str(saved_run.id),
                "workflow_id": str(saved_run.workflow_id),
                "action": "RESUME",
                "step_id": str(step_id),
            },
        )

        # Publish event
        await self.event_bus.publish(
            topic=str(saved_run.id),
            event_type="RUN_RESUMED",
            payload={"run_id": str(saved_run.id), "step_id": str(step_id)},
        )
        return saved_run

    async def get_run_steps(self, run_id: UUID) -> Sequence[RunStep]:
        """Gets steps and traces for a run."""
        return await self.run_repo.get_steps(run_id)
