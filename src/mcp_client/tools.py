"""
MCP Tools Module - Compatibility Layer
This module maintains backward compatibility by re-exporting all functions from the refactored tools package.
"""

# Import everything from the refactored modules to maintain backward compatibility
from .tools.core import (
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

from .tools.file_search import (
    extract_path_context_from_message,
    extract_filename_from_message,
    smart_file_resolution
)

from .tools.mcp_wrappers import (
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

# Re-export everything for backward compatibility
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