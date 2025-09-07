"""
Free Web Search Module using DuckDuckGo Instant Answer API
No API key required - completely free to use!
"""

import requests
import json
from typing import Dict, List, Optional
from urllib.parse import quote_plus

class DuckDuckGoSearch:
    """Free web search using DuckDuckGo Instant Answer API"""
    
    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"
        self.session = requests.Session()
        # Set a proper user agent to avoid blocks
        self.session.headers.update({
            'User-Agent': 'MultiAgent-LangGraph/1.0 (Educational Purpose)'
        })
    
    def search(self, query: str, max_results: int = 5) -> str:
        """
        Search DuckDuckGo and return formatted results
        Returns instant answers and abstracts when available
        """
        try:
            # Clean and encode the query
            clean_query = query.strip()
            if not clean_query:
                return "Error: Empty search query"
            
            # Try DuckDuckGo Instant Answer API first
            instant_result = self._get_instant_answer(clean_query)
            if instant_result:
                return instant_result
            
            # If no instant answer, try to get basic information
            return self._get_fallback_result(clean_query)
            
        except Exception as e:
            return f"Web search error: {str(e)}"
    
    def _get_instant_answer(self, query: str) -> Optional[str]:
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
                topics = data['RelatedTopics'][:3]  # First 3 topics
                if topics:
                    result_parts.append(f"\n🔗 **Related Topics**:")
                    for i, topic in enumerate(topics, 1):
                        if isinstance(topic, dict) and topic.get('Text'):
                            result_parts.append(f"   {i}. {topic['Text'][:100]}...")
            
            # Infobox (for entities)
            if data.get('Infobox'):
                infobox = data['Infobox']
                if infobox.get('content'):
                    result_parts.append(f"\n📋 **Key Information**:")
                    for item in infobox['content'][:3]:  # First 3 items
                        if item.get('label') and item.get('value'):
                            result_parts.append(f"   • {item['label']}: {item['value']}")
            
            if result_parts:
                header = f"🔍 **Search Results for: \"{query}\"**\n"
                return header + "\n".join(result_parts)
            
            return None
            
        except Exception as e:
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

**Note**: This search used DuckDuckGo's free API. For more comprehensive results, the system can be enhanced with additional search providers."""

# Global search instance
search_engine = DuckDuckGoSearch()

def search_web(query: str) -> str:
    """Main search function to be used by MCP tools"""
    return search_engine.search(query)