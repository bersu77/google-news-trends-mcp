import httpx
import asyncio

async def test_root():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get('http://google-trends-mcp:8080/')
            print(f'GET / - Status: {r.status_code}')
            print(f'Body: {r.text[:200]}')
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(test_root())
