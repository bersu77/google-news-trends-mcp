from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer
import httpx
import logging
from typing import Dict, Any

from app.schemas.auth import LoginRequest, LoginResponse, RefreshTokenRequest
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.supabase_url}/auth/v1/token?grant_type=password",
                json={
                    "email": request.email,
                    "password": request.password,
                    "gotrue_meta_security": {}
                },
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"Supabase login failed: {response.status_code} - {response.text}")
                try:
                    error_data = response.json()
                    if error_data.get("error_code") == "email_not_confirmed" or "Email not confirmed" in error_data.get("msg", ""):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email not confirmed. Please check your inbox and verify your email address."
                        )
                except ValueError:
                    pass
                    
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            data = response.json()
            
            return LoginResponse(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                user=data["user"]
            )
            
    except httpx.RequestError as e:
        logger.error(f"Authentication service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )


@router.post("/signup", response_model=LoginResponse)
async def signup(request: LoginRequest):
    try:
        async with httpx.AsyncClient(verify=False) as client:
            # Supabase signup
            response = await client.post(
                f"{settings.supabase_url}/auth/v1/signup",
                json={
                    "email": request.email,
                    "password": request.password,
                },
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Supabase signup failed: {response.status_code} - {response.text}")
                try:
                    error_data = response.json()
                    detail = error_data.get("msg", error_data.get("message", "Signup failed"))
                except:
                    detail = response.text or "Signup failed"
                    
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=detail
                )
            
            data = response.json()
            
            if "access_token" not in data:
                # This happens if email confirmation is required
                return LoginResponse(
                    access_token="",
                    refresh_token="",
                    user=data.get("user", {})
                )

            return LoginResponse(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                user=data["user"]
            )
            
    except httpx.RequestError as e:
        logger.error(f"Signup service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Signup service unavailable"
        )


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.supabase_url}/auth/v1/token?grant_type=refresh_token",
                json={
                    "refresh_token": request.refresh_token
                },
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            data = response.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"]
            }
            
    except httpx.RequestError as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )


@router.get("/me")
async def get_current_user(request: Request):
    return {
        "id": request.state.user_id,
        "email": request.state.email
    }
