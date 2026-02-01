#!/usr/bin/env python3
"""
AAA: AlphA AI - Store Comparison Script
ChromaDB vs pgvector 검색 결과 비교 (dev-only)

Usage:
    python scripts/compare_stores.py "검색할 쿼리"
    python scripts/compare_stores.py "사용자가 좋아하는 음식" --top-k 10
"""

import argparse
import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from tabulate import tabulate


def get_embedding(text: str) -> list[float]:
    """텍스트를 임베딩 벡터로 변환"""
    from app.services.embedding import get_embedding_service
    
    embedding_service = get_embedding_service()
    return embedding_service.embed_text(text)


def search_chroma(query_embedding: list[float], top_k: int) -> list[dict]:
    """ChromaDB 검색"""
    from app.config import get_settings
    from app.database.chroma import ChromaDB
    from app.services.embedding import get_embedding_service
    
    settings = get_settings()
    embedding_service = get_embedding_service()
    
    chroma_db = ChromaDB(
        persist_dir=settings.chroma_path,
        embedding_function=embedding_service.get_chroma_embedding_function()
    )
    
    results = chroma_db.search(query_embedding, top_k)
    return [
        {
            "id": r[0],
            "distance": r[1],
            "type": r[2].get("type", ""),
            "summary": r[2].get("summary", "")[:50]
        }
        for r in results
    ]


def search_pgvector(query_embedding: list[float], top_k: int) -> list[dict]:
    """pgvector 검색"""
    try:
        from app.database.pgvector_db import get_pgvector_db
        
        pgvector_db = get_pgvector_db()
        results = pgvector_db.search(query_embedding, top_k)
        return [
            {
                "id": r[0],
                "distance": r[1],
                "type": r[2].get("type", ""),
                "summary": r[2].get("summary", "")[:50]
            }
            for r in results
        ]
    except Exception as e:
        print(f"pgvector 검색 실패: {e}")
        return []


def compare_results(chroma_results: list[dict], pgvector_results: list[dict]):
    """검색 결과 비교 및 출력"""
    print("\n" + "="*60)
    print("ChromaDB 결과")
    print("="*60)
    if chroma_results:
        print(tabulate(chroma_results, headers="keys", tablefmt="grid"))
    else:
        print("결과 없음")
    
    print("\n" + "="*60)
    print("pgvector 결과")
    print("="*60)
    if pgvector_results:
        print(tabulate(pgvector_results, headers="keys", tablefmt="grid"))
    else:
        print("결과 없음 (DATABASE_URL 설정 필요)")
    
    # ID 일치율 계산
    chroma_ids = set(r["id"] for r in chroma_results)
    pgvector_ids = set(r["id"] for r in pgvector_results)
    
    if chroma_ids and pgvector_ids:
        overlap = chroma_ids & pgvector_ids
        print(f"\n일치하는 ID 수: {len(overlap)} / {len(chroma_ids)} (ChromaDB)")
        print(f"일치율: {len(overlap) / len(chroma_ids) * 100:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="ChromaDB vs pgvector 검색 결과 비교"
    )
    parser.add_argument("query", help="검색 쿼리")
    parser.add_argument("--top-k", type=int, default=5, help="상위 K개 결과 (기본값: 5)")
    
    args = parser.parse_args()
    
    print(f"쿼리: {args.query}")
    print(f"Top-K: {args.top_k}")
    
    # 임베딩 생성
    print("\n임베딩 생성 중...")
    try:
        embedding = get_embedding(args.query)
        print(f"임베딩 차원: {len(embedding)}")
    except Exception as e:
        print(f"임베딩 생성 실패: {e}")
        sys.exit(1)
    
    # 검색 실행
    print("\n검색 실행 중...")
    chroma_results = search_chroma(embedding, args.top_k)
    pgvector_results = search_pgvector(embedding, args.top_k)
    
    # 결과 비교
    compare_results(chroma_results, pgvector_results)


if __name__ == "__main__":
    main()
