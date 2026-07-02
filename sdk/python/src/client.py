import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict
import httpx
import websockets

logger = logging.getLogger(__name__)


class WorkflowClient:
    def __init__(self, client: "NeuroMeshClient") -> None:
        self.client = client

    async def create(self, name: str, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a workflow DAG on the control plane."""
        return await self.client.request("POST", "/api/v1/workflows/", json={"name": name, "definition": definition})

    async def run(self, workflow_id: str, idempotency_key: str | None = None) -> Dict[str, Any]:
        """Triggers a workflow execution run."""
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return await self.client.request("POST", f"/api/v1/workflows/{workflow_id}/run", headers=headers)


class AgentClient:
    def __init__(self, client: "NeuroMeshClient") -> None:
        self.client = client

    async def list(self) -> Dict[str, Any]:
        """Lists all registered agents and models."""
        return await self.client.request("GET", "/api/v1/agents/")


class RunClient:
    def __init__(self, client: "NeuroMeshClient") -> None:
        self.client = client

    async def approve_step(self, run_id: str, step_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Appproves a paused human step."""
        return await self.client.request(
            "POST",
            f"/api/v1/workflows/runs/{run_id}/steps/{step_id}/approve",
            json={"approval_data": approval_data},
        )

    async def get_steps(self, run_id: str) -> Dict[str, Any]:
        """Gets steps execution history list for a run."""
        return await self.client.request("GET", f"/api/v1/workflows/runs/{run_id}/steps")


class SecretsClient:
    def __init__(self, client: "NeuroMeshClient") -> None:
        self.client = client

    async def set_secret(self, key: str, value: str) -> Dict[str, Any]:
        """Securely registers or rotates a secret key on the control plane."""
        return await self.client.request("POST", "/api/v1/secrets/", json={"key": key, "value": value})


class NeuroMeshClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: str | None = None, retries: int = 3) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.retries = retries
        
        ws_prefix = "wss://" if self.base_url.startswith("https://") else "ws://"
        clean_host = self.base_url.replace("https://", "").replace("http://", "")
        self.ws_url = f"{ws_prefix}{clean_host}/api/ws"
        
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        # Sub-clients configurations
        self.workflows = WorkflowClient(self)
        self.agents = AgentClient(self)
        self.runs = RunClient(self)
        self.secrets = SecretsClient(self)

    async def __aenter__(self) -> "NeuroMeshClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def request(self, method: str, path: str, headers: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """Centralized HTTP request router supporting exponential backoff retries."""
        url = f"{self.base_url}{path}"
        req_headers = self.headers.copy()
        if headers:
            req_headers.update(headers)

        attempt = 0
        backoff = 0.5
        while attempt < self.retries:
            try:
                async with httpx.AsyncClient(headers=req_headers, timeout=10.0) as client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                attempt += 1
                if attempt >= self.retries:
                    logger.error(f"HTTP Request failed after {self.retries} attempts: {e}")
                    raise
                logger.warning(f"Request failed: {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2

    async def subscribe_run_traces(
        self, run_id: str, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]
    ) -> None:
        """Connects to the real-time WebSocket channel and pipes trace events to callback."""
        url = f"{self.ws_url}/runs/{run_id}"
        async with websockets.connect(url) as websocket:
            logger.info(f"Subscribed to WebSocket trace events for Run ID {run_id}")
            try:
                async for message in websocket:
                    data = json.loads(message)
                    await callback(data)
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"WebSocket trace stream for Run ID {run_id} closed by server.")
            except Exception as e:
                logger.error(f"Error reading WebSocket trace stream: {e}", exc_info=True)
                raise
