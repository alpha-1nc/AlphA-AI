"use client";

import { useRef, useEffect, forwardRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble, TypingIndicator, type Message } from "./MessageBubble";
import { ChatInput, type ChatInputRef } from "./ChatInput";
import { MessageSquare, Brain } from "lucide-react";
import { CitationCard } from "@/components/citation/CitationCard";
import type { Citation } from "@/lib/api";

interface ChatContainerProps {
  messages: Message[];
  citations?: Citation[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
}

export const ChatContainer = forwardRef<ChatInputRef, ChatContainerProps>(
  ({ messages, citations = [], isLoading, onSendMessage }, ref) => {
    const scrollRef = useRef<HTMLDivElement>(null);

    // 새 메시지 시 스크롤
    useEffect(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }, [messages, isLoading]);

    return (
      <div className="flex flex-col h-full">
        {/* 메시지 영역 */}
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground py-20">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                <MessageSquare className="w-8 h-8" />
              </div>
              <h3 className="font-semibold text-lg mb-2">AAA: AlphA AI</h3>
              <p className="text-sm max-w-sm">
                안녕하세요! 저는 당신의 개인 비서 AI입니다.
                <br />
                대화 내용을 기억하고 맞춤형 도움을 드립니다.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* 참고한 기억 섹션 */}
              {citations.length > 0 && (
                <div className="mb-6 space-y-3">
                  <h3 className="font-semibold flex items-center gap-2 text-sm">
                    <Brain className="w-4 h-4" />
                    참고한 기억
                  </h3>
                  <div className="space-y-2">
                    {citations.map((citation) => (
                      <CitationCard key={citation.id} citation={citation} />
                    ))}
                  </div>
                </div>
              )}

              {/* 메시지 목록 */}
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isLoading && <TypingIndicator />}
            </div>
          )}
        </ScrollArea>

        {/* 입력 영역 */}
        <ChatInput ref={ref} onSend={onSendMessage} disabled={isLoading} />
      </div>
    );
  }
);

ChatContainer.displayName = "ChatContainer";
