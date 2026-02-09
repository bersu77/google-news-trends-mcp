import httpx
import asyncio
import json

async def test_mcp_endpoint():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test MCP endpoint without auth
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
            
            print("Testing MCP endpoint...")
            resp = await client.post('http://google-trends-mcp:8080/mcp', json=payload)
            print(f'Status: {resp.status_code}')
            print(f'Body: {resp.text}')
            
    except Exception as e:
        print(f'Error: {str(e)}')

asyncio.run(test_mcp_endpoint())
