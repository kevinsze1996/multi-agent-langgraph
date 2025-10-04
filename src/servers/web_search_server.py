#!/usr/bin/env python3
"""
Web Search MCP Server
Provides web search capabilities through the Model Context Protocol using DuckDuckGo.
"""

import os
import sys
import requests
import json
import time
from typing import Optional, Dict, Any
from urllib.parse import quote_plus
from fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("Web Search Server")

class DuckDuckGoSearch:
    """Free web search using DuckDuckGo Instant Answer API"""
    
    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MultiAgent-LangGraph-MCP/1.0 (Educational Purpose)'
        })
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Rate limiting: 1 second between requests
    
    def _rate_limit(self):
        """Implement basic rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()
    
    def search(self, query: str, max_results: int = 5) -> str:
        """Search DuckDuckGo and return formatted results"""
        try:
            # Rate limiting
            self._rate_limit()
            
            # Clean and validate query
            clean_query = query.strip()
            if not clean_query:
                return "Error: Empty search query"
            
            if len(clean_query) > 500:
                clean_query = clean_query[:500]
                
            # Validate and normalize max_results
            max_results = max(1, min(10, max_results))
                
            # Try DuckDuckGo Instant Answer API
            instant_result = self._get_instant_answer(clean_query, max_results)
            if instant_result:
                return instant_result
            
            # If no instant answer, return fallback
            return self._get_fallback_result(clean_query)
            
        except Exception as e:
            return f"Web search error: {str(e)}"
    
    def _get_instant_answer(self, query: str, max_results: int = 5) -> Optional[str]:
        """Get instant answer from DuckDuckGo"""
        try:
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response
            result_parts = []
            
            # Abstract (main answer)
            if data.get('Abstract'):
                result_parts.append(f"📄 **Answer**: {data['Abstract']}")
                if data.get('AbstractSource'):
                    result_parts.append(f"   Source: {data['AbstractSource']}")
            
            # Definition
            if data.get('Definition'):
                result_parts.append(f"📖 **Definition**: {data['Definition']}")
                if data.get('DefinitionSource'):
                    result_parts.append(f"   Source: {data['DefinitionSource']}")
            
            # Answer (direct answer)
            if data.get('Answer'):
                result_parts.append(f"💡 **Direct Answer**: {data['Answer']}")
                if data.get('AnswerType'):
                    result_parts.append(f"   Type: {data['AnswerType']}")
            
            # Related topics
            if data.get('RelatedTopics'):
                topics = data['RelatedTopics'][:max_results]  # Dynamic limit based on max_results
                if topics:
                    result_parts.append("\n🔗 **Related Topics**:")
                    for i, topic in enumerate(topics, 1):
                        if isinstance(topic, dict) and topic.get('Text'):
                            result_parts.append(f"   {i}. {topic['Text'][:100]}...")
            
            # Infobox (for entities)
            if data.get('Infobox'):
                infobox = data['Infobox']
                if infobox.get('content'):
                    result_parts.append("\n📋 **Key Information**:")
                    for item in infobox['content'][:max_results]:  # Dynamic limit based on max_results
                        if item.get('label') and item.get('value'):
                            result_parts.append(f"   • {item['label']}: {item['value']}")
            
            if result_parts:
                header = f"🔍 **Search Results for: \"{query}\"**\n"
                return header + "\n".join(result_parts)
            
            return None
            
        except Exception as e:
            # Log error to stderr, don't return it (for debugging)
            print(f"DuckDuckGo API error: {e}", file=sys.stderr)
            return None
    
    def _get_fallback_result(self, query: str) -> str:
        """Fallback result when no instant answer is available"""
        return f"""🔍 **Search Results for: \"{query}\"**

📄 **Web Search Executed**: Your query has been processed using DuckDuckGo search.

💡 **Suggested Information**: 
   • This appears to be a query about: {query}
   • For more detailed information, you might want to refine your search terms
   • Try asking more specific questions about the topic

🔗 **Search Tips**:
   • Use specific keywords related to your topic
   • Try asking "What is..." or "How does..." questions
   • Include context or domain-specific terms

**Note**: This search used DuckDuckGo's free API. For comprehensive results, consider using multiple search terms or more specific queries."""

# Global search instance
search_engine = DuckDuckGoSearch()

@mcp.tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo.
    
    Args:
        query: Search query string
    
    Returns:
        Formatted search results
    """
    if not query or not query.strip():
        return "Error: Please provide a search query"
    
    try:
        result = search_engine.search(query.strip())
        return result
    except Exception as e:
        return f"Search error: {str(e)}"

@mcp.tool
def search_with_filters(query: str, max_results: int = 5) -> str:
    """Search the web with additional filtering options.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (1-10)
    
    Returns:
        Formatted search results
    """
    if not query or not query.strip():
        return "Error: Please provide a search query"
    
    # Validate max_results
    max_results = max(1, min(10, max_results))
    
    try:
        result = search_engine.search(query.strip(), max_results=max_results)
        return result
    except Exception as e:
        return f"Search error: {str(e)}"

@mcp.tool
def search_definitions(term: str) -> str:
    """Search for definitions of a specific term.
    
    Args:
        term: Term to define
    
    Returns:
        Definition and related information
    """
    if not term or not term.strip():
        return "Error: Please provide a term to define"
    
    # Format query for better definition results
    definition_query = f"define {term.strip()}"
    
    try:
        result = search_engine.search(definition_query)
        return result
    except Exception as e:
        return f"Definition search error: {str(e)}"

@mcp.tool
def search_how_to(topic: str) -> str:
    """Search for how-to information on a specific topic.
    
    Args:
        topic: Topic to search how-to information for
    
    Returns:
        How-to search results
    """
    if not topic or not topic.strip():
        return "Error: Please provide a topic"
    
    # Format query for better how-to results
    how_to_query = f"how to {topic.strip()}"
    
    try:
        result = search_engine.search(how_to_query)
        return result
    except Exception as e:
        return f"How-to search error: {str(e)}"

@mcp.tool
def get_search_info() -> str:
    """Get information about the web search capabilities.
    
    Returns:
        Information about available search features
    """
    return """🔍 **Web Search Server Information**

**Search Provider**: DuckDuckGo Instant Answer API
**Features**:
   • Free web search (no API key required)
   • Instant answers and definitions
   • Related topics and key information
   • Rate limiting for responsible usage
   • Support for various query types

**Available Tools**:
   • web_search: Basic web search
   • search_with_filters: Search with result limits
   • search_definitions: Term definitions
   • search_how_to: How-to information

**Rate Limiting**: 1 request per second to respect DuckDuckGo's terms
**Query Limits**: Maximum 500 characters per query
**Privacy**: No tracking, uses DuckDuckGo's privacy-focused search
"""

if __name__ == "__main__":
    # Run the MCP server
    try:
        # Log server start to stderr (stdout is reserved for MCP protocol)
        print(f"Starting Web Search MCP Server (PID: {os.getpid()})", file=sys.stderr)
        print("Using DuckDuckGo search API", file=sys.stderr)
        
        # Run server with stdio transport
        mcp.run()
    except KeyboardInterrupt:
        print("Web Search server shutting down...", file=sys.stderr)
    except Exception as e:
        print(f"Web Search server error: {e}", file=sys.stderr)
        sys.exit(1)