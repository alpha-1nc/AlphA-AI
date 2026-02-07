"use client";

import { useState, useEffect } from "react";
import { Calendar, MapPin, Clock, X, Check, AlertCircle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { getCalendarEvents, createCalendarEvent, type CalendarEvent } from "@/lib/api";
import { getTodayRange, getTomorrowRange, formatTime, parseQuickAdd, type QuickAddDraft } from "@/lib/calendar-utils";

interface CalendarPanelProps {
    className?: string;
}

/**
 * CalendarPanel Component
 * 
 * 우측 패널 - 캘린더 모드
 * - 오늘/내일 일정 리스트
 * - 빠른 추가 입력 → 미리보기 → 확인 시 생성
 */
export function CalendarPanel({ className = "" }: CalendarPanelProps) {
    const [todayEvents, setTodayEvents] = useState<CalendarEvent[]>([]);
    const [tomorrowEvents, setTomorrowEvents] = useState<CalendarEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 빠른 추가
    const [quickAddInput, setQuickAddInput] = useState("");
    const [draft, setDraft] = useState<QuickAddDraft | null>(null);
    const [creating, setCreating] = useState(false);

    // 초기 로드
    useEffect(() => {
        loadEvents();
    }, []);

    const loadEvents = async () => {
        try {
            setLoading(true);
            setError(null);

            const todayRange = getTodayRange();
            const tomorrowRange = getTomorrowRange();

            const [today, tomorrow] = await Promise.all([
                getCalendarEvents(todayRange.time_min, todayRange.time_max),
                getCalendarEvents(tomorrowRange.time_min, tomorrowRange.time_max),
            ]);

            setTodayEvents(today);
            setTomorrowEvents(tomorrow);
        } catch (err: any) {
            console.error("Failed to load calendar events:", err);
            // err.detail이 객체일 수 있으므로 문자열만 추출
            const errorMsg = typeof err?.detail === 'string'
                ? err.detail
                : err?.detail?.detail || err?.message || "일정을 불러올 수 없습니다";
            setError(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    const handlePreview = () => {
        const parsed = parseQuickAdd(quickAddInput);
        if (!parsed) {
            setError("형식: [오늘|내일] HH:MM [제목] [N시간|N분] [@장소]\n예: 내일 16:00 배드민턴 4시간 @송림동\n예: 오늘 09:30 회의 1시간");
            return;
        }
        setDraft(parsed);
        setError(null);
    };

    const handleCancelDraft = () => {
        setDraft(null);
        setQuickAddInput("");
    };

    const handleConfirmDraft = async () => {
        if (!draft) return;

        try {
            setCreating(true);
            setError(null);

            await createCalendarEvent({
                summary: draft.summary,
                start_iso: draft.start_iso,
                end_iso: draft.end_iso,
                description: draft.description,
                location: draft.location,
            });

            // 성공 시 초기화 및 재로드
            setDraft(null);
            setQuickAddInput("");
            await loadEvents();
        } catch (err: any) {
            console.error("Failed to create event:", err);
            // err.detail이 객체일 수 있으므로 문자열만 추출
            const errorMsg = typeof err?.detail === 'string'
                ? err.detail
                : err?.detail?.detail || err?.message || "일정 생성 실패";
            setError(errorMsg);
        } finally {
            setCreating(false);
        }
    };

    return (
        <div className={`flex flex-col h-full bg-background/80 backdrop-blur-md border-l border-border/50 ${className}`}>
            {/* Header */}
            <header className="px-4 py-3.5 flex items-center justify-between bg-muted/30 backdrop-blur-sm z-20 shrink-0 border-b border-border/5">
                <h3 className="font-bold flex items-center gap-2 text-[12px] tracking-widest uppercase text-muted-foreground">
                    <Calendar className="w-3.5 h-3.5 text-primary opacity-80" />
                    일정
                </h3>
            </header>

            {/* Content */}
            <ScrollArea className="flex-1">
                <div className="px-4 py-3 space-y-4">
                    {/* Loading */}
                    {loading && (
                        <div className="flex items-center justify-center py-10">
                            <p className="text-xs text-muted-foreground">로딩 중...</p>
                        </div>
                    )}

                    {/* Error (non-draft) */}
                    {!loading && error && !draft && (
                        <div className="bg-destructive/10 border border-destructive/20 rounded-md px-3 py-2 flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 text-destructive mt-0.5 shrink-0" />
                            <p className="text-xs text-destructive">{error}</p>
                        </div>
                    )}

                    {/* 오늘 일정 */}
                    {!loading && (
                        <section>
                            <h4 className="text-xs font-semibold text-muted-foreground mb-2">오늘</h4>
                            {todayEvents.length === 0 ? (
                                <p className="text-xs text-muted-foreground/60 py-2">오늘 일정이 없습니다</p>
                            ) : (
                                <div className="space-y-2">
                                    {todayEvents.map((event) => (
                                        <EventCard key={event.id} event={event} />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {/* 내일 일정 */}
                    {!loading && (
                        <section>
                            <h4 className="text-xs font-semibold text-muted-foreground mb-2">내일</h4>
                            {tomorrowEvents.length === 0 ? (
                                <p className="text-xs text-muted-foreground/60 py-2">내일 일정이 없습니다</p>
                            ) : (
                                <div className="space-y-2">
                                    {tomorrowEvents.map((event) => (
                                        <EventCard key={event.id} event={event} />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {/* Draft Preview */}
                    {draft && (
                        <section className="border border-primary/20 rounded-md bg-primary/5 p-3 space-y-2">
                            <h4 className="text-xs font-semibold text-primary flex items-center gap-1">
                                <Check className="w-3.5 h-3.5" />
                                미리보기
                            </h4>
                            <div className="space-y-1.5 text-xs">
                                <p className="font-semibold">{draft.summary}</p>
                                <p className="text-muted-foreground flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {formatTime(draft.start_iso)} ~ {formatTime(draft.end_iso)}
                                </p>
                                {draft.location && (
                                    <p className="text-muted-foreground flex items-center gap-1">
                                        <MapPin className="w-3 h-3" />
                                        {draft.location}
                                    </p>
                                )}
                            </div>
                            {/* Error in draft */}
                            {error && (
                                <div className="bg-destructive/10 border border-destructive/20 rounded px-2 py-1.5 flex items-start gap-1">
                                    <AlertCircle className="w-3 h-3 text-destructive mt-0.5 shrink-0" />
                                    <p className="text-[10px] text-destructive">{error}</p>
                                </div>
                            )}
                            <div className="flex gap-2 pt-1">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleCancelDraft}
                                    disabled={creating}
                                    className="flex-1 text-xs h-7"
                                >
                                    <X className="w-3 h-3 mr-1" />
                                    취소
                                </Button>
                                <Button
                                    size="sm"
                                    onClick={handleConfirmDraft}
                                    disabled={creating}
                                    className="flex-1 text-xs h-7 bg-primary hover:bg-primary/90"
                                >
                                    <Check className="w-3 h-3 mr-1" />
                                    {creating ? "생성 중..." : "확인"}
                                </Button>
                            </div>
                        </section>
                    )}
                </div>
            </ScrollArea>

            {/* 빠른 추가 입력 (하단 고정) */}
            <div className="border-t border-border/40 p-3 bg-muted/20 shrink-0">
                <div className="space-y-2">
                    <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                        빠른 추가
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={quickAddInput}
                            onChange={(e) => setQuickAddInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !draft) {
                                    handlePreview();
                                }
                            }}
                            placeholder="예: 내일 16:00 배드민턴 4시간 @송림동"
                            disabled={!!draft}
                            className="flex-1 px-3 py-1.5 text-xs border border-border rounded-md bg-background focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                        />
                        {!draft && (
                            <Button
                                size="sm"
                                onClick={handlePreview}
                                disabled={!quickAddInput.trim()}
                                className="text-xs h-8 px-3"
                            >
                                미리보기
                            </Button>
                        )}
                    </div>
                    <p className="text-[9px] text-muted-foreground/60">
                        형식: [오늘|내일] HH:MM [제목] [N시간|N분] [@장소]
                    </p>
                </div>
            </div>
        </div>
    );
}

/**
 * EventCard - 개별 일정 카드
 */
function EventCard({ event }: { event: CalendarEvent }) {
    return (
        <div className="border border-border/30 rounded-md bg-card/50 p-2.5 hover:bg-card/80 transition-colors">
            <p className="text-xs font-semibold mb-1">{event.summary}</p>
            <div className="space-y-0.5 text-[10px] text-muted-foreground">
                <p className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTime(event.start)} ~ {formatTime(event.end)}
                </p>
                {event.location && (
                    <p className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {event.location}
                    </p>
                )}
            </div>
        </div>
    );
}
