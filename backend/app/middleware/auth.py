from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt
from jose.exceptions import JWTError
import logging
import httpx
import time
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache for JWKS
jwks_cache = {
    "keys": None,
    "last_fetched": 0,
    "ttl": 3600  # 1 hour
}

async def get_jwks():
    now = time.time()
    if jwks_cache["keys"] and (now - jwks_cache["last_fetched"] < jwks_cache["ttl"]):
        return jwks_cache["keys"]
    
    try:
        if not settings.supabase_jwks_url:
            # Construct from supabase_url if not explicitly provided
            jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        else:
            jwks_url = settings.supabase_jwks_url
            
        logger.info(f"Fetching JWKS from: {jwks_url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=5.0)
            logger.info(f"JWKS response status: {response.status_code}")
            if response.status_code == 200:
                jwks_cache["keys"] = response.json()
                jwks_cache["last_fetched"] = now
                logger.info("Successfully cached JWKS")
                return jwks_cache["keys"]
            else:
                logger.warning(f"Failed to fetch JWKS, status: {response.status_code}, body: {response.text[:100]}")
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {type(e).__name__}: {str(e)}")
    
    return None

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/health") or request.url.path == "/":
            return await call_next(request)

        if request.url.path.startswith("/api/auth/login") or request.url.path.startswith("/api/auth/refresh") or request.url.path.startswith("/api/auth/signup"):
            return await call_next(request)

        # Allow OPTIONS requests for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid authorization header")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"}
            )

        token = auth_header.split(" ")[1]
        
        try:
            # Try to decode without verification first to check header
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg")
            logger.info(f"JWT Header Alg: {alg}")
            
            payload = None
            if alg == "ES256":
                # Likely a Supabase token, use JWKS
                jwks = await get_jwks()
                if jwks:
                    logger.info("Attempting ES256 decode using JWKS")
                    try:
                        payload = jwt.decode(
                            token,
                            jwks,
                            algorithms=["ES256"],
                            audience="authenticated"
                        )
                        logger.info("ES256 decode successful")
                    except JWTError as e:
                        logger.warning(f"ES256 verification failed: {str(e)}")
                        # If it's ES256 and verification failed, don't fallback to HS256
                        # because it's guaranteed to fail there too.
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": f"Supabase token validation failed: {str(e)}"}
                        )
                else:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Authentication server (Supabase) keys unavailable"}
                    )
            
            if not payload:
                # Fallback to HS256 with local secret
                logger.info(f"Attempting {settings.algorithm} decode with local secret")
                try:
                    payload = jwt.decode(
                        token,
                        settings.secret_key,
                        algorithms=[settings.algorithm],
                        audience="authenticated"
                    )
                    logger.info(f"{settings.algorithm} decode successful")
                except JWTError as e:
                    logger.warning(f"Local token validation failed: {str(e)}")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": f"Invalid token: {str(e)}"}
                    )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID"
                )
            
            request.state.user_id = user_id
            request.state.email = payload.get("email")
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid token: {str(e)}"}
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication failed"}
            )

        return await call_next(request)
