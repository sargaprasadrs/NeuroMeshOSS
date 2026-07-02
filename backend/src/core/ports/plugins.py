from abc import ABC, abstractmethod
from typing import Any, Dict


class IPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name of the plugin."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """SemVer compatibility version."""
        pass

    @abstractmethod
    async def on_load(self, context: Dict[str, Any]) -> None:
        """Executed during module load registration."""
        pass

    @abstractmethod
    async def on_unload(self) -> None:
        """Executed prior to system container shutdown."""
        pass


class IPluginRegistry(ABC):
    @abstractmethod
    def register(self, plugin: IPlugin) -> None:
        """Registers plugin reference in host memory space."""
        pass

    @abstractmethod
    def get(self, name: str) -> IPlugin | None:
        """Retrieves active plugin instance by name."""
        pass
