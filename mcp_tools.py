"""
MCP Tools Module
Contains all MCP tool functions that replace the mock implementations.
"""

from mcp_config import mcp_manager
from typing import Dict, List

# Tool configuration mapping agents to their available tools
MCP_TOOLS_CONFIG = {
    "logical": ["web_search"],
    "brainstormer": ["web_search"], 
    "debater": ["web_search"],
    "teacher": ["web_search"],
    "coder": ["file_system"],
    "therapist": [],  # No tools for therapist initially
    "planner": []     # No tools for planner initially
}

async def initialize_mcp_tools():
    """Initialize all MCP tools and servers"""
    await mcp_manager.initialize_servers()

# Real MCP Tool Functions (replacing mocks)

async def mcp_web_search(query: str) -> str:
    """Real web search using MCP server"""
    try:
        result = await mcp_manager.call_tool("web_search", "search", {"query": query})
        return result
    except Exception as e:
        return f"Web search error: {str(e)}"

async def mcp_file_system_read(file_path: str) -> str:
    """Real file system read using MCP server"""
    try:
        result = await mcp_manager.call_tool("filesystem", "read_file", {"path": file_path})
        return result
    except Exception as e:
        return f"File read error: {str(e)}"

async def mcp_file_system_write(file_path: str, content: str) -> str:
    """Real file system write using MCP server"""
    try:
        result = await mcp_manager.call_tool("filesystem", "write_file", {
            "path": file_path, 
            "content": content
        })
        return result
    except Exception as e:
        return f"File write error: {str(e)}"

async def execute_mcp_tool(tool_name: str, **kwargs) -> str:
    """Execute an MCP tool with given parameters"""
    try:
        if tool_name == "web_search":
            query = kwargs.get("query", "")
            return await mcp_web_search(query)
        elif tool_name == "file_system" or tool_name == "file_system_read":
            file_path = kwargs.get("file_path", "")
            return await mcp_file_system_read(file_path)
        elif tool_name == "file_system_write":
            file_path = kwargs.get("file_path", "")
            content = kwargs.get("content", "")
            return await mcp_file_system_write(file_path, content)
        else:
            return f"Unknown MCP tool: {tool_name}"
    except Exception as e:
        return f"MCP tool execution error: {str(e)}"

# Utility functions for tool management

def get_available_tools(agent_name: str) -> List[str]:
    """Get list of available tools for a specific agent"""
    return MCP_TOOLS_CONFIG.get(agent_name, [])

def should_use_web_search(message: str) -> bool:
    """Determine if web search should be triggered based on message content"""
    search_keywords = ["search", "find", "what is", "tell me about", "research", 
                      "explain", "define", "how does", "latest", "news"]
    return any(keyword in message.lower() for keyword in search_keywords)

def should_use_file_system(message: str) -> bool:
    """Determine if file system should be triggered based on message content"""
    file_keywords = ["file", "read", "write", "code", "save", "load", 
                    "create", "edit", "directory", "folder", "show", "display", "open"]
    return any(keyword in message.lower() for keyword in file_keywords)

def extract_filename_from_message(message: str) -> str:
    """Extract filename from user message"""
    import re
    
    # Common file patterns
    patterns = [
        r'(?:read|open|show|display|load)\s+(?:the\s+)?(?:contents\s+of\s+)?([^\s]+\.\w+)',  # "read main.py" or "show me the contents of test.py"
        r'(?:show|display)\s+(?:me\s+)?([^\s]+\.\w+)',  # "show me CLAUDE.md"
        r'([^\s]+\.\w+)',  # Any filename with extension
        r'(?:file|path)\s+([^\s]+)',  # "file main.py" or "path /etc/config"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        if matches:
            # Return the first match
            filename = matches[0].strip()
            # Clean common prefixes/suffixes
            filename = filename.strip('"\'')
            return filename
    
    return ""

async def determine_and_execute_tools(agent_name: str, user_message: str) -> Dict[str, str]:
    """Determine which tools to use and execute them based on agent and message"""
    available_tools = get_available_tools(agent_name)
    tool_results = {}
    
    if not available_tools:
        return tool_results
    
    # Check if web search should be used
    if "web_search" in available_tools and should_use_web_search(user_message):
        print(f"🔍 Executing web search for: {user_message[:50]}...")
        result = await execute_mcp_tool("web_search", query=user_message)
        tool_results["web_search"] = result
    
    # Check if file system should be used
    if "file_system" in available_tools and should_use_file_system(user_message):
        filename = extract_filename_from_message(user_message)
        if filename:
            print(f"📁 Reading file: {filename}")
            result = await execute_mcp_tool("file_system", file_path=filename)
            tool_results["file_system"] = result
        else:
            print("📁 File system tools ready for code operations")
            tool_results["file_system"] = "File system tools available for code operations"
    
    return tool_results

# Backwards compatibility - Sync wrapper functions for existing code

def execute_tool(tool_name: str, **kwargs) -> str:
    """Synchronous wrapper for execute_mcp_tool (backwards compatibility)"""
    import asyncio
    
    # Simple approach: always create a new event loop for tool execution
    try:
        return asyncio.run(execute_mcp_tool(tool_name, **kwargs))
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            # If we're in a running loop, use nest_asyncio or handle differently
            try:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(execute_mcp_tool(tool_name, **kwargs))
            except ImportError:
                # Fallback: execute synchronously using the MCP manager directly
                import threading
                result = [None]
                exception = [None]
                
                def run_async():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result[0] = loop.run_until_complete(execute_mcp_tool(tool_name, **kwargs))
                        loop.close()
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=run_async)
                thread.start()
                thread.join()
                
                if exception[0]:
                    return f"Error executing {tool_name}: {exception[0]}"
                return result[0]
        else:
            return f"Error executing {tool_name}: {e}"