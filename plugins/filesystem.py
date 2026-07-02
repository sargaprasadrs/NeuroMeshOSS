from typing import Any, Dict
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from src.core.ports.plugins import IPlugin


class FilesystemPlugin(IPlugin):
    @property
    def name(self) -> str:
        return "filesystem-tool"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    async def on_load(self, context: Dict[str, Any]) -> None:
        print("[FilesystemPlugin] Initialized local workspace paths.")

    async def on_unload(self) -> None:
        print("[FilesystemPlugin] Scopes closed.")

    async def read_file(self, filepath: str) -> str:
        """Reads content from a whitelisted directory path, preventing traversal out of sandbox."""
        base_dir = os.path.abspath(os.getcwd())
        target_path = os.path.abspath(filepath)
        
        # Prevent directory traversal attacks
        if os.path.commonpath([base_dir]) != os.path.commonpath([base_dir, target_path]):
            raise PermissionError("Directory traversal attempt detected. Access denied.")
            
        print(f"[FilesystemPlugin] Reading file safely inside sandbox: {target_path}")
        return "mocked content"
