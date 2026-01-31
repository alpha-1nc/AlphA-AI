"""
메모리 서비스
SQLite + Chroma 통합 관리
"""
import logging
from typing import Optional
from pathlib import Path

from ..config import Settings, get_settings
from ..database import SQLiteDB, ChromaDB
from ..models import (
    Memory, 
    MemoryCreate, 
    MemoryCandidate,
    Citation
)
from .embedding import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


class MemoryService:
    """메모리 저장/검색/삭제 통합 서비스"""
    
    def __init__(
        self, 
        settings: Settings,
        embedding_service: EmbeddingService
    ):
        self.settings = settings
        self.embedding_service = embedding_service
        
        # 데이터 디렉토리 생성
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # SQLite 초기화
        self.sqlite = SQLiteDB(settings.sqlite_path)
        
        # Chroma 초기화
        self.chroma = ChromaDB(
            persist_dir=settings.chroma_path,
            embedding_function=embedding_service.embedding_function
        )
        
        logger.info("MemoryService initialized")
    
    def save_memory(self, candidate: MemoryCandidate, dedup: bool = True) -> Optional[Memory]:
        """
        메모리 저장 (SQLite + Chroma)
        중복 검사: 유사한 기억이 있으면 저장 스킵
        
        Returns:
            Memory: 저장된 메모리 객체
            None: 중복으로 스킵된 경우
        """
        # 1. 중복 검사: 저장 전 유사도 체크 (필요 시)
        embedding = self.embedding_service.embed_document(candidate.text)
        
        if dedup and self.chroma.get_count() > 0:
            # Chroma에서 가장 유사한 메모리 1개 검색
            similar_results = self.chroma.search(embedding, top_k=1)
            
            if similar_results:
                memory_id, distance, metadata = similar_results[0]
                
                # distance가 threshold 이하면 중복으로 판단 (cosine distance: 낮을수록 유사)
                if distance <= self.settings.MEMORY_DEDUP_THRESHOLD:
                    logger.info(
                        f"Memory dedup skipped: distance={distance:.4f} <= {self.settings.MEMORY_DEDUP_THRESHOLD} "
                        f"(similar to: {memory_id})"
                    )
                    return None
        
        # 2. 중복이 아니면 저장
        # SQLite에 저장
        memory_create = MemoryCreate(
            type=candidate.type,
            text=candidate.text,
            summary=candidate.summary,
            confidence=candidate.confidence
        )
        memory = self.sqlite.insert_memory(memory_create)
        
        # Chroma에 임베딩과 함께 저장
        self.chroma.upsert_memory(memory, embedding)
        
        logger.info(f"Memory saved: {memory.id} ({memory.type})")
        return memory
    
    def check_duplicate(self, candidate: MemoryCandidate) -> Optional[tuple[str, float]]:
        """
        중복 검사만 수행 (저장하지 않음)
        
        Returns:
            tuple[existing_id, distance]: 중복이면 (기존 메모리 ID, 거리) 반환
            None: 중복이 아닌 경우
        """
        embedding = self.embedding_service.embed_document(candidate.text)
        
        if self.chroma.get_count() > 0:
            similar_results = self.chroma.search(embedding, top_k=1)
            
            if similar_results:
                memory_id, distance, metadata = similar_results[0]
                
                if distance <= self.settings.MEMORY_DEDUP_THRESHOLD:
                    return (memory_id, distance)
        
        return None

    def get_memory_by_text(self, text: str) -> Optional[Memory]:
        """텍스트로 메모리 조회 (정확히 일치)"""
        return self.sqlite.get_memory_by_text(text)
    
    def get_memory_by_source_message_id(self, source_message_id: str) -> Optional[Memory]:
        """source_message_id로 메모리 조회"""
        return self.sqlite.get_memory_by_source_message_id(source_message_id)
    
    def search_memories(
        self, 
        query: str, 
        top_k: Optional[int] = None
    ) -> list[Memory]:
        """
        쿼리로 관련 메모리 검색
        """
        top_k = top_k or self.settings.MEMORY_TOP_K
        
        # 쿼리 임베딩 생성
        query_embedding = self.embedding_service.embed_query(query)
        
        # Chroma에서 검색
        results = self.chroma.search(query_embedding, top_k)
        
        if not results:
            return []
        
        # SQLite에서 상세 정보 조회
        memory_ids = [r[0] for r in results]
        memories = self.sqlite.get_memories_by_ids(memory_ids)
        
        # 검색 순서 유지
        id_to_memory = {m.id: m for m in memories}
        ordered_memories = [id_to_memory[mid] for mid in memory_ids if mid in id_to_memory]
        
        return ordered_memories
    
    def get_memories_as_context(self, query: str) -> list[dict]:
        """
        LLM 컨텍스트용 메모리 조회
        """
        memories = self.search_memories(query)
        return [
            {
                "id": m.id,
                "type": m.type.value,
                "summary": m.summary,
                "text": m.text,
                "created_at": m.created_at.isoformat()
            }
            for m in memories
        ]
    
    def get_citations(self, memories: list[Memory]) -> list[Citation]:
        """
        메모리를 Citation으로 변환
        """
        return [
            Citation(
                id=m.id,
                type=m.type,
                summary=m.summary,
                created_at=m.created_at
            )
            for m in memories
        ]
    
    def list_memories(
        self, 
        limit: int = 20, 
        offset: int = 0
    ) -> tuple[list[Memory], int]:
        """
        메모리 목록 조회
        """
        return self.sqlite.list_memories(limit, offset)
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        메모리 삭제 (SQLite + Chroma)
        """
        # SQLite에서 삭제
        sqlite_deleted = self.sqlite.delete_memory(memory_id)
        
        # Chroma에서 삭제
        chroma_deleted = self.chroma.delete_memory(memory_id)
        
        if sqlite_deleted or chroma_deleted:
            logger.info(f"Memory deleted: {memory_id}")
            return True
        return False
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        ID로 메모리 조회
        """
        return self.sqlite.get_memory(memory_id)


# 싱글톤 인스턴스
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """메모리 서비스 싱글톤 반환"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(
            settings=get_settings(),
            embedding_service=get_embedding_service()
        )
    return _memory_service
