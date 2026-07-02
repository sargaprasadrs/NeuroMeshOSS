import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI
from src.main import create_app
from src.adapters.database.session import get_db_session
from src.core.ports.queue import IJobQueue, IEventBus


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Overrides the default pytest-asyncio loop to preserve session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Fixture providing a mocked SQLAlchemy AsyncSession."""
    session = AsyncMock()
    # Mocking standard SQLAlchemy methods
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_job_queue() -> AsyncMock:
    """Fixture providing a mocked Redis Job Queue."""
    queue = AsyncMock(spec=IJobQueue)
    queue.enqueue.return_value = "msg_12345"
    queue.listen = AsyncMock()
    queue.close = AsyncMock()
    return queue


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Fixture providing a mocked Redis Event Bus."""
    bus = AsyncMock(spec=IEventBus)
    bus.publish = AsyncMock()
    bus.subscribe = AsyncMock()
    bus.close = AsyncMock()
    return bus


@pytest.fixture
def test_app(mock_db_session: AsyncMock, mock_job_queue: AsyncMock, mock_event_bus: AsyncMock) -> FastAPI:
    """FastAPI application fixture with database and queue dependencies mocked."""
    app = create_app()

    # Override the database session dependency
    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    # Inject mock queues into app state singletons
    app.state.job_queue = mock_job_queue
    app.state.event_bus = mock_event_bus

    return app


from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """HTTP Client fixture for making asynchronous requests against test_app."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client
