"""Shared adapter contract for legacy CAPUBBS and the future new forum."""

from __future__ import annotations

from typing import Protocol

from chexie_agent.domain import ForumPost, ForumSearchResult, ForumThread, ThreadRef


class ForumAdapter(Protocol):
    """Minimal forum operations expected by account-agent workflows."""

    name: str
    base_url: str

    def legacy_thread_url(self, thread: ThreadRef, page: int = 1) -> str:
        """Return the canonical legacy URL for a thread."""

    def new_thread_url(self, thread: ThreadRef) -> str:
        """Return the canonical new-forum URL for a thread."""

    def parse_thread_ref(self, value: str) -> ThreadRef | None:
        """Parse a URL or thread id into `ThreadRef` when possible."""

    def fetch_thread_posts(self, thread: ThreadRef, page: int = 1) -> list[ForumPost]:
        """Read posts from one thread page."""

    def fetch_thread(self, thread: ThreadRef, page: int = 1) -> ForumThread:
        """Read one thread page and return structured metadata plus posts."""

    def fetch_thread_pages(
        self,
        thread: ThreadRef,
        *,
        start_page: int = 1,
        max_pages: int | None = None,
    ) -> ForumThread:
        """Read and merge multiple pages from one thread."""

    def search_threads(
        self,
        keyword: str,
        *,
        author: str = "",
        search_type: str = "thread",
        bid: int = -1,
        starttime: str = "2001-01-01",
        endtime: str = "2100-01-01",
    ) -> list[ForumSearchResult]:
        """Search public legacy thread references by keyword."""
