# Multi-Agent LangGraph Chatbot with Real Tool Integration

A conversational AI system with 7 specialized agents and real external tool capabilities (web search & file operations).

## Quick Start

```bash
# Run the chatbot
uv run python src/main.py

# Type 'q' to quit and save conversation history
```

## Project Structure

```
├── src/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Core chatbot with LangGraph multi-agent system
│   ├── mcp_client/
│   │   ├── __init__.py       # MCP client module
│   │   ├── config.py         # Real MCP client configuration
│   │   └── tools.py          # MCP tool routing and execution
│   └── servers/
│       ├── __init__.py       # Servers module
│       ├── filesystem_server.py  # FastMCP filesystem server
│       └── web_search_server.py  # FastMCP web search server
├── pyproject.toml            # Dependencies and project config
├── uv.lock                   # Dependency lock file
├── conversation_history.json # Persistent chat history (runtime)
├── CLAUDE.md                 # This documentation
└── README.md                 # Project README
```

## Agent Types & Capabilities

| Agent | Triggers | Tools | Purpose |
|-------|----------|-------|---------|
| **therapist** | emotions, feelings, problems | none | Emotional support and empathy |
| **logical** | facts, "what is", research | web_search | Objective information and analysis |
| **planner** | "how to", plans, steps | none | Step-by-step project planning |
| **coder** | code, files, programming | file_system | Code help and file operations |
| **brainstormer** | ideas, creativity, names | web_search | Creative idea generation |
| **debater** | pros/cons, arguments | web_search | Multi-perspective analysis |
| **teacher** | explanations, "explain" | web_search | Simple explanations of complex topics |

## Tool Capabilities

### 🔍 Web Search (DuckDuckGo)
- **Triggers**: "search", "find", "what is", "research", "explain"
- **Free API** - no keys required
- **Agents**: logical, brainstormer, debater, teacher

### 📁 File System
- **Triggers**: "file", "read", "write", "code", "show", "display", "open"
- **Auto-extracts filenames** from natural language (e.g., "read main.py")
- **Agents**: coder

## Example Interactions

**File Reading:**
```
You: Please read the CLAUDE.md file
📁 Reading file: CLAUDE.md
Assistant: Here's the content of CLAUDE.md: [shows actual file contents]
```

**Web Search:**
```
You: What is machine learning?
🔍 Executing web search for: What is machine learning?
Assistant: Based on search results, machine learning is... [real DuckDuckGo results]
```

**Emotional Support:**
```
You: I'm feeling overwhelmed with work
Assistant: I understand that work can feel overwhelming... [no tools, pure support]
```

## Technical Architecture

### Message Flow
```
User Input → Classification → Agent Selection → Tool Execution → LLM Response
```

### Smart Tool Triggering
- **Automatic filename detection**: "read CLAUDE.md" → extracts "CLAUDE.md" → reads file
- **Keyword-based activation**: Web search triggers on research keywords
- **Agent-specific tools**: Only coder has file access, only some agents have web search

### Key Implementation Features
- **Real external data**: DuckDuckGo API and actual file operations
- **Persistent chat history**: Conversations saved between sessions
- **Graceful error handling**: Tools fail gracefully with informative messages
- **Async/sync compatibility**: Handles mixed async tools with sync LangGraph

## Configuration

### Agent Tools Assignment
```python
MCP_TOOLS_CONFIG = {
    "logical": ["web_search"],
    "brainstormer": ["web_search"], 
    "debater": ["web_search"],
    "teacher": ["web_search"],
    "coder": ["file_system"],
    "therapist": [],  # No tools - pure conversation
    "planner": []     # No tools - planning only
}
```

### Dependencies
- **langchain-ollama**: Local LLM integration
- **langgraph**: Multi-agent workflow
- **mcp**: Model Context Protocol client
- **requests**: HTTP requests for web search
- **pydantic**: Data validation

## Troubleshooting

### Common Issues
- **"Server not initialized"**: MCP manager needs initialization (handled automatically in main.py)
- **Web search timeout**: DuckDuckGo API delays (has fallback responses)
- **File not found**: Check file path and permissions

### Debug Commands
```bash
# Test web search directly
uv run python -c "from web_search import search_web; print(search_web('test'))"

# Verify dependencies
uv run python -c "import mcp, requests, langchain_core; print('All imports OK')"
```

## Development Notes

### Architecture Philosophy
- **Direct tool integration** rather than separate MCP server processes
- **Zero-cost implementation** using free APIs only
- **Modular design** with clear separation of concerns
- **Production-ready** with proper error handling and fallbacks

### File Organization
- `src/main.py`: Core LangGraph logic and agent definitions
- `src/mcp_client/config.py`: Real MCP client management and server connections
- `src/mcp_client/tools.py`: MCP tool routing and smart triggering logic
- `src/servers/filesystem_server.py`: FastMCP filesystem operations server
- `src/servers/web_search_server.py`: FastMCP DuckDuckGo search server

The system provides real MCP server capabilities with process isolation, standards compliance, and compatibility with Claude Desktop, Cursor, and other MCP clients.