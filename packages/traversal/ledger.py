from dataclasses import dataclass, field


@dataclass
class LedgerState:
    traversal_type: str = "pagination"
    pages_visited: int = 0
    items_discovered: int = 0
    duplicate_items_skipped: int = 0
    stop_reason: str = ""
    completion_status: str = "uncertain"
    visited_urls: set[str] = field(default_factory=set)
