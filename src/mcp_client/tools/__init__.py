"""
MCP Tools Package
Organized tool functionality for the MCP client
"""

# Import from the split modules
from .core import (
    MCP_TOOLS_CONFIG,
    SERVER_TOOL_MAPPING,
    initialize_mcp_tools,
    get_available_tools,
    should_use_web_search,
    should_use_file_system,
    determine_and_execute_tools,
    determine_and_execute_tools_sync,
    execute_tool
)

from .file_search import (
    extract_path_context_from_message,
    extract_filename_from_message,
    smart_file_resolution
)

from .mcp_wrappers import (
    mcp_web_search,
    mcp_web_search_sync,
    mcp_file_system_read,
    mcp_file_system_read_sync,
    mcp_file_system_write,
    mcp_file_system_write_sync,
    mcp_file_system_list,
    mcp_file_system_list_sync,
    execute_mcp_tool
)

__all__ = [
    # Core functionality
    "MCP_TOOLS_CONFIG",
    "SERVER_TOOL_MAPPING", 
    "initialize_mcp_tools",
    "get_available_tools",
    "should_use_web_search",
    "should_use_file_system",
    "determine_and_execute_tools",
    "determine_and_execute_tools_sync",
    "execute_tool",
    
    # File search functionality
    "extract_path_context_from_message",
    "extract_filename_from_message",
    "smart_file_resolution",
    
    # MCP wrapper functions
    "mcp_web_search",
    "mcp_web_search_sync",
    "mcp_file_system_read",
    "mcp_file_system_read_sync",
    "mcp_file_system_write",
    "mcp_file_system_write_sync",
    "mcp_file_system_list",
    "mcp_file_system_list_sync",
    "execute_mcp_tool"
]