"""
로컬 임베딩 서비스
multilingual-e5-small 모델 사용 (CPU 동작)
"""
import logging
from typing import Optional
from functools import lru_cache

from chromadb import EmbeddingFunction, Documents, Embeddings

from ..config import get_settings, Settings

logger = logging.getLogger(__name__)


class LocalEmbeddingFunction(EmbeddingFunction):
    """Chroma용 로컬 임베딩 함수"""
    
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
    
    def _load_model(self):
        """모델 지연 로딩"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Embedding model loaded on {self.device}")
    
    def __call__(self, input: Documents) -> Embeddings:
        """문서 임베딩 생성"""
        self._load_model()
        # e5 모델은 query/passage prefix 권장
        # 저장 시에는 passage prefix 사용
        texts = [f"passage: {doc}" for doc in input]
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> list[float]:
        """검색 쿼리 임베딩 생성"""
        self._load_model()
        # 검색 시에는 query prefix 사용
        text = f"query: {query}"
        embedding = self._model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()
    
    def embed_document(self, document: str) -> list[float]:
        """문서 임베딩 생성"""
        self._load_model()
        text = f"passage: {document}"
        embedding = self._model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()


class EmbeddingService:
    """임베딩 서비스"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._embedding_fn: Optional[LocalEmbeddingFunction] = None
    
    @property
    def embedding_function(self) -> LocalEmbeddingFunction:
        """임베딩 함수 반환 (지연 초기화)"""
        if self._embedding_fn is None:
            self._embedding_fn = LocalEmbeddingFunction(
                model_name=self.settings.EMBEDDING_MODEL,
                device=self.settings.EMBEDDING_DEVICE
            )
        return self._embedding_fn
    
    def embed_query(self, query: str) -> list[float]:
        """검색 쿼리 임베딩"""
        return self.embedding_function.embed_query(query)
    
    def embed_document(self, document: str) -> list[float]:
        """문서 임베딩"""
        return self.embedding_function.embed_document(document)


# 싱글톤 인스턴스
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """임베딩 서비스 싱글톤 반환"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(get_settings())
    return _embedding_service
