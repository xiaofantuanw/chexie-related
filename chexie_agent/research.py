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
            f"# {thread.title or '未命名帖子'}",
            "",
        ]
        if thread.board:
            lines.append(f"- 版面: {thread.board.name or '未知版面'}")
        if thread.total_pages:
            lines.append(f"- 总页数: {thread.total_pages}")
        if thread.login_required:
            lines.append("- 需要登录: 是")
        lines.append("")

        for post in thread.posts:
            heading = f"## 第 {post.floor} 楼 {post.author} {post.posted_at}".strip()
            lines.extend([heading, ""])
            lines.append(post.content_text.strip() or "(empty)")
            if include_nested and post.nested_replies:
                lines.extend(["", "楼中楼:"])
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
            lines.append(f"{index}. {result.title or '未命名帖子'}{board}")
            if result.excerpt:
                lines.append(f"   - 摘要: {result.excerpt}")
        return "\n".join(lines) + "\n"
