"""
기억 관리 API 라우터
GET /memories
POST /memories (수동 저장)
POST /memories/search
DELETE /memories/{id}
"""
import logging
from fastapi import APIRouter, HTTPException, Query

from ..models import Memory, MemorySearchRequest, MemoryListResponse, MemoryCreate
from ..services.memory import get_memory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("", response_model=Memory, status_code=201)
async def create_memory(memory_data: MemoryCreate):
    """
    수동 기억 저장
    사용자가 명시적으로 기억하기를 원하는 메시지 저장
    """
    try:
        memory_service = get_memory_service()
        
        # 중복 체크 1: source_message_id가 있으면 먼저 확인
        if memory_data.source_message_id:
            existing_memory = memory_service.get_memory_by_source_message_id(memory_data.source_message_id)
            if existing_memory:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "reason": "dedup",
                        "existing_id": existing_memory.id,
                        "message": "이미 동일한 기억이 저장되어 있습니다"
                    }
                )
        
        # 중복 체크 2: 텍스트로도 확인 (정확히 일치)
        existing_memory = memory_service.get_memory_by_text(memory_data.text)
        if existing_memory:
            raise HTTPException(
                status_code=409,
                detail={
                    "reason": "dedup",
                    "existing_id": existing_memory.id,
                    "message": "이미 동일한 기억이 저장되어 있습니다"
                }
            )
        
        # SQLite에 직접 저장 (source_message_id 포함)
        saved_memory = memory_service.sqlite.insert_memory(memory_data)
        
        # Chroma에도 저장
        embedding = memory_service.embedding_service.embed_document(memory_data.text)
        memory_service.chroma.upsert_memory(saved_memory, embedding)
        
        logger.info(f"Memory manually saved: {saved_memory.id} (source_message_id: {memory_data.source_message_id})")
        
        return saved_memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create memory error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기억 저장 오류: {str(e)}")


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    limit: int = Query(default=20, ge=1, le=1000, description="페이지당 개수"),
    offset: int = Query(default=0, ge=0, description="시작 위치")
):
    """
    기억 목록 조회 (페이지네이션)
    """
    try:
        memory_service = get_memory_service()
        memories, total = memory_service.list_memories(limit=limit, offset=offset)
        
        return MemoryListResponse(
            memories=memories,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"List memories error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기억 목록 조회 오류: {str(e)}")


@router.post("/search", response_model=list[Memory])
async def search_memories(request: MemorySearchRequest):
    """
    기억 검색
    """
    try:
        memory_service = get_memory_service()
        memories = memory_service.search_memories(request.query)
        return memories
    except Exception as e:
        logger.error(f"Search memories error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기억 검색 오류: {str(e)}")


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """
    기억 삭제
    """
    try:
        memory_service = get_memory_service()
        
        # 존재 여부 확인
        memory = memory_service.get_memory(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="기억을 찾을 수 없습니다")
        
        # 삭제
        deleted = memory_service.delete_memory(memory_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="기억 삭제 실패")
        
        return {"message": "기억이 삭제되었습니다", "id": memory_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete memory error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기억 삭제 오류: {str(e)}")


@router.get("/{memory_id}", response_model=Memory)
async def get_memory(memory_id: str):
    """
    기억 상세 조회
    """
    try:
        memory_service = get_memory_service()
        memory = memory_service.get_memory(memory_id)
        
        if not memory:
            raise HTTPException(status_code=404, detail="기억을 찾을 수 없습니다")
        
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get memory error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기억 조회 오류: {str(e)}")
