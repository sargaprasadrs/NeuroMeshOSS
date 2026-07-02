import json
import logging
from typing import Any, Callable, Coroutine, Dict
import redis.asyncio as aioredis
from src.core.ports.queue import IJobQueue, IEventBus

logger = logging.getLogger(__name__)


class RedisJobQueue(IJobQueue):
    def __init__(self, redis_url: str) -> None:
        self.client = aioredis.from_url(redis_url, decode_responses=True)

    async def enqueue(self, queue_name: str, payload: Dict[str, Any]) -> str:
        # Serializing payload data
        data = {"payload": json.dumps(payload)}
        # XADD key ID field value [field value ...]
        message_id: str = await self.client.xadd(queue_name, data)
        return message_id

    async def listen(
        self,
        queue_name: str,
        group_name: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], Coroutine[Any, Any, bool]],
    ) -> None:
        # Create group if not exists
        try:
            await self.client.xgroup_create(queue_name, group_name, id="0", mkstream=True)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        logger.info(f"Worker {consumer_name} listening on Stream {queue_name} group {group_name}")
        while True:
            try:
                # Read stream block for 2 seconds
                streams = await self.client.xreadgroup(
                    groupname=group_name,
                    consumername=consumer_name,
                    streams={queue_name: ">"},
                    count=1,
                    block=2000,
                )
                if not streams:
                    continue

                for stream, messages in streams:
                    for message_id, content in messages:
                        payload = json.loads(content["payload"])
                        # Execute handler
                        success = await handler(payload)
                        if success:
                            # Acknowledge completion
                            await self.client.xack(queue_name, group_name, message_id)
            except Exception as e:
                logger.error(f"Error executing task in worker group {group_name}: {e}", exc_info=True)


class RedisEventBus(IEventBus):
    def __init__(self, redis_url: str) -> None:
        self.client = aioredis.from_url(redis_url, decode_responses=True)

    async def publish(self, topic: str, event_type: str, payload: Dict[str, Any]) -> None:
        data = {
            "event_type": event_type,
            "payload": json.dumps(payload),
        }
        # Publish to Stream for persistence
        await self.client.xadd(f"events:{topic}", data)
        # Broadcast to PubSub channels for real-time WebSockets
        await self.client.publish(f"pubsub:{topic}", json.dumps({"event_type": event_type, "payload": payload}))

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[str, Dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        pubsub = self.client.pubsub()
        await pubsub.subscribe(f"pubsub:{topic}")
        logger.info(f"Subscribed handler to pubsub:{topic}")
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await handler(data["event_type"], data["payload"])
                except Exception as e:
                    logger.error(f"Error in EventBus subscription handler: {e}", exc_info=True)
            # Short yield loop check
