import httpx
from jose import jwt
import logging
from typing import Dict, Any, List
import asyncio
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleTrendsMCPTool:
    def __init__(self):
        self.base_url = settings.google_trends_mcp_url.rstrip('/') + "-direct"
        self.jwt_secret = settings.google_trends_mcp_jwt_secret
    
    def _generate_jwt(self) -> str:
        payload = {
            "sub": "ai-chat-system",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=5),
            "aud": "google-trends-mcp",
            "iss": "ai-chat-system"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self._generate_jwt()}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                retries = 3
                for attempt in range(retries):
                    try:
                        response = await client.post(
                            self.base_url,
                            json=payload,
                            headers=headers
                        )
                        break
                    except (httpx.ConnectError, httpx.NetworkError) as e:
                        if attempt == retries - 1:
                            raise e
                        logger.warning(f"MCP connection failed (attempt {attempt+1}/{retries}): {str(e)}. Retrying...")
                        await asyncio.sleep(1 * (attempt + 1))
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("result"):
                        return {
                            "success": True,
                            "data": result["result"]["content"][0]["text"] if result["result"].get("content") else "",
                            "tool": tool_name,
                            "arguments": arguments
                        }
                    else:
                        return {
                            "success": False,
                            "error": "No result returned from MCP server",
                            "tool": tool_name,
                            "arguments": arguments
                        }
                else:
                    logger.error(f"MCP server error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"MCP server error: {response.status_code}",
                        "tool": tool_name,
                        "arguments": arguments
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"MCP server timeout for tool {tool_name}")
            return {
                "success": False,
                "error": "MCP server timeout",
                "tool": tool_name,
                "arguments": arguments
            }
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "arguments": arguments
            }
    
    async def search_google_news(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        return await self.call_tool("get_news_by_keyword", {
            "keyword": query,
            "max_results": max_results
        })
    
    async def get_google_trends(self, keywords: List[str], timeframe: str = "today 3-m") -> Dict[str, Any]:
        return await self.call_tool("get_trending_terms", {
            "keywords": keywords
        })
    
    async def analyze_trend_data(self, keywords: List[str], category: int = 0) -> Dict[str, Any]:
        return await self.call_tool("analyze_trend_data", {
            "keywords": keywords,
            "category": category
        })


def get_google_trends_tool() -> GoogleTrendsMCPTool:
    return GoogleTrendsMCPTool()
