"use client";

import Image from "next/image";
import { useTheme } from "next-themes";
import { Moon, Sun, Home, Calendar, Brain, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";

interface HeaderProps {
    onHomeClick?: () => void;
    onMemoryClick?: () => void;
    onScheduleClick?: () => void;
    onSettingsClick?: () => void;
}

/**
 * Header component featuring a top navigation bar.
 * Improved to have navigation menu right-aligned with icon-only mode and tooltips.
 */
export function Header({
    onHomeClick,
    onMemoryClick,
    onScheduleClick,
    onSettingsClick
}: HeaderProps) {
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);

    // Prevent hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    const toggleTheme = () => {
        setTheme(theme === "dark" ? "light" : "dark");
    };

    const menuItems = [
        { icon: Home, label: "홈", onClick: onHomeClick },
        { icon: Brain, label: "기억 저장소", onClick: onMemoryClick },
        { icon: Calendar, label: "일정", onClick: onScheduleClick },
        { icon: Settings, label: "설정", onClick: onSettingsClick },
    ];

    return (
        <header className="glass-header h-16 flex items-center justify-between px-4 md:px-6 shrink-0 sticky top-0 z-50 transition-all duration-300 shadow-sm">
            {/* Left: Logo & Brand */}
            <div className="flex items-center gap-3">
                {/* Logo */}
                <div
                    className="relative w-10 h-10 flex-shrink-0 cursor-pointer hover:scale-105 active:scale-95 transition-transform duration-200"
                    onClick={onHomeClick}
                >
                    <Image
                        src={mounted && theme === "dark" ? "/logo-dark.png" : "/logo.png"}
                        alt="AlphA AI Logo"
                        fill
                        className="object-contain"
                        priority
                    />
                </div>

                {/* Brand name */}
                <div className="hidden sm:block">
                    <h1 className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
                        AlphA <span className="text-primary dark:text-white">AI</span>
                    </h1>
                </div>
            </div>

            {/* Right: Navigation & Theme Toggle */}
            <div className="flex items-center gap-2 sm:gap-4">
                {/* Navigation Menu (Icon-only with Tooltips) */}
                <nav className="flex items-center gap-1 sm:gap-2">
                    {menuItems.map((item) => (
                        <div key={item.label} className="relative group">
                            <Button
                                variant="ghost"
                                size="icon"
                                className="w-10 h-10 rounded-full hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-all duration-300"
                                onClick={item.onClick}
                            >
                                <item.icon className="w-5 h-5" />
                                <span className="sr-only">{item.label}</span>
                            </Button>

                            {/* Premium Tooltip */}
                            <div className="absolute top-[calc(100%+12px)] left-1/2 -translate-x-1/2 px-3 py-1.5 bg-black/90 dark:bg-white text-white dark:text-black text-[10px] font-bold uppercase tracking-wider rounded-md opacity-0 group-hover:opacity-100 transform scale-75 group-hover:scale-100 transition-all duration-200 whitespace-nowrap pointer-events-none shadow-2xl z-[100] border border-white/10 dark:border-black/10 backdrop-blur-sm">
                                {item.label}
                                {/* Tooltip Arrow */}
                                <div className="absolute -top-1 left-1/2 -translate-x-1/2 border-l-4 border-l-transparent border-r-4 border-r-transparent border-b-4 border-b-black/90 dark:border-b-white"></div>
                            </div>
                        </div>
                    ))}
                </nav>

                {/* Vertical Separator */}
                <div className="w-[1px] h-6 bg-border mx-1 hidden xs:block" />

                {/* Theme toggle Tooltip Wrapped */}
                <div className="relative group">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={toggleTheme}
                        className="w-10 h-10 rounded-full hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-all duration-300"
                        title="" // Remove default title to use custom tooltip
                    >
                        {mounted && theme === "dark" ? (
                            <Sun className="w-5 h-5" />
                        ) : (
                            <Moon className="w-5 h-5" />
                        )}
                        <span className="sr-only">테마 전환</span>
                    </Button>

                    {/* Theme Tooltip */}
                    <div className="absolute top-[calc(100%+12px)] left-1/2 -translate-x-1/2 px-3 py-1.5 bg-black/90 dark:bg-white text-white dark:text-black text-[10px] font-bold uppercase tracking-wider rounded-md opacity-0 group-hover:opacity-100 transform scale-75 group-hover:scale-100 transition-all duration-200 whitespace-nowrap pointer-events-none shadow-2xl z-[100] border border-white/10 dark:border-black/10 backdrop-blur-sm">
                        {mounted ? (theme === "dark" ? "라이트 모드" : "다크 모드") : "테마 전환"}
                        {/* Tooltip Arrow */}
                        <div className="absolute -top-1 left-1/2 -translate-x-1/2 border-l-4 border-l-transparent border-r-4 border-r-transparent border-b-4 border-b-black/90 dark:border-b-white"></div>
                    </div>
                </div>
            </div>
        </header>
    );
}
