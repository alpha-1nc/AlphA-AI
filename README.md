# AAA: AlphA AI

개인 비서형 AI - 장기 기억 기반 채팅 시스템

## Google Calendar 연동 테스트

### 1. OAuth 연동

```bash
# 1. Authorization URL 받기
curl http://127.0.0.1:8000/calendar/auth/url

# 2. 반환된 URL을 브라우저에서 접속 후 Google 계정으로 로그인 및 권한 승인
# 3. 자동으로 callback URL로 리다이렉트되며 연동 완료
```

### 2. 일정 조회

```bash
# 오늘 일정 조회 (기본값: 오늘 00:00 ~ 내일 00:00 KST)
curl http://127.0.0.1:8000/calendar/events

# 특정 기간 조회
curl "http://127.0.0.1:8000/calendar/events?time_min=2026-01-31T00:00:00%2B09:00&time_max=2026-02-01T00:00:00%2B09:00"
```

### 3. 일정 생성

```bash
# 일정 생성
curl -X POST http://127.0.0.1:8000/calendar/events \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "팀 미팅",
    "start_iso": "2026-02-01T14:00:00+09:00",
    "end_iso": "2026-02-01T15:00:00+09:00",
    "description": "Q1 계획 논의",
    "location": "회의실 A"
  }'
```

## 환경 설정

`.env` 파일에 다음 설정 필요:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/calendar/auth/callback
GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar.events
```

## 실행

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm run dev
```
