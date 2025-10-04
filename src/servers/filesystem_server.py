#!/usr/bin/env python3
"""
Filesystem MCP Server
Provides file system operations through the Model Context Protocol.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("Filesystem Server")

# Security: Restrict access to project directory only
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()  # Go up to project root

def _validate_path(file_path: str) -> Path:
    """Validate and resolve file path within project boundaries"""
    try:
        # Convert to absolute path and resolve
        if os.path.isabs(file_path):
            path = Path(file_path).resolve()
        else:
            path = (PROJECT_ROOT / file_path).resolve()
        
        # Security check: ensure path is within project root
        if not str(path).startswith(str(PROJECT_ROOT)):
            raise ValueError(f"Access denied: Path outside project directory")
        
        return path
    except Exception as e:
        raise ValueError(f"Invalid path: {e}")

@mcp.tool
def read_file(file_path: str) -> str:
    """Read contents of a file within the project directory.
    
    Args:
        file_path: Path to the file to read (relative to project root or absolute)
    
    Returns:
        File contents as a string
    """
    try:
        path = _validate_path(file_path)
        
        if not path.exists():
            return f"Error: File '{file_path}' does not exist"
        
        if not path.is_file():
            return f"Error: '{file_path}' is not a file"
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"File: {file_path}\nSize: {len(content)} characters\n\nContent:\n{content}"
    
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"

@mcp.tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file within the project directory.
    
    Args:
        file_path: Path to the file to write (relative to project root or absolute)
        content: Content to write to the file
    
    Returns:
        Success or error message
    """
    try:
        path = _validate_path(file_path)
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} characters to '{file_path}'"
    
    except Exception as e:
        return f"Error writing to file '{file_path}': {str(e)}"

@mcp.tool
def list_directory(dir_path: str = ".") -> str:
    """List contents of a directory within the project.
    
    Args:
        dir_path: Path to the directory to list (relative to project root or absolute)
    
    Returns:
        Directory listing with file types and sizes
    """
    try:
        path = _validate_path(dir_path)
        
        if not path.exists():
            return f"Error: Directory '{dir_path}' does not exist"
        
        if not path.is_dir():
            return f"Error: '{dir_path}' is not a directory"
        
        items = []
        for item in sorted(path.iterdir()):
            if item.is_file():
                size = item.stat().st_size
                items.append(f"📄 {item.name} ({size} bytes)")
            elif item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                items.append(f"🔗 {item.name}")
        
        if not items:
            return f"Directory '{dir_path}' is empty"
        
        return f"Directory listing for '{dir_path}':\n" + "\n".join(items)
    
    except Exception as e:
        return f"Error listing directory '{dir_path}': {str(e)}"

@mcp.tool
def file_exists(file_path: str) -> str:
    """Check if a file or directory exists within the project.
    
    Args:
        file_path: Path to check (relative to project root or absolute)
    
    Returns:
        Information about the path's existence and type
    """
    try:
        path = _validate_path(file_path)
        
        if not path.exists():
            return f"Path '{file_path}' does not exist"
        
        if path.is_file():
            size = path.stat().st_size
            return f"File '{file_path}' exists ({size} bytes)"
        elif path.is_dir():
            return f"Directory '{file_path}' exists"
        else:
            return f"Path '{file_path}' exists (special file type)"
    
    except Exception as e:
        return f"Error checking path '{file_path}': {str(e)}"

@mcp.tool
def get_project_info() -> str:
    """Get information about the current project directory.
    
    Returns:
        Project directory information
    """
    try:
        total_files = 0
        total_dirs = 0
        total_size = 0
        
        for item in PROJECT_ROOT.rglob("*"):
            if item.is_file():
                total_files += 1
                try:
                    total_size += item.stat().st_size
                except:
                    pass  # Skip files we can't access
            elif item.is_dir():
                total_dirs += 1
        
        return f"""Project Information:
Root Directory: {PROJECT_ROOT}
Total Files: {total_files}
Total Directories: {total_dirs}
Total Size: {total_size:,} bytes
"""
    
    except Exception as e:
        return f"Error getting project info: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server
    try:
        # Log server start to stderr (stdout is reserved for MCP protocol)
        print(f"Starting Filesystem MCP Server (PID: {os.getpid()})", file=sys.stderr)
        print(f"Project root: {PROJECT_ROOT}", file=sys.stderr)
        
        # Run server with stdio transport
        mcp.run()
    except KeyboardInterrupt:
        print("Filesystem server shutting down...", file=sys.stderr)
    except Exception as e:
        print(f"Filesystem server error: {e}", file=sys.stderr)
        sys.exit(1)