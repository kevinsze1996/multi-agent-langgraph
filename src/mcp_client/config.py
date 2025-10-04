"""
MCP Client Configuration Module
Handles MCP client connections to standalone FastMCP servers for the multi-agent system.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict
from .direct_client import DirectMCPClient

# MCP Server Configurations - now using real FastMCP servers
PROJECT_ROOT = Path(__file__).parent.parent.absolute()  # Go up to src/ then project root

MCP_SERVERS = {
    "filesystem": {
        "script_path": str(PROJECT_ROOT / "servers" / "filesystem_server.py"),
        "description": "Filesystem operations server using FastMCP"
    },
    "web_search": {
        "script_path": str(PROJECT_ROOT / "servers" / "web_search_server.py"),
        "description": "DuckDuckGo web search server using FastMCP"
    }
}

class MCPManager:
    """Manages MCP client sessions and server connections to FastMCP servers"""
    
    def __init__(self):
        self.clients: Dict[str, DirectMCPClient] = {}
        self.initialized = False
        
    async def initialize_servers(self):
        """Initialize MCP client connections to FastMCP servers"""
        if self.initialized:
            return
            
        print("Initializing MCP client connections to FastMCP servers...")
        
        for server_name, config in MCP_SERVERS.items():
            try:
                print(f"  Starting {server_name} server...")
                print(f"    Script path: {config['script_path']}")
                success = await self._start_server(server_name, config)
                if success:
                    print(f"  ✓ {server_name} server ready")
                else:
                    print(f"  ⚠ Failed to start {server_name} server")
            except Exception as e:
                print(f"  ⚠ Failed to start {server_name} server: {e}")
                import traceback
                traceback.print_exc()
                # Continue with other servers even if one fails
                
        self.initialized = True
        print("MCP client initialization complete")
    
    async def _start_server(self, server_name: str, config: dict) -> bool:
        """Start a FastMCP server process using our custom direct client"""
        try:
            script_path = config["script_path"]
            
            # Create and start our custom MCP client
            client = DirectMCPClient(script_path, server_name)
            success = await client.start()
            
            if success:
                # Store the client
                self.clients[server_name] = client
                return True
            else:
                return False
            
        except Exception as e:
            print(f"    Error starting {server_name}: {e}")
            return False
    
    def call_tool_sync(self, server_name: str, tool_name: str, arguments: dict) -> str:
        """Synchronous wrapper for call_tool using threading"""
        import asyncio
        import threading
        
        result = [None]
        exception = [None]
        
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result[0] = loop.run_until_complete(self.call_tool(server_name, tool_name, arguments))
                loop.close()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=run_async)
        thread.start()
        thread.join()
        
        if exception[0]:
            return f"Error: {exception[0]}"
        
        return result[0]

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> str:
        """Call a tool on a specific MCP server using our direct client"""
        if server_name not in self.clients:
            return f"Error: Server {server_name} not initialized"
        
        client = self.clients[server_name]
        
        try:
            # Call the tool using our direct client
            result = await client.call_tool(tool_name, arguments)
            return result
                
        except Exception as e:
            # Try to restart the server if the call failed
            print(f"Tool call failed for {server_name}.{tool_name}: {e}")
            
            # Attempt to restart the client
            try:
                await self._restart_server(server_name)
                client = self.clients.get(server_name)
                if client:
                    result = await client.call_tool(tool_name, arguments)
                    return result
                else:
                    return f"Tool call failed and restart failed: no client available"
            except Exception as restart_error:
                return f"Tool call failed and restart failed: {restart_error}"

    async def _restart_server(self, server_name: str):
        """Restart a failed MCP server and client"""
        try:
            # Close existing client if any
            if self.clients.get(server_name):
                try:
                    await self.clients[server_name].close()
                except Exception:
                    pass
                del self.clients[server_name]
            
            # Wait a moment
            await asyncio.sleep(1.0)
            
            # Restart the server
            config = MCP_SERVERS[server_name]
            await self._start_server(server_name, config)
            
        except Exception as e:
            print(f"Failed to restart server {server_name}: {e}")

    async def list_tools(self, server_name: str) -> list:
        """List available tools for a specific server"""
        if server_name not in self.clients:
            return []
        
        try:
            client = self.clients[server_name]
            tools_list = await client.list_tools()
            return tools_list
                
        except Exception as e:
            print(f"Failed to list tools for {server_name}: {e}")
            return []
    
    async def close(self):
        """Close all MCP client connections"""
        print("Closing MCP clients...")
        
        # Close all clients
        for server_name, client in self.clients.items():
            if client:
                try:
                    await client.close()
                    print(f"    Closed client for {server_name}")
                except Exception as e:
                    print(f"    Error closing client for {server_name}: {e}")
        
        self.clients.clear()
        self.initialized = False
        print("MCP clients closed")

# Global MCP manager instance
mcp_manager = MCPManager()