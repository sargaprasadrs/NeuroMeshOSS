from uuid import uuid4
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.entities.user import User
from src.core.entities.workflow import Workflow, WorkflowDefinition
from src.core.entities.run import Run, RunStatus
from src.adapters.database.repositories import (
    SqlAlchemyUserRepository,
    SqlAlchemyWorkflowRepository,
    SqlAlchemyRunRepository,
)
from src.adapters.database.models import UserModel, WorkflowModel, RunModel


@pytest.mark.asyncio
async def test_user_repository_save(mock_db_session: AsyncMock):
    repo = SqlAlchemyUserRepository(mock_db_session)
    user = User(
        id=uuid4(),
        email="test@neuromesh.org",
        password_hash="hashed_bytes_string",
    )
    
    # Mocking get method to return None (simulating new insertion)
    mock_db_session.get.return_value = None
    
    saved_user = await repo.save(user)
    
    assert saved_user.email == user.email
    mock_db_session.add.assert_called_once()
    mock_db_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_repository_get_by_id(mock_db_session: AsyncMock):
    repo = SqlAlchemyWorkflowRepository(mock_db_session)
    workflow_id = uuid4()
    user_id = uuid4()
    
    # Set up mock SQLAlchemy DB record
    mock_db_session.get.return_value = WorkflowModel(
        id=workflow_id,
        user_id=user_id,
        name="Test Market Flow",
        definition={"nodes": [], "edges": []},
        is_active=True,
        version=1,
    )
    
    workflow = await repo.get_by_id(workflow_id)
    
    assert workflow is not None
    assert workflow.id == workflow_id
    assert workflow.name == "Test Market Flow"
    assert len(workflow.definition.nodes) == 0


@pytest.mark.asyncio
async def test_run_repository_concurrency_check(mock_db_session: AsyncMock):
    repo = SqlAlchemyRunRepository(mock_db_session)
    run_id = uuid4()
    
    # Set up active database state with version=1
    mock_model = RunModel(
        id=run_id,
        workflow_id=uuid4(),
        status="PENDING",
        current_state={},
        version=1,
    )
    mock_db_session.get.return_value = mock_model
    
    # Domain run payload with version=2 (concurrency mismatch)
    run_payload = Run(
        id=run_id,
        workflow_id=mock_model.workflow_id,
        status=RunStatus.RUNNING,
        current_state={},
        version=2, # Concurrency collision trigger
    )
    
    with pytest.raises(ValueError, match="Concurrency collision"):
        await repo.save(run_payload)
