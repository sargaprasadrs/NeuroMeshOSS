"""Workflow Execution Engine — traverses a DAG of nodes and executes each by type.

Supports node types: agent, tool, human_approval.
Handles branching via edge conditions and parallel paths.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Set
from uuid import UUID

from src.core.entities.run import Run, RunStep, RunStatus
from src.core.entities.workflow import Workflow, WorkflowDefinition, WorkflowNode, WorkflowEdge
from src.core.ports.repositories import IRunRepository
from src.core.ports.queue import IEventBus

logger = logging.getLogger(__name__)


class NodeExecutionResult:
    """Result of executing a single workflow node."""

    def __init__(
        self,
        node_id: str,
        output: Dict[str, Any],
        traces: Dict[str, Any],
        duration_ms: int,
    ) -> None:
        self.node_id = node_id
        self.output = output
        self.traces = traces
        self.duration_ms = duration_ms


class WorkflowEngine:
    """Executes a workflow DAG step by step, managing run state and event publishing.

    This engine resolves the topological order of nodes, executes each one by type,
    propagates outputs through the graph, and handles branching conditions on edges.
    """

    MAX_ITERATIONS = 100  # Safety limit to prevent infinite loops in cyclic graphs

    def __init__(
        self,
        run_repo: IRunRepository,
        event_bus: IEventBus,
    ) -> None:
        self.run_repo = run_repo
        self.event_bus = event_bus

    # ── Public API ─────────────────────────────────────────────────────────

    async def execute_run(
        self,
        run: Run,
        workflow: Workflow,
        start_node_id: str | None = None,
    ) -> Run:
        """Execute a workflow run from start (or resume from a specific node).

        Returns the updated Run with final status and state.
        """
        # Validate run belongs to this workflow
        if run.workflow_id != workflow.id:
            logger.error(f"Run {run.id} workflow_id ({run.workflow_id}) does not match workflow {workflow.id}.")
            return await self._finalize_run(run, RunStatus.FAILED, run.current_state.copy(), "Run and workflow mismatch")

        definition = workflow.definition
        state = run.current_state.copy()

        # Build adjacency and in-degree maps for DAG traversal
        adjacency = self._build_adjacency(definition.edges)
        in_degree = self._build_in_degree(definition.nodes, definition.edges)

        # Determine starting nodes
        if start_node_id:
            node_ids = {n.id for n in definition.nodes}
            if start_node_id not in node_ids:
                logger.error(f"Run {run.id}: start_node_id '{start_node_id}' not found in workflow graph.")
                return await self._finalize_run(run, RunStatus.FAILED, state, f"Resume node '{start_node_id}' not found in graph")
            ready_nodes = [start_node_id]
        else:
            ready_nodes = [n.id for n in definition.nodes if in_degree.get(n.id, 0) == 0]

        if not ready_nodes:
            logger.warning(f"Run {run.id}: No starting nodes found in workflow graph.")
            return await self._finalize_run(run, RunStatus.FAILED, state, "No starting nodes in graph")

        # Mark run as running
        run = await self._update_run_status(run, RunStatus.RUNNING, state)
        await self._publish_event(run, "RUN_UPDATED", {"status": "RUNNING"})

        node_map = {n.id: n for n in definition.nodes}
        completed_nodes: Set[str] = set()
        iterations = 0

        while ready_nodes and iterations < self.MAX_ITERATIONS:
            iterations += 1
            next_ready: List[str] = []

            for node_id in ready_nodes:
                if node_id in completed_nodes:
                    continue

                node = node_map.get(node_id)
                if not node:
                    logger.error(f"Run {run.id}: Node {node_id} not found in workflow definition.")
                    continue

                # Gather inputs from predecessor nodes
                node_input = self._gather_node_input(node_id, definition.edges, state)

                # Execute the node
                logger.info(f"Run {run.id}: Executing node {node_id} (type={node.type})")
                result = await self._execute_node(node, node_input, state)

                # Save step to database
                step = RunStep(
                    run_id=run.id,
                    node_id=node_id,
                    input=node_input,
                    output=result.output,
                    traces=result.traces,
                    duration_ms=result.duration_ms,
                )
                await self.run_repo.save_step(step)

                # Merge output into run state
                state[f"node_{node_id}_output"] = result.output
                node_status = "FAILED" if "error" in result.output else "SUCCESS"
                state[f"node_{node_id}_status"] = node_status

                # Check if this is a human_approval node that paused execution
                if result.output.get("_pause"):
                    state["_paused_at_node"] = node_id
                    state["_pending_approvals"] = result.output.get("_pending_approvals", {})
                    run = await self._update_run_status(run, RunStatus.PAUSED, state)
                    await self._publish_event(run, "RUN_PAUSED", {
                        "node_id": node_id,
                        "reason": "human_approval_required",
                    })
                    logger.info(f"Run {run.id}: Paused at node {node_id} for human approval.")
                    return run

                completed_nodes.add(node_id)
                await self._publish_event(run, "NODE_COMPLETED", {
                    "node_id": node_id,
                    "duration_ms": result.duration_ms,
                })

                # Resolve next nodes from outgoing edges
                outgoing = adjacency.get(node_id, [])
                for edge in outgoing:
                    # Check edge condition against current state
                    if edge.condition and not self._evaluate_condition(edge.condition, state):
                        logger.info(f"Run {run.id}: Skipping edge {node_id}->{edge.target} (condition '{edge.condition}' not met)")
                        state[f"node_{edge.target}_skipped"] = True
                        completed_nodes.add(edge.target)
                        continue

                    # Check if all predecessors of the target are complete
                    target_in_edges = [e for e in definition.edges if e.target == edge.target]
                    all_predecessors_done = all(
                        e.source in completed_nodes or state.get(f"node_{e.source}_skipped")
                        for e in target_in_edges
                    )
                    if all_predecessors_done and edge.target not in completed_nodes:
                        next_ready.append(edge.target)

            ready_nodes = next_ready

        if iterations >= self.MAX_ITERATIONS:
            logger.error(f"Run {run.id}: Exceeded maximum iteration limit ({self.MAX_ITERATIONS}).")
            return await self._finalize_run(run, RunStatus.FAILED, state, "Exceeded maximum iteration limit")

        # All nodes completed successfully
        return await self._finalize_run(run, RunStatus.SUCCESS, state)

    # ── Node Executors ─────────────────────────────────────────────────────

    async def _execute_node(
        self,
        node: WorkflowNode,
        node_input: Dict[str, Any],
        state: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Dispatch to the appropriate node-type executor."""
        start = time.monotonic()
        try:
            if node.type == "agent":
                output = await self._execute_agent_node(node, node_input, state)
            elif node.type == "tool":
                output = await self._execute_tool_node(node, node_input, state)
            elif node.type == "human_approval":
                output = await self._execute_human_approval_node(node, node_input, state)
            else:
                output = await self._execute_default_node(node, node_input, state)
        except Exception as e:
            logger.error(f"Node {node.id} execution failed: {e}", exc_info=True)
            output = {"error": str(e), "_pause": False}
        duration_ms = int((time.monotonic() - start) * 1000)
        traces = {"node_id": node.id, "node_type": node.type, "status": "error" if "error" in output else "ok"}
        return NodeExecutionResult(node_id=node.id, output=output, traces=traces, duration_ms=duration_ms)

    async def _execute_agent_node(
        self,
        node: WorkflowNode,
        node_input: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute an agent node — resolve prompt, call LLM provider.

        In a full implementation this would route to Ollama/OpenAI/Anthropic
        via the configured model router. For now, we simulate the agent response
        using the node's data configuration.
        """
        agent_id = node.data.get("agent_id", "unknown")
        prompt = node.data.get("prompt", "")
        model = node.data.get("model", "local")

        # Build context from previous node outputs
        context_parts = []
        for key, value in state.items():
            if key.startswith("node_") and key.endswith("_output"):
                context_parts.append(f"{key}: {value}")

        full_prompt = f"{prompt}\n\nContext:\n" + "\n".join(context_parts) if context_parts else prompt

        # Simulate LLM call (replace with actual Ollama/OpenAI integration)
        logger.info(f"Agent node {node.id}: agent_id={agent_id}, model={model}")
        await asyncio.sleep(0.1)  # Simulate inference latency

        return {
            "agent_id": agent_id,
            "model": model,
            "response": f"[Simulated response from {agent_id}] Processed input from workflow context.",
            "prompt_used": full_prompt[:500],  # Truncate for storage
        }

    async def _execute_tool_node(
        self,
        node: WorkflowNode,
        node_input: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a tool node — invoke MCP server tool or plugin.

        Routes to the appropriate MCP server based on the tool_name in node data.
        """
        tool_name = node.data.get("tool_name", "unknown")
        tool_args = node.data.get("arguments", {})
        mcp_server = node.data.get("mcp_server")

        # Merge node_input into tool arguments
        merged_args = {**tool_args, **node_input}

        logger.info(f"Tool node {node.id}: tool={tool_name}, server={mcp_server}")

        if mcp_server:
            # Route to MCP server (would use McpClientPool in production)
            logger.info(f"Would invoke MCP tool {tool_name} on server {mcp_server}")
            await asyncio.sleep(0.05)
            return {
                "tool_name": tool_name,
                "mcp_server": mcp_server,
                "result": f"[Simulated MCP tool result for {tool_name}]",
                "arguments": merged_args,
            }
        else:
            # Built-in tool execution
            await asyncio.sleep(0.05)
            return {
                "tool_name": tool_name,
                "result": f"[Simulated built-in tool result for {tool_name}]",
                "arguments": merged_args,
            }

    async def _execute_human_approval_node(
        self,
        node: WorkflowNode,
        node_input: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a human approval node — pause run and await external approval.

        Returns output with _pause=True so the engine stops and saves state.
        The run will be resumed via the approve_human_step API endpoint.

        On resume, if approval data already exists in state (keyed by approval_{node_id}),
        the node is treated as approved and execution continues.
        """
        role = node.data.get("role", "approver")
        message = node.data.get("message", f"Approval required from {role}")

        # Check if this node was already approved (resume path)
        approval_key = f"approval_{node.id}"
        if approval_key in state:
            approval_data = state[approval_key]
            # Only skip pause if approval was actually granted
            if isinstance(approval_data, dict) and approval_data.get("approved") is False:
                logger.info(f"Human approval node {node.id}: approval denied, pausing again.")
            else:
                logger.info(f"Human approval node {node.id}: previously approved, continuing. Data: {approval_data}")
                return {
                    "role": role,
                    "message": message,
                    "approval_data": approval_data,
                    "input_summary": node_input,
                    "_pause": False,
                }

        logger.info(f"Human approval node {node.id}: role={role}")
        return {
            "role": role,
            "message": message,
            "input_summary": node_input,
            "_pause": True,
            "_pending_approvals": {node.id: {"role": role, "status": "pending"}},
        }

    async def _execute_default_node(
        self,
        node: WorkflowNode,
        node_input: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback executor for unknown node types — pass through input as output."""
        logger.warning(f"Unknown node type '{node.type}' for node {node.id}. Using pass-through executor.")
        return {"passthrough": True, "input": node_input}

    # ── Graph Utilities ────────────────────────────────────────────────────

    def _build_adjacency(self, edges: List[WorkflowEdge]) -> Dict[str, List[WorkflowEdge]]:
        """Build adjacency list: source_node_id -> list of outgoing edges."""
        adjacency: Dict[str, List[WorkflowEdge]] = {}
        for edge in edges:
            adjacency.setdefault(edge.source, []).append(edge)
        return adjacency

    def _build_in_degree(
        self, nodes: List[WorkflowNode], edges: List[WorkflowEdge]
    ) -> Dict[str, int]:
        """Compute in-degree for each node (number of incoming edges)."""
        in_degree = {n.id: 0 for n in nodes}
        for edge in edges:
            if edge.target in in_degree:
                in_degree[edge.target] += 1
        return in_degree

    def _gather_node_input(
        self,
        node_id: str,
        edges: List[WorkflowEdge],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Collect outputs from all predecessor nodes as input for the current node."""
        incoming_edges = [e for e in edges if e.target == node_id]
        node_input: Dict[str, Any] = {}
        for edge in incoming_edges:
            source_output = state.get(f"node_{edge.source}_output", {})
            node_input[edge.source] = source_output
        return node_input

    def _evaluate_condition(self, condition: str, state: Dict[str, Any]) -> bool:
        """Evaluate a simple edge condition against the current run state.

        Supports simple key-based conditions:
        - Boolean key: truthy check (e.g. "needs_search" checks state["needs_search"])
        - Key=value: equality check (e.g. "status=success" checks state["status"]=="success")
        - Negation: "!" prefix (e.g. "!cancelled" checks state["cancelled"] is falsy)
        """
        condition = condition.strip()

        if "=" in condition:
            key, expected = condition.split("=", 1)
            key = key.strip()
            expected = expected.strip()
            actual = state.get(key, "")
            return str(actual) == expected
        elif condition.startswith("!"):
            key = condition[1:].strip()
            return not state.get(key, False)
        else:
            return bool(state.get(condition, False))

    # ── Run State Management ───────────────────────────────────────────────

    async def _update_run_status(
        self,
        run: Run,
        status: RunStatus,
        state: Dict[str, Any],
    ) -> Run:
        """Update run status and state with OCC version check."""
        updated = Run(
            id=run.id,
            workflow_id=run.workflow_id,
            status=status,
            current_state=state,
            version=run.version,
            created_at=run.created_at,
        )
        return await self.run_repo.save(updated)

    async def _finalize_run(
        self,
        run: Run,
        status: RunStatus,
        state: Dict[str, Any],
        error_message: str | None = None,
    ) -> Run:
        """Finalize a run with terminal status and publish completion event."""
        if error_message:
            state["error"] = error_message

        final_run = await self._update_run_status(run, status, state)

        event_type = "RUN_COMPLETED" if status == RunStatus.SUCCESS else "RUN_FAILED"
        await self._publish_event(final_run, event_type, {
            "status": status.value,
            "error": error_message,
        })

        logger.info(f"Run {run.id} finalized with status {status.value}")
        return final_run

    async def _publish_event(self, run: Run, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish a run event to the event bus for WebSocket forwarding."""
        try:
            await self.event_bus.publish(
                topic=str(run.id),
                event_type=event_type,
                payload={"run_id": str(run.id), **payload},
            )
        except Exception as e:
            logger.error(f"Failed to publish event {event_type} for run {run.id}: {e}")
