"""
Chroma 벡터 데이터베이스 관리
"""
import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..models import Memory

logger = logging.getLogger(__name__)


class ChromaDB:
    """Chroma 벡터 DB 매니저"""
    
    COLLECTION_NAME = "memories"
    
    def __init__(self, persist_dir: Path, embedding_function):
        self.persist_dir = persist_dir
        self.embedding_function = embedding_function
        self._ensure_dir()
        self._init_client()
    
    def _ensure_dir(self):
        """디렉토리 생성"""
        self.persist_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_client(self):
        """Chroma 클라이언트 초기화"""
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function
        )
        logger.info(f"Chroma collection initialized: {self.COLLECTION_NAME}")
    
    def upsert_memory(self, memory: Memory, embedding: Optional[list[float]] = None):
        """메모리 벡터 저장/업데이트"""
        metadata = {
            "type": memory.type.value,
            "summary": memory.summary,
            "confidence": memory.confidence,
            "created_at": memory.created_at.isoformat()
        }
        
        # source_message_id가 있으면 메타데이터에 추가
        if memory.source_message_id:
            metadata["source_message_id"] = memory.source_message_id
        
        if embedding:
            self.collection.upsert(
                ids=[memory.id],
                embeddings=[embedding],
                documents=[memory.text],
                metadatas=[metadata]
            )
        else:
            self.collection.upsert(
                ids=[memory.id],
                documents=[memory.text],
                metadatas=[metadata]
            )
        
        logger.info(f"Memory upserted to Chroma: {memory.id}")
    
    def search(
        self, 
        query_embedding: list[float], 
        top_k: int = 5
    ) -> list[tuple[str, float, dict]]:
        """
        유사도 검색
        
        Returns:
            list of (id, distance, metadata)
        """
        if self.collection.count() == 0:
            logger.info("Chroma collection is empty, skipping search")
            return []
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["distances", "metadatas", "documents"]
        )
        
        if not results["ids"] or not results["ids"][0]:
            return []
        
        search_results = []
        for i, memory_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results["distances"] else 0.0
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            search_results.append((memory_id, distance, metadata))
        
        logger.info(f"Chroma search returned {len(search_results)} results")
        return search_results
    
    def delete_memory(self, memory_id: str) -> bool:
        """메모리 벡터 삭제"""
        try:
            self.collection.delete(ids=[memory_id])
            logger.info(f"Memory deleted from Chroma: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from Chroma: {e}")
            return False
    
    def get_count(self) -> int:
        """저장된 벡터 수"""
        return self.collection.count()
