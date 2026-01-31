"""
설정 관리 모듈
환경변수 로드 및 앱 설정
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """앱 설정"""
    
    # 앱 기본 설정
    APP_NAME: str = "AAA: AlphA AI"
    DEBUG: bool = False
    
    # LLM 제공자 선택 (openai 또는 gemini)
    LLM_PROVIDER: Literal["openai", "gemini"] = "openai"
    
    # OpenAI 설정
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Gemini 설정
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # 임베딩 설정
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    EMBEDDING_DEVICE: str = "cpu"
    
    # 데이터베이스 경로
    DATA_DIR: Path = Path("./data")
    SQLITE_DB_PATH: str = "memories.db"
    CHROMA_PERSIST_DIR: str = "chroma_db"
    
    # 메모리 검색 설정
    MEMORY_TOP_K: int = 5
    MEMORY_MIN_CONFIDENCE: float = 0.4
    MEMORY_DEDUP_THRESHOLD: float = 0.05
    
    # CORS 설정
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Google OAuth 설정
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/calendar/auth/callback"
    GOOGLE_SCOPES: str = "https://www.googleapis.com/auth/calendar"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def sqlite_path(self) -> Path:
        return self.DATA_DIR / self.SQLITE_DB_PATH
    
    @property
    def chroma_path(self) -> Path:
        return self.DATA_DIR / self.CHROMA_PERSIST_DIR


@lru_cache()
def get_settings() -> Settings:
    """싱글톤 설정 인스턴스 반환"""
    return Settings()
