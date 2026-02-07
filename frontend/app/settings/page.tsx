"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
    const router = useRouter();

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="glass-header h-16 flex items-center justify-between px-4 md:px-6 shrink-0 sticky top-0 z-50 transition-all duration-300 shadow-sm border-b border-border">
                <div className="flex items-center gap-3">
                    <Button
                        variant="ghost"
                        onClick={() => router.push("/")}
                        className="hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black"
                    >
                        ← 돌아가기
                    </Button>
                </div>
                <h1 className="text-xl font-bold">설정</h1>
                <div className="w-24"></div> {/* Spacer for centering */}
            </header>

            {/* Main Content */}
            <main className="max-w-2xl mx-auto p-6 space-y-6">
                {/* Future Settings Sections */}
                <section className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow-sm opacity-50">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                        추가 설정
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        곧 더 많은 설정 옵션이 추가될 예정입니다.
                    </p>
                </section>
            </main>
        </div>
    );
}
