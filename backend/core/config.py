import os
from typing import List

class Settings:
    PROJECT_NAME: str = "PHC Bridge"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./phc_bridge.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "phc-bridge-secure-hex-key-secret-2026-ayushman-proto")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # AI Engine Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "auto")  # 'gemini', 'openai', or 'auto' (fallback to intelligent local mock)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
