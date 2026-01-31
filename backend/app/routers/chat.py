"""
채팅 API 라우터
POST /chat
"""
import logging
from fastapi import APIRouter, HTTPException

from ..models import ChatRequest, ChatResponse, Citation
from ..services.llm import get_llm_service
from ..services.memory import get_memory_service
from ..services.extractor import MemoryExtractor
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    채팅 API
    
    동작:
    1. Chroma에서 관련 기억 검색 (topK=5)
    2. 검색 결과를 근거로 LLM 답변 생성
    3. memory_candidate_extractor로 저장 후보 추출
    4. 저장 정책 적용 후 통과한 것만 저장
    """
    try:
        settings = get_settings()
        llm_service = get_llm_service()
        memory_service = get_memory_service()
        extractor = MemoryExtractor(settings)
        
        # 1. 관련 기억 검색
        logger.info(f"Searching memories for: {request.message[:50]}...")
        context_memories = memory_service.get_memories_as_context(request.message)
        logger.info(f"Found {len(context_memories)} relevant memories")
        
        # 2. LLM 응답 생성
        logger.info("Generating LLM response...")
        reply = await llm_service.generate_response(
            user_message=request.message,
            context_memories=context_memories
        )
        
        # 3. 기억 후보 추출 (별도 단계)
        logger.info("Extracting memory candidates...")
        conversation = f"사용자: {request.message}\nAI: {reply}"
        extraction_response = await llm_service.extract_memories(conversation)
        
        # 4. 저장 정책 적용 및 저장
        candidates = await extractor.extract_and_filter(extraction_response)
        logger.info(f"Candidates after filtering: {len(candidates)}")
        
        saved_count = 0
        skipped_count = 0
        for candidate in candidates:
            try:
                result = memory_service.save_memory(candidate)
                if result:
                    saved_count += 1
                    logger.info(f"Saved memory: {candidate.type} - {candidate.summary[:30]}...")
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error(f"Failed to save memory: {e}")
        
        logger.info(f"Memory save summary: saved={saved_count}, skipped={skipped_count}")
        
        # 5. 인용 정보 생성
        citations: list[Citation] = []
        if context_memories:
            used_memories = memory_service.search_memories(request.message)
            citations = memory_service.get_citations(used_memories)
        
        return ChatResponse(reply=reply, citations=citations)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"서버 설정 오류: {str(e)}. .env 파일을 확인하세요."
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류: {str(e)}")
