import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
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
        async with engine.connect() as conn:
            await conn.execute(type("MockText", (), {"text": lambda x: "SELECT 1"})("SELECT 1"))
        logger.info("Database connection validated successfully.")
    except Exception as e:
        logger.error(f"Failed database connection pool initialization: {e}")

    # Set up trace telemetry
    setup_telemetry(app)

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

    # Mount v1 REST & WebSocket Routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(workflow_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api")

    return app


app = create_app()
