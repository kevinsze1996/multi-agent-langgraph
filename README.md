# Multi-Agent LangGraph Chatbot with MCP Integration

A conversational AI system featuring 7 specialized agents and real external tool capabilities through Model Context Protocol (MCP) servers.

## Quick Start

```bash
# Run the chatbot
uv run python src/main.py

# Type 'q' to quit and save conversation history
```

## Features

- **7 Specialized Agents**: therapist, logical, planner, coder, brainstormer, debater, teacher
- **Real MCP Integration**: FastMCP servers for filesystem and web search operations
- **Custom MCP Client**: Bypasses buggy stdio_client with direct JSON-RPC implementation
- **Smart Tool Routing**: Automatic tool selection based on message content and agent type
- **Persistent History**: Conversation history saved between sessions

## Architecture

- **FastMCP Servers**: Real MCP protocol servers for external capabilities
- **Custom DirectMCP Client**: Direct JSON-RPC communication bypassing library issues
- **LangGraph Multi-Agent**: Intelligent agent selection and workflow management
- **Local LLM**: Uses Ollama llama3.2 for all agent responses

## Tools

- **= Web Search**: DuckDuckGo integration (free, no API key required)
- **=Á File System**: Secure file operations within project directory
- **> Agent Selection**: Automatic routing based on message intent

See `CLAUDE.md` for detailed documentation, usage examples, and technical architecture.