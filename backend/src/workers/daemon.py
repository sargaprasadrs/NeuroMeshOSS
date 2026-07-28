import argparse
import asyncio
import logging
from typing import Any, Dict
from uuid import UUID

from src.adapters.queue.redis_queue import RedisJobQueue, RedisEventBus
from src.adapters.database.session import AsyncSessionLocal
from src.adapters.database.repositories import SqlAlchemyWorkflowRepository, SqlAlchemyRunRepository
from src.services.workflow_engine import WorkflowEngine
from src.config.settings import settings

logger = logging.getLogger(__name__)

# Reuse a single event bus instance across all jobs in this worker process
_event_bus: RedisEventBus | None = None


def _get_event_bus() -> RedisEventBus:
    """Return the shared event bus singleton for this worker process."""
    global _event_bus
    if _event_bus is None:
        _event_bus = RedisEventBus(settings.REDIS_URL)
    return _event_bus


async def handle_workflow_job(payload: Dict[str, Any]) -> bool:
    """Process a workflow job from the Redis Stream queue.

    Supports actions:
    - START: Begin executing a workflow run from the start
    - RESUME: Resume a paused run (e.g. after human approval)
    """
    run_id = payload.get("run_id")
    workflow_id = payload.get("workflow_id")
    action = payload.get("action", "START")
    correlation_id = payload.get("correlation_id", "N/A")
    step_id = payload.get("step_id")

    log_prefix = f"[Correlation ID: {correlation_id}] [Run: {run_id}]"
    logger.info(f"{log_prefix} Worker received job. Action={action}, Workflow={workflow_id}")

    try:
        async with AsyncSessionLocal() as session:
            workflow_repo = SqlAlchemyWorkflowRepository(session)
            run_repo = SqlAlchemyRunRepository(session)

            # Load workflow and run from database
            wf_id = UUID(workflow_id) if workflow_id else None
            run_uuid = UUID(run_id) if run_id else None

            if not wf_id or not run_uuid:
                logger.error(f"{log_prefix} Invalid workflow_id or run_id.")
                return False

            workflow = await workflow_repo.get_by_id(wf_id)
            run = await run_repo.get_by_id(run_uuid)

            if not workflow:
                logger.error(f"{log_prefix} Workflow {wf_id} not found.")
                return False
            if not run:
                logger.error(f"{log_prefix} Run {run_uuid} not found.")
                return False

            # Use the shared event bus for real-time WebSocket publishing
            event_bus = _get_event_bus()
            engine = WorkflowEngine(run_repo=run_repo, event_bus=event_bus)

            if action == "START":
                logger.info(f"{log_prefix} Starting workflow execution...")
                final_run = await engine.execute_run(run, workflow)

            elif action == "RESUME":
                logger.info(f"{log_prefix} Resuming from node {step_id}...")
                final_run = await engine.execute_run(run, workflow, start_node_id=step_id)

            else:
                logger.warning(f"{log_prefix} Unknown action '{action}'. Skipping.")
                return False

            logger.info(f"{log_prefix} Execution complete. Final status: {final_run.status.value}")
            return True

    except Exception as e:
        logger.error(f"{log_prefix} Workflow execution failed: {e}", exc_info=True)
        return False


async def shutdown_event_bus() -> None:
    """Close the shared event bus on worker shutdown."""
    global _event_bus
    if _event_bus is not None:
        await _event_bus.close()
        _event_bus = None


async def main() -> None:
    # Set up arguments parser
    parser = argparse.ArgumentParser(description="NeuroMeshOSS Background Worker Daemon")
    parser.add_argument("--queue", default="workflow_jobs", help="Target queue stream name")
    parser.add_argument("--group", default="default_group", help="Consumer group name")
    parser.add_argument("--name", default="worker_node_1", help="Consumer unique identifier name")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info(f"Initializing Worker Daemon: {args.name}...")

    # Instantiate Redis streams queue port
    job_queue = RedisJobQueue(settings.REDIS_URL)

    # Graceful shutdown handler registration
    import sys
    import signal
    loop = asyncio.get_running_loop()
    main_task = asyncio.current_task()

    def handle_exit() -> None:
        logger.info("Received termination signal. Triggering graceful shutdown...")
        if main_task:
            main_task.cancel()

    if sys.platform != "win32":
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, handle_exit)
            except ValueError:
                pass  # Fallback if loop does not support signal handling

    try:
        # Listen loop
        await job_queue.listen(
            queue_name=args.queue,
            group_name=args.group,
            consumer_name=args.name,
            handler=handle_workflow_job,
        )
    except asyncio.CancelledError:
        logger.info("Worker daemon execution task was cancelled.")
    finally:
        logger.info("Closing Worker Queue connection pool...")
        await job_queue.close()
        await shutdown_event_bus()
        logger.info("Worker Queue connection pool closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker Daemon interrupted and stopped by user.")
