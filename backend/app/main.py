"""
AAA: AlphA AI - FastAPI 메인 애플리케이션
"""
import os  
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'  
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import chat_router, memories_router, calendar_router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트"""
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    logger.info(f"Data Directory: {settings.DATA_DIR}")
    
    # 데이터 디렉토리 생성
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    yield
    
    logger.info(f"Shutting down {settings.APP_NAME}")


# FastAPI 앱 생성
app = FastAPI(
    title="AAA: AlphA AI",
    description="개인 비서형 AI - 장기 기억 기반",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 - 환경변수 기반
settings = get_settings()
cors_origins = ["http://localhost:3000"]  # 개발용 항상 포함
if settings.FRONTEND_ORIGIN:
    cors_origins.append(settings.FRONTEND_ORIGIN)
logger.info(f"CORS allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat_router)
app.include_router(memories_router)
app.include_router(calendar_router)


@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "name": "AAA: AlphA AI",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/healthz")
async def healthz():
    """Railway health check endpoint"""
    return {"ok": True}


@app.get("/health")
async def health():
    """상세 헬스 체크"""
    settings = get_settings()
    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL
    }
