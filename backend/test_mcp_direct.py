import httpx
import asyncio
import json

async def test_direct_mcp():
    url = "http://google-trends-mcp:8080/mcp-direct"
    
    # Simple tool call to search_google_news
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search_google_news",
            "arguments": {
                "query": "AI news",
                "max_results": 1
            }
        },
        "id": 1
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"Calling tool via {url}...")
            resp = await client.post(url, json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_direct_mcp())
