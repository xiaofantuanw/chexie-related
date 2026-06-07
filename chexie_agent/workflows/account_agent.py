"""High-level workflow facade for account-agent features."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chexie_agent.adapters.base import ForumAdapter
from chexie_agent.domain import ForumThread, ThreadRef
from chexie_agent.safety import ActionKind, ActionRequest, require_live_authorization
from chexie_agent.serialization import to_plain_data


@dataclass(frozen=True)
class ReplyDraft:
    """Local-only reply draft metadata and exact payload."""

    request: ActionRequest
    thread: ForumThread
    created_at: str

    @property
    def title(self) -> str:
        return self.thread.title or "未命名帖子"

    @property
    def board_name(self) -> str:
        if self.thread.board and self.thread.board.name:
            return self.thread.board.name
        return "未知版面"

    @property
    def latest_post_summary(self) -> str:
        if not self.thread.posts:
            return "未读取到楼层内容"
        post = self.thread.posts[-1]
        pieces = [f"第 {post.floor} 楼"]
        if post.author:
            pieces.append(post.author)
        if post.posted_at:
            pieces.append(post.posted_at)
        return " ".join(pieces)


@dataclass
class AccountAgentWorkflow:
    adapter: ForumAdapter

    def resolve_thread(self, value: str) -> ThreadRef:
        thread = self.adapter.parse_thread_ref(value)
        if thread is None:
            raise ValueError(f"Cannot resolve Chexie thread reference: {value}")
        return thread

    def draft_reply(self, thread: ThreadRef, text: str) -> ActionRequest:
        return ActionRequest(
            kind=ActionKind.DRAFT,
            target=self.adapter.legacy_thread_url(thread),
            summary="Draft a forum reply locally.",
            exact_payload=text,
        )

    def create_reply_draft(self, value: str, text: str, *, created_at: str | None = None) -> ReplyDraft:
        thread_ref = self.resolve_thread(value)
        thread = self.adapter.fetch_thread(thread_ref)
        timestamp = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return ReplyDraft(
            request=self.draft_reply(thread_ref, text),
            thread=thread,
            created_at=timestamp,
        )

    def render_reply_draft_markdown(self, draft: ReplyDraft) -> str:
        lines = [
            f"# 回帖草稿: {draft.title}",
            "",
            f"- 版面: {draft.board_name}",
            f"- 创建时间: {draft.created_at}",
            f"- 最近读取楼层: {draft.latest_post_summary}",
            "- 状态: 本地草稿，未发帖",
        ]
        if draft.thread.login_required:
            lines.append("- 需要登录: 是")
        lines.extend(
            [
                "",
                "## 正文",
                "",
                draft.request.exact_payload.rstrip(),
                "",
            ]
        )
        return "\n".join(lines)

    def save_reply_draft(self, draft: ReplyDraft, drafts_dir: Path) -> tuple[Path, Path]:
        drafts_dir.mkdir(parents=True, exist_ok=True)
        base_name = _draft_base_name(draft)
        json_path = drafts_dir / f"{base_name}.json"
        markdown_path = drafts_dir / f"{base_name}.md"

        json_path.write_text(
            json.dumps(_reply_draft_data(draft), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(self.render_reply_draft_markdown(draft), encoding="utf-8")
        return json_path, markdown_path

    def approve_reply(self, thread: ThreadRef, text: str, authorized: bool) -> ActionRequest:
        request = ActionRequest(
            kind=ActionKind.WRITE,
            target=self.adapter.legacy_thread_url(thread),
            summary="Post a reply to a Chexie thread.",
            exact_payload=text,
        )
        require_live_authorization(request, authorized)
        return request


def _reply_draft_data(draft: ReplyDraft) -> dict[str, Any]:
    return {
        "created_at": draft.created_at,
        "status": "draft",
        "request": to_plain_data(draft.request),
        "thread": to_plain_data(draft.thread),
    }


def _draft_base_name(draft: ReplyDraft) -> str:
    created = draft.created_at.replace(":", "").replace("+", "Z")
    slug = _slugify(draft.title)
    return f"{created}_reply_{slug}"[:120].rstrip("_")


def _slugify(value: str) -> str:
    cleaned = re.sub(r"\s+", "_", value.strip())
    cleaned = re.sub(r"[^\w.-]+", "_", cleaned, flags=re.UNICODE)
    cleaned = cleaned.strip("._")
    return cleaned or "untitled"
