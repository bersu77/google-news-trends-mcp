from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.middleware.auth import AuthMiddleware
from app.routers import auth, chat, health
from app.services.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to initialize database: {e}")
        # Continue application startup even if DB fails
    yield


app = FastAPI(
    title="AI Chat System",
    description="Production-quality AI chat system with LangChain ReAct agent",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(health.router, prefix="/api/health", tags=["health"])


@app.get("/")
async def root():
    return {"message": "AI Chat System API"}
