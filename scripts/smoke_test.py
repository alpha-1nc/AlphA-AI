#!/usr/bin/env python3
"""
AAA: AlphA AI - Smoke Test Script
배포 환경 또는 로컬 환경에서 기본 기능 테스트

Usage:
    python scripts/smoke_test.py                          # 기본값: http://localhost:8000
    python scripts/smoke_test.py --base-url https://api.yourdomain.com
    python scripts/smoke_test.py --base-url http://localhost:8000 --verbose
"""

import argparse
import sys
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Tuple, Optional

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def make_request(
    url: str,
    method: str = "GET",
    data: Optional[dict] = None,
    timeout: int = 30
) -> Tuple[int, dict]:
    """HTTP 요청 수행"""
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    
    req = Request(url, data=body, headers=headers, method=method)
    
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        try:
            error_body = json.loads(e.read().decode("utf-8"))
        except:
            error_body = {"detail": str(e)}
        return e.code, error_body
    except URLError as e:
        return 0, {"detail": f"Connection failed: {e.reason}"}


def test_healthz(base_url: str, verbose: bool = False) -> bool:
    """GET /healthz 테스트"""
    url = f"{base_url}/healthz"
    status, body = make_request(url)
    
    success = status == 200 and body.get("ok") is True
    
    if verbose:
        print(f"  URL: {url}")
        print(f"  Response: {json.dumps(body, ensure_ascii=False)}")
    
    return success


def test_health(base_url: str, verbose: bool = False) -> bool:
    """GET /health 테스트"""
    url = f"{base_url}/health"
    status, body = make_request(url)
    
    success = status == 200 and body.get("status") == "healthy"
    
    if verbose:
        print(f"  URL: {url}")
        print(f"  Response: {json.dumps(body, ensure_ascii=False)}")
    
    return success


def test_chat(base_url: str, verbose: bool = False) -> bool:
    """POST /chat 테스트 - 간단한 메시지 전송"""
    url = f"{base_url}/chat"
    data = {"message": "안녕하세요, 테스트입니다."}
    
    status, body = make_request(url, method="POST", data=data, timeout=60)
    
    success = status == 200 and "reply" in body
    
    if verbose:
        print(f"  URL: {url}")
        print(f"  Request: {json.dumps(data, ensure_ascii=False)}")
        if success:
            reply = body.get("reply", "")
            print(f"  Reply: {reply[:100]}..." if len(reply) > 100 else f"  Reply: {reply}")
        else:
            print(f"  Error: {json.dumps(body, ensure_ascii=False)}")
    
    return success


def test_memories(base_url: str, verbose: bool = False) -> bool:
    """GET /memories 테스트 - 목록 조회"""
    url = f"{base_url}/memories?limit=5"
    status, body = make_request(url)
    
    success = status == 200 and "memories" in body
    
    if verbose:
        print(f"  URL: {url}")
        if success:
            print(f"  Total memories: {body.get('total', 0)}")
        else:
            print(f"  Error: {json.dumps(body, ensure_ascii=False)}")
    
    return success


def test_calendar_auth_url(base_url: str, verbose: bool = False) -> bool:
    """GET /calendar/auth/url 테스트 - OAuth URL 생성"""
    url = f"{base_url}/calendar/auth/url"
    status, body = make_request(url)
    
    success = status == 200 and "url" in body
    
    if verbose:
        print(f"  URL: {url}")
        if success:
            auth_url = body.get("url", "")
            print(f"  Auth URL: {auth_url[:80]}..." if len(auth_url) > 80 else f"  Auth URL: {auth_url}")
        else:
            print(f"  Error: {json.dumps(body, ensure_ascii=False)}")
    
    return success


def run_tests(base_url: str, verbose: bool = False) -> bool:
    """모든 테스트 실행"""
    tests = [
        ("Health (Railway)", test_healthz),
        ("Health (Detailed)", test_health),
        ("Chat API", test_chat),
        ("Memories API", test_memories),
        ("Calendar OAuth URL", test_calendar_auth_url),
    ]
    
    print(f"\n{'='*50}")
    print(f"AAA Smoke Test - Target: {base_url}")
    print(f"{'='*50}\n")
    
    all_passed = True
    
    for name, test_func in tests:
        print(f"Testing: {name}...")
        try:
            passed = test_func(base_url, verbose)
            if passed:
                print(f"  {GREEN}✓ PASSED{RESET}\n")
            else:
                print(f"  {RED}✗ FAILED{RESET}\n")
                all_passed = False
        except Exception as e:
            print(f"  {RED}✗ ERROR: {e}{RESET}\n")
            all_passed = False
    
    print(f"{'='*50}")
    if all_passed:
        print(f"{GREEN}All tests passed!{RESET}")
    else:
        print(f"{RED}Some tests failed.{RESET}")
    print(f"{'='*50}\n")
    
    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="AAA: AlphA AI Smoke Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/smoke_test.py
  python scripts/smoke_test.py --base-url https://api.yourdomain.com
  python scripts/smoke_test.py --verbose
        """
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed request/response info"
    )
    
    args = parser.parse_args()
    
    # trailing slash 제거
    base_url = args.base_url.rstrip("/")
    
    success = run_tests(base_url, args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
