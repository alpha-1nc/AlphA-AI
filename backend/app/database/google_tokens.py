"""
Google OAuth 토큰 저장 관리
단일 사용자 토큰을 SQLite에 저장/조회
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class GoogleTokenDB:
    """Google OAuth 토큰 데이터베이스 관리"""
    
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
            logger.error(f"Google token DB error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """google_tokens 테이블 초기화"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS google_tokens (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expiry INTEGER NOT NULL,
                    scope TEXT NOT NULL
                )
            """)
            logger.info("Google tokens table initialized")
    
    def save_token(
        self,
        access_token: str,
        refresh_token: Optional[str],
        expiry: int,
        scope: str
    ):
        """토큰 저장 (단일 사용자, UPSERT)"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO google_tokens (id, access_token, refresh_token, expiry, scope)
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    access_token = excluded.access_token,
                    refresh_token = COALESCE(excluded.refresh_token, refresh_token),
                    expiry = excluded.expiry,
                    scope = excluded.scope
                """,
                (access_token, refresh_token, expiry, scope)
            )
        logger.info("Google token saved successfully")
    
    def get_token(self) -> Optional[dict]:
        """저장된 토큰 조회"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT access_token, refresh_token, expiry, scope FROM google_tokens WHERE id = 1"
            ).fetchone()
        
        if row:
            return {
                "access_token": row["access_token"],
                "refresh_token": row["refresh_token"],
                "expiry": row["expiry"],
                "scope": row["scope"]
            }
        return None
    
    def delete_token(self):
        """토큰 삭제"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM google_tokens WHERE id = 1")
        logger.info("Google token deleted")
