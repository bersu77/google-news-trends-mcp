import httpx
import asyncio

async def test_simple():
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            url = "http://google-trends-mcp:8080/mcp/"
            
            # Simple POST test
            print(f"Testing POST to: {url}")
            response = await client.post(url, json={"test": "data"})
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Body: {response.text[:500]}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

asyncio.run(test_simple())
