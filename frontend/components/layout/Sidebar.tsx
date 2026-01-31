"use client";

import { Home, Calendar, Brain, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { showToast } from "@/lib/useToast";

interface SidebarProps {
    onHomeClick?: () => void;
    onMemoryClick?: () => void;
}

export function Sidebar({ onHomeClick, onMemoryClick }: SidebarProps) {
    const handleMenuClick = (label: string) => {
        switch (label) {
            case "홈":
                onHomeClick?.();
                break;
            case "기억":
                onMemoryClick?.();
                break;
            case "일정":
                showToast("준비 중입니다", "info");
                break;
            case "설정":
                showToast("준비 중입니다", "info");
                break;
        }
    };

    const menuItems = [
        { icon: Home, label: "홈" },
        { icon: Calendar, label: "일정" },
        { icon: Brain, label: "기억" },
        { icon: Settings, label: "설정" },
    ];

    return (
        <aside className="glass-panel w-64 h-full flex flex-col p-4">
            <nav className="flex-1 space-y-2">
                {menuItems.map((item) => (
                    <Button
                        key={item.label}
                        variant="ghost"
                        className="w-full justify-start gap-3 hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-colors duration-200"
                        onClick={() => handleMenuClick(item.label)}
                    >
                        <item.icon className="w-5 h-5" />
                        <span>{item.label}</span>
                    </Button>
                ))}
            </nav>

            <div className="pt-4 border-t border-border/50">
                <p className="text-xs text-muted-foreground px-3">
                    AlphA AI v1.0
                </p>
            </div>
        </aside>
    );
}
