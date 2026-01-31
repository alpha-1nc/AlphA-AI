"""LLM service layer for AAA (AlphA AI).

Provides a unified interface over OpenAI and Gemini.
- No proxy parameters are passed to OpenAI constructors.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta

from ..config import get_settings, Settings

logger = logging.getLogger(__name__)


# Google Calendar Function Calling Tools Schema
CALENDAR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": (
                "사용자의 Google Calendar에서 특정 기간의 일정을 조회합니다. "
                "이 함수는 다음 용도로 사용됩니다:\n"
                "1. 일정 조회: 사용자가 요청한 기간의 일정 확인\n"
                "2. 캘린더 목록 확인: 응답에 포함된 'calendar_summary' 필드로 사용 가능한 캘린더 이름 파악\n"
                "3. 충돌 감지: 새 일정을 생성하기 전 해당 시간대에 기존 일정이 있는지 1회만 확인\n\n"
                "⚠️ 중요 규칙:\n"
                "- create_calendar_event 호출 전 반드시 1회 조회할 것\n"
                "- 사용자가 '추가해', '응', '진행시켜' 등으로 확인하면 절대 재조회하지 말 것\n"
                "- 조회 결과를 기반으로 즉시 판단하고, 중복 호출 금지"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "조회 시작 시간 (ISO 8601 형식, 예: 2026-01-31T00:00:00+09:00)"
                    },
                    "time_max": {
                        "type": "string",
                        "description": "조회 종료 시간 (ISO 8601 형식, 예: 2026-02-01T00:00:00+09:00)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": (
                "사용자의 Google Calendar에 새로운 일정을 생성합니다.\n\n"
                "🔥 CRITICAL EXECUTION RULES (강제 실행 규칙):\n"
                "1. IF user confirms with '추가해', '응', '네', '진행시켜', '추가하세요' etc.,\n"
                "   → RUN THIS FUNCTION IMMEDIATELY. DO NOT check conflicts again.\n\n"
                "2. IF get_calendar_events shows EMPTY time slot OR only ALL-DAY events (no specific time),\n"
                "   → RUN THIS FUNCTION IMMEDIATELY. DO NOT ask for permission.\n\n"
                "3. ONLY ask for user confirmation IF there is a TIME-OVERLAPPING event with specific hours.\n"
                "   Example: 'That time already has [Meeting] scheduled. Add anyway?'\n\n"
                "4. NEVER call get_calendar_events again after user confirmation.\n"
                "5. NEVER mention past dates or irrelevant conflicts after user confirms."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "일정 제목"
                    },
                    "start_iso": {
                        "type": "string",
                        "description": "시작 시간 (ISO 8601 형식)"
                    },
                    "end_iso": {
                        "type": "string",
                        "description": "종료 시간 (ISO 8601 형식)"
                    },
                    "location": {
                        "type": "string",
                        "description": "장소 (선택사항)"
                    },
                    "description": {
                        "type": "string",
                        "description": "상세 설명 (선택사항)"
                    },
                    "calendar_summary": {
                        "type": "string",
                        "description": (
                            "일정을 추가할 캘린더 이름. 사용자가 명시하지 않으면 일정 내용을 분석하여 자동 추론하세요.\n\n"
                            "🎯 스마트 라우팅 (Auto-Routing) 예시:\n"
                            "- '수강신청', '강의', '과제', '시험', '학점' → '대학교'\n"
                            "- '알바', '근무', '출근', '시급' → '근로'\n"
                            "- '운동', '헬스', '조깅', '러닝', '웨이트' → '운동'\n"
                            "- '데이트', '여자친구', '남자친구' → '기본' (또는 '개인')\n"
                            "- '회의', '프로젝트', '미팅', '업무' → '업무' (또는 '회사')\n"
                            "- 키워드가 애매하면 → '기본' 캘린더로 자동 선택\n\n"
                            "💡 TIP: 먼저 get_calendar_events를 호출하면 응답의 'calendar_summary' 필드에서\n"
                            "사용 가능한 캘린더 이름들을 확인할 수 있습니다."
                        )
                    }
                },
                "required": ["summary", "start_iso", "end_iso"]
            }
        }
    }
]


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> tuple[str, Optional[List]]:
        """Generate response, optionally with tools. Returns (text, tool_calls)."""
        raise NotImplementedError


class OpenAILLM(BaseLLM):
    """OpenAI implementation (AsyncOpenAI)."""

    def __init__(self, api_key: str, model: str):
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)  # IMPORTANT: no `proxies=` here
        self.model = model
        logger.info("OpenAI LLM initialized with model: %s", model)

    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> tuple[str, Optional[List]]:
        """
        Generate response with optional tool calling support.
        
        Returns:
            tuple: (response_text, tool_calls)
            - response_text: LLM의 텍스트 응답
            - tool_calls: tool_calls 객체 리스트 (없으면 None)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        
        # tools가 제공되면 추가
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        resp = await self.client.chat.completions.create(**kwargs)
        
        message = resp.choices[0].message
        text_content = (message.content or "").strip()
        tool_calls = message.tool_calls if hasattr(message, 'tool_calls') else None
        
        return text_content, tool_calls


class GeminiLLM(BaseLLM):
    """Gemini implementation via google-generativeai."""

    def __init__(self, api_key: str, model: str):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        logger.info("Gemini LLM initialized with model: %s", model)

    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> tuple[str, Optional[List]]:
        """Gemini doesn't support function calling in the same way, so we ignore tools."""
        full_prompt = prompt if not system_prompt else f"{system_prompt}\n\n{prompt}"
        resp = await self.model.generate_content_async(
            full_prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2000,
            },
        )
        return (resp.text or "").strip(), None


class LLMService:
    """Service that chooses provider from Settings."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._llm: Optional[BaseLLM] = None

    def _provider_name(self) -> str:
        return (getattr(self.settings, "LLM_PROVIDER", "openai") or "openai").strip().lower()

    def _openai_model(self) -> str:
        return getattr(self.settings, "OPENAI_MODEL", None) or "gpt-4o-mini"

    def _gemini_model(self) -> str:
        return getattr(self.settings, "GEMINI_MODEL", None) or "gemini-1.5-flash"

    def _get_llm(self) -> BaseLLM:
        if self._llm is not None:
            return self._llm

        provider = self._provider_name()
        if provider == "openai":
            api_key = getattr(self.settings, "OPENAI_API_KEY", None)
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set")
            self._llm = OpenAILLM(api_key=api_key, model=self._openai_model())
        elif provider == "gemini":
            api_key = getattr(self.settings, "GEMINI_API_KEY", None)
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set")
            self._llm = GeminiLLM(api_key=api_key, model=self._gemini_model())
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

        return self._llm

    async def generate_response(self, user_message: str, context_memories: List[Dict]) -> str:
        """Generate response with optional Calendar function calling."""
        # 현재 시간 정보 (KST)
        kst = timezone(timedelta(hours=9))
        current_time = datetime.now(kst)
        current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        
        system_prompt = (
            f"You are AAA (AlphA AI), a calendar execution bot.\n"
            f"Current Time: {current_time_str} (KST)\n\n"
            "## 🚨 ABSOLUTE RULES - NO EXCEPTIONS 🚨\n\n"
            "### 📌 RULE 1: NO CHECKING (검사 금지)\n"
            "**WHEN the user asks to create/add an event (e.g., '일정 잡아줘', '추가해줘'):**\n"
            "- **DO NOT** call `get_calendar_events` to check availability.\n"
            "- **DO NOT** check for conflicts.\n"
            "- **DO NOT** check if the time slot is empty.\n"
            "- **IMMEDIATELY** call `create_calendar_event` on the FIRST response.\n\n"
            "### 📌 RULE 2: NO ASKING (질문 금지)\n"
            "**NEVER ask for confirmation:**\n"
            "- ❌ '그 시간에 일정이 있는데 추가할까요?'\n"
            "- ❌ '추가하시겠습니까?'\n"
            "- ❌ 'Should I add this event?'\n"
            "- ❌ '일정이 겹치는데 괜찮을까요?'\n\n"
            "**Just add it. Google Calendar will handle overlaps visually.**\n\n"
            "### 📌 RULE 3: IMMEDIATE EXECUTION (즉시 실행)\n"
            "**WHEN the user makes a calendar request:**\n"
            "1. **DO NOT think.** Do not hesitate.\n"
            "2. **IMMEDIATELY generate the `create_calendar_event` tool call in your FIRST response.**\n"
            "3. **DO NOT** reply with text like '잠시만요', '추가하겠습니다', 'I will add it'.\n"
            "4. **Execute the tool FIRST, then respond with text** (e.g., '일정 추가했습니다').\n\n"
            "### 📌 RULE 4: SMART CALENDAR ROUTING (자동 캘린더 선택)\n"
            "**IF the user does NOT specify a calendar, infer from keywords:**\n"
            "- '수강신청', '강의', '과제', '시험', '학점' → calendar_summary='대학교'\n"
            "- '알바', '근무', '출근', '시급' → calendar_summary='근로'\n"
            "- '운동', '헬스', '조깅', '러닝' → calendar_summary='운동'\n"
            "- '회의', '프로젝트', '미팅', '업무' → calendar_summary='업무'\n"
            "- Otherwise → calendar_summary='기본'\n\n"
            "### 📌 RULE 5: ONLY USE `get_calendar_events` FOR QUERIES (조회만 가능)\n"
            "**`get_calendar_events` is ONLY for:**\n"
            "- User asks '일정 알려줘', 'What's on my schedule?', '내일 뭐 있어?'\n"
            "- Listing events, NOT for checking conflicts before adding.\n\n"
            "**DO NOT use `get_calendar_events` before `create_calendar_event`.**\n\n"
            "---\n\n"
            "## 🧠 기억 활용 원칙 (Memory Usage Principles - STRICT FILTERING)\n\n"
            "### 📌 RULE 6: MANDATORY RELEVANCE CHECK (강제 관련성 검사)\n\n"
            "**⚠️ CRITICAL: You MUST perform a 2-step relevance check BEFORE using any memories.**\n\n"
            "**STEP 1: Identify User Intent (사용자 의도 파악)**\n"
            "- Is this a **casual greeting** ('안녕', 'hi', 'hello', '잘 지냈어?', '오늘 날씨 어때?')?\n"
            "- Is this a **simple exclamation** ('와우', '대박', '좋네', '그렇구나')?\n"
            "- Is this **small talk** ('심심해', '뭐 해?', 'how are you?', '재미있네')?\n\n"
            "→ **IF YES:** The user is NOT requesting information. Proceed to STEP 2.\n\n"
            "→ **IF NO:** The user is asking for specific information ('내 일정 뭐야?', '나 뭐 좋아하지?', '내일 뭐 해?').\n"
            "   **ACTION:** Use relevant memories to answer accurately.\n\n"
            "**STEP 2: Memory Filtering Decision (기억 사용 여부 결정)**\n\n"
            "**[Case A: Casual Conversation → IGNORE ALL MEMORIES]**\n"
            "- **Condition:** User made a greeting, exclamation, or small talk (identified in STEP 1).\n"
            "- **Action:**\n"
            "  1. **COMPLETELY IGNORE** the 'Context/Memories' section below.\n"
            "  2. **DO NOT** mention user's name, school, job, preferences, or any stored info.\n"
            "  3. **DO NOT** act like you know them ('청운대 다니시는군요', '탁구 치시는군요', '피자 좋아하시죠?').\n"
            "  4. **RESPOND** with a generic, friendly reply as if meeting someone new.\n\n"
            "- **Examples:**\n\n"
            "  **EXAMPLE 1 (Bad Response - DO NOT DO THIS):**\n"
            "  ```\n"
            "  User: '안녕'\n"
            "  Context: [User's name is 유중경, User studies at 청운대, User likes 탁구]\n"
            "  AI: '안녕하세요 유중경님! 청운대 다니시고 탁구 좋아하시는군요!' ❌ WRONG\n"
            "  ```\n\n"
            "  **EXAMPLE 2 (Good Response - DO THIS):**\n"
            "  ```\n"
            "  User: '안녕'\n"
            "  Context: [User's name is 유중경, User studies at 청운대, User likes 탁구]\n"
            "  AI: '안녕하세요! 오늘 하루는 어떠신가요?' ✅ CORRECT (Context IGNORED)\n"
            "  ```\n\n"
            "  **EXAMPLE 3 (Bad Response - DO NOT DO THIS):**\n"
            "  ```\n"
            "  User: '잘 지냈어?'\n"
            "  Context: [User has exam on 3/10, User likes chicken over pizza]\n"
            "  AI: '잘 지냈습니다! 3월 10일 시험 준비는 잘 되고 계신가요? 치킨 드시면서 공부하세요!' ❌ WRONG\n"
            "  ```\n\n"
            "  **EXAMPLE 4 (Good Response - DO THIS):**\n"
            "  ```\n"
            "  User: '잘 지냈어?'\n"
            "  Context: [User has exam on 3/10, User likes chicken over pizza]\n"
            "  AI: '네, 잘 지냈습니다! 요즘 어떻게 지내세요?' ✅ CORRECT (Context IGNORED)\n"
            "  ```\n\n"
            "**[Case B: Information Request → USE RELEVANT MEMORIES ONLY]**\n"
            "- **Condition:** User explicitly asked for specific information (e.g., '나 전공 뭐였지?', '내일 일정 뭐야?', '내가 뭐 좋아하지?').\n"
            "- **Action:**\n"
            "  1. **FILTER** the memories: Select ONLY those directly related to the question.\n"
            "  2. **USE** only the relevant memories in your answer.\n"
            "  3. **IGNORE** unrelated memories even if they exist.\n\n"
            "- **Examples:**\n\n"
            "  **EXAMPLE 5 (Good Response - Selective Usage):**\n"
            "  ```\n"
            "  User: '나 전공이 뭐였지?'\n"
            "  Context: [User studies CS, User likes pizza, User has exam on 3/10]\n"
            "  AI: '컴퓨터공학을 전공하고 계십니다.' ✅ CORRECT (Only CS memory used)\n"
            "  ```\n\n"
            "  **EXAMPLE 6 (Good Response - Relevant Info Only):**\n"
            "  ```\n"
            "  User: '내일 일정 뭐야?'\n"
            "  Context: [Tomorrow: 5PM table tennis, User likes chicken, User's name is 민수]\n"
            "  AI: '내일 오후 5시에 탁구 일정이 있습니다.' ✅ CORRECT (Only schedule used)\n"
            "  ```\n\n"
            "**핵심 원칙 (Core Principles):**\n"
            "1. **기억은 투명 인간(Invisible)**: 사용자가 직접 물어보지 않으면 기억을 언급하지 마세요.\n"
            "2. **아는 척 금지(No Show-off)**: 일반 대화에서 신상정보를 나열하지 마세요.\n"
            "3. **선택적 사용(Selective Usage)**: 질문받았을 때도 관련된 기억만 사용하세요.\n"
            "4. **자연스러운 대화(Natural Flow)**: 기억이 있어도 맥락에 맞지 않으면 무시하세요.\n\n"
            "**REMEMBER: Memories are BACKGROUND KNOWLEDGE, not MANDATORY TALKING POINTS.**\n\n"
            "---\n\n"
            "## 일반 원칙 (General Principles)\n"
            "- 사용자와의 이전 대화에서 기억한 정보를 활용하여 개인화된 도움을 제공합니다.\n"
            "- 친절하고 자연스럽게 대화하되, 없는 정보를 지어내지 마세요.\n"
            "- 모든 시간은 ISO 8601 형식으로 표현하세요 (예: 2026-01-31T14:00:00+09:00).\n"
            "- 필요한 정보가 부족하면 먼저 질문하세요 (시간, 날짜 등).\n\n"
            "**REMEMBER: When user says '추가해', JUST DO IT. No thinking, no checking, no asking.**"
        )

        context_text = ""
        if context_memories:
            context_text = "\n\n[관련 기억]:\n"
            for i, mem in enumerate(context_memories, 1):
                mtype = mem.get("type", "")
                summary = mem.get("summary", "")
                context_text += f"{i}. [{mtype}] {summary}\n"

        prompt = f"""{context_text}

[사용자 메시지]:
{user_message}

위 정보를 참고하여 사용자에게 도움이 되는 응답을 생성하세요."""

        llm = self._get_llm()
        
        # OpenAI인 경우에만 tools 파라미터 전달
        tools = CALENDAR_TOOLS if isinstance(llm, OpenAILLM) else None
        
        # 첫 번째 LLM 호출
        response_text, tool_calls = await llm.generate(prompt, system_prompt, tools=tools)
        
        # Tool calls가 없으면 바로 반환
        if not tool_calls:
            return response_text
        
        # Tool calls 실행
        logger.info(f"Executing {len(tool_calls)} tool calls")
        tool_results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"Calling {function_name} with args: {function_args}")
            
            try:
                result = await self._execute_calendar_function(function_name, function_args)
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                })
        
        # Tool 결과를 포함해서 LLM에 재요청
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
            {
                "role": "assistant",
                "content": response_text or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            }
        ]
        messages.extend(tool_results)
        
        # OpenAI API로 최종 응답 생성
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        
        final_resp = await client.chat.completions.create(
            model=self._openai_model(),
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return (final_resp.choices[0].message.content or "").strip()
    
    async def _execute_calendar_function(self, function_name: str, args: Dict) -> Dict:
        """Execute a calendar function and return the result."""
        from .google_calendar import get_calendar_service
        
        calendar_service = get_calendar_service()
        
        if function_name == "get_calendar_events":
            time_min = args.get("time_min")
            time_max = args.get("time_max")
            events = calendar_service.list_events(time_min=time_min, time_max=time_max)
            return {"events": events}
        
        elif function_name == "create_calendar_event":
            summary = args["summary"]
            start_iso = args["start_iso"]
            end_iso = args["end_iso"]
            location = args.get("location")
            description = args.get("description")
            calendar_summary = args.get("calendar_summary")
            
            event = calendar_service.create_event(
                summary=summary,
                start_iso=start_iso,
                end_iso=end_iso,
                location=location,
                description=description,
                calendar_summary=calendar_summary
            )
            return {"event": event}
        
        else:
            raise ValueError(f"Unknown function: {function_name}")

    async def extract_memories(self, conversation: str) -> str:
        system_prompt = (
            "당신은 대화에서 장기 기억으로 저장할 가치가 있는 정보를 추출하는 전문가입니다.\n"
            "다음 규칙을 엄격히 따르세요. 저장할 것이 없으면 [] 만 반환합니다.\n\n"
            "**최우선 추출 대상 (High Priority):**\n"
            "1. 사용자의 신상 정보: 이름, 나이, 성별, 소속(학교/직장), 거주지, 직업 등\n"
            "2. 사용자의 취향 및 선호도: 좋아하는 음식/음료/취미, 싫어하는 것, 관심사 등\n"
            "3. 사용자가 '기억해', '알아둬', '저장해'라고 명시적으로 요청한 모든 내용\n"
            "4. **사용자의 향후 계획 및 일정 (Future Plans & Schedules):**\n"
            "   - 사용자가 일정을 추가하거나 계획을 언급할 때 (예: '시험 일정 잡아줘', '3월 10일 회의', '여행 갈 거야'),\n"
            "   - 이를 단순 명령이 아니라 **'사용자의 향후 계획(Future Plan)'**이라는 **핵심 기억(Core Memory)**으로 추출하세요.\n"
            "   - 추출 예시:\n"
            "     * User: '3월 10일 DB 시험 추가해' → Memory: '2026년 3월 10일에 데이터베이스 전공 시험이 있다.' (type: plan, confidence: 0.85)\n"
            "     * User: '내일 오후 2시 회의 잡아줘' → Memory: '사용자는 내일 오후 2시에 회의 일정이 있다.' (type: plan, confidence: 0.85)\n"
            "     * User: '다음 주 여행 갈 거야' → Memory: '사용자는 다음 주에 여행을 계획하고 있다.' (type: plan, confidence: 0.8)\n\n"
            "위 4가지 카테고리에 해당하는 정보는 내용이 사소하더라도 반드시 추출하고, confidence를 0.8 이상으로 설정하세요.\n"
            "예시: '나는 치킨을 좋아해', '내 이름은 민수야', '나 피자보다 파스타 좋아해', '3월 10일 시험 있어' 등은 모두 저장 대상입니다."
        )

        prompt = f"""다음 대화에서 장기 기억으로 저장할 정보를 추출하세요.

[대화]:
{conversation}

**추출 우선순위:**
1. 사용자의 이름, 나이, 소속, 거주지 같은 신상 정보 (type: profile, confidence: 0.85-0.95)
2. 사용자의 음식/취미/관심사 같은 취향 정보 (type: preference, confidence: 0.8-0.9)
3. 사용자가 '기억해', '알아둬'라고 명시한 내용 (해당 type, confidence: 0.9-1.0)
4. 미래 계획이나 일정 (type: plan, confidence: 0.7-0.9)
5. 중요한 결정 사항 (type: decision, confidence: 0.7-0.9)
6. 기타 의미 있는 에피소드 (type: episode, confidence: 0.6-0.8)

반드시 다음 JSON 배열 형식으로만 응답하세요 (다른 텍스트 없이):
[
  {{
    \"type\": \"decision|preference|plan|profile|episode\",
    \"text\": \"원본 텍스트\",
    \"summary\": \"요약 (1-2문장)\",
    \"confidence\": 0.0-1.0,
    \"pii_flag\": true|false
  }}
]
"""

        llm = self._get_llm()
        response_text, _ = await llm.generate(prompt, system_prompt)
        return response_text


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(get_settings())
    return _llm_service
