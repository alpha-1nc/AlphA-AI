"""
pgvector 기반 벡터 데이터베이스
ChromaDB와 동일한 인터페이스로 구현
"""
import logging
from typing import Optional
from datetime import datetime

from ..models import Memory

logger = logging.getLogger(__name__)


class PgVectorDB:
    """pgvector 벡터 DB 매니저 - ChromaDB 인터페이스 호환"""
    
    TABLE_NAME = "memories_vector"
    
    def __init__(self, postgres_db):
        """
        Args:
            postgres_db: PostgresDB 인스턴스
        """
        self.db = postgres_db
        self._init_table()
    
    def _init_table(self):
        """벡터 테이블 초기화"""
        # 1536: OpenAI ada-002 기본 차원
        # 384: multilingual-e5-small 차원
        # 동적으로 처리하기 위해 1536으로 설정 (더 작은 벡터도 호환)
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            text TEXT NOT NULL,
            summary TEXT NOT NULL,
            confidence REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_message_id TEXT,
            embedding vector(384)
        );
        
        CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_type 
            ON {self.TABLE_NAME}(type);
        CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_created_at 
            ON {self.TABLE_NAME}(created_at DESC);
        """
        
        try:
            self.db.execute(create_table_sql)
            logger.info(f"pgvector table '{self.TABLE_NAME}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pgvector table: {e}")
            raise
    
    def upsert_memory(self, memory: Memory, embedding: Optional[list[float]] = None):
        """메모리 벡터 저장/업데이트"""
        if embedding:
            # 벡터 포함 upsert
            sql = f"""
            INSERT INTO {self.TABLE_NAME} 
                (id, type, text, summary, confidence, created_at, source_message_id, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                type = EXCLUDED.type,
                text = EXCLUDED.text,
                summary = EXCLUDED.summary,
                confidence = EXCLUDED.confidence,
                source_message_id = EXCLUDED.source_message_id,
                embedding = EXCLUDED.embedding
            """
            # 벡터를 PostgreSQL vector 형식으로 변환
            embedding_str = f"[{','.join(map(str, embedding))}]"
            params = (
                memory.id,
                memory.type.value,
                memory.text,
                memory.summary,
                memory.confidence,
                memory.created_at,
                memory.source_message_id,
                embedding_str
            )
        else:
            # 벡터 없이 upsert
            sql = f"""
            INSERT INTO {self.TABLE_NAME} 
                (id, type, text, summary, confidence, created_at, source_message_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                type = EXCLUDED.type,
                text = EXCLUDED.text,
                summary = EXCLUDED.summary,
                confidence = EXCLUDED.confidence,
                source_message_id = EXCLUDED.source_message_id
            """
            params = (
                memory.id,
                memory.type.value,
                memory.text,
                memory.summary,
                memory.confidence,
                memory.created_at,
                memory.source_message_id
            )
        
        self.db.execute(sql, params)
        logger.info(f"Memory upserted to pgvector: {memory.id}")
    
    def search(
        self, 
        query_embedding: list[float], 
        top_k: int = 5
    ) -> list[tuple[str, float, dict]]:
        """
        코사인 유사도 검색
        
        Returns:
            list of (id, distance, metadata)
        """
        # 벡터를 PostgreSQL vector 형식으로 변환
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # 코사인 거리 검색 (1 - cosine_similarity)
        sql = f"""
        SELECT 
            id,
            type,
            summary,
            confidence,
            created_at,
            source_message_id,
            embedding <=> %s::vector AS distance
        FROM {self.TABLE_NAME}
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        
        try:
            rows = self.db.fetch_all(sql, (embedding_str, embedding_str, top_k))
            
            results = []
            for row in rows:
                metadata = {
                    "type": row["type"],
                    "summary": row["summary"],
                    "confidence": row["confidence"],
                    "created_at": row["created_at"].isoformat() if isinstance(row["created_at"], datetime) else row["created_at"],
                }
                if row.get("source_message_id"):
                    metadata["source_message_id"] = row["source_message_id"]
                
                results.append((row["id"], row["distance"], metadata))
            
            logger.info(f"pgvector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"pgvector search failed: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """메모리 벡터 삭제"""
        try:
            sql = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
            self.db.execute(sql, (memory_id,))
            logger.info(f"Memory deleted from pgvector: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from pgvector: {e}")
            return False
    
    def get_count(self) -> int:
        """저장된 벡터 수"""
        sql = f"SELECT COUNT(*) as count FROM {self.TABLE_NAME}"
        result = self.db.fetch_one(sql)
        return result["count"] if result else 0


# 싱글톤 인스턴스
_pgvector_db: Optional[PgVectorDB] = None


def get_pgvector_db() -> PgVectorDB:
    """pgvector DB 싱글톤 인스턴스 반환"""
    global _pgvector_db
    
    if _pgvector_db is None:
        from .postgres import get_postgres_db
        postgres_db = get_postgres_db()
        _pgvector_db = PgVectorDB(postgres_db)
    
    return _pgvector_db
