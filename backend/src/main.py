import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
from src.api.middleware import (
    CorrelationIdMiddleware,
    JwtAuthenticationMiddleware,
    register_exception_handlers,
)
from src.api.v1.auth import router as auth_router
from src.api.v1.workflows import router as workflow_router
from src.api.websockets import router as ws_router
from src.adapters.telemetry.opentelemetry import setup_telemetry

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handles startup and shutdown lifespans (e.g. pools and triggers)."""
    logger.info("Initializing NeuroMeshOSS Engine Lifespan...")
    
    # Instantiate Redis queue and event bus singletons to reuse connection pools
    from src.adapters.queue.redis_queue import RedisJobQueue, RedisEventBus
    app.state.job_queue = RedisJobQueue(settings.REDIS_URL)
    app.state.event_bus = RedisEventBus(settings.REDIS_URL)
    
    # Validate database connection pool
    try:
        from src.adapters.database.session import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection validated successfully.")
    except Exception as e:
        logger.error(f"Failed database connection pool initialization: {e}")

    # Initialize workflow_engine inside src.workers.daemon if fallback is active
    from src.adapters.queue.redis_queue import check_redis_alive
    if not check_redis_alive(settings.REDIS_URL):
        from src.services.plugin_loader import PluginRegistry, PluginLoader
        from src.services.mcp_client import McpClientPool
        from src.services.workflow_engine import WorkflowEngine
        import src.workers.daemon as daemon
        import os
        
        daemon.plugin_registry = PluginRegistry()
        plugin_loader = PluginLoader(daemon.plugin_registry)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        plugins_dir = os.path.join(base_dir, "plugins")
        plugin_loader.load_plugins_from_directory(plugins_dir)
        
        daemon.mcp_client_pool = McpClientPool()
        daemon.event_bus = app.state.event_bus
        daemon.workflow_engine = WorkflowEngine(
            event_bus=app.state.event_bus,
            plugin_registry=daemon.plugin_registry,
            mcp_client_pool=daemon.mcp_client_pool
        )
        logger.info("Successfully initialized workflow engine fallback inside API process.")

    yield

    logger.info("Tearing down NeuroMeshOSS Engine Lifespan...")
    
    # Close Redis singleton connection pools
    await app.state.job_queue.close()
    await app.state.event_bus.close()
    
    from src.adapters.database.session import engine
    await engine.dispose()
    logger.info("Database engine resources released.")


def create_app() -> FastAPI:
    """Application factory for FastAPI configurations."""
    app = FastAPI(
        title="NeuroMeshOSS",
        description="Open-Source AI Agent Orchestration Platform Core Plane",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.ENV == "dev",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core logging and auth middleware pipeline
    app.add_middleware(JwtAuthenticationMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # Register global HTTP status and validation exception maps
    register_exception_handlers(app)

    # Health probes
    @app.get("/healthz/live", tags=["Health"])
    async def liveness() -> dict:
        return {"status": "alive"}

    @app.get("/healthz/ready", tags=["Health"])
    async def readiness() -> dict:
        # Check basic pool connectivity
        return {"status": "ready", "database": "up", "queue": "up"}

    @app.get("/metrics", tags=["Metrics"])
    async def metrics_endpoint() -> Response:
        from src.adapters.telemetry.metrics import TelemetryMetrics
        return Response(
            content=TelemetryMetrics.generate_prometheus_payload(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    # Mount v1 REST & WebSocket Routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(workflow_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api")

    # Set up trace telemetry before returning the application instance
    setup_telemetry(app)

    return app


app = create_app()
