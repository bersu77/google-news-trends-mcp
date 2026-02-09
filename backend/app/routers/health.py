from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
import httpx

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "ai-chat-backend"}


@router.get("/dependencies")
async def check_dependencies():
    status = {
        "status": "healthy",
        "services": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://google-trends-mcp:8000/healthz", timeout=5.0)
            status["services"]["google_trends_mcp"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception:
            status["services"]["google_trends_mcp"] = "unreachable"
    
    return status
