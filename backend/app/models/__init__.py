from .memory import (
    MemoryType,
    MemoryCandidate,
    Memory,
    MemoryCreate,
    ChatRequest,
    ChatResponse,
    Citation,
    MemorySearchRequest,
    MemoryListResponse,
)

__all__ = [
    "MemoryType",
    "MemoryCandidate",
    "Memory",
    "MemoryCreate",
    "ChatRequest",
    "ChatResponse",
    "Citation",
    "MemorySearchRequest",
    "MemoryListResponse",
    "MEMORY_TYPE_PRIORITY",
]

# Priority order used by the memory extractor when deciding what to store first.
# Higher number = higher priority.
MEMORY_TYPE_PRIORITY = {
    "decision": 5,
    "preference": 4,
    "plan": 3,
    "profile": 2,
    "episode": 1,
}
