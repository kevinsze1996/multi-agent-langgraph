"""
MCP Wrapper Functions Module
Contains all MCP tool wrapper functions for interacting with FastMCP servers.
"""

from mcp_client.config import mcp_manager

# Real MCP Tool Functions using FastMCP servers

def mcp_web_search_sync(query: str, tool_name: str = "web_search") -> str:
    """Real web search using FastMCP web search server (sync version)"""
    try:
        result = mcp_manager.call_tool_sync("web_search", tool_name, {"query": query})
        return result
    except Exception as e:
        return f"Web search error: {str(e)}"

def mcp_file_system_read_sync(file_path: str) -> str:
    """Real file system read using FastMCP filesystem server (sync version)"""
    try:
        result = mcp_manager.call_tool_sync("filesystem", "read_file", {"file_path": file_path})
        return result
    except Exception as e:
        return f"File read error: {str(e)}"

def mcp_file_system_write_sync(file_path: str, content: str) -> str:
    """Real file system write using FastMCP filesystem server (sync version)"""
    try:
        result = mcp_manager.call_tool_sync("filesystem", "write_file", {
            "file_path": file_path, 
            "content": content
        })
        return result
    except Exception as e:
        return f"File write error: {str(e)}"

def mcp_file_system_list_sync(dir_path: str = ".") -> str:
    """List directory contents using FastMCP filesystem server (sync version)"""
    try:
        result = mcp_manager.call_tool_sync("filesystem", "list_directory", {"dir_path": dir_path})
        return result
    except Exception as e:
        return f"Directory listing error: {str(e)}"

# Keep async versions for backwards compatibility
async def mcp_web_search(query: str, tool_name: str = "web_search") -> str:
    """Real web search using FastMCP web search server"""
    try:
        result = await mcp_manager.call_tool("web_search", tool_name, {"query": query})
        return result
    except Exception as e:
        return f"Web search error: {str(e)}"

async def mcp_file_system_read(file_path: str) -> str:
    """Real file system read using FastMCP filesystem server"""
    try:
        result = await mcp_manager.call_tool("filesystem", "read_file", {"file_path": file_path})
        return result
    except Exception as e:
        return f"File read error: {str(e)}"

async def mcp_file_system_write(file_path: str, content: str) -> str:
    """Real file system write using FastMCP filesystem server"""
    try:
        result = await mcp_manager.call_tool("filesystem", "write_file", {
            "file_path": file_path, 
            "content": content
        })
        return result
    except Exception as e:
        return f"File write error: {str(e)}"

async def mcp_file_system_list(dir_path: str = ".") -> str:
    """List directory contents using FastMCP filesystem server"""
    try:
        result = await mcp_manager.call_tool("filesystem", "list_directory", {"dir_path": dir_path})
        return result
    except Exception as e:
        return f"Directory listing error: {str(e)}"

async def execute_mcp_tool(tool_name: str, **kwargs) -> str:
    """Execute an MCP tool with given parameters using FastMCP servers"""
    try:
        if tool_name == "web_search":
            query = kwargs.get("query", "")
            search_tool = kwargs.get("search_tool", "web_search")  # Default to basic search
            return await mcp_web_search(query, search_tool)
        elif tool_name == "file_system" or tool_name == "file_system_read":
            file_path = kwargs.get("file_path", "")
            return await mcp_file_system_read(file_path)
        elif tool_name == "file_system_write":
            file_path = kwargs.get("file_path", "")
            content = kwargs.get("content", "")
            return await mcp_file_system_write(file_path, content)
        elif tool_name == "file_system_list":
            dir_path = kwargs.get("dir_path", ".")
            return await mcp_file_system_list(dir_path)
        else:
            return f"Unknown MCP tool: {tool_name}"
    except Exception as e:
        return f"MCP tool execution error: {str(e)}"