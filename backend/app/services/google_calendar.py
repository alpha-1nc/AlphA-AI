"""
Google Calendar OAuth 및 API 서비스
"""
import logging
import time
from datetime import datetime
from typing import Optional
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from fastapi import HTTPException

from ..config import get_settings
from ..database.google_tokens import GoogleTokenDB

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Google Calendar OAuth 및 API 관리"""
    
    def __init__(self):
        self.settings = get_settings()
        self.token_db = GoogleTokenDB(self.settings.sqlite_path)
        
        # OAuth 2.0 클라이언트 설정
        self.client_config = {
            "web": {
                "client_id": self.settings.GOOGLE_CLIENT_ID,
                "client_secret": self.settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [self.settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        
        self.scopes = self.settings.GOOGLE_SCOPES.split(",")
    
    def get_authorization_url(self) -> str:
        """OAuth 동의 URL 생성"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            redirect_uri=self.settings.GOOGLE_REDIRECT_URI
        )
        
        # access_type=offline, prompt=consent으로 refresh_token 확실히 받기
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true"
        )
        
        return auth_url
    
    def handle_oauth_callback(self, code: str) -> dict:
        """OAuth callback 처리 및 토큰 저장"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            redirect_uri=self.settings.GOOGLE_REDIRECT_URI
        )
        
        # code로 토큰 교환
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # refresh_token 누락 경고
        if not credentials.refresh_token:
            logger.warning(
                "refresh_token not received! Token will expire and require re-authentication. "
                "User may need to revoke app access and re-authorize with prompt=consent."
            )
        
        # 토큰 저장
        expiry_timestamp = int(credentials.expiry.timestamp()) if credentials.expiry else 0
        self.token_db.save_token(
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expiry=expiry_timestamp,
            scope=" ".join(self.scopes)
        )
        
        logger.info("OAuth token saved successfully")
        
        # 응답에 refresh_token 상태 포함
        return {
            "has_refresh_token": credentials.refresh_token is not None,
            "warning": None if credentials.refresh_token else (
                "refresh_token이 없습니다. 토큰 만료 시 재인증이 필요합니다. "
                "문제가 지속되면 Google 계정 설정에서 앱 액세스를 취소 후 다시 연동하세요."
            )
        }
    
    def _get_credentials(self) -> Credentials:
        """저장된 토큰으로 Credentials 생성 및 갱신"""
        token_data = self.token_db.get_token()
        
        if not token_data:
            raise HTTPException(
                status_code=401,
                detail="Google Calendar not connected. Please authorize first at /calendar/auth/url"
            )
        
        # DB 정보로 Credentials 객체 생성
        credentials = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.GOOGLE_CLIENT_ID,
            client_secret=self.settings.GOOGLE_CLIENT_SECRET,
            scopes=self.scopes
        )
        
        # 만료되었으면 갱신
        if credentials.expired and credentials.refresh_token:
            logger.info("Access token expired, refreshing...")
            credentials.refresh(Request())
            
            # [수정됨] 객체 속성을 바꾸지 않고, 갱신된 값을 DB에 저장
            new_expiry = int(credentials.expiry.timestamp()) if credentials.expiry else 0
            self.token_db.save_token(
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expiry=new_expiry,
                scope=token_data["scope"]
            )
            logger.info("Token refreshed and saved successfully")
        
        return credentials
    
    def list_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None
    ) -> list[dict]:
        """모든 캘린더의 events 조회"""
        credentials = self._get_credentials()
        service = build("calendar", "v3", credentials=credentials)
        
        # 기본값: 오늘 00:00 ~ 내일 00:00 (Asia/Seoul)
        if not time_min:
            from datetime import timezone, timedelta
            kst = timezone(timedelta(hours=9))
            today = datetime.now(kst).replace(hour=0, minute=0, second=0, microsecond=0)
            time_min = today.isoformat()
        
        if not time_max:
            from datetime import timezone, timedelta
            kst = timezone(timedelta(hours=9))
            tomorrow = datetime.now(kst).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            time_max = tomorrow.isoformat()
        
        all_events = []
        
        try:
            # 1. 사용자의 모든 캘린더 목록 가져오기
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            
            logger.info(f"Found {len(calendars)} calendars")
            
            # 2. 각 캘린더에서 일정 조회
            for calendar in calendars:
                calendar_id = calendar["id"]
                calendar_summary = calendar.get("summary", "Unknown Calendar")
                
                try:
                    # 개별 캘린더의 일정 조회
                    events_result = service.events().list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy="startTime"
                    ).execute()
                    
                    events = events_result.get("items", [])
                    
                    # 각 일정에 캘린더 정보 추가
                    for event in events:
                        all_events.append({
                            "id": event["id"],
                            "summary": event.get("summary", ""),
                            "start": event["start"].get("dateTime") or event["start"].get("date"),
                            "end": event["end"].get("dateTime") or event["end"].get("date"),
                            "location": event.get("location", ""),
                            "calendar_summary": calendar_summary  # 캘린더 이름 추가
                        })
                    
                    logger.info(f"Retrieved {len(events)} events from calendar '{calendar_summary}'")
                    
                except Exception as e:
                    # 특정 캘린더 조회 실패 시 해당 캘린더만 건너뛰고 계속 진행
                    logger.warning(f"Failed to retrieve events from calendar '{calendar_summary}' ({calendar_id}): {e}")
                    continue
            
            logger.info(f"Total {len(all_events)} events retrieved from all calendars")
            return all_events
            
        except Exception as e:
            logger.error(f"Failed to list calendars or events: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")
    
    def create_event(
        self,
        summary: str,
        start_iso: str,
        end_iso: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_summary: Optional[str] = None
    ) -> dict:
        """Calendar event 생성
        
        Args:
            summary: 일정 제목
            start_iso: 시작 시간 (ISO 8601)
            end_iso: 종료 시간 (ISO 8601)
            description: 상세 설명 (선택)
            location: 장소 (선택)
            calendar_summary: 캘린더 이름 (선택, 예: "업무", "개인")
        """
        credentials = self._get_credentials()
        service = build("calendar", "v3", credentials=credentials)
        
        # 캘린더 ID 결정
        calendar_id = "primary"
        
        if calendar_summary:
            try:
                # 사용자의 모든 캘린더 목록 조회
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get("items", [])
                
                # 대소문자 무시하고 이름 매칭
                target_name = calendar_summary.strip().lower()
                matched_calendar = None
                
                for cal in calendars:
                    cal_name = cal.get("summary", "").strip().lower()
                    if cal_name == target_name:
                        matched_calendar = cal
                        break
                
                if matched_calendar:
                    calendar_id = matched_calendar["id"]
                    logger.info(f"Using calendar '{matched_calendar.get('summary')}' (ID: {calendar_id})")
                else:
                    logger.warning(f"Calendar '{calendar_summary}' not found. Using primary calendar.")
                    
            except Exception as e:
                logger.warning(f"Failed to lookup calendar '{calendar_summary}': {e}. Using primary calendar.")
        
        event_body = {
            "summary": summary,
            "start": {"dateTime": start_iso, "timeZone": "Asia/Seoul"},
            "end": {"dateTime": end_iso, "timeZone": "Asia/Seoul"},
        }
        
        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        
        try:
            event = service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()
            
            logger.info(f"Event created successfully in calendar ID: {calendar_id}")
            
            return {
                "id": event["id"],
                "summary": event.get("summary", ""),
                "start": event["start"].get("dateTime") or event["start"].get("date"),
                "end": event["end"].get("dateTime") or event["end"].get("date"),
                "location": event.get("location", ""),
                "htmlLink": event.get("htmlLink", "")
            }
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")


# 싱글톤 인스턴스
_calendar_service: Optional[GoogleCalendarService] = None


def get_calendar_service() -> GoogleCalendarService:
    """Calendar 서비스 싱글톤 인스턴스 반환"""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = GoogleCalendarService()
    return _calendar_service
