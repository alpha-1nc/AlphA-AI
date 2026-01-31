"""
메모리 관련 Pydantic 모델 정의
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """기억 타입 (우선순위 순)"""
    DECISION = "decision"       # 결정
    PREFERENCE = "preference"   # 선호
    PLAN = "plan"              # 계획
    PROFILE = "profile"        # 프로필
    EPISODE = "episode"        # 에피소드


# 타입별 우선순위 (숫자가 높을수록 높은 우선순위)
MEMORY_TYPE_PRIORITY = {
    MemoryType.DECISION: 5,
    MemoryType.PREFERENCE: 4,
    MemoryType.PLAN: 3,
    MemoryType.PROFILE: 2,
    MemoryType.EPISODE: 1,
}


class MemoryCandidate(BaseModel):
    """memory_candidate_extractor 출력 형식"""
    type: MemoryType
    text: str = Field(..., description="원본 텍스트")
    summary: str = Field(..., description="요약")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    pii_flag: bool = Field(default=False, description="개인정보 포함 여부")


class MemoryCreate(BaseModel):
    """메모리 생성 요청"""
    type: MemoryType
    text: str
    summary: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_message_id: Optional[str] = None


class Memory(BaseModel):
    """저장된 메모리"""
    id: str
    type: MemoryType
    text: str
    summary: str
    confidence: float
    created_at: datetime
    source_message_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class Citation(BaseModel):
    """채팅 응답의 근거 인용"""
    id: str
    type: MemoryType
    summary: str
    created_at: datetime


class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str = Field(..., min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    """채팅 응답"""
    reply: str
    citations: list[Citation] = Field(default_factory=list)


class MemorySearchRequest(BaseModel):
    """메모리 검색 요청"""
    query: str = Field(..., min_length=1)


class MemoryListResponse(BaseModel):
    """메모리 목록 응답"""
    memories: list[Memory]
    total: int
    limit: int
    offset: int
