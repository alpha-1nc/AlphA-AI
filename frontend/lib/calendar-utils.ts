/**
 * 캘린더 관련 유틸리티
 * Asia/Seoul 기준 시간 계산 및 파싱
 */

const KST_OFFSET = 9 * 60; // UTC+9 (minutes)

/**
 * 오늘 00:00~24:00 (Asia/Seoul)
 */
export function getTodayRange(): { time_min: string; time_max: string } {
    const now = new Date();
    const kstNow = new Date(now.getTime() + KST_OFFSET * 60 * 1000);

    const todayStart = new Date(kstNow);
    todayStart.setUTCHours(0, 0, 0, 0);

    const todayEnd = new Date(todayStart);
    todayEnd.setUTCDate(todayEnd.getUTCDate() + 1);

    return {
        time_min: todayStart.toISOString(),
        time_max: todayEnd.toISOString(),
    };
}

/**
 * 내일 00:00~24:00 (Asia/Seoul)
 */
export function getTomorrowRange(): { time_min: string; time_max: string } {
    const now = new Date();
    const kstNow = new Date(now.getTime() + KST_OFFSET * 60 * 1000);

    const tomorrowStart = new Date(kstNow);
    tomorrowStart.setUTCHours(0, 0, 0, 0);
    tomorrowStart.setUTCDate(tomorrowStart.getUTCDate() + 1);

    const tomorrowEnd = new Date(tomorrowStart);
    tomorrowEnd.setUTCDate(tomorrowEnd.getUTCDate() + 1);

    return {
        time_min: tomorrowStart.toISOString(),
        time_max: tomorrowEnd.toISOString(),
    };
}

/**
 * ISO 시간을 "HH:MM" 형태로 포맷
 */
export function formatTime(isoString: string): string {
    const date = new Date(isoString);
    const kstDate = new Date(date.getTime() + KST_OFFSET * 60 * 1000);
    const hours = kstDate.getUTCHours().toString().padStart(2, "0");
    const minutes = kstDate.getUTCMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
}

/**
 * 빠른 추가 입력 파싱
 * 예: "내일 3시 회의 1시간 @카페" → { summary, start_iso, end_iso, location }
 */
export interface QuickAddDraft {
    summary: string;
    start_iso: string;
    end_iso: string;
    location?: string;
    description?: string;
}

/**
 * 빠른 추가 입력 파싱 (엄격한 형식 검증)
 * 
 * 허용 형식: [오늘|내일] HH:MM [제목] [N시간|N분] [@장소]
 * - 시간: HH:MM 형식만 허용 (예: 16:00, 09:30)
 * - 기간: 필수 (N시간 또는 N분)
 * - 장소: 선택적 (@로 시작)
 * 
 * 거부 사례: "4시", "오후 2시", "20시~22시", "2/3일" 등
 */
export function parseQuickAdd(input: string): QuickAddDraft | null {
    try {
        const trimmed = input.trim();
        if (!trimmed) return null;

        // 엄격한 형식 검증
        // 패턴: [오늘|내일] HH:MM [제목] [N시간|N분] [@장소(선택)]

        // 1) 날짜 토큰 확인 (오늘 또는 내일 필수)
        const hasToday = /오늘/.test(trimmed);
        const hasTomorrow = /내일/.test(trimmed);

        if (!hasToday && !hasTomorrow) {
            // 날짜 토큰 없음 - 거부
            return null;
        }

        const isToday = hasToday;

        // 2) 시간 형식 검증 (HH:MM만 허용)
        const timeMatch = trimmed.match(/(\d{1,2}):(\d{2})/);

        if (!timeMatch) {
            // HH:MM 형식 없음 - 거부
            return null;
        }

        const hour = parseInt(timeMatch[1], 10);
        const minute = parseInt(timeMatch[2], 10);

        // 시간 범위 검증
        if (hour < 0 || hour > 23 || minute < 0 || minute > 59) {
            return null;
        }

        // 3) 기간 파싱 (필수)
        const hourDurationMatch = trimmed.match(/(\d+)시간/);
        const minuteDurationMatch = trimmed.match(/(\d+)분/);

        let duration: number;

        if (hourDurationMatch) {
            duration = parseInt(hourDurationMatch[1], 10) * 60;
        } else if (minuteDurationMatch) {
            duration = parseInt(minuteDurationMatch[1], 10);
        } else {
            // 기간 토큰 없음 - 거부
            return null;
        }

        // 4) 장소 파싱 (선택적)
        const locationMatch = trimmed.match(/@([^\s]+)/);
        const location = locationMatch ? locationMatch[1] : undefined;

        // 5) 제목 추출
        let summary = trimmed;

        // 날짜 제거
        summary = summary.replace(/오늘|내일/g, "");

        // 시간 제거
        summary = summary.replace(/\d{1,2}:\d{2}/g, "");

        // 기간 제거
        summary = summary.replace(/\d+시간/g, "");
        summary = summary.replace(/\d+분/g, "");

        // 장소 제거
        summary = summary.replace(/@[^\s]+/g, "");

        // 공백 정리
        summary = summary.replace(/\s+/g, " ").trim();

        if (!summary) {
            summary = "일정";
        }

        // 6) 시작/종료 시간 계산 (Asia/Seoul)
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth();
        const date = now.getDate();

        const baseDate = new Date(year, month, date, 0, 0, 0, 0);

        if (!isToday) {
            baseDate.setDate(baseDate.getDate() + 1);
        }

        baseDate.setHours(hour, minute, 0, 0);

        const endDate = new Date(baseDate.getTime() + duration * 60 * 1000);

        return {
            summary,
            start_iso: baseDate.toISOString(),
            end_iso: endDate.toISOString(),
            location,
        };
    } catch (error) {
        console.error("Failed to parse quick add:", error);
        return null;
    }
}
