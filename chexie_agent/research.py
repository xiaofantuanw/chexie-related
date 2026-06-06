"""Read-only research workflow for Chexie forum content."""

from __future__ import annotations

from dataclasses import dataclass

from chexie_agent.adapters.base import ForumAdapter
from chexie_agent.domain import ForumSearchResult, ForumThread, ThreadRef


@dataclass
class ForumResearchAgent:
    """Small facade for forum reading tasks.

    This class deliberately avoids write actions. It is meant to become the
    first stable layer that future account-agent workflows can depend on.
    """

    adapter: ForumAdapter

    def resolve_thread(self, value: str) -> ThreadRef:
        thread = self.adapter.parse_thread_ref(value)
        if thread is None:
            raise ValueError(f"Cannot resolve Chexie thread reference: {value}")
        return thread

    def read_thread(self, value: str, *, all_pages: bool = False, max_pages: int | None = None) -> ForumThread:
        thread = self.resolve_thread(value)
        if all_pages:
            return self.adapter.fetch_thread_pages(thread, max_pages=max_pages)
        return self.adapter.fetch_thread(thread)

    def search(
        self,
        keyword: str,
        *,
        author: str = "",
        search_type: str = "thread",
        bid: int = -1,
        starttime: str = "2001-01-01",
        endtime: str = "2100-01-01",
    ) -> list[ForumSearchResult]:
        return self.adapter.search_threads(
            keyword,
            author=author,
            search_type=search_type,
            bid=bid,
            starttime=starttime,
            endtime=endtime,
        )

    def render_thread_markdown(self, thread: ForumThread, *, include_nested: bool = True) -> str:
        lines = [
            f"# {thread.title or thread.ref.short_label}",
            "",
            f"- Thread: {thread.ref.short_label}",
            f"- URL: {self.adapter.legacy_thread_url(thread.ref, thread.page)}",
        ]
        if thread.board:
            lines.append(f"- Board: {thread.board.name or thread.board.bid}")
        if thread.total_pages:
            lines.append(f"- Pages: {thread.total_pages}")
        if thread.login_required:
            lines.append("- Login required: true")
        lines.append("")

        for post in thread.posts:
            heading = f"## {post.ref.label} {post.author} {post.posted_at}".strip()
            lines.extend([heading, ""])
            lines.append(post.content_text.strip() or "(empty)")
            if include_nested and post.nested_replies:
                lines.extend(["", "Nested replies:"])
                for reply in post.nested_replies:
                    suffix = f" {reply.posted_at}" if reply.posted_at else ""
                    lines.append(f"- {reply.author}{suffix}: {reply.content_text}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def render_search_markdown(self, results: list[ForumSearchResult]) -> str:
        lines = ["# Search Results", ""]
        if not results:
            lines.append("(no results)")
            return "\n".join(lines) + "\n"
        for index, result in enumerate(results, start=1):
            board = f" [{result.board.name}]" if result.board and result.board.name else ""
            lines.append(f"{index}. {result.title or result.ref.short_label}{board}")
            lines.append(f"   - Thread: {result.ref.short_label}")
            lines.append(f"   - URL: {result.url}")
            if result.excerpt:
                lines.append(f"   - Excerpt: {result.excerpt}")
        return "\n".join(lines) + "\n"
