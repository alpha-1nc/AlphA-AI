# AAA: AlphA AI

개인 비서형 AI - 장기 기억 기반 채팅 시스템

## 배포

### Railway (Backend)

#### 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `PORT` | ✅ | Railway 자동 주입 |
| `OPENAI_API_KEY` | ✅ | OpenAI API 키 |
| `LLM_PROVIDER` | - | `openai` (기본값) 또는 `gemini` |
| `GEMINI_API_KEY` | - | Gemini 사용 시 필요 |
| `GOOGLE_CLIENT_ID` | ✅ | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth |
| `GOOGLE_REDIRECT_URI` | ✅ | `https://api.<domain>/calendar/auth/callback` |
| `FRONTEND_ORIGIN` | - | CORS 허용 (예: `https://app.<domain>`) |
| `SQLITE_PATH` | - | 기본값: `./data/app.db` |
| `CHROMA_DIR` | - | 기본값: `./data/chroma` |

#### Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### Health Check
- Path: `/healthz`
- Expected: `{"ok": true}`

---

### Vercel (Frontend)

#### 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `NEXT_PUBLIC_API_BASE` | ✅ | `https://api.<domain>` |

---

### 배포 체크리스트

- [ ] Railway 프로젝트 생성 및 환경변수 설정
- [ ] Railway에서 `/healthz` 응답 확인
- [ ] Vercel 프로젝트 생성 및 환경변수 설정
- [ ] 프론트엔드에서 API 연결 확인
- [ ] Google Cloud Console에서 Redirect URI 추가
- [ ] DNS 설정 (api.domain, app.domain)

---

### Smoke Test

배포 후 기본 기능 테스트:

```bash
python scripts/smoke_test.py --base-url https://api.<domain>
```

---

## 로컬 개발

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

---

## Google Calendar 연동

### OAuth 연동

```bash
# 1. Authorization URL 받기
curl http://127.0.0.1:8000/calendar/auth/url

# 2. 반환된 URL을 브라우저에서 접속 후 Google 계정으로 로그인 및 권한 승인
# 3. 자동으로 callback URL로 리다이렉트되며 연동 완료
```

### 일정 조회

```bash
# 오늘 일정 조회 (기본값: 오늘 00:00 ~ 내일 00:00 KST)
curl http://127.0.0.1:8000/calendar/events
```

### 일정 생성

```bash
curl -X POST http://127.0.0.1:8000/calendar/events \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "팀 미팅",
    "start_iso": "2026-02-01T14:00:00+09:00",
    "end_iso": "2026-02-01T15:00:00+09:00"
  }'
```

### 일정 패널 사용법 (Frontend)

상단 메뉴의 **일정(캘린더 아이콘)** 버튼을 클릭하면 우측 패널이 일정 모드로 전환됩니다.

**빠른 추가 입력 형식:**
- `내일 3시 회의 1시간 @카페` → 내일 03:00~04:00, 장소: 카페
- `오늘 오후 2시 점심 30분` → 오늘 14:00~14:30
- `15시 미팅 2시간 @본사` → 오늘 15:00~17:00, 장소: 본사

**흐름:** 입력 → [미리보기] → 미리보기 확인 → [확인] 버튼 클릭 시 Google Calendar에 일정 생성


---

## 환경 설정

Backend: `backend/.env.example` 참고  
Frontend: `frontend/.env.example` 참고
