"use client";

import { CitationList } from "@/components/citation/CitationCard";
import { MemoryPanel } from "@/components/memory/MemoryPanel";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Database, Brain } from "lucide-react";
import type { Citation } from "@/lib/api";

interface MemorySidebarProps {
    citations: Citation[];
    className?: string;
}

/**
 * MemorySidebar Component
 * 
 * Reorganized right sidebar UI with two sections:
 * 1. Referenced Memories (Section 1: 참고한 기억)
 * 2. Memory Repository (Section 2: 기억 저장소)
 * 
 * Aesthetic improvements: Glassmorphism, improved spacing, and always-visible headers.
 */
export function MemorySidebar({ citations, className = "" }: MemorySidebarProps) {
    return (
        <div className={`flex flex-col h-full bg-background/80 backdrop-blur-md border-l border-border/50 ${className}`}>
            {/* Section 1: 참고한 기억 (Referenced Memories) - Dynamic max height (35%) */}
            <section className="flex flex-col h-[35%] min-h-[220px] border-b border-border/40 overflow-hidden">
                <header className="px-4 py-3.5 flex items-center justify-between bg-muted/30 backdrop-blur-sm z-20 shrink-0 border-b border-border/5">
                    <h3 className="font-bold flex items-center gap-2 text-[12px] tracking-widest uppercase text-muted-foreground">
                        <Database className="w-3.5 h-3.5 text-primary opacity-80" />
                        참고한 기억
                    </h3>
                    {citations.length > 0 && (
                        <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-bold tabular-nums">
                            {citations.length}
                        </span>
                    )}
                </header>

                <ScrollArea className="flex-1">
                    <div className="px-4 py-2">
                        {citations.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-10 text-center space-y-2 opacity-50">
                                <Database className="w-8 h-8 text-muted-foreground/20" />
                                <p className="text-xs text-muted-foreground">사용된 기억이 없습니다</p>
                            </div>
                        ) : (
                            <div className="pb-4">
                                <CitationList citations={citations} hideHeader />
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </section>

            {/* Section 2: 기억 저장소 (Memory Repository) - Flexible height */}
            <section className="flex-1 flex flex-col min-h-0 bg-background/20 overflow-hidden">
                <header className="px-4 py-3.5 flex items-center justify-between bg-muted/30 backdrop-blur-sm z-20 shrink-0 border-b border-border/5">
                    <h3 className="font-bold flex items-center gap-2 text-[12px] tracking-widest uppercase text-muted-foreground">
                        <Brain className="w-3.5 h-3.5 text-primary opacity-80" />
                        기억 저장소
                    </h3>
                </header>

                <div className="flex-1 min-h-0">
                    <MemoryPanel className="h-full" hideHeader />
                </div>
            </section>
        </div>
    );
}
