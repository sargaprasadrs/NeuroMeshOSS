from typing import Any, Dict
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from src.core.ports.plugins import IPlugin


class GitHubPlugin(IPlugin):
    @property
    def name(self) -> str:
        return "github-sync"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    async def on_load(self, context: Dict[str, Any]) -> None:
        print(f"[GitHubPlugin] Dynamic setup completed.")

    async def on_unload(self) -> None:
        print("[GitHubPlugin] Connection context released.")

    async def sync_repository(self, repo_url: str) -> None:
        """Syncs local workspace with GitHub repo."""
        print(f"[GitHubPlugin] Syncing files from repository: {repo_url}")
