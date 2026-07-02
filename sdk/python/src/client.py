import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict
import httpx
import websockets

logger = logging.getLogger(__name__)


class NeuroMeshClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        # Extract ws scheme from http url
        ws_prefix = "wss://" if self.base_url.startswith("https://") else "ws://"
        clean_host = self.base_url.replace("https://", "").replace("http://", "")
        self.ws_url = f"{ws_prefix}{clean_host}/api/ws"
        
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def create_workflow(self, name: str, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new workflow on the control plane."""
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/workflows/",
                json={"name": name, "definition": definition},
            )
            response.raise_for_status()
            return response.json()

    async def run_workflow(self, workflow_id: str, idempotency_key: str | None = None) -> Dict[str, Any]:
        """Triggers a workflow run."""
        headers = self.headers.copy()
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.post(f"{self.base_url}/api/v1/workflows/{workflow_id}/run")
            response.raise_for_status()
            return response.json()

    async def approve_step(self, run_id: str, step_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Appproves a paused human step."""
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/workflows/runs/{run_id}/steps/{step_id}/approve",
                json={"approval_data": approval_data},
            )
            response.raise_for_status()
            return response.json()

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
