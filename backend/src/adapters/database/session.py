import logging
import socket
from collections.abc import AsyncGenerator
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.config.settings import settings

logger = logging.getLogger(__name__)

# Check if PostgreSQL is reachable; otherwise fallback to local SQLite
db_url = settings.DATABASE_URL
use_sqlite = False

if "postgresql" in db_url.lower():
    try:
        parsed = urlparse(db_url)
        # Attempt a quick TCP connection to test availability
        s = socket.create_connection((parsed.hostname, parsed.port or 5432), timeout=1.0)
        s.close()
        logger.info("Successfully connected to PostgreSQL container database.")
    except Exception:
        logger.warning("PostgreSQL database is unreachable. Falling back to local SQLite (neuromesh.db).")
        use_sqlite = True
        db_url = "sqlite+aiosqlite:///neuromesh.db"

# Configure async engine
if use_sqlite:
    engine = create_async_engine(
        db_url,
        echo=settings.DEBUG,
    )
else:
    engine = create_async_engine(
        db_url,
        pool_size=20,
        max_overflow=10,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injector yield loop for FastAPI endpoint requests."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Only commit if there are active changes in the session
            if session.new or session.dirty or session.deleted:
                await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
