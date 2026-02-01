"""
PostgreSQL 기반 Google OAuth 토큰 저장소
GoogleTokenDB(SQLite)와 동일한 인터페이스
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PostgresTokenDB:
    """PostgreSQL 기반 Google OAuth 토큰 저장소"""
    
    TABLE_NAME = "google_tokens"
    
    def __init__(self, postgres_db):
        """
        Args:
            postgres_db: PostgresDB 인스턴스
        """
        self.db = postgres_db
        self._init_table()
    
    def _init_table(self):
        """google_tokens 테이블 초기화"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expiry INTEGER NOT NULL,
            scope TEXT NOT NULL
        )
        """
        
        try:
            self.db.execute(create_table_sql)
            logger.info(f"PostgreSQL table '{self.TABLE_NAME}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize {self.TABLE_NAME} table: {e}")
            raise
    
    def save_token(
        self,
        access_token: str,
        refresh_token: Optional[str],
        expiry: int,
        scope: str
    ):
        """토큰 저장 (단일 사용자, UPSERT)"""
        sql = f"""
        INSERT INTO {self.TABLE_NAME} (id, access_token, refresh_token, expiry, scope)
        VALUES (1, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            access_token = EXCLUDED.access_token,
            refresh_token = COALESCE(EXCLUDED.refresh_token, {self.TABLE_NAME}.refresh_token),
            expiry = EXCLUDED.expiry,
            scope = EXCLUDED.scope
        """
        
        self.db.execute(sql, (access_token, refresh_token, expiry, scope))
        logger.info("Google token saved to PostgreSQL successfully")
    
    def get_token(self) -> Optional[dict]:
        """저장된 토큰 조회"""
        sql = f"""
        SELECT access_token, refresh_token, expiry, scope 
        FROM {self.TABLE_NAME} 
        WHERE id = 1
        """
        
        row = self.db.fetch_one(sql)
        
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
        sql = f"DELETE FROM {self.TABLE_NAME} WHERE id = 1"
        self.db.execute(sql)
        logger.info("Google token deleted from PostgreSQL")


# 싱글톤 인스턴스
_postgres_token_db: Optional[PostgresTokenDB] = None


def get_postgres_token_db() -> PostgresTokenDB:
    """PostgreSQL Token DB 싱글톤 인스턴스 반환"""
    global _postgres_token_db
    
    if _postgres_token_db is None:
        from .postgres import get_postgres_db
        postgres_db = get_postgres_db()
        _postgres_token_db = PostgresTokenDB(postgres_db)
    
    return _postgres_token_db
