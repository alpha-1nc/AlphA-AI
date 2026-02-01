"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MemoryCard } from "./MemoryCard";
import { MemorySearch } from "./MemorySearch";
import { getMemories, searchMemories, deleteMemory, type Memory } from "@/lib/api";
import { Database, RefreshCw, ChevronLeft, ChevronRight, Brain, Heart, Calendar, User, BookOpen, Filter } from "lucide-react";
import { rebuildFromMemories } from "@/lib/memoryStore";

interface MemoryPanelProps {
  className?: string;
  hideHeader?: boolean;
}

type MemoryType = "all" | "decision" | "preference" | "plan" | "profile" | "episode";

const typeFilterOptions: Array<{
  value: MemoryType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
    { value: "all", label: "전체", icon: Database },
    { value: "decision", label: "결정", icon: Brain },
    { value: "preference", label: "선호", icon: Heart },
    { value: "plan", label: "계획", icon: Calendar },
    { value: "profile", label: "프로필", icon: User },
    { value: "episode", label: "에피소드", icon: BookOpen },
  ];

export function MemoryPanel({ className, hideHeader = false }: MemoryPanelProps) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchResults, setSearchResults] = useState<Memory[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [currentSearchQuery, setCurrentSearchQuery] = useState<string>("");
  const [selectedType, setSelectedType] = useState<MemoryType>("all");
  const limit = 50;

  const loadMemories = useCallback(async (newOffset = 0) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getMemories(limit, newOffset);
      setMemories(response.memories);
      setTotal(response.total);
      setOffset(newOffset);

      // savedMap 재구성 (derived state)
      rebuildFromMemories(response.memories);
    } catch (err) {
      // 네트워크 오류 시 UI에 에러 표시하지 않고 콘솔에만 로그
      console.error("Failed to fetch memories:", err);
      // 빈 상태 유지
      setMemories([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMemories();
  }, [loadMemories]);

  const handleSearch = useCallback(async (query: string) => {
    const trimmedQuery = query.trim();

    // 빈 검색어는 무시
    if (!trimmedQuery) {
      setSearchResults(null);
      setCurrentSearchQuery("");
      return;
    }

    setCurrentSearchQuery(trimmedQuery);
    setIsLoading(true);
    setError(null);
    try {
      const results = await searchMemories(trimmedQuery);

      // 프론트엔드에서 정확한 키워드 매칭 필터링 (벡터 검색 결과에서 무관한 항목 제거)
      const filteredResults = results.filter((memory) => {
        const lowerQuery = trimmedQuery.toLowerCase();
        const summaryMatch = (memory.summary || "").toLowerCase().includes(lowerQuery);
        const textMatch = (memory.text || "").toLowerCase().includes(lowerQuery);
        return summaryMatch || textMatch;
      });

      // 검색 결과를 replace (append 금지)
      setSearchResults(filteredResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : "검색 실패");
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 전역 이벤트 리스너: 기억 저장 시 목록 갱신
  useEffect(() => {
    const handleMemoriesRefresh = (event: Event) => {
      const customEvent = event as CustomEvent<{ existingId?: string | null }>;
      const existingId = customEvent.detail?.existingId;

      // 검색 중이면 검색 재실행, 아니면 첫 페이지(offset=0)로 재로드
      if (currentSearchQuery.trim()) {
        handleSearch(currentSearchQuery);
      } else {
        loadMemories(0);
      }

      // TODO: existingId가 있으면 해당 카드 하이라이트/스크롤 (선택사항)
      if (existingId) {
        // 하이라이트 로직은 나중에 추가 가능
        console.log("Existing memory ID:", existingId);
      }
    };

    window.addEventListener("memories:refresh", handleMemoriesRefresh);
    return () => window.removeEventListener("memories:refresh", handleMemoriesRefresh);
  }, [loadMemories, handleSearch, currentSearchQuery]);

  const handleClearSearch = () => {
    setSearchResults(null);
    setCurrentSearchQuery("");
  };

  const handleDelete = async (id: string) => {
    try {
      const result = await deleteMemory(id);

      if (result.ok || result.notFound) {
        // 성공 또는 이미 삭제된 경우 모두 목록 갱신
        if (searchResults) {
          setSearchResults(searchResults.filter((m) => m.id !== id));
        }

        // loadMemories가 rebuildFromMemories를 호출하므로 savedMap도 갱신됨
        await loadMemories(offset);

        // memories:refresh 이벤트 발생하여 모든 MessageBubble 동기화
        window.dispatchEvent(new CustomEvent("memories:refresh"));
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "삭제 실패");
    }
  };

  // 타입 필터링 로직 (전체 탭 및 검색 탭 모두 적용)
  const filteredMemories = useMemo(() => {
    const sourceList = searchResults !== null ? searchResults : memories;
    if (selectedType === "all") {
      return sourceList;
    }
    return sourceList.filter((memory) => memory.type === selectedType);
  }, [memories, searchResults, selectedType]);

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className={`flex flex-col h-full min-h-0 ${className || ""}`}>
      <Tabs defaultValue="all" className="h-full min-h-0 flex flex-col">
        {!hideHeader && (
          <div className="px-4 pt-4 pb-2 border-b shrink-0">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold flex items-center gap-2">
                <Brain className="w-4 h-4" />
                기억 저장소
              </h3>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => {
                  setSearchResults(null);
                  loadMemories(0);
                }}
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
              </Button>
            </div>

            <TabsList className="w-full">
              <TabsTrigger value="all" className="flex-1">전체</TabsTrigger>
              <TabsTrigger value="search" className="flex-1">검색</TabsTrigger>
            </TabsList>
          </div>
        )}

        {hideHeader && (
          <div className="px-4 py-2 border-b shrink-0 flex items-center justify-between">
            <TabsList className="flex-1 mr-2">
              <TabsTrigger value="all" className="flex-1 h-8 text-xs">전체</TabsTrigger>
              <TabsTrigger value="search" className="flex-1 h-8 text-xs">검색</TabsTrigger>
            </TabsList>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0"
              onClick={() => {
                setSearchResults(null);
                loadMemories(0);
              }}
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        )}

        {/* 타입 필터 UI */}
        <div className="px-4 py-2 border-b shrink-0">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <Select value={selectedType} onValueChange={(value) => setSelectedType(value as MemoryType)}>
              <SelectTrigger className="w-full h-9 focus:ring-black/10 dark:focus:ring-white/20">
                <SelectValue placeholder="타입 선택" />
              </SelectTrigger>
              <SelectContent>
                {typeFilterOptions.map((option) => {
                  const Icon = option.icon;
                  return (
                    <SelectItem key={option.value} value={option.value}>
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4" />
                        <span>{option.label}</span>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>
        </div>

        <TabsContent value="all" className="flex-1 min-h-0 flex flex-col mt-0 data-[state=inactive]:hidden">
          <div className="flex-1 min-h-0 overflow-y-auto px-4 py-2">
            {error && (
              <div className="text-sm text-destructive text-center py-4">
                {error}
              </div>
            )}

            {!error && filteredMemories.length === 0 && !isLoading && (
              <div className="text-sm text-muted-foreground text-center py-8">
                {selectedType === "all" ? "저장된 기억이 없습니다" : "해당 타입의 기억이 없습니다"}
              </div>
            )}

            <div className="space-y-2 pb-2">
              {filteredMemories.map((memory) => (
                <MemoryCard
                  key={memory.id}
                  memory={memory}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          </div>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-2 border-t shrink-0">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => loadMemories(Math.max(0, offset - limit))}
                disabled={offset === 0 || isLoading}
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                이전
              </Button>
              <span className="text-sm text-muted-foreground">
                {currentPage} / {totalPages}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => loadMemories(offset + limit)}
                disabled={offset + limit >= total || isLoading}
              >
                다음
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          )}
        </TabsContent>

        <TabsContent value="search" className="flex-1 min-h-0 flex flex-col mt-0 data-[state=inactive]:hidden">
          <div className="px-4 py-3 border-b shrink-0">
            <MemorySearch onSearch={handleSearch} onClear={handleClearSearch} />
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto px-4 py-2">
            {error && (
              <div className="text-sm text-destructive text-center py-4">
                {error}
              </div>
            )}

            {searchResults === null && (
              <div className="text-sm text-muted-foreground text-center py-8">
                검색어를 입력하세요
              </div>
            )}

            {searchResults && filteredMemories.length === 0 && (
              <div className="text-sm text-muted-foreground text-center py-8">
                {selectedType === "all" ? "검색 결과가 없습니다" : "해당 타입의 검색 결과가 없습니다"}
              </div>
            )}

            {searchResults !== null && (
              <div className="space-y-2 pb-2">
                {filteredMemories.map((memory) => (
                  <MemoryCard
                    key={memory.id}
                    memory={memory}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
