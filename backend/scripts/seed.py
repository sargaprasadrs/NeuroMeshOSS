"""NeuroMeshOSS Database Seeder

Populates the local PostgreSQL with a default admin user and a sample
"Market Analyzer Agent Flow" workflow for development and testing.

Usage:
    cd backend
    poetry run python scripts/seed.py

What this script does:
    1. Creates all required database tables (if they don't exist) using
       SQLAlchemy's Base.metadata.create_all().
    2. Inserts a default admin user (admin@neuromesh.com) if not present.
    3. Creates a sample 4-node DAG workflow with Researcher -> Web Search ->
       Writer -> Human Approval nodes.

Default Credentials:
    Email:    admin@neuromesh.com
    Password: admin_secure_password_123

Notes:
    - This script is idempotent — running it multiple times is safe.
    - Requires PostgreSQL to be running locally (via `docker compose up -d`).
    - Uses sys.path manipulation to allow direct execution without PYTHONPATH.
"""

import asyncio
import logging
import sys
import os
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure the backend directory is on the Python path so that imports from
# src.* work when running as `python scripts/seed.py` directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters.database.session import engine, AsyncSessionLocal
from src.adapters.database.models import Base, UserModel, WorkflowModel
from src.services.auth_service import AuthService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed")

# Default User and Workflow definitions
DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000000")
DEFAULT_USER_EMAIL = "admin@neuromesh.com"
DEFAULT_USER_PASSWORD = "admin_secure_password_123"

SAMPLE_WORKFLOW_ID = UUID("11111111-1111-1111-1111-111111111111")
SAMPLE_WORKFLOW_NAME = "Market Analyzer Agent Flow"
SAMPLE_WORKFLOW_DEF = {
    "nodes": [
        {"id": "node_1", "type": "agent", "data": {"agent_id": "researcher_llama"}},
        {"id": "node_2", "type": "tool", "data": {"tool_name": "web_search"}},
        {"id": "node_3", "type": "agent", "data": {"agent_id": "writer_llama"}},
        {"id": "node_4", "type": "human_approval", "data": {"role": "editor"}},
    ],
    "edges": [
        {"source": "node_1", "target": "node_2", "condition": "needs_search"},
        {"source": "node_2", "target": "node_3"},
        {"source": "node_3", "target": "node_4"},
    ]
}


async def seed_data() -> None:
    # Create all tables if they don't exist yet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")

    async with AsyncSessionLocal() as session:
        try:
            logger.info("Starting database seeding...")
            
            # 1. Create default user if not exists
            user = await session.get(UserModel, DEFAULT_USER_ID)
            if not user:
                hashed_pwd = AuthService.get_password_hash(DEFAULT_USER_PASSWORD)
                user = UserModel(
                    id=DEFAULT_USER_ID,
                    email=DEFAULT_USER_EMAIL,
                    password_hash=hashed_pwd,
                    is_active=True,
                    role="admin"
                )
                session.add(user)
                logger.info(f"Created default user: {DEFAULT_USER_EMAIL}")
            else:
                logger.info(f"Default user {DEFAULT_USER_EMAIL} already exists.")
            
            # 2. Create sample workflow if not exists
            workflow = await session.get(WorkflowModel, SAMPLE_WORKFLOW_ID)
            if not workflow:
                workflow = WorkflowModel(
                    id=SAMPLE_WORKFLOW_ID,
                    user_id=DEFAULT_USER_ID,
                    name=SAMPLE_WORKFLOW_NAME,
                    definition=SAMPLE_WORKFLOW_DEF,
                    is_active=True,
                    version=1
                )
                session.add(workflow)
                logger.info(f"Created sample workflow: {SAMPLE_WORKFLOW_NAME}")
            else:
                logger.info(f"Sample workflow {SAMPLE_WORKFLOW_NAME} already exists.")
                
            await session.commit()
            logger.info("Database seeding completed successfully.")
            
        except Exception as e:
            logger.error(f"Error occurred during database seeding: {e}", exc_info=True)
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_data())
