"""
메모리 후보 추출 및 필터링
저장 정책 적용
"""
import re
import json
import logging
from typing import Optional

from ..models import MemoryCandidate, MemoryType, MEMORY_TYPE_PRIORITY
from ..config import Settings

logger = logging.getLogger(__name__)

# PII 감지 패턴
PII_PATTERNS = [
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 이메일
    r'\b\d{6}[-\s]?\d{7}\b',  # 주민번호
    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 카드번호
    r'\b(?:password|passwd|pwd|비밀번호|비번)[:\s=]*\S+',  # 비밀번호
    r'\b(?:token|토큰|api[_-]?key|apikey)[:\s=]*\S+',  # 토큰/API키
    r'\b(?:secret|시크릿)[:\s=]*\S+',  # 시크릿
    r'\b(?:account|계정|아이디|id)[:\s=]*\S+',  # 계정
    r'\b인증[코드번호]?\s*[:=]?\s*\d{4,8}\b',  # 인증코드
    r'\b(?:sk-|pk-|bearer\s+)[a-zA-Z0-9_-]+',  # API 키 형태
]


class MemoryExtractor:
    """메모리 추출 및 저장 정책 관리"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.min_confidence = settings.MEMORY_MIN_CONFIDENCE
        self._pii_patterns = [re.compile(p, re.IGNORECASE) for p in PII_PATTERNS]
    
    def parse_llm_response(self, response: str) -> list[MemoryCandidate]:
        """
        LLM 응답을 MemoryCandidate 리스트로 파싱
        """
        candidates = []
        
        # JSON 배열 추출 시도
        try:
            # 코드 블록 내 JSON 처리
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    for item in data:
                        try:
                            candidate = MemoryCandidate(
                                type=MemoryType(item["type"]),
                                text=item["text"],
                                summary=item["summary"],
                                confidence=float(item["confidence"]),
                                pii_flag=bool(item.get("pii_flag", False))
                            )
                            candidates.append(candidate)
                        except (KeyError, ValueError) as e:
                            logger.warning(f"Failed to parse candidate: {e}")
                            continue
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
        
        return candidates
    
    def detect_pii(self, text: str) -> bool:
        """
        텍스트에서 PII 감지
        """
        for pattern in self._pii_patterns:
            if pattern.search(text):
                logger.warning(f"PII detected in text")
                return True
        return False
    
    def apply_storage_policy(
        self, 
        candidates: list[MemoryCandidate]
    ) -> list[MemoryCandidate]:
        """
        저장 정책 적용
        
        정책:
        1. confidence >= 0.5 만 저장 (개인 정보/취향 저장을 위해 완화)
        2. pii_flag=true 또는 PII 패턴 감지 시 저장 금지
        3. 우선순위 순 정렬 (decision > preference > plan > profile > episode)
        """
        filtered = []
        
        for candidate in candidates:
            # 신뢰도 검사
            if candidate.confidence < self.min_confidence:
                logger.info(f"Skipping low confidence memory: {candidate.confidence}")
                continue
            
            # PII 검사 (LLM 플래그 + 자체 패턴 검사)
            if candidate.pii_flag:
                logger.info("Skipping memory with pii_flag=true")
                continue
            
            if self.detect_pii(candidate.text) or self.detect_pii(candidate.summary):
                logger.info("Skipping memory with detected PII")
                continue
            
            filtered.append(candidate)
        
        # 우선순위 순 정렬 (높은 우선순위 먼저)
        filtered.sort(
            key=lambda x: MEMORY_TYPE_PRIORITY.get(x.type, 0),
            reverse=True
        )
        
        return filtered
    
    async def extract_and_filter(
        self, 
        llm_response: str
    ) -> list[MemoryCandidate]:
        """
        LLM 응답 파싱 + 저장 정책 적용
        """
        candidates = self.parse_llm_response(llm_response)
        logger.info(f"Parsed {len(candidates)} memory candidates")
        
        filtered = self.apply_storage_policy(candidates)
        logger.info(f"After policy: {len(filtered)} candidates passed")
        
        return filtered
