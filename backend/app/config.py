"""
설정 관리 모듈
환경변수 로드 및 앱 설정
"""
import os
import sys
import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Literal, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


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
    
    # 데이터베이스 경로 (Railway 볼륨 지원)
    DATA_DIR: Path = Path("./data")
    SQLITE_PATH: Optional[str] = None  # 전체 경로 또는 DATA_DIR 상대 경로
    CHROMA_DIR: Optional[str] = None   # 전체 경로 또는 DATA_DIR 상대 경로
    
    # 레거시 호환 (기존 .env 파일 지원)
    SQLITE_DB_PATH: str = "app.db"
    CHROMA_PERSIST_DIR: str = "chroma"
    
    # 메모리 검색 설정
    MEMORY_TOP_K: int = 5
    MEMORY_MIN_CONFIDENCE: float = 0.4
    MEMORY_DEDUP_THRESHOLD: float = 0.05
    
    # CORS 설정
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    FRONTEND_ORIGIN: Optional[str] = None  # 배포 환경 프론트엔드 URL
    
    # Google OAuth 설정
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/calendar/auth/callback"
    GOOGLE_SCOPES: str = "https://www.googleapis.com/auth/calendar"
    
    # ===================
    # Phase B: Feature Flags (안전 마이그레이션)
    # ===================
    
    # 저장소 선택 (chroma → pgvector 점진 전환)
    MEMORY_STORE: Literal["chroma", "pgvector"] = "chroma"
    
    # 토큰 저장소 선택 (sqlite → postgres 점진 전환)
    TOKEN_STORE: Literal["sqlite", "postgres"] = "sqlite"
    
    # Dual-write: pgvector 전환 시 chroma에도 동시 저장 (테스트/검증용)
    MEMORY_DUAL_WRITE: bool = False
    
    # PostgreSQL 연결 (Phase B에서 사용)
    DATABASE_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def sqlite_path(self) -> Path:
        """SQLite 경로 반환 (절대/상대 경로 지원)"""
        if self.SQLITE_PATH:
            p = Path(self.SQLITE_PATH)
            return p if p.is_absolute() else self.DATA_DIR / p
        return self.DATA_DIR / self.SQLITE_DB_PATH
    
    @property
    def chroma_path(self) -> Path:
        """Chroma 경로 반환 (절대/상대 경로 지원)"""
        if self.CHROMA_DIR:
            p = Path(self.CHROMA_DIR)
            return p if p.is_absolute() else self.DATA_DIR / p
        return self.DATA_DIR / self.CHROMA_PERSIST_DIR
    
    def validate_required_envs(self) -> list[str]:
        """필수 환경변수 검증. 누락된 변수 목록 반환."""
        missing = []
        
        # LLM API 키 검증
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY (LLM_PROVIDER=openai)")
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY (LLM_PROVIDER=gemini)")
        
        # Google OAuth 검증 (선택적이지만 경고)
        if not self.GOOGLE_CLIENT_ID:
            logger.warning("GOOGLE_CLIENT_ID not set - Calendar features disabled")
        if not self.GOOGLE_CLIENT_SECRET:
            logger.warning("GOOGLE_CLIENT_SECRET not set - Calendar features disabled")
        
        return missing


@lru_cache()
def get_settings() -> Settings:
    """싱글톤 설정 인스턴스 반환"""
    settings = Settings()
    
    # 필수 환경변수 검증
    missing = settings.validate_required_envs()
    if missing:
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        # 프로덕션에서는 시작 중단
        if not settings.DEBUG:
            sys.exit(f"FATAL: {error_msg}")
    
    return settings

