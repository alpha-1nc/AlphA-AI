"""
SQLite 데이터베이스 관리
"""
import sqlite3
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from ..models import Memory, MemoryType, MemoryCreate

logger = logging.getLogger(__name__)


class SQLiteDB:
    """SQLite 데이터베이스 매니저"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()
    
    def _ensure_dir(self):
        """데이터 디렉토리 생성"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """테이블 초기화"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_message_id TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_source_message_id ON memories(source_message_id)
            """)
            logger.info("SQLite database initialized")
    
    def insert_memory(self, memory: MemoryCreate) -> Memory:
        """메모리 저장"""
        memory_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memories (id, type, text, summary, confidence, created_at, source_message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (memory_id, memory.type.value, memory.text, memory.summary, 
                 memory.confidence, created_at, memory.source_message_id)
            )
        
        logger.info(f"Memory inserted: {memory_id} ({memory.type})")
        return Memory(
            id=memory_id,
            type=memory.type,
            text=memory.text,
            summary=memory.summary,
            confidence=memory.confidence,
            created_at=created_at,
            source_message_id=memory.source_message_id
        )
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """ID로 메모리 조회"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?",
                (memory_id,)
            ).fetchone()
        
        if row:
            return self._row_to_memory(row)
        return None

    def get_memory_by_text(self, text: str) -> Optional[Memory]:
        """텍스트로 메모리 조회 (정확히 일치)"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE text = ? LIMIT 1",
                (text,)
            ).fetchone()
        
        if row:
            return self._row_to_memory(row)
        return None
    
    def get_memory_by_source_message_id(self, source_message_id: str) -> Optional[Memory]:
        """source_message_id로 메모리 조회"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE source_message_id = ? LIMIT 1",
                (source_message_id,)
            ).fetchone()
        
        if row:
            return self._row_to_memory(row)
        return None
    
    def get_memories_by_ids(self, memory_ids: list[str]) -> list[Memory]:
        """여러 ID로 메모리 조회"""
        if not memory_ids:
            return []
        
        placeholders = ",".join("?" * len(memory_ids))
        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders})",
                memory_ids
            ).fetchall()
        
        return [self._row_to_memory(row) for row in rows]
    
    def list_memories(self, limit: int = 20, offset: int = 0) -> tuple[list[Memory], int]:
        """메모리 목록 조회 (페이지네이션)"""
        with self._get_connection() as conn:
            # 전체 개수
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            
            # 목록 조회
            rows = conn.execute(
                """
                SELECT * FROM memories 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            ).fetchall()
        
        memories = [self._row_to_memory(row) for row in rows]
        return memories, total
    
    def delete_memory(self, memory_id: str) -> bool:
        """메모리 삭제"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,)
            )
            deleted = cursor.rowcount > 0
        
        if deleted:
            logger.info(f"Memory deleted: {memory_id}")
        return deleted
    
    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        """Row를 Memory 모델로 변환"""
        return Memory(
            id=row["id"],
            type=MemoryType(row["type"]),
            text=row["text"],
            summary=row["summary"],
            confidence=row["confidence"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            source_message_id=row["source_message_id"] if "source_message_id" in row.keys() else None
        )
