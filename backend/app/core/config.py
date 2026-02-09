from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: Optional[str] = None
    supabase_jwks_url: Optional[str] = None
    openai_api_key: str
    openai_api_base: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    tavily_api_key: str
    google_trends_mcp_url: str = "http://google-trends-mcp:8080/mcp/"
    google_trends_mcp_jwt_secret: str
    secret_key: str
    algorithm: str = "HS256"
    use_mock_agent: bool = False
    access_token_expire_minutes: int = 30
    environment: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
