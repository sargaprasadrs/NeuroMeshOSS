import argparse
import asyncio
import logging
from typing import Any, Dict
from src.adapters.queue.redis_queue import RedisJobQueue
from src.config.settings import settings

logger = logging.getLogger(__name__)


async def handle_workflow_job(payload: Dict[str, Any]) -> bool:
    """Orchestrates job state processing."""
    run_id = payload.get("run_id")
    workflow_id = payload.get("workflow_id")
    action = payload.get("action")
    correlation_id = payload.get("correlation_id", "N/A")
    logger.info(f"[Correlation ID: {correlation_id}] Worker received execution job. Run: {run_id}, Workflow: {workflow_id}, Action: {action}")
    
    # Stub: simulated node execution steps
    await asyncio.sleep(0.5)
    logger.info(f"[Correlation ID: {correlation_id}] Execution step complete for Run {run_id}")
    return True


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
        logger.info("Worker Queue connection pool closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker Daemon interrupted and stopped by user.")
