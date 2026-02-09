import httpx
import asyncio
import jwt
import time

async def test_detailed():
    try:
        # Generate JWT
        secret = "mcp_jwt_secret_8K9xN2mP5qR7vL3wS6tY1uJ4fZ8cX5bA9dE2gH6iK0oP3nM7jV1sW4rT8yU5fZ"
        payload = {
            "exp": int(time.time()) + 300,
            "iat": int(time.time())
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Test MCP call
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = "http://google-trends-mcp:8080/mcp/"
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_google_trends",
                    "arguments": {"keywords": ["Python"], "timeframe": "today 3-m"}
                }
            }
            
            print(f"URL: {url}")
            print(f"Headers: {headers}")
            print(f"Payload: {data}")
            
            response = await client.post(url, json=data, headers=headers)
            
            print(f"\nStatus: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\nException: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

asyncio.run(test_detailed())
