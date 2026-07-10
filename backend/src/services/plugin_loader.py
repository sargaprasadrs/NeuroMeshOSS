import importlib.util
import logging
import os
from typing import Dict
from src.core.ports.plugins import IPlugin, IPluginRegistry

logger = logging.getLogger(__name__)


class PluginRegistry(IPluginRegistry):
    def __init__(self) -> None:
        self._plugins: Dict[str, IPlugin] = {}

    def register(self, plugin: IPlugin) -> None:
        if plugin.name in self._plugins:
            logger.warning(f"Plugin {plugin.name} is already registered. Overwriting.")
        self._plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.name} (v{plugin.version})")

    def get(self, name: str) -> IPlugin | None:
        return self._plugins.get(name)


class PluginLoader:
    def __init__(self, registry: IPluginRegistry, host_version: str = "0.1.0") -> None:
        self.registry = registry
        self.host_version = host_version

    def check_compatibility(self, plugin_version: str) -> bool:
        """Verifies if the major version of the plugin matches the host version."""
        try:
            host_parts = self.host_version.split(".")
            plugin_parts = plugin_version.split(".")
            # Strict SemVer: major versions must align
            return host_parts[0] == plugin_parts[0]
        except (ValueError, IndexError):
            return False

    def load_plugin_from_file(self, filepath: str) -> None:
        """Loads a plugin module dynamically from a file path."""
        if not filepath.endswith(".py"):
            return

        plugin_name = os.path.basename(filepath)[:-3]
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, filepath)
            if not spec or not spec.loader:
                logger.error(f"Failed to load spec for plugin: {filepath}")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for instances implementing IPlugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, IPlugin)
                    and attr is not IPlugin
                ):
                    plugin_instance: IPlugin = attr()
                    
                    # Verify third-party dependencies listed by the plugin
                    plugin_deps = getattr(plugin_instance, "dependencies", [])
                    missing_deps = [dep for dep in plugin_deps if importlib.util.find_spec(dep) is None]
                    if missing_deps:
                        logger.error(
                            f"Failed to load plugin '{plugin_instance.name}': "
                            f"Missing required dependencies: {missing_deps}"
                        )
                        continue

                    if self.check_compatibility(plugin_instance.version):
                        self.registry.register(plugin_instance)
                    else:
                        logger.error(
                            f"Incompatible plugin version: {plugin_instance.name} "
                            f"(v{plugin_instance.version}) on host (v{self.host_version})"
                        )
        except Exception as e:
            logger.error(f"Error loading plugin file {filepath}: {e}", exc_info=True)

    def load_plugins_from_directory(self, directory: str) -> None:
        """Scans a directory for plugin files and dynamically loads them."""
        if not os.path.exists(directory):
            logger.warning(f"Plugin directory does not exist: {directory}")
            return

        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath) and filename.endswith(".py"):
                self.load_plugin_from_file(filepath)
