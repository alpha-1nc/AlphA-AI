/**
 * API 클라이언트
 * 백엔드와 통신
 */

// NEXT_PUBLIC_API_BASE: 배포 환경에서 설정 (예: https://api.yourdomain.com)
// 설정되지 않으면 /api로 프록시 (로컬 개발용 next.config.js rewrites)
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export interface Citation {
  id: string;
  type: "decision" | "preference" | "plan" | "profile" | "episode";
  summary: string;
  created_at: string;
}

export interface ChatResponse {
  reply: string;
  citations: Citation[];
}

export interface Memory {
  id: string;
  type: "decision" | "preference" | "plan" | "profile" | "episode";
  text: string;
  summary: string;
  confidence: number;
  created_at: string;
  source_message_id?: string;
}

export interface MemoryListResponse {
  memories: Memory[];
  total: number;
  limit: number;
  offset: number;
}

class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: any) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "알 수 없는 오류" }));
    throw new ApiError(response.status, error.detail || error.message || "요청 실패", error);
  }
  return response.json();
}

/**
 * 채팅 API
 */
export async function sendChat(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return handleResponse<ChatResponse>(response);
}

/**
 * 기억 목록 조회
 */
export async function getMemories(
  limit = 50,
  offset = 0
): Promise<MemoryListResponse> {
  const response = await fetch(
    `${API_BASE}/memories?limit=${limit}&offset=${offset}`
  );
  return handleResponse<MemoryListResponse>(response);
}

/**
 * 기억 검색
 */
export async function searchMemories(query: string): Promise<Memory[]> {
  const response = await fetch(`${API_BASE}/memories/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return handleResponse<Memory[]>(response);
}

export type CreateMemoryResult =
  | { ok: true; status: number; memory: Memory }
  | {
    ok: false;
    status: number;
    reason: "dedup" | "error";
    existingId?: string | null;
    detail?: any;
    message?: string;
  };

/**
 * 기억 수동 저장
 */
export async function createMemory(payload: {
  type: "decision" | "preference" | "plan" | "profile" | "episode";
  text: string;
  summary: string;
  confidence: number;
  source_message_id?: string;
}): Promise<CreateMemoryResult> {
  const response = await fetch(`${API_BASE}/memories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  // 409 에러는 특별 처리 (detail 정보 보존)
  if (response.status === 409) {
    const errorDetail = await response.json().catch(() => ({ detail: "이미 저장된 기억입니다" }));
    const existingId = errorDetail.existing_id || errorDetail.existingId || null;
    if (existingId) {
      console.log("[createMemory] dedup existing_id:", existingId);
    }
    return {
      ok: false,
      status: 409,
      reason: "dedup",
      existingId,
      detail: errorDetail,
      message: errorDetail.message || errorDetail.detail || "이미 저장된 기억입니다",
    };
  }

  if (!response.ok) {
    const errorDetail = await response.json().catch(() => ({ detail: "요청 실패" }));
    return {
      ok: false,
      status: response.status,
      reason: "error",
      detail: errorDetail,
      message: errorDetail.detail || errorDetail.message || "요청 실패",
    };
  }

  const memory = await response.json();
  return { ok: true, status: response.status, memory };
}

export type DeleteMemoryResult =
  | { ok: true; status: number }
  | { ok: false; notFound: true; status: number }
  | { ok: false; notFound: false; status: number; error: string };

/**
 * 기억 삭제
 */
export async function deleteMemory(id: string): Promise<DeleteMemoryResult> {
  try {
    const response = await fetch(`${API_BASE}/memories/${id}`, {
      method: "DELETE",
    });

    // 404/410: already deleted, not an error
    if (response.status === 404 || response.status === 410) {
      return { ok: false, notFound: true, status: response.status };
    }

    // 200/204: success
    if (response.ok) {
      return { ok: true, status: response.status };
    }

    // Other errors
    const errorDetail = await response.json().catch(() => ({ detail: "삭제 실패" }));
    return {
      ok: false,
      notFound: false,
      status: response.status,
      error: errorDetail.detail || errorDetail.message || "삭제 실패",
    };
  } catch (error) {
    return {
      ok: false,
      notFound: false,
      status: 0,
      error: error instanceof Error ? error.message : "네트워크 오류",
    };
  }
}

/**
 * 헬스 체크
 */
export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse(response);
}
