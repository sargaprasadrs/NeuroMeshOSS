import asyncio
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.adapters.queue.redis_queue import RedisEventBus
from src.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSockets"])


class ConnectionManager:
    def __init__(self) -> None:
        # Maps run_id to active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, run_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)
        logger.info(f"WebSocket client connected to Run topic {run_id}")

    def disconnect(self, run_id: str, websocket: WebSocket) -> None:
        if run_id in self.active_connections:
            self.active_connections[run_id].remove(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
        logger.info(f"WebSocket client disconnected from Run topic {run_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        await websocket.send_json(message)

    async def broadcast(self, run_id: str, message: dict) -> None:
        if run_id in self.active_connections:
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting WebSocket message to run {run_id}: {e}")


manager = ConnectionManager()


@router.websocket("/runs/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str) -> None:
    await manager.connect(run_id, websocket)
    event_bus = websocket.app.state.event_bus

    # Define the event handler for this specific run_id subscription
    async def handle_bus_event(event_type: str, payload: dict) -> None:
        try:
            await manager.send_personal_message(
                {"event_type": event_type, "payload": payload}, websocket
            )
        except Exception as e:
            logger.error(f"Failed to forward event to WebSocket client: {e}")

    # Set up subscription task
    subscription_task = asyncio.create_task(
        event_bus.subscribe(topic=run_id, handler=handle_bus_event)
    )

    try:
        # Keep connection open and check for client disconnects
        while True:
            # We discard client payloads since this is a unidirectional trace stream
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(run_id, websocket)
    finally:
        subscription_task.cancel()
        try:
            await subscription_task
        except asyncio.CancelledError:
            pass
