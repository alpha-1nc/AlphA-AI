/**
 * Global Memory Store
 * Single source of truth for savedMap (messageId → memoryId)
 */

import type { Memory } from "./api";

// Global state
let savedMap: Record<string, string> = {};
let isInitialized = false;

// Event emitter for React components
const STORE_CHANGE_EVENT = "memoryStore:change";

/**
 * Get the entire savedMap
 */
export function getSavedMap(): Record<string, string> {
    return { ...savedMap };
}

/**
 * Replace the entire savedMap
 */
export function setSavedMap(map: Record<string, string>): void {
    savedMap = { ...map };
    emitChange();
}

/**
 * Add an entry to savedMap
 */
export function addToSavedMap(messageId: string, memoryId: string): void {
    savedMap[messageId] = memoryId;
    emitChange();
}

/**
 * Remove an entry from savedMap
 */
export function removeFromSavedMap(messageId: string): void {
    delete savedMap[messageId];
    emitChange();
}

/**
 * Check if a message is saved
 */
export function isMessageSaved(messageId: string): boolean {
    return messageId in savedMap;
}

/**
 * Get the memory ID for a message
 */
export function getMemoryId(messageId: string): string | undefined {
    return savedMap[messageId];
}

/**
 * Rebuild savedMap from a list of memories
 * This treats savedMap as derived state from the API
 */
export function rebuildFromMemories(memories: Memory[]): void {
    const newMap: Record<string, string> = {};

    memories.forEach((memory) => {
        if (memory.source_message_id) {
            newMap[memory.source_message_id] = memory.id;
        }
    });

    savedMap = newMap;
    isInitialized = true;
    emitChange();
}

/**
 * Check if the store has been initialized
 */
export function getIsInitialized(): boolean {
    return isInitialized;
}

/**
 * Mark store as initialized (used during initial load)
 */
export function markAsInitialized(): void {
    isInitialized = true;
}

/**
 * Emit change event to notify React components
 */
function emitChange(): void {
    if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent(STORE_CHANGE_EVENT));
    }
}

/**
 * Subscribe to store changes
 * Returns unsubscribe function
 */
export function subscribeToStore(callback: () => void): () => void {
    if (typeof window === "undefined") {
        return () => { };
    }

    window.addEventListener(STORE_CHANGE_EVENT, callback);
    return () => window.removeEventListener(STORE_CHANGE_EVENT, callback);
}
