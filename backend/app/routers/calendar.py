"""
Google Calendar API 라우터
OAuth 인증 및 일정 조회/생성
"""
import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from ..services.google_calendar import get_calendar_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


# === Request/Response Models ===

class AuthUrlResponse(BaseModel):
    """OAuth URL 응답"""
    url: str


class CreateEventRequest(BaseModel):
    """일정 생성 요청"""
    summary: str
    start_iso: str  # ISO 8601 format
    end_iso: str    # ISO 8601 format
    description: Optional[str] = None
    location: Optional[str] = None


class EventResponse(BaseModel):
    """일정 응답"""
    id: str
    summary: str
    start: str
    end: str
    location: str


# === Endpoints ===

@router.get("/auth/url", response_model=AuthUrlResponse)
async def get_auth_url():
    """
    Google OAuth 동의 URL 생성
    - access_type=offline, prompt=consent 포함하여 refresh_token 확실히 받음
    """
    try:
        calendar_service = get_calendar_service()
        auth_url = calendar_service.get_authorization_url()
        return {"url": auth_url}
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")


@router.get("/auth/callback")
async def oauth_callback(code: str = Query(...)):
    """
    Google OAuth callback 처리
    - code를 token으로 교환 → SQLite 저장
    """
    try:
        calendar_service = get_calendar_service()
        calendar_service.handle_oauth_callback(code)
        
        # 간단한 HTML 응답
        return {
            "message": "Google Calendar 연동 완료!",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.get("/events", response_model=list[EventResponse])
async def get_events(
    time_min: Optional[str] = Query(None, description="ISO 8601 format (default: today 00:00 KST)"),
    time_max: Optional[str] = Query(None, description="ISO 8601 format (default: tomorrow 00:00 KST)")
):
    """
    Calendar events 조회
    - 기본값: 오늘 00:00 ~ 내일 00:00 (Asia/Seoul)
    - primary 캘린더에서 조회
    """
    try:
        calendar_service = get_calendar_service()
        events = calendar_service.list_events(time_min=time_min, time_max=time_max)
        return events
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@router.post("/events", response_model=EventResponse)
async def create_event(request: CreateEventRequest):
    """
    Calendar event 생성
    - events.insert로 일정 생성
    - 생성된 event 정보 반환
    """
    try:
        calendar_service = get_calendar_service()
        event = calendar_service.create_event(
            summary=request.summary,
            start_iso=request.start_iso,
            end_iso=request.end_iso,
            description=request.description,
            location=request.location
        )
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")
