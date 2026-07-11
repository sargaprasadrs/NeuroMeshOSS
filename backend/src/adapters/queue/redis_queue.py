import json
import logging
import asyncio
import socket
from typing import Any, Callable, Coroutine, Dict
from urllib.parse import urlparse
from uuid import uuid4
import redis.asyncio as aioredis
from src.core.ports.queue import IJobQueue, IEventBus

logger = logging.getLogger(__name__)


def check_redis_alive(redis_url: str) -> bool:
    try:
        parsed = urlparse(redis_url)
        s = socket.create_connection((parsed.hostname, parsed.port or 6379), timeout=1.0)
        s.close()
        return True
    except Exception:
        return False


class RedisJobQueue(IJobQueue):
    def __init__(self, redis_url: str) -> None:
        self.use_fallback = not check_redis_alive(redis_url)
        if self.use_fallback:
            logger.warning("Redis is unreachable. Falling back to InMemoryJobQueue.")
            self.handler = None
        else:
            self.client = aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                socket_keepalive=True,
                retry_on_timeout=True,
            )

    async def enqueue(self, queue_name: str, payload: Dict[str, Any]) -> str:
        if self.use_fallback:
            message_id = f"in_mem_{uuid4()}"
            logger.info(f"[InMemoryQueue] Enqueued job {message_id}: {payload}")
            if self.handler:
                asyncio.create_task(self.handler(payload))
            else:
                try:
                    from src.workers.daemon import handle_workflow_job
                    asyncio.create_task(handle_workflow_job(payload))
                except ImportError:
                    logger.warning("[InMemoryQueue] No task execution handler registered.")
            return message_id

        data = {"payload": json.dumps(payload)}
        message_id: str = await self.client.xadd(queue_name, data)
        return message_id

    async def listen(
        self,
        queue_name: str,
        group_name: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], Coroutine[Any, Any, bool]],
    ) -> None:
        if self.use_fallback:
            self.handler = handler
            logger.info(f"[InMemoryQueue] Registered listener for {queue_name}")
            while True:
                await asyncio.sleep(1.0)
            return

        try:
            await self.client.xgroup_create(queue_name, group_name, id="0", mkstream=True)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        logger.info(f"Worker {consumer_name} listening on Stream {queue_name} group {group_name}")
        while True:
            try:
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
                        success = await handler(payload)
                        if success:
                            await self.client.xack(queue_name, group_name, message_id)
            except Exception as e:
                logger.error(f"Error executing task in worker group {group_name}: {e}", exc_info=True)

    async def close(self) -> None:
        if not self.use_fallback:
            await self.client.close()


class RedisEventBus(IEventBus):
    def __init__(self, redis_url: str) -> None:
        self.use_fallback = not check_redis_alive(redis_url)
        if self.use_fallback:
            logger.warning("Redis is unreachable. Falling back to InMemoryEventBus.")
            self.subscribers = {}
        else:
            self.client = aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                socket_keepalive=True,
                retry_on_timeout=True,
            )

    async def publish(self, topic: str, event_type: str, payload: Dict[str, Any]) -> None:
        if self.use_fallback:
            logger.info(f"[InMemoryEventBus] Published to {topic}: {event_type}")
            if topic in self.subscribers:
                for handler in self.subscribers[topic]:
                    try:
                        await handler(event_type, payload)
                    except Exception as e:
                        logger.error(f"Error in InMemoryEventBus subscriber: {e}")
            return

        data = {
            "event_type": event_type,
            "payload": json.dumps(payload),
        }
        await self.client.xadd(f"events:{topic}", data)
        await self.client.publish(f"pubsub:{topic}", json.dumps({"event_type": event_type, "payload": payload}))

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[str, Dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        if self.use_fallback:
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(handler)
            logger.info(f"[InMemoryEventBus] Subscribed handler to topic {topic}")
            return

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

    async def close(self) -> None:
        if not self.use_fallback:
            await self.client.close()
