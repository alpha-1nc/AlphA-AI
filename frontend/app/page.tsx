"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { EmptyState } from "@/components/chat/EmptyState";
import { RightPanel, MemorySidebar, type RightPanelMode } from "@/components/memory/MemorySidebar";
import { Header } from "@/components/layout/Header";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ToastContainer } from "@/components/ui/Toast";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { setPanelState, showToast } from "@/lib/useToast";
import { sendChat, type Citation } from "@/lib/api";
import type { Message } from "@/components/chat/MessageBubble";
import type { ChatInputRef } from "@/components/chat/ChatInput";

// UUID 생성 함수
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export default function Home() {
  const [sessionId, setSessionId] = useState<string>(() => generateUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showMemoryPanel, setShowMemoryPanel] = useState(false);
  const [showMemoryMobile, setShowMemoryMobile] = useState(false);
  const [showDashboard, setShowDashboard] = useState(true);
  const [rightPanelMode, setRightPanelMode] = useState<RightPanelMode>("memories");
  const chatInputRef = useRef<ChatInputRef>(null);

  // 패널 상태를 전역으로 동기화
  useEffect(() => {
    setPanelState(showMemoryPanel);
  }, [showMemoryPanel]);

  const handleSendMessage = useCallback(async (content: string) => {
    // Hide dashboard when first message is sent
    setShowDashboard(false);

    // 사용자 메시지 추가
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setCitations([]);

    try {
      const response = await sendChat(content);

      // AI 응답 추가
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.reply,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setCitations(response.citations);
    } catch (error) {
      // 에러 메시지 추가
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content:
          error instanceof Error
            ? `오류가 발생했습니다: ${error.message}`
            : "알 수 없는 오류가 발생했습니다.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleStartConversation = useCallback(() => {
    // Hide dashboard and focus input
    setShowDashboard(false);
    // Use setTimeout to ensure ChatInput is rendered before focusing
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 0);
  }, []);

  const handleHomeClick = useCallback(() => {
    // Reset session: generate new sessionId to clear conversation context
    setSessionId(generateUUID());
    // Reset to dashboard by clearing messages
    setMessages([]);
    setCitations([]);
    setShowDashboard(true);
  }, []);

  const handleMemoryClick = useCallback(() => {
    // Toggle memory panel, switch to memories mode
    setRightPanelMode("memories");
    if (window.innerWidth >= 1024) {
      setShowMemoryPanel((prev) => !prev);
    } else {
      setShowMemoryMobile(true);
    }
  }, []);

  const handleScheduleClick = useCallback(() => {
    // Toggle calendar panel if already in calendar mode, otherwise switch to calendar mode
    if (window.innerWidth >= 1024) {
      if (rightPanelMode === "calendar" && showMemoryPanel) {
        // Already in calendar mode and panel is open, so close it
        setShowMemoryPanel(false);
      } else {
        // Switch to calendar mode and show panel
        setRightPanelMode("calendar");
        setShowMemoryPanel(true);
      }
    } else {
      setRightPanelMode("calendar");
      setShowMemoryMobile(true);
    }
  }, [rightPanelMode, showMemoryPanel]);

  const handleSettingsClick = useCallback(() => {
    showToast("준비 중입니다", "info");
  }, []);

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <Header
        onHomeClick={handleHomeClick}
        onMemoryClick={handleMemoryClick}
        onScheduleClick={handleScheduleClick}
        onSettingsClick={handleSettingsClick}
      />

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area - Full Width */}
        <main className="flex-1 flex flex-col min-w-0 bg-background">
          {showDashboard ? (
            <EmptyState onStartConversation={handleStartConversation} />
          ) : (
            <ChatContainer
              ref={chatInputRef}
              messages={messages}
              isLoading={isLoading}
              onSendMessage={handleSendMessage}
            />
          )}
        </main>

        {/* Desktop Right Panel (Citations + Memory) - hidden on mobile */}
        <aside
          className={`
            w-80 flex-col shrink-0
            ${showMemoryPanel ? "hidden lg:flex" : "hidden"}
          `}
        >
          <RightPanel mode={rightPanelMode} citations={citations} className="flex-1" />
        </aside>
      </div>

      {/* Mobile Memory Sheet */}
      <Sheet open={showMemoryMobile} onOpenChange={setShowMemoryMobile}>
        <SheetContent side="right" className="w-80 p-0">
          <RightPanel mode={rightPanelMode} citations={citations} className="flex-1" />
        </SheetContent>
      </Sheet>

      {/* Toast 컨테이너 */}
      <ToastContainer />
    </div>
  );
}
