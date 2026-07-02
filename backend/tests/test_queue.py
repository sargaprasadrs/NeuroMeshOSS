import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from src.adapters.queue.redis_queue import RedisJobQueue, RedisEventBus


@pytest.mark.asyncio
async def test_job_queue_enqueue():
    # Patch the aioredis from_url client creation
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        mock_client.xadd.return_value = "msg_id_1"
        
        queue = RedisJobQueue("redis://localhost:6379/0")
        msg_id = await queue.enqueue("test_queue", {"task": "run"})
        
        assert msg_id == "msg_id_1"
        mock_client.xadd.assert_called_once_with("test_queue", {"payload": '{"task": "run"}'})


@pytest.mark.asyncio
async def test_event_bus_publish():
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        bus = RedisEventBus("redis://localhost:6379/0")
        await bus.publish("topic_run", "RUN_UPDATED", {"progress": 50})
        
        # Verify both Redis Streams persistence and PubSub channels broadcast are triggered
        mock_client.xadd.assert_called_once()
        mock_client.publish.assert_called_once()
