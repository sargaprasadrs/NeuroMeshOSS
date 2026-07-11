import asyncio
import json
import logging
import time
from uuid import UUID, uuid4
from typing import Dict, Any, List

import httpx

from src.core.entities.run import Run, RunStep, RunStatus
from src.core.entities.workflow import Workflow
from src.core.ports.queue import IEventBus
from src.core.ports.plugins import IPluginRegistry
from src.services.mcp_client import McpClientPool
from src.config.settings import settings
from src.adapters.database.repositories import SqlAlchemyRunRepository, SqlAlchemyWorkflowRepository
from src.adapters.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(
        self,
        event_bus: IEventBus,
        plugin_registry: IPluginRegistry,
        mcp_client_pool: McpClientPool,
    ) -> None:
        self.event_bus = event_bus
        self.plugin_registry = plugin_registry
        self.mcp_client_pool = mcp_client_pool

    async def execute(
        self,
        run_id: UUID,
        workflow_id: UUID,
        action: str,
        step_id: str | None = None,
        approval_data: dict | None = None,
        correlation_id: str | None = None,
    ) -> bool:
        """Executes or resumes a workflow run."""
        correlation_id = correlation_id or "N/A"
        logger.info(f"[Correlation ID: {correlation_id}] Starting execution for Run {run_id}, Workflow {workflow_id}, Action {action}")
        
        async with AsyncSessionLocal() as session:
            run_repo = SqlAlchemyRunRepository(session)
            workflow_repo = SqlAlchemyWorkflowRepository(session)
            
            run = await run_repo.get_by_id(run_id)
            workflow = await workflow_repo.get_by_id(workflow_id)
            
            if not run or not workflow:
                logger.error(f"Run {run_id} or Workflow {workflow_id} not found in database.")
                return False

            # Set up or load execution state
            state = run.current_state or {}
            variables = state.get("variables", {})
            node_statuses = state.get("node_statuses", {})
            node_outputs = state.get("node_outputs", {})
            
            # Helper to check if a condition evaluates to true
            def evaluate_condition(condition: str | None, current_node_output: dict) -> bool:
                if not condition:
                    return True
                # Check current node output keys
                if current_node_output.get(condition):
                    return True
                # Check run variables keys
                if variables.get(condition):
                    return True
                # Check case-insensitive match in values
                cond_lower = condition.lower()
                for val in list(current_node_output.values()) + list(variables.values()):
                    if cond_lower in str(val).lower():
                        return True
                return False

            # Build dependency map (predecessors)
            predecessors: Dict[str, List[str]] = {node.id: [] for node in workflow.definition.nodes}
            nodes_by_id = {node.id: node for node in workflow.definition.nodes}
            
            for edge in workflow.definition.edges:
                if edge.target in predecessors:
                    predecessors[edge.target].append(edge.source)

            # Adjust state based on action
            if action == "RESUME":
                logger.info(f"[Correlation ID: {correlation_id}] Resuming run {run_id} at step/node {step_id}")
                
                # Update status of this approved node to SUCCESS
                if step_id and step_id in node_statuses:
                    node_statuses[step_id] = "SUCCESS"
                    node_outputs[step_id] = approval_data or {"approved": True}
                    variables[f"approval_{step_id}"] = approval_data or {"approved": True}
                    if approval_data:
                        variables.update(approval_data)
                else:
                    # Fallback: look for the first human_approval node in node_statuses with status PENDING or paused
                    for node in workflow.definition.nodes:
                        if node.type == "human_approval" and node_statuses.get(node.id) in ("PENDING", "PAUSED"):
                            node_statuses[node.id] = "SUCCESS"
                            node_outputs[node.id] = approval_data or {"approved": True}
                            variables[f"approval_{node.id}"] = approval_data or {"approved": True}
                            if approval_data:
                                variables.update(approval_data)
                            break

                # Set Run Status back to RUNNING
                run = Run(
                    id=run.id,
                    workflow_id=run.workflow_id,
                    status=RunStatus.RUNNING,
                    current_state={
                        "variables": variables,
                        "node_statuses": node_statuses,
                        "node_outputs": node_outputs,
                    },
                    version=run.version,
                    created_at=run.created_at,
                )
                await run_repo.save(run)
                await session.commit()
            
            elif action == "START":
                # Start nodes have no predecessors
                for node_id in predecessors:
                    if not predecessors[node_id]:
                        node_statuses[node_id] = "PENDING"
                
                run = Run(
                    id=run.id,
                    workflow_id=run.workflow_id,
                    status=RunStatus.RUNNING,
                    current_state={
                        "variables": variables,
                        "node_statuses": node_statuses,
                        "node_outputs": node_outputs,
                    },
                    version=run.version,
                    created_at=run.created_at,
                )
                await run_repo.save(run)
                await session.commit()
                
                await self.event_bus.publish(
                    topic=str(run.id),
                    event_type="RUN_RUNNING",
                    payload={"run_id": str(run.id), "status": RunStatus.RUNNING.value},
                )

            # Execution loop
            paused = False
            failed = False
            error_message = None
            
            while True:
                # Find all nodes that are PENDING and whose predecessors are fully resolved (SUCCESS or SKIPPED)
                nodes_to_execute = []
                for node_id, status in node_statuses.items():
                    if status == "PENDING":
                        # Check predecessors
                        preds = predecessors.get(node_id, [])
                        if all(node_statuses.get(p) in ("SUCCESS", "SKIPPED") for p in preds):
                            nodes_to_execute.append(nodes_by_id[node_id])
                
                if not nodes_to_execute:
                    # Check if there are any remaining nodes that can eventually run or if we're done
                    running_or_pending = any(status in ("PENDING", "RUNNING") for status in node_statuses.values())
                    if not running_or_pending:
                        break
                    else:
                        break

                for node in nodes_to_execute:
                    # Update status to RUNNING
                    node_statuses[node.id] = "RUNNING"
                    
                    # Persist run state
                    run = Run(
                        id=run.id,
                        workflow_id=run.workflow_id,
                        status=RunStatus.RUNNING,
                        current_state={
                            "variables": variables,
                            "node_statuses": node_statuses,
                            "node_outputs": node_outputs,
                        },
                        version=run.version,
                        created_at=run.created_at,
                    )
                    run = await run_repo.save(run)
                    await session.commit()
                    
                    # Notify node start
                    await self.event_bus.publish(
                        topic=str(run.id),
                        event_type="NODE_STARTED",
                        payload={"run_id": str(run.id), "node_id": node.id, "type": node.type},
                    )
                    
                    logger.info(f"[Correlation ID: {correlation_id}] Executing Node {node.id} ({node.type})")
                    start_time = time.time()
                    node_output = {}
                    node_input = {**variables}
                    
                    try:
                        if node.type == "agent":
                            agent_id = node.data.get("agent_id", "default_agent")
                            prompt = f"Executing Agent: {agent_id}\nCurrent Run State Variables:\n{json.dumps(variables, indent=2)}"
                            try:
                                async with httpx.AsyncClient(timeout=10.0) as client:
                                    response = await client.post(
                                        f"{settings.OLLAMA_HOST}/api/generate",
                                        json={
                                            "model": "llama3:8b",
                                            "prompt": prompt,
                                            "stream": False
                                        }
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        node_output = {"response": result.get("response", ""), "agent_id": agent_id}
                                        if "search" in result.get("response", "").lower():
                                            node_output["needs_search"] = True
                                    else:
                                        raise RuntimeError(f"Ollama server returned code {response.status_code}")
                            except Exception as ex:
                                logger.warning(f"Ollama agent call failed, falling back to mock: {ex}")
                                fallback_text = f"Mock response: Agent {agent_id} processed the input context successfully."
                                needs_search = False
                                if "researcher" in agent_id.lower() or "research" in agent_id.lower():
                                    fallback_text += " I need to execute a web search tool to find market trends."
                                    needs_search = True
                                node_output = {
                                    "response": fallback_text,
                                    "agent_id": agent_id,
                                    "needs_search": needs_search
                                }
                        
                        elif node.type == "tool":
                            tool_name = node.data.get("tool_name")
                            plugin = self.plugin_registry.get(tool_name)
                            if plugin:
                                if tool_name == "filesystem-tool":
                                    filepath = node.data.get("filepath", "local_test_file.txt")
                                    content = await plugin.read_file(filepath)
                                    node_output = {"status": "success", "content": content}
                                elif tool_name == "github-sync":
                                    repo_url = node.data.get("repo_url", "https://github.com/sargaprasadrs/NeuroMeshOSS")
                                    await plugin.sync_repository(repo_url)
                                    node_output = {"status": "success", "synced_url": repo_url}
                                elif tool_name == "slack-notification":
                                    channel = node.data.get("channel", "#general")
                                    text = node.data.get("text", f"Workflow notification for run {run.id}")
                                    await plugin.post_message(channel, text)
                                    node_output = {"status": "success", "channel": channel, "posted": True}
                                else:
                                    node_output = {"status": "success", "result": f"Executed tool plugin {tool_name}"}
                            else:
                                logger.info(f"Plugin {tool_name} not found, checking MCP or executing mock fallback.")
                                node_output = {
                                    "status": "success",
                                    "tool_name": tool_name,
                                    "result": f"Executed tool {tool_name} successfully."
                                }
                        
                        elif node.type == "human_approval":
                            logger.info(f"[Correlation ID: {correlation_id}] Reached human approval node {node.id}. Pausing workflow.")
                            node_statuses[node.id] = "PENDING"
                            paused = True
                            break
                        
                        else:
                            node_output = {"status": "success", "result": f"Processed custom node type {node.type}"}
                        
                        duration_ms = int((time.time() - start_time) * 1000)
                        
                        # Node completion updates
                        node_statuses[node.id] = "SUCCESS"
                        node_outputs[node.id] = node_output
                        variables.update(node_output)
                        
                        # Save step execution history
                        step = RunStep(
                            id=uuid4(),
                            run_id=run.id,
                            node_id=node.id,
                            input=node_input,
                            output=node_output,
                            traces={"correlation_id": correlation_id},
                            duration_ms=duration_ms,
                        )
                        await run_repo.save_step(step)
                        await session.commit()
                        
                        # Notify node completion
                        await self.event_bus.publish(
                            topic=str(run.id),
                            event_type="NODE_COMPLETED",
                            payload={"run_id": str(run.id), "node_id": node.id, "status": "SUCCESS"},
                        )
                        
                        # Update downstream edge targets
                        for edge in workflow.definition.edges:
                            if edge.source == node.id:
                                condition_met = evaluate_condition(edge.condition, node_output)
                                if condition_met:
                                    node_statuses[edge.target] = "PENDING"
                                else:
                                    node_statuses[edge.target] = "SKIPPED"
                                    
                    except Exception as node_err:
                        logger.error(f"Node {node.id} execution failed: {node_err}", exc_info=True)
                        node_statuses[node.id] = "FAILED"
                        failed = True
                        error_message = str(node_err)
                        
                        step = RunStep(
                            id=uuid4(),
                            run_id=run.id,
                            node_id=node.id,
                            input=node_input,
                            output={"error": error_message},
                            traces={"correlation_id": correlation_id},
                            duration_ms=int((time.time() - start_time) * 1000),
                        )
                        await run_repo.save_step(step)
                        await session.commit()
                        
                        await self.event_bus.publish(
                            topic=str(run.id),
                            event_type="NODE_COMPLETED",
                            payload={"run_id": str(run.id), "node_id": node.id, "status": "FAILED", "error": error_message},
                        )
                        break
                
                if paused or failed:
                    break

            # Set final run status
            final_status = run.status
            if failed:
                final_status = RunStatus.FAILED
            elif paused:
                final_status = RunStatus.PAUSED
            else:
                all_resolved = all(status in ("SUCCESS", "SKIPPED") for status in node_statuses.values())
                if all_resolved:
                    final_status = RunStatus.SUCCESS
                else:
                    final_status = RunStatus.FAILED
            
            run = Run(
                id=run.id,
                workflow_id=run.workflow_id,
                status=final_status,
                current_state={
                    "variables": variables,
                    "node_statuses": node_statuses,
                    "node_outputs": node_outputs,
                },
                version=run.version,
                created_at=run.created_at,
            )
            await run_repo.save(run)
            await session.commit()
            
            event_type = "RUN_COMPLETED" if final_status == RunStatus.SUCCESS else "RUN_FAILED" if final_status == RunStatus.FAILED else "RUN_PAUSED"
            await self.event_bus.publish(
                topic=str(run.id),
                event_type=event_type,
                payload={
                    "run_id": str(run.id),
                    "status": final_status.value,
                    "error": error_message,
                },
            )
            
            logger.info(f"[Correlation ID: {correlation_id}] Execution complete. Run ID: {run_id}, Status: {final_status.value}")
            return not failed
