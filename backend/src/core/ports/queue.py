from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict


class IJobQueue(ABC):
    @abstractmethod
    async def enqueue(self, queue_name: str, payload: Dict[str, Any]) -> str:
        """Enqueues a task payload. Returns the generated message ID."""
        pass

    @abstractmethod
    async def listen(
        self,
        queue_name: str,
        group_name: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], Coroutine[Any, Any, bool]],
    ) -> None:
        """Listens to tasks off the queue using consumer groups, passing payload to handler."""
        pass


class IEventBus(ABC):
    @abstractmethod
    async def publish(self, topic: str, event_type: str, payload: Dict[str, Any]) -> None:
        """Broadcasts an event structure to a specific topic."""
        pass

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: Callable[[str, Dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        """Subscribes a callback handler to events on a topic."""
        pass
