"use client";

import { useToast, type Toast as ToastType } from "@/lib/useToast";
import { CheckCircle2, Info, XCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

const iconMap = {
    success: CheckCircle2,
    info: Info,
    error: XCircle,
};

const colorMap = {
    success: "bg-green-600 shadow-green-900/20",
    info: "bg-blue-600 shadow-blue-900/20",
    error: "bg-red-600 shadow-red-900/20",
};

interface ToastItemProps {
    toast: ToastType;
    onClose: () => void;
}

function ToastItem({ toast, onClose }: ToastItemProps) {
    const Icon = iconMap[toast.type];

    return (
        <div
            className={cn(
                "flex items-center gap-3 px-5 py-4 rounded-xl shadow-2xl text-white min-w-[320px] max-w-[420px] pointer-events-auto transition-all transform",
                "animate-slide-in-right border border-white/10",
                colorMap[toast.type]
            )}
        >
            <div className="bg-white/20 p-1.5 rounded-full">
                <Icon className="w-5 h-5 flex-shrink-0" />
            </div>
            <p className="text-sm font-medium flex-1 tracking-tight">{toast.message}</p>
            <button
                onClick={onClose}
                className="flex-shrink-0 hover:bg-white/20 rounded-lg p-1.5 transition-colors"
                aria-label="닫기"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
}

export function ToastContainer() {
    const { toasts, removeToast } = useToast();

    return (
        <div className="fixed top-8 right-8 z-[1000] flex flex-col gap-4 pointer-events-none">
            {toasts.map((toast) => (
                <div key={toast.id} className="transition-all duration-300">
                    <ToastItem toast={toast} onClose={() => removeToast(toast.id)} />
                </div>
            ))}
        </div>
    );
}
