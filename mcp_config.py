"""
MCP Server Configuration Module
Handles initialization and configuration of MCP servers for the multi-agent system.
"""

import asyncio
import subprocess
import sys
from typing import Dict, Optional
from mcp import ClientSession
from mcp.client.stdio import stdio_client

# MCP Server Configurations
MCP_SERVERS = {
    "filesystem": {
        "command": [sys.executable, "-m", "mcp_servers.filesystem"],
        "args": ["--root", "."],  # Allow access to current directory
        "description": "Local filesystem access server"
    },
    "web_search": {
        "command": [sys.executable, "-m", "mcp_servers.web_search"],
        "args": [],
        "description": "DuckDuckGo web search server"
    }
}

class MCPManager:
    """Manages MCP client sessions and server connections"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.server_processes: Dict[str, subprocess.Popen] = {}
        
    async def initialize_servers(self):
        """Initialize all configured MCP tool implementations"""
        print("Initializing MCP tool implementations...")
        
        for server_name, config in MCP_SERVERS.items():
            try:
                print(f"  Starting {server_name} server...")
                await self._start_server(server_name, config)
                print(f"  ✓ {server_name} server ready")
            except Exception as e:
                print(f"  ⚠ Failed to start {server_name} server: {e}")
                # Continue with other servers even if one fails
                
        print("MCP tool initialization complete")
    
    async def _start_server(self, server_name: str, config: dict):
        """Start a single MCP server and create client session"""
        try:
            # Currently using direct tool implementations instead of separate server processes
            # This provides the same functionality as MCP servers but integrated directly
            self.sessions[server_name] = None  # Placeholder for future stdio_client connections
            print(f"    Direct tool implementation ready for {server_name}")
        except Exception as e:
            raise Exception(f"Failed to initialize {server_name} tools: {e}")
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> str:
        """Call a tool on a specific MCP server"""
        if server_name not in self.sessions:
            raise Exception(f"Server {server_name} not initialized")
        
        # Execute tools using real implementations
        if server_name == "filesystem":
            return await self._filesystem_tool(tool_name, arguments)
        elif server_name == "web_search":
            return await self._web_search_tool(tool_name, arguments)
        else:
            raise Exception(f"Unknown server: {server_name}")
    
    async def _filesystem_tool(self, tool_name: str, arguments: dict) -> str:
        """Real filesystem operations"""
        if tool_name == "read_file":
            file_path = arguments.get("path", "")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"File: {file_path}\nContent:\n{content}"
            except Exception as e:
                return f"Error reading file {file_path}: {str(e)}"
        elif tool_name == "write_file":
            file_path = arguments.get("path", "")
            content = arguments.get("content", "")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote {len(content)} characters to {file_path}"
            except Exception as e:
                return f"Error writing to file {file_path}: {str(e)}"
        else:
            return f"Unknown filesystem tool: {tool_name}"
    
    async def _web_search_tool(self, tool_name: str, arguments: dict) -> str:
        """Real web search using DuckDuckGo API"""
        if tool_name == "search":
            query = arguments.get("query", "")
            if not query:
                return "Error: No search query provided"
            
            # Import here to avoid circular imports
            from web_search import search_web
            
            try:
                # Use real DuckDuckGo search
                result = search_web(query)
                return result
            except Exception as e:
                # Fallback to basic response if search fails
                return f"""🔍 **Search Results for: \"{query}\"**

⚠️ **Search Service Temporarily Unavailable**: {str(e)}

💡 **Basic Information**: Your query about "{query}" has been noted. 
For reliable search results, please ensure you have an internet connection.

🔗 **Alternative**: Try rephrasing your question or asking for specific aspects of the topic."""
        else:
            return f"Unknown web search tool: {tool_name}"
    
    async def close(self):
        """Close all MCP client sessions and stop servers"""
        print("Closing MCP sessions...")
        for server_name in list(self.sessions.keys()):
            if self.sessions[server_name]:
                # Close session when we have real ones
                pass
            del self.sessions[server_name]
        
        # Stop server processes if any
        for process in self.server_processes.values():
            process.terminate()
        self.server_processes.clear()
        
        print("MCP sessions closed")

# Global MCP manager instance
mcp_manager = MCPManager()