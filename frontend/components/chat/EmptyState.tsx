"use client";

import { MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

interface EmptyStateProps {
    onStartConversation?: () => void;
}

export function EmptyState({ onStartConversation }: EmptyStateProps) {
    const { theme } = useTheme();
    const [mounted, setMounted] = useState(false);

    // Prevent hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    return (
        <div className="flex-1 flex items-center justify-center p-8">
            <div className="max-w-2xl w-full text-center space-y-8 animate-fade-in-up">
                {/* Welcome message */}
                <div className="space-y-4">
                    <div className="relative inline-flex items-center justify-center w-20 h-20 mb-4 bg-transparent">
                        <Image
                            src="/34C8AED3-A785-4263-ADE1-191C460BCB30.png"
                            alt="AlphA AI Logo"
                            width={80}
                            height={80}
                            className={`object-contain ${mounted && theme === "dark" ? "logo-dark-mode" : ""}`}
                            priority
                        />
                    </div>
                    <h2 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
                        안녕하세요, CEO님
                    </h2>
                    <p className="text-lg text-muted-foreground">
                        저는 AlphA Inc. 의 인공지능 비서 AAA입니다.
                    </p>
                </div>

                {/* Quick actions */}
                <div className="space-y-3">
                    <div className="flex flex-wrap gap-3 justify-center">
                        <Button
                            variant="outline"
                            className="glass-panel hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-colors duration-200"
                            onClick={() => onStartConversation?.()}
                        >
                            <MessageSquare className="w-4 h-4 mr-2" />
                            대화 시작
                        </Button>
                    </div>
                </div>

                {/* Decorative gradient */}
                <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
                    <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
                </div>
            </div>
        </div>
    );
}
