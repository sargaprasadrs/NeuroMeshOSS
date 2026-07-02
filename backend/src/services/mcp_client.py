import asyncio
import json
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class McpServerConnection:
    """Manages stdio-based subprocess lifecycle for a single MCP server connection."""

    def __init__(self, name: str, command: str, args: List[str], retry_limit: int = 3) -> None:
        self.name = name
        self.command = command
        self.args = args
        self.retry_limit = retry_limit
        
        self.process: Optional[subprocess.Popen] = None
        self.is_connected = False
        self.capabilities: Dict[str, Any] = {}
        self.tools: List[Dict[str, Any]] = []

    async def connect(self) -> None:
        """Spawns stdio subprocess and queries capabilities via JSON-RPC handshake."""
        attempts = 0
        while attempts < self.retry_limit:
            try:
                logger.info(f"Connecting to MCP server '{self.name}' using command: {self.command} {self.args}")
                self.process = subprocess.Popen(
                    [self.command] + self.args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
                self.is_connected = True
                
                # Retrieve capabilities
                await self.query_capabilities()
                logger.info(f"Successfully connected to MCP Server '{self.name}'. Registered {len(self.tools)} tools.")
                return
            except Exception as e:
                attempts += 1
                logger.warning(f"Failed connection attempt {attempts} to MCP server '{self.name}': {e}")
                await asyncio.sleep(1.0 * attempts)
        
        raise ConnectionError(f"Failed to connect to MCP server '{self.name}' after {self.retry_limit} attempts.")

    async def query_capabilities(self) -> None:
        """Sends JSON-RPC initialize/tools listing request to discovery server capabilities."""
        # Standard MCP initialize call
        init_req = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "NeuroMeshHost", "version": "1.0.0"},
            },
        }
        
        try:
            res = await self.send_rpc(init_req)
            self.capabilities = res.get("capabilities", {})
            
            # Retrieve tools list
            tools_req = {"jsonrpc": "2.0", "id": "2", "method": "tools/list", "params": {}}
            res_tools = await self.send_rpc(tools_req)
            self.tools = res_tools.get("tools", [])
        except Exception as e:
            logger.error(f"Error executing discovery handshake with '{self.name}': {e}")
            self.tools = []

    async def send_rpc(self, request: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """Sends JSON-RPC frame over stdout and parses response frame from stdout."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise ConnectionError(f"Server '{self.name}' process is not running.")

        try:
            raw_req = json.dumps(request) + "\n"
            self.process.stdin.write(raw_req)
            self.process.stdin.flush()
            
            # Read line asynchronously using executor to prevent loop block
            loop = asyncio.get_running_loop()
            raw_res = await asyncio.wait_for(
                loop.run_in_executor(None, self.process.stdout.readline),
                timeout=timeout,
            )
            
            if not raw_res:
                raise ConnectionAbortedError(f"Received empty response from server '{self.name}'.")
                
            response = json.loads(raw_res)
            if "error" in response:
                raise ValueError(f"JSON-RPC Error: {response['error']}")
                
            return response.get("result", {})
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for JSON-RPC response from MCP server '{self.name}'.")
            raise
        except Exception as e:
            logger.error(f"Connection failure communicating with MCP server '{self.name}': {e}")
            self.is_connected = False
            raise

    async def ping_heartbeat(self) -> bool:
        """Sends lightweight query to check if server is responsive."""
        if not self.is_connected:
            return False
        try:
            req = {"jsonrpc": "2.0", "id": "hb", "method": "ping", "params": {}}
            await self.send_rpc(req, timeout=2.0)
            return True
        except Exception:
            logger.warning(f"Heartbeat failed for MCP server '{self.name}'. Attempting auto-reconnect...")
            self.is_connected = False
            return False

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a registered tool."""
        req = {
            "jsonrpc": "2.0",
            "id": f"exec_{name}",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        return await self.send_rpc(req, timeout=10.0)

    def close(self) -> None:
        """Shutdown subprocess cleanly."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.is_connected = False
            logger.info(f"MCP Connection to '{self.name}' terminated.")


class McpClientPool:
    """Manages connections pool and tool invocation routing for registered MCP servers."""

    def __init__(self) -> None:
        self.connections: Dict[str, McpServerConnection] = {}

    async def register_server(self, name: str, command: str, args: List[str]) -> None:
        """Creates connection and registers it in the pool."""
        conn = McpServerConnection(name, command, args)
        await conn.connect()
        self.connections[name] = conn

    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Routes execution call to target server, with automatic reconnection failover."""
        conn = self.connections.get(server_name)
        if not conn:
            raise KeyError(f"MCP Server '{server_name}' not registered in client pool.")

        # Heartbeat check/reconnect before routing execution
        if not conn.is_connected:
            logger.info(f"MCP server '{server_name}' disconnected. Reconnecting before execution...")
            await conn.connect()

        try:
            return await conn.execute_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"Execution failed on MCP server '{server_name}': {e}. Attempting retry...")
            # Try to reconnect and retry once
            await conn.connect()
            return await conn.execute_tool(tool_name, arguments)

    def close_all(self) -> None:
        """Cleans up all child processes."""
        for name, conn in self.connections.items():
            conn.close()
        self.connections.clear()
