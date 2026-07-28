"""Tests for the Workflow Execution Engine."""

from uuid import uuid4
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.entities.run import Run, RunStep, RunStatus
from src.core.entities.workflow import Workflow, WorkflowDefinition, WorkflowNode, WorkflowEdge
from src.core.ports.repositories import IRunRepository
from src.core.ports.queue import IEventBus
from src.services.workflow_engine import WorkflowEngine


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def mock_run_repo() -> AsyncMock:
    repo = AsyncMock(spec=IRunRepository)
    repo.save = AsyncMock(side_effect=lambda run: run)
    repo.save_step = AsyncMock(side_effect=lambda step: step)
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    bus = AsyncMock(spec=IEventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def engine(mock_run_repo: AsyncMock, mock_event_bus: AsyncMock) -> WorkflowEngine:
    return WorkflowEngine(run_repo=mock_run_repo, event_bus=mock_event_bus)


def _make_workflow(nodes: list[dict], edges: list[dict]) -> Workflow:
    wf_nodes = [WorkflowNode(**n) for n in nodes]
    wf_edges = [WorkflowEdge(**e) for e in edges]
    return Workflow(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Workflow",
        definition=WorkflowDefinition(nodes=wf_nodes, edges=wf_edges),
    )


def _make_run(workflow: Workflow | None = None, **kwargs) -> Run:
    defaults = {
        "id": uuid4(),
        "workflow_id": workflow.id if workflow else uuid4(),
        "status": RunStatus.PENDING,
        "current_state": {},
        "version": 1,
    }
    defaults.update(kwargs)
    return Run(**defaults)


# ── DAG Traversal Tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_linear_dag_executes_all_nodes(engine: WorkflowEngine):
    """A -> B -> C linear chain executes all three nodes in order."""
    workflow = _make_workflow(
        nodes=[
            {"id": "A", "type": "agent", "data": {"agent_id": "agent1"}},
            {"id": "B", "type": "tool", "data": {"tool_name": "web_search"}},
            {"id": "C", "type": "agent", "data": {"agent_id": "agent2"}},
        ],
        edges=[
            {"source": "A", "target": "B"},
            {"source": "B", "target": "C"},
        ],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.SUCCESS
    assert "node_A_output" in result.current_state
    assert "node_B_output" in result.current_state
    assert "node_C_output" in result.current_state


@pytest.mark.asyncio
async def test_single_node_workflow(engine: WorkflowEngine):
    """Single node with no edges executes and completes."""
    workflow = _make_workflow(
        nodes=[{"id": "only", "type": "agent", "data": {"agent_id": "solo"}}],
        edges=[],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.SUCCESS
    assert "node_only_output" in result.current_state


@pytest.mark.asyncio
async def test_diamond_dag(engine: WorkflowEngine):
    """Diamond graph: A -> B, A -> C, B -> D, C -> D."""
    workflow = _make_workflow(
        nodes=[
            {"id": "A", "type": "agent", "data": {}},
            {"id": "B", "type": "tool", "data": {"tool_name": "t1"}},
            {"id": "C", "type": "tool", "data": {"tool_name": "t2"}},
            {"id": "D", "type": "agent", "data": {"agent_id": "final"}},
        ],
        edges=[
            {"source": "A", "target": "B"},
            {"source": "A", "target": "C"},
            {"source": "B", "target": "D"},
            {"source": "C", "target": "D"},
        ],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.SUCCESS
    assert "node_D_output" in result.current_state


@pytest.mark.asyncio
async def test_empty_graph_fails(engine: WorkflowEngine):
    """Empty workflow with no nodes should fail."""
    workflow = _make_workflow(nodes=[], edges=[])
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.FAILED


# ── Node Type Execution Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_node_returns_response(engine: WorkflowEngine):
    """Agent node produces a simulated LLM response."""
    workflow = _make_workflow(
        nodes=[{"id": "agent1", "type": "agent", "data": {"agent_id": "llama_8b"}}],
        edges=[],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    output = result.current_state["node_agent1_output"]
    assert output["agent_id"] == "llama_8b"
    assert "response" in output


@pytest.mark.asyncio
async def test_tool_node_returns_result(engine: WorkflowEngine):
    """Tool node produces a tool execution result."""
    workflow = _make_workflow(
        nodes=[{"id": "tool1", "type": "tool", "data": {"tool_name": "web_search"}}],
        edges=[],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    output = result.current_state["node_tool1_output"]
    assert output["tool_name"] == "web_search"
    assert "result" in output


@pytest.mark.asyncio
async def test_human_approval_pauses_run(engine: WorkflowEngine):
    """Human approval node pauses the run and returns PAUSED status."""
    workflow = _make_workflow(
        nodes=[
            {"id": "start", "type": "agent", "data": {"agent_id": "a1"}},
            {"id": "approve", "type": "human_approval", "data": {"role": "editor"}},
        ],
        edges=[{"source": "start", "target": "approve"}],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.PAUSED
    assert result.current_state.get("_paused_at_node") == "approve"


@pytest.mark.asyncio
async def test_unknown_node_type_passes_through(engine: WorkflowEngine):
    """Unknown node type uses the default pass-through executor."""
    workflow = _make_workflow(
        nodes=[{"id": "custom", "type": "custom_type", "data": {}}],
        edges=[],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.SUCCESS
    output = result.current_state["node_custom_output"]
    assert output["passthrough"] is True


# ── Edge Condition Tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_edge_condition_skip(engine: WorkflowEngine):
    """Edge with unmet condition is skipped, target node not executed."""
    workflow = _make_workflow(
        nodes=[
            {"id": "A", "type": "agent", "data": {}},
            {"id": "B", "type": "tool", "data": {"tool_name": "t1"}},
        ],
        edges=[
            {"source": "A", "target": "B", "condition": "needs_search"},
        ],
    )
    # State does not have "needs_search" set, so condition is falsy
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.SUCCESS
    assert "node_B_output" not in result.current_state
    assert result.current_state.get("node_B_skipped") is True


@pytest.mark.asyncio
async def test_edge_condition_met(engine: WorkflowEngine):
    """Edge with met condition executes the target node."""
    workflow = _make_workflow(
        nodes=[
            {"id": "A", "type": "agent", "data": {}},
            {"id": "B", "type": "tool", "data": {"tool_name": "t1"}},
        ],
        edges=[
            {"source": "A", "target": "B", "condition": "needs_search"},
        ],
    )
    # Pre-set state to satisfy the condition
    run = _make_run(workflow, current_state={"needs_search": True})

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.SUCCESS
    assert "node_B_output" in result.current_state


# ── Input Gathering Tests ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_node_receives_predecessor_outputs(engine: WorkflowEngine):
    """Node B receives node A's output as input."""
    workflow = _make_workflow(
        nodes=[
            {"id": "A", "type": "agent", "data": {"agent_id": "producer"}},
            {"id": "B", "type": "tool", "data": {"tool_name": "consumer"}},
        ],
        edges=[{"source": "A", "target": "B"}],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow)

    # B's output should contain the arguments from A's output
    b_output = result.current_state["node_B_output"]
    assert "A" in b_output.get("arguments", {})


# ── Step Persistence Tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_steps_saved_to_repo(engine: WorkflowEngine, mock_run_repo: AsyncMock):
    """Each executed node produces a RunStep saved to the repository."""
    workflow = _make_workflow(
        nodes=[
            {"id": "X", "type": "agent", "data": {}},
            {"id": "Y", "type": "tool", "data": {"tool_name": "t"}},
        ],
        edges=[{"source": "X", "target": "Y"}],
    )
    run = _make_run(workflow)

    await engine.execute_run(run, workflow)

    assert mock_run_repo.save_step.call_count == 2


# ── Event Publishing Tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_events_published(engine: WorkflowEngine, mock_event_bus: AsyncMock):
    """Engine publishes RUN_UPDATED, NODE_COMPLETED, and RUN_COMPLETED events."""
    workflow = _make_workflow(
        nodes=[{"id": "n1", "type": "agent", "data": {}}],
        edges=[],
    )
    run = _make_run(workflow)

    await engine.execute_run(run, workflow)

    event_types = [call.kwargs.get("event_type") or (call.args[1] if len(call.args) > 1 else None) for call in mock_event_bus.publish.call_args_list]
    assert "RUN_UPDATED" in event_types
    assert "NODE_COMPLETED" in event_types
    assert "RUN_COMPLETED" in event_types


@pytest.mark.asyncio
async def test_paused_run_publishes_run_paused_event(engine: WorkflowEngine, mock_event_bus: AsyncMock):
    """Human approval node publishes RUN_PAUSED event."""
    workflow = _make_workflow(
        nodes=[{"id": "h", "type": "human_approval", "data": {"role": "editor"}}],
        edges=[],
    )
    run = _make_run(workflow)

    await engine.execute_run(run, workflow)

    event_types = [call.kwargs.get("event_type") or (call.args[1] if len(call.args) > 1 else None) for call in mock_event_bus.publish.call_args_list]
    assert "RUN_PAUSED" in event_types


# ── Condition Evaluation Unit Tests ───────────────────────────────────────


def test_evaluate_condition_boolean_key(engine: WorkflowEngine):
    state = {"needs_search": True}
    assert engine._evaluate_condition("needs_search", state) is True


def test_evaluate_condition_negation(engine: WorkflowEngine):
    state = {"cancelled": False}
    assert engine._evaluate_condition("!cancelled", state) is True
    assert engine._evaluate_condition("!cancelled", {"cancelled": True}) is False


def test_evaluate_condition_equality(engine: WorkflowEngine):
    state = {"status": "success"}
    assert engine._evaluate_condition("status=success", state) is True
    assert engine._evaluate_condition("status=failed", state) is False


def test_evaluate_condition_missing_key(engine: WorkflowEngine):
    state = {}
    assert engine._evaluate_condition("missing", state) is False
    assert engine._evaluate_condition("!missing", state) is True


# ── Resume After Approval Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_resume_after_human_approval(engine: WorkflowEngine, mock_run_repo: AsyncMock):
    """After human approval, engine resumes from the paused node and completes."""
    workflow = _make_workflow(
        nodes=[
            {"id": "A", "type": "agent", "data": {"agent_id": "a1"}},
            {"id": "H", "type": "human_approval", "data": {"role": "editor"}},
            {"id": "B", "type": "tool", "data": {"tool_name": "t1"}},
        ],
        edges=[
            {"source": "A", "target": "H"},
            {"source": "H", "target": "B"},
        ],
    )
    # Simulate a paused run with approval data already in state
    run = _make_run(
        workflow,
        current_state={
            "node_A_output": {"response": "done"},
            "node_A_status": "SUCCESS",
            "approval_H": {"approved": True, "comment": "Looks good"},
            "_paused_at_node": "H",
        },
    )

    result = await engine.execute_run(run, workflow, start_node_id="H")

    assert result.status == RunStatus.SUCCESS
    assert "node_H_output" in result.current_state
    assert "node_B_output" in result.current_state


@pytest.mark.asyncio
async def test_resume_invalid_node_id_fails(engine: WorkflowEngine):
    """Resuming from a non-existent node ID should fail."""
    workflow = _make_workflow(
        nodes=[{"id": "A", "type": "agent", "data": {}}],
        edges=[],
    )
    run = _make_run(workflow)

    result = await engine.execute_run(run, workflow, start_node_id="nonexistent")

    assert result.status == RunStatus.FAILED
    assert "not found" in result.current_state.get("error", "")


# ── Run/Workflow Mismatch Test ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mismatched_run_workflow_fails(engine: WorkflowEngine):
    """Run with wrong workflow_id should fail validation."""
    workflow = _make_workflow(
        nodes=[{"id": "A", "type": "agent", "data": {}}],
        edges=[],
    )
    run = _make_run()  # No workflow passed → random workflow_id

    result = await engine.execute_run(run, workflow)

    assert result.status == RunStatus.FAILED
    assert "mismatch" in result.current_state.get("error", "").lower()
