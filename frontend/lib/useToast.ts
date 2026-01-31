import { useState, useEffect } from "react";

export type ToastType = "success" | "info" | "error";

export interface Toast {
    id: string;
    message: string;
    type: ToastType;
    duration: number;
}

let toastListeners: Array<(toast: Toast) => void> = [];
let toastIdCounter = 0;

// 패널 상태를 전역으로 관리 (로그용으로 유지)
let isPanelOpen = false;

export function setPanelState(isOpen: boolean) {
    isPanelOpen = isOpen;
}

export function showToast(
    message: string,
    type: ToastType = "info",
    duration: number = 3000
) {
    // 사용자의 요청에 따라 패널 상태와 관계없이 항상 알림을 표시함
    const toast: Toast = {
        id: `toast-${++toastIdCounter}`,
        message,
        type,
        duration,
    };

    toastListeners.forEach((listener) => listener(toast));
}

export function useToast() {
    const [toasts, setToasts] = useState<Toast[]>([]);

    useEffect(() => {
        const addToast = (toast: Toast) => {
            setToasts((prev) => [...prev, toast]);

            // 자동 제거
            setTimeout(() => {
                setToasts((prev) => prev.filter((t) => t.id !== toast.id));
            }, toast.duration);
        };

        toastListeners.push(addToast);

        return () => {
            toastListeners = toastListeners.filter((listener) => listener !== addToast);
        };
    }, []);

    const removeToast = (id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    return { toasts, removeToast };
}
