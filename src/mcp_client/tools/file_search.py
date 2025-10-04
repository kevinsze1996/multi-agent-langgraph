"""
Smart File Search Module
Contains path-aware file search and resolution functionality.
"""

import re
from pathlib import Path
from typing import List, Tuple

from .mcp_wrappers import mcp_file_system_read_sync, mcp_file_system_list_sync

def extract_path_context_from_message(message: str) -> str:
    """Extract path context hints from user message"""
    # Path context patterns
    path_patterns = [
        # "in X folder" patterns
        r'in\s+(?:the\s+)?([a-zA-Z0-9_/-]+)\s+(?:folder|directory|dir)',
        r'from\s+(?:the\s+)?([a-zA-Z0-9_/-]+)\s+(?:folder|directory|dir)',
        
        # "in X/" or "from X/" patterns  
        r'in\s+([a-zA-Z0-9_/-]+)/',
        r'from\s+([a-zA-Z0-9_/-]+)/',
        
        # "X/filename" patterns (extract the path part)
        r'([a-zA-Z0-9_/-]+)/[a-zA-Z0-9_.-]+',
        
        # "inside X" patterns
        r'inside\s+(?:the\s+)?([a-zA-Z0-9_/-]+)',
        
        # "under X" patterns
        r'under\s+(?:the\s+)?([a-zA-Z0-9_/-]+)',
    ]
    
    for pattern in path_patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        if matches:
            path_hint = matches[0].strip()
            # Clean common words
            if path_hint.lower() not in ['the', 'a', 'an', 'this', 'that']:
                return path_hint
    
    return ""

def extract_filename_from_message(message: str) -> str:
    """Extract filename from user message"""
    # Enhanced file patterns with better dotfile and complex message support
    patterns = [
        # Specific command patterns (highest priority)
        r'(?:read|open|show|display|load)\s+(?:the\s+)?(?:contents\s+of\s+)?([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)(?:\s+file)?',  # "read main.py" or "read contents of README.md"
        r'(?:read|open|show|display|load)\s+(?:the\s+)?(?:file\s+)?(\.[a-zA-Z0-9_-]+)(?:\s+file)?',  # ".gitignore file" or "read .env"
        
        # Show/display patterns (including dotfiles)
        r'(?:show|display)\s+(?:me\s+)?(?:the\s+)?([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)(?:\s+file)?',  # "show me CLAUDE.md"
        r'(?:show|display)\s+(?:me\s+)?(?:the\s+)?(\.[a-zA-Z0-9_-]+)(?:\s+file)?',  # "show me the .bashrc"
        
        # Reverse patterns (filename mentioned before action)
        r'([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)\s+(?:file\s+)?(?:for\s+me|please)',  # "main.py file please"
        r'(\.[a-zA-Z0-9_-]+)\s+(?:file\s+)?(?:for\s+me|please)',  # ".gitignore file for me"
        
        # File/path prefix patterns
        r'(?:file|path)\s+([a-zA-Z0-9_/.,-]+)',  # "file main.py" or "path /etc/config"
        
        # Any file with extension (lowest priority, word boundaries to avoid partial matches)
        r'\b([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)\b',  # Any regular file with extension
        r'\b(\.[a-zA-Z0-9_-]+)\b',  # Any dotfile
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        if matches:
            # Return the first match
            filename = matches[0].strip()
            # Clean common prefixes/suffixes
            filename = filename.strip('"\'')
            # Skip if it's obviously not a filename (exact word matches only)
            if filename and filename.lower() not in ['for', 'me', 'please', 'can', 'you', 'the', 'file']:
                return filename
    
    return ""

def _should_exclude_path(path: str) -> bool:
    """Check if a path should be excluded from search results"""
    exclude_patterns = [
        # Virtual environments
        '.venv/', 'venv/', 'env/', '.env/',
        # Package managers
        'node_modules/', '__pycache__/', '.git/', 
        # Python site-packages (dependency files)
        'site-packages/', 'dist-packages/',
        # Common build/cache directories
        '.cache/', 'build/', 'dist/', '.tox/',
        # IDE/editor directories
        '.vscode/', '.idea/', '.vs/',
        # OS directories
        '.DS_Store', 'Thumbs.db'
    ]
    
    path_lower = path.lower()
    return any(exclude in path_lower for exclude in exclude_patterns)

def _filter_by_path_context(file_paths: List[str], path_context: str) -> List[str]:
    """Filter file paths based on path context hint"""
    if not path_context:
        return file_paths
    
    # Normalize path context (remove trailing slashes, etc.)
    context_clean = path_context.rstrip('/').lower()
    
    # Filter files that match the path context
    filtered = []
    for path in file_paths:
        path_lower = path.lower()
        # Check if the path contains the context
        if context_clean in path_lower or path_lower.startswith(context_clean + '/'):
            filtered.append(path)
    
    # If we have matches with the context, return those; otherwise return original
    return filtered if filtered else file_paths

def _is_similar_filename(target: str, candidate: str) -> bool:
    """Simple similarity check for filenames"""
    target_lower = target.lower()
    candidate_lower = candidate.lower()
    
    # Remove extensions for comparison
    target_base = target_lower.split('.')[0] if '.' in target_lower else target_lower
    candidate_base = candidate_lower.split('.')[0] if '.' in candidate_lower else candidate_lower
    
    # Check various similarity conditions
    conditions = [
        # Substring match
        target_base in candidate_base or candidate_base in target_base,
        # Missing/extra characters (simple edit distance)
        abs(len(target_base) - len(candidate_base)) <= 2 and 
        sum(c1 != c2 for c1, c2 in zip(target_base, candidate_base)) <= 2,
        # Partial filename match (for files like "main" matching "main.py")
        target_base == candidate_base[:len(target_base)] or 
        candidate_base == target_base[:len(candidate_base)]
    ]
    
    return any(conditions)

def search_for_file_in_project(filename: str, path_context: str = "") -> Tuple[List[str], List[str]]:
    """Search for files in project and return (exact_matches, similar_matches) with optional path filtering"""
    try:
        exact_matches = []
        all_files = []
        
        # Try MCP tool first, fall back to direct filesystem if it fails
        def scan_directory(dir_path: str = "."):
            result = mcp_file_system_list_sync(dir_path)
            
            # If MCP fails, use direct filesystem access
            if "Error:" in result:
                return scan_directory_direct(dir_path)
            
            # Parse the MCP directory listing
            lines = result.split('\n')[1:]  # Skip header line
            for line in lines:
                if line.strip():
                    if line.startswith('📁'):
                        # It's a directory, scan recursively
                        subdir_name = line.split('📁 ')[1].rstrip('/')
                        if dir_path == ".":
                            subdir_path = subdir_name
                        else:
                            subdir_path = f"{dir_path}/{subdir_name}"
                        
                        # Skip excluded directories early
                        if not _should_exclude_path(subdir_path):
                            scan_directory(subdir_path)
                            
                    elif line.startswith('📄'):
                        # It's a file
                        file_info = line.split('📄 ')[1]
                        file_name = file_info.split(' (')[0]  # Remove size info
                        
                        if dir_path == ".":
                            full_path = file_name
                        else:
                            full_path = f"{dir_path}/{file_name}"
                        
                        # Skip excluded files
                        if _should_exclude_path(full_path):
                            continue
                        
                        all_files.append((file_name, full_path))
                        
                        # Check for exact match
                        if file_name == filename:
                            exact_matches.append(full_path)
        
        def scan_directory_direct(dir_path: str = "."):
            """Direct filesystem scanning fallback"""
            try:
                base_path = Path(dir_path) if dir_path != "." else Path.cwd()
                
                # Only scan within reasonable limits to avoid system directories
                for item in base_path.rglob("*"):
                    if item.is_file():
                        full_path = str(item.relative_to(Path.cwd()))
                        
                        # Skip excluded files using our enhanced exclusion logic
                        if _should_exclude_path(full_path):
                            continue
                        
                        file_name = item.name
                        all_files.append((file_name, full_path))
                        
                        # Check for exact match
                        if file_name == filename:
                            exact_matches.append(full_path)
                            
            except Exception as e:
                print(f"Direct filesystem scan error: {e}")
        
        # Start scanning from project root
        scan_directory(".")
        
        # Apply path context filtering if provided
        if path_context:
            exact_matches = _filter_by_path_context(exact_matches, path_context)
        
        # Find similar matches using simple string similarity
        similar_matches = []
        if not exact_matches:
            for file_name, full_path in all_files:
                # Simple fuzzy matching - check if filename is similar
                if _is_similar_filename(filename, file_name):
                    similar_matches.append(full_path)
            
            # Apply path context filtering to similar matches too
            if path_context:
                similar_matches = _filter_by_path_context(similar_matches, path_context)
        
        return exact_matches, similar_matches
        
    except Exception as e:
        print(f"Error searching for file: {e}")
        return [], []

def _direct_file_read(file_path: str) -> str:
    """Direct file reading fallback when MCP is not available"""
    try:
        # Security: only read files within current directory and subdirectories
        path = Path(file_path).resolve()
        cwd = Path.cwd().resolve()
        
        # Check if path is within current working directory
        try:
            path.relative_to(cwd)
        except ValueError:
            return "Error: Access denied - file outside project directory"
        
        if not path.exists():
            return f"Error: File '{file_path}' does not exist"
        
        if not path.is_file():
            return f"Error: '{file_path}' is not a file"
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"File: {file_path}\nSize: {len(content)} characters\n\nContent:\n{content}"
        
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"


def smart_file_resolution(filename: str, user_message: str = "") -> str:
    """Enhanced file resolution with smart search and user interaction"""
    # First try direct path (backward compatibility)
    result = mcp_file_system_read_sync(filename)
    
    # Check if we got an error that indicates we should try smart search
    server_error = "Server" in result and "not initialized" in result
    file_not_found = "Error: File" in result and "does not exist" in result
    
    # If file was read successfully (no relevant errors), return it
    if not (server_error or file_not_found):
        return result
    
    # If MCP server failed, try direct file read first
    if server_error:
        direct_result = _direct_file_read(filename)
        if not direct_result.startswith("Error:"):
            return direct_result
    
    # Extract path context from user message for smarter search
    path_context = extract_path_context_from_message(user_message) if user_message else ""
    
    # File not found directly, search for it with path context
    print(f"🔍 Searching for '{filename}' in project...")
    if path_context:
        print(f"    🎯 Using path context: '{path_context}'")
    
    exact_matches, similar_matches = search_for_file_in_project(filename, path_context)
    
    if len(exact_matches) == 1:
        # Single exact match - use it automatically
        found_path = exact_matches[0]
        print(f"📁 Found: {found_path}")
        
        # Try MCP first, fall back to direct read
        mcp_result = mcp_file_system_read_sync(found_path)
        if "Server" in mcp_result and "not initialized" in mcp_result:
            return _direct_file_read(found_path)
        else:
            return mcp_result
    
    elif len(exact_matches) > 1:
        # Multiple exact matches - prompt user
        prompt = f"📁 Multiple files named '{filename}' found:\n"
        for i, path in enumerate(exact_matches, 1):
            # Get file size for context
            file_info = mcp_file_system_read_sync(path)
            if "Size:" in file_info:
                size_line = [line for line in file_info.split('\n') if line.startswith('Size:')][0]
                size = size_line.split('Size: ')[1].split(' ')[0]
                prompt += f"{i}. {path} ({size} characters)\n"
            else:
                prompt += f"{i}. {path}\n"
        
        prompt += "\nPlease specify the full path or use a more specific query to disambiguate."
        return prompt
    
    elif similar_matches:
        # No exact matches but found similar ones
        prompt = f"❌ File '{filename}' not found. Did you mean:\n"
        for i, path in enumerate(similar_matches[:5], 1):  # Limit to top 5 suggestions
            prompt += f"{i}. {path}\n"
        prompt += "\nPlease specify the correct filename or full path."
        return prompt
    
    else:
        # No matches at all
        return f"❌ File '{filename}' not found in project. Use 'list directory' to see available files."