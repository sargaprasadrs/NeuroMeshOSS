from typing import Any, Dict
# Adding sys.path configurations inside plugin for local-first resolution
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from src.core.ports.plugins import IPlugin


class SlackPlugin(IPlugin):
    @property
    def name(self) -> str:
        return "slack-notification"

    @property
    def version(self) -> str:
        # Compatibility version matching the host "0.1.0" major version range
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        # Required external library dependencies (mocked or standard modules for example)
        return []

    async def on_load(self, context: Dict[str, Any]) -> None:
        print(f"[SlackPlugin] loaded with context keys: {list(context.keys())}")

    async def on_unload(self) -> None:
        print("[SlackPlugin] unloaded and connection pools disposed.")

    async def post_message(self, channel: str, text: str) -> None:
        """Sends a notification payload to Slack."""
        print(f"[SlackPlugin] Posting message to channel {channel}: {text}")
