from tavily import TavilyClient
import logging
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class TavilySearchTool:
    def __init__(self):
        self.client = TavilyClient(api_key=settings.tavily_api_key)
    
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        try:
            result = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=True,
                include_raw_content=False
            )
            
            return {
                "success": True,
                "query": query,
                "results": result.get("results", []),
                "answer": result.get("answer", ""),
                "sources": [r.get("url", "") for r in result.get("results", [])]
            }
            
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "answer": "I encountered an error while searching the web.",
                "sources": []
            }


def get_tavily_tool() -> TavilySearchTool:
    return TavilySearchTool()
