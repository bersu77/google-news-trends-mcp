import httpx
import asyncio

async def test_mcp():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test health endpoint
            resp = await client.get('http://google-trends-mcp:8080/healthz')
            print(f'Health check - Status: {resp.status_code}, Body: {resp.text}')
            
            # Test MCP endpoint
            from app.services.tools.google_trends_mcp import GoogleTrendsMCPTool
            tool = GoogleTrendsMCPTool()
            result = await tool.get_google_trends(['Python'])
            
            if result.get('success'):
                print('\n✅ MCP IS WORKING!')
                print(f'Result: {result.get("data", "")[:200]}...')
            else:
                print(f'\n❌ MCP FAILED: {result.get("error")}')
                
    except Exception as e:
        print(f'\n❌ CONNECTION ERROR: {str(e)}')

asyncio.run(test_mcp())
