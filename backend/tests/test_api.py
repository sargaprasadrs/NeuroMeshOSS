from uuid import uuid4
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from src.core.entities.workflow import Workflow, WorkflowDefinition
from src.core.entities.run import Run, RunStatus


@pytest.mark.asyncio
async def test_health_endpoints(async_client: AsyncClient):
    # Test liveness check
    response = await async_client.get("/healthz/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

    # Test readiness check
    response = await async_client.get("/healthz/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "up", "queue": "up"}


@pytest.mark.asyncio
async def test_metrics_endpoint(async_client: AsyncClient):
    response = await async_client.get("/metrics")
    assert response.status_code == 200
    assert "neuromesh_active_db_connections" in response.text


@pytest.mark.asyncio
async def test_create_workflow(async_client: AsyncClient, mock_db_session: AsyncMock):
    # Setup mock return values for repositories inside route
    # In workflows.py, SqlAlchemyWorkflowRepository.save is called.
    # We can mock session methods to prevent errors.
    mock_db_session.execute = AsyncMock()
    
    payload = {
        "name": "Test Market Analyzer Flow",
        "definition": {
            "nodes": [
                {"id": "node_1", "type": "agent", "data": {"agent_id": "llama_8b"}},
                {"id": "node_2", "type": "tool", "data": {"tool_name": "web_search"}}
            ],
            "edges": [
                {"source": "node_1", "target": "node_2"}
            ]
        }
    }
    
    response = await async_client.post("/api/v1/workflows/", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["name"] == "Test Market Analyzer Flow"
    assert "id" in res_data
    assert len(res_data["definition"]["nodes"]) == 2


@pytest.mark.asyncio
async def test_run_workflow(async_client: AsyncClient, mock_db_session: AsyncMock, mock_job_queue: AsyncMock):
    workflow_id = uuid4()
    run_id = uuid4()
    
    # Mocking the repository calls inside the route
    from src.adapters.database.models import WorkflowModel, RunModel
    mock_workflow_model = WorkflowModel(
        id=workflow_id,
        user_id=uuid4(),
        name="Test Flow",
        definition={"nodes": [], "edges": []},
        is_active=True,
        version=1
    )
    
    # Mock get workflow and save run
    mock_db_session.get = AsyncMock(side_effect=lambda model_class, ident: (
        mock_workflow_model if model_class == WorkflowModel else None
    ))
    
    response = await async_client.post(f"/api/v1/workflows/{workflow_id}/run")
    assert response.status_code == 200
    res_data = response.json()
    assert "run_id" in res_data
    assert res_data["workflow_id"] == str(workflow_id)
    assert res_data["status"] == "PENDING"
    
    # Verify job was enqueued in mock job queue
    mock_job_queue.enqueue.assert_called_once()
