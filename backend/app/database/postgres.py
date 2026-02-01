"""
PostgreSQL 데이터베이스 연결 모듈
Phase B: pgvector 및 토큰 저장소용
"""
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# psycopg2 동적 임포트 (설치되지 않으면 에러)
try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None
    pool = None
    RealDictCursor = None


class PostgresDB:
    """PostgreSQL 데이터베이스 연결 관리"""
    
    def __init__(self, database_url: str, min_conn: int = 1, max_conn: int = 10):
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 is not installed. Install with: pip install psycopg2-binary"
            )
        
        self.database_url = database_url
        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self.min_conn = min_conn
        self.max_conn = max_conn
        
        self._init_pool()
        self._ensure_extensions()
    
    def _init_pool(self):
        """Connection pool 초기화"""
        try:
            self._pool = pool.ThreadedConnectionPool(
                self.min_conn,
                self.max_conn,
                self.database_url
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise
    
    def _ensure_extensions(self):
        """필요한 확장(pgvector) 활성화"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # pgvector 확장 생성 (없으면)
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    conn.commit()
                    logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"Failed to enable pgvector extension: {e}")
            # 확장 설치 권한이 없을 수 있음 - 경고만 출력
    
    @contextmanager
    def get_connection(self):
        """Connection pool에서 연결 가져오기"""
        if not self._pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """커서 컨텍스트 매니저"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cur = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"PostgreSQL error: {e}")
                raise
            finally:
                cur.close()
    
    def execute(self, query: str, params: tuple = None) -> None:
        """쿼리 실행 (결과 없음)"""
        with self.get_cursor(dict_cursor=False) as cur:
            cur.execute(query, params)
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[dict]:
        """단일 row 조회"""
        with self.get_cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()
    
    def fetch_all(self, query: str, params: tuple = None) -> list[dict]:
        """복수 row 조회"""
        with self.get_cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
    def close(self):
        """Connection pool 종료"""
        if self._pool:
            self._pool.closeall()
            logger.info("PostgreSQL connection pool closed")


# 싱글톤 인스턴스
_postgres_db: Optional[PostgresDB] = None


def get_postgres_db() -> PostgresDB:
    """PostgreSQL DB 싱글톤 인스턴스 반환"""
    global _postgres_db
    
    if _postgres_db is None:
        from ..config import get_settings
        settings = get_settings()
        
        if not settings.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL not set. Required for PostgreSQL/pgvector features."
            )
        
        _postgres_db = PostgresDB(settings.DATABASE_URL)
    
    return _postgres_db
