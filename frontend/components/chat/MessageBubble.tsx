"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { User, Bot, Star } from "lucide-react";
import { createMemory, deleteMemory, getMemories } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { showToast } from "@/lib/useToast";
import {
  isMessageSaved,
  getMemoryId,
  addToSavedMap,
  removeFromSavedMap,
  rebuildFromMemories,
  subscribeToStore,
  getIsInitialized,
  markAsInitialized,
} from "@/lib/memoryStore";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface MessageBubbleProps {
  message: Message;
}

// 메시지 ID 생성 함수 (간단한 해시)
function generateMessageId(text: string, timestamp: Date): string {
  const data = `${text}_${timestamp.getTime()}`;
  let hash = 0;
  for (let i = 0; i < data.length; i++) {
    const char = data.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36);
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const messageId = isUser ? generateMessageId(message.content, message.timestamp) : "";

  // 초기 동기화: 저장된 메모리 불러오기 (한 번만)
  useEffect(() => {
    if (!getIsInitialized()) {
      markAsInitialized();
      getMemories(1000, 0)
        .then((response) => {
          rebuildFromMemories(response.memories);
        })
        .catch((error) => {
          console.error("Failed to load saved memories:", error);
        });
    }
  }, []);

  // 현재 메시지의 저장 상태 확인 (store 구독)
  useEffect(() => {
    const updateSavedState = () => {
      if (messageId) {
        setIsSaved(isMessageSaved(messageId));
      }
    };

    // 초기 상태 설정
    updateSavedState();


    // Store 변경 구독
    const unsubscribe = subscribeToStore(updateSavedState);
    return unsubscribe;
  }, [messageId]);

  const handleStarClick = async () => {
    if (isSaving || !messageId) return;

    setIsSaving(true);
    try {
      if (isSaved) {
        // 저장 취소 (삭제)
        const memoryId = getMemoryId(messageId);
        if (memoryId) {
          const result = await deleteMemory(memoryId);

          if (result.ok) {
            // 200/204: 정상 삭제
            removeFromSavedMap(messageId);
            setIsSaved(false);
            showToast("🗑️ 기억 저장 취소됨", "info");
            window.dispatchEvent(new CustomEvent("memories:refresh"));
          } else if (result.notFound) {
            // 404/410: 이미 삭제됨 (오류 아님)
            removeFromSavedMap(messageId);
            setIsSaved(false);
            showToast("ℹ️ 이미 삭제된 기억입니다", "info");
            window.dispatchEvent(new CustomEvent("memories:refresh"));
          } else {
            // 기타 오류
            showToast(`❌ 삭제 실패: ${result.error}`, "error");
          }
        }
      } else {
        // 저장
        const result = await createMemory({
          type: "episode",
          text: message.content,
          summary: message.content.length > 100
            ? message.content.substring(0, 100) + "..."
            : message.content,
          confidence: 1.0,
          source_message_id: messageId,
        });

        if (result.ok) {
          addToSavedMap(messageId, result.memory.id);
          setIsSaved(true);
          showToast("✨ 새로운 기억이 저장되었습니다", "success");
          window.dispatchEvent(new CustomEvent("memories:refresh"));
        } else if (result.reason === "dedup" && result.existingId) {
          // 409: 이미 저장됨
          addToSavedMap(messageId, result.existingId);
          setIsSaved(true);
          showToast("ℹ️ 이미 저장된 기억입니다", "info");
          window.dispatchEvent(new CustomEvent("memories:refresh"));
        } else {
          showToast("❌ 저장 실패", "error");
        }
      }
    } catch (error: any) {
      console.error("Star click error:", error);
      showToast("❌ 오류 발생", "error");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className={cn(
        "flex gap-3 animate-fade-in-up group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* 아바타 */}
      <div
        className={cn(
          "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-md",
          isUser
            ? "bg-neutral-800 text-white dark:bg-white dark:text-black"
            : "bg-neutral-200 text-neutral-800 dark:bg-neutral-700 dark:text-white"
        )}
      >
        {isUser ? (
          <User className="w-5 h-5" />
        ) : (
          <Bot className="w-5 h-5" />
        )}
      </div>

      {/* 메시지 버블 */}
      <div className="max-w-[75%] relative overflow-hidden">
        {/* 사용자 메시지에만 기억하기 버튼 표시 */}
        {isUser && (
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "absolute -top-1 -right-1 h-7 w-7 opacity-0 group-hover:opacity-100 transition-all duration-200",
              "glass-panel hover:accent-glow-sm"
            )}
            onClick={handleStarClick}
            disabled={isSaving}
            title={isSaved ? "저장됨" : "기억하기"}
          >
            <Star
              className={cn(
                "h-4 w-4 transition-all",
                isSaving && "animate-pulse",
                isSaved && "fill-yellow-400 text-yellow-400"
              )}
            />
          </Button>
        )}

        <div
          className={cn(
            "px-4 py-3 rounded-2xl shadow-sm transition-all duration-200",
            isUser
              ? "bg-[#333] text-white rounded-br-sm dark:bg-white dark:text-black dark:shadow-lg"
              : "bg-neutral-200 text-black rounded-bl-sm hover:shadow-md dark:bg-[#262626] dark:text-white"
          )}
        >
          <p className="text-sm whitespace-pre-wrap break-words overflow-wrap-anywhere leading-relaxed">
            {message.content}
          </p>
          <p
            className={cn(
              "text-[10px] mt-2 opacity-60",
              isUser ? "text-right" : "text-left"
            )}
          >
            {message.timestamp.toLocaleTimeString("ko-KR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in-up">
      <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-neutral-200 text-neutral-800 dark:bg-neutral-700 dark:text-white shadow-md">
        <Bot className="w-5 h-5" />
      </div>
      <div className="bg-neutral-200 text-black dark:bg-[#262626] dark:text-white px-4 py-3 rounded-2xl rounded-bl-sm shadow-sm">
        <div className="flex gap-1">
          <span className="typing-dot w-2 h-2 bg-neutral-600 dark:bg-neutral-400 rounded-full" />
          <span className="typing-dot w-2 h-2 bg-neutral-600 dark:bg-neutral-400 rounded-full" />
          <span className="typing-dot w-2 h-2 bg-neutral-600 dark:bg-neutral-400 rounded-full" />
        </div>
      </div>
    </div>
  );
}
