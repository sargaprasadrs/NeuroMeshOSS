import argparse
import asyncio
import logging
import os
import sys
from typing import Any, Dict
from uuid import UUID

from src.adapters.queue.redis_queue import RedisJobQueue, RedisEventBus
from src.config.settings import settings
from src.services.plugin_loader import PluginRegistry, PluginLoader
from src.services.mcp_client import McpClientPool
from src.services.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)

# Global instances initialized in main()
event_bus = None
plugin_registry = None
mcp_client_pool = None
workflow_engine = None


async def handle_workflow_job(payload: Dict[str, Any]) -> bool:
    """Orchestrates job state processing using the WorkflowEngine."""
    run_id_str = payload.get("run_id")
    workflow_id_str = payload.get("workflow_id")
    action = payload.get("action", "START")
    step_id = payload.get("step_id")
    approval_data = payload.get("approval_data")
    correlation_id = payload.get("correlation_id", "N/A")
    
    if not run_id_str or not workflow_id_str:
        logger.error(f"[Correlation ID: {correlation_id}] Missing run_id or workflow_id in job payload: {payload}")
        return False
        
    try:
        run_id = UUID(run_id_str)
        workflow_id = UUID(workflow_id_str)
    except ValueError as e:
        logger.error(f"[Correlation ID: {correlation_id}] Invalid UUID in payload: {e}")
        return False

    logger.info(f"[Correlation ID: {correlation_id}] Worker received execution job. Run: {run_id}, Workflow: {workflow_id}, Action: {action}")
    
    global workflow_engine
    if workflow_engine is None:
        logger.error("WorkflowEngine not initialized in worker daemon.")
        return False
        
    # Execute the workflow run
    success = await workflow_engine.execute(
        run_id=run_id,
        workflow_id=workflow_id,
        action=action,
        step_id=step_id,
        approval_data=approval_data,
        correlation_id=correlation_id,
    )
    return success


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

    # Initialize dependencies for WorkflowEngine
    global event_bus, plugin_registry, mcp_client_pool, workflow_engine
    event_bus = RedisEventBus(settings.REDIS_URL)
    plugin_registry = PluginRegistry()
    
    # Load plugins dynamically from workspace
    plugin_loader = PluginLoader(plugin_registry)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    plugins_dir = os.path.join(base_dir, "plugins")
    logger.info(f"Scanning and loading plugins from: {plugins_dir}")
    plugin_loader.load_plugins_from_directory(plugins_dir)
    
    mcp_client_pool = McpClientPool()
    
    workflow_engine = WorkflowEngine(
        event_bus=event_bus,
        plugin_registry=plugin_registry,
        mcp_client_pool=mcp_client_pool,
    )

    # Graceful shutdown handler registration
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
        logger.info("Closing Worker Queue and Event Bus connection pools...")
        await job_queue.close()
        await event_bus.close()
        logger.info("Worker connections closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker Daemon interrupted and stopped by user.")
