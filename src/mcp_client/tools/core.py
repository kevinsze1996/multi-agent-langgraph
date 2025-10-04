"""
Core MCP Tools Module
Contains tool configuration and basic execution logic.
"""

import asyncio
import threading
from typing import Dict, List

from mcp_client.config import mcp_manager
from .file_search import extract_filename_from_message, extract_path_context_from_message, smart_file_resolution
from .mcp_wrappers import execute_mcp_tool, mcp_file_system_read_sync, mcp_file_system_list_sync, mcp_web_search_sync

# Tool configuration mapping agents to their available MCP servers and tools
MCP_TOOLS_CONFIG = {
    "logical": ["web_search"],
    "brainstormer": ["web_search"], 
    "debater": ["web_search"],
    "teacher": ["web_search"],
    "coder": ["file_system"],
    "therapist": [],  # No tools for therapist
    "planner": []     # No tools for planner
}

# Map MCP server names to their primary tool names
SERVER_TOOL_MAPPING = {
    "web_search": "web_search",
    "file_system": "read_file"  # Default filesystem tool
}

async def initialize_mcp_tools():
    """Initialize all MCP tools and servers"""
    await mcp_manager.initialize_servers()

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

async def determine_and_execute_tools(agent_name: str, user_message: str) -> Dict[str, str]:
    """Determine which tools to use and execute them based on agent and message using FastMCP servers"""
    available_tools = get_available_tools(agent_name)
    tool_results = {}
    
    if not available_tools:
        return tool_results
    
    # Check if web search should be used
    if "web_search" in available_tools and should_use_web_search(user_message):
        print(f"🔍 Executing web search for: {user_message[:50]}...")
        
        # Determine which web search tool to use based on message content
        search_tool = "web_search"  # Default
        if "define" in user_message.lower() or "definition" in user_message.lower():
            search_tool = "search_definitions"
        elif "how to" in user_message.lower():
            search_tool = "search_how_to"
        
        result = await execute_mcp_tool("web_search", query=user_message, search_tool=search_tool)
        tool_results["web_search"] = result
    
    # Check if file system should be used
    if "file_system" in available_tools and should_use_file_system(user_message):
        filename = extract_filename_from_message(user_message)
        if filename:
            print(f"📁 Reading file: {filename}")
            result = await execute_mcp_tool("file_system", file_path=filename)
            tool_results["file_system"] = result
        elif "list" in user_message.lower() or "directory" in user_message.lower():
            print("📁 Listing directory contents")
            # Extract directory path if specified, otherwise use current directory
            dir_path = "."
            result = await execute_mcp_tool("file_system_list", dir_path=dir_path)
            tool_results["file_system"] = result
        else:
            print("📁 File system tools ready for code operations")
            tool_results["file_system"] = "File system tools available for code operations. Use specific commands like 'read filename' or 'list directory'."
    
    return tool_results

def determine_and_execute_tools_sync(agent_name: str, user_message: str) -> Dict[str, str]:
    """Synchronous version of determine_and_execute_tools using sync MCP calls"""
    from .mcp_wrappers import mcp_web_search_sync, mcp_file_system_list_sync
    
    available_tools = get_available_tools(agent_name)
    tool_results = {}
    
    if not available_tools:
        return tool_results
    
    # Check if web search should be used
    if "web_search" in available_tools and should_use_web_search(user_message):
        print(f"🔍 Executing web search for: {user_message[:50]}...")
        
        # Determine which web search tool to use based on message content
        search_tool = "web_search"  # Default
        if "define" in user_message.lower() or "definition" in user_message.lower():
            search_tool = "search_definitions"
        elif "how to" in user_message.lower():
            search_tool = "search_how_to"
        
        result = mcp_web_search_sync(user_message, search_tool)
        tool_results["web_search"] = result
    
    # Check if file system should be used
    if "file_system" in available_tools and should_use_file_system(user_message):
        filename = extract_filename_from_message(user_message)
        if filename:
            # Extract path context and construct full path if needed
            path_context = extract_path_context_from_message(user_message)
            if path_context and not filename.startswith(path_context):
                # Try direct path first like "src/config.py"
                full_path = f"{path_context.rstrip('/')}/{filename}"
                print(f"📁 Reading file: {full_path}")
                result = mcp_file_system_read_sync(full_path)
                
                # If direct path fails, use smart file resolution (which has recursive search)
                if "Error:" in result or ("File" in result and "does not exist" in result):
                    result = smart_file_resolution(filename, user_message)
            else:
                # Use smart file resolution directly (which includes recursive search)
                result = smart_file_resolution(filename, user_message)
            
            tool_results["file_system"] = result
        elif "list" in user_message.lower() or "directory" in user_message.lower():
            print("📁 Listing directory contents")
            # Extract directory path if specified, otherwise use current directory
            dir_path = "."
            result = mcp_file_system_list_sync(dir_path)
            tool_results["file_system"] = result
        else:
            print("📁 File system tools ready for code operations")
            tool_results["file_system"] = "File system tools available for code operations. Use specific commands like 'read filename' or 'list directory'."
    
    return tool_results

def execute_tool(tool_name: str, **kwargs) -> str:
    """Synchronous wrapper for execute_mcp_tool (backwards compatibility)"""    
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