from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from security.verification import verify_mcp_jwt

from auth import UnauthorizedError, check_authorization
from tools import BrowserManager, register_tools



class LooseAcceptMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = [
                (k, v) for k, v in scope["headers"] 
                if k.lower() != b"accept"
            ]
            headers.append((b"accept", b"application/json, text/event-stream"))
            scope["headers"] = headers
        await self.app(scope, receive, send)


class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            verify_mcp_jwt(request.headers)
        except UnauthorizedError as exc:
            return JSONResponse({"error": {"message": str(exc)}}, status_code=401)
        return await call_next(request)


@asynccontextmanager
async def lifespan(_: FastMCP):
    async with BrowserManager():
        yield


mcp = FastMCP(
    name="google-news-trends",
    instructions="This server provides tools to search, analyze, and summarize Google News articles and Google Trends",
    lifespan=lifespan,
    on_duplicate_tools="replace",
)

register_tools(mcp)

# Authentication enabled for MCP endpoint
mcp_http_app = mcp.http_app(path="/", middleware=[
    Middleware(LooseAcceptMiddleware),
    Middleware(AuthorizationMiddleware)
])
