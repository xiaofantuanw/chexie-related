import json
import subprocess
import sys
from pathlib import Path

import pytest

from chexie_agent.domain import BoardRef, ForumPost, ForumThread, ThreadRef
from chexie_agent.safety import ActionKind
from chexie_agent.workflows import AccountAgentWorkflow


class FakeAdapter:
    name = "fake"
    base_url = "https://chexie.net/bbs"

    def legacy_thread_url(self, thread: ThreadRef, page: int = 1) -> str:
        return f"{self.base_url}/content/?bid={thread.bid}&tid={thread.tid}&p={page}"

    def new_thread_url(self, thread: ThreadRef) -> str:
        return f"https://test.chexie.net/bbs-new/threads/{thread.new_thread_id}"

    def parse_thread_ref(self, value: str) -> ThreadRef | None:
        if value == "sample":
            return ThreadRef(28, 150)
        return None

    def fetch_thread_posts(self, thread: ThreadRef, page: int = 1) -> list[ForumPost]:
        return list(self.fetch_thread(thread, page).posts)

    def fetch_thread(self, thread: ThreadRef, page: int = 1) -> ForumThread:
        return ForumThread(
            ref=thread,
            title="新版论坛指南",
            board=BoardRef(thread.bid, "网站维护"),
            posts=(
                ForumPost(
                    thread=thread,
                    floor=1,
                    author="alice",
                    posted_at="2026-05-27 15:38:31",
                    content_text="announcement",
                ),
            ),
            source_url=self.legacy_thread_url(thread, page),
        )

    def fetch_thread_pages(
        self,
        thread: ThreadRef,
        *,
        start_page: int = 1,
        max_pages: int | None = None,
    ) -> ForumThread:
        return self.fetch_thread(thread, start_page)

    def search_threads(self, keyword: str, **kwargs):
        return []


def test_account_workflow_creates_local_reply_draft():
    workflow = AccountAgentWorkflow(FakeAdapter())

    draft = workflow.create_reply_draft("sample", "收到，感谢更新。", created_at="2026-06-06T12:00:00+00:00")

    assert draft.request.kind is ActionKind.DRAFT
    assert draft.request.exact_payload == "收到，感谢更新。"
    assert draft.title == "新版论坛指南"
    assert draft.board_name == "网站维护"
    assert draft.latest_post_summary == "第 1 楼 alice 2026-05-27 15:38:31"


def test_account_workflow_saves_json_and_markdown_without_user_facing_internal_ids(tmp_path):
    workflow = AccountAgentWorkflow(FakeAdapter())
    draft = workflow.create_reply_draft("sample", "本地草稿正文", created_at="2026-06-06T12:00:00+00:00")

    json_path, markdown_path = workflow.save_reply_draft(draft, tmp_path)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    rendered = markdown_path.read_text(encoding="utf-8")
    assert data["status"] == "draft"
    assert data["request"]["kind"] == "draft"
    assert data["request"]["exact_payload"] == "本地草稿正文"
    assert "回帖草稿: 新版论坛指南" in rendered
    assert "状态: 本地草稿，未发帖" in rendered
    assert "本地草稿正文" in rendered
    assert "28-150" not in rendered
    assert "bid=" not in rendered
    assert "tid=" not in rendered


def test_account_workflow_blocks_unapproved_write():
    workflow = AccountAgentWorkflow(FakeAdapter())

    with pytest.raises(PermissionError):
        workflow.approve_reply(ThreadRef(28, 150), "exact payload", authorized=False)


def test_account_draft_cli_rejects_empty_text(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/chexie_account_draft.py",
            "reply",
            "sample",
            "--text",
            " ",
            "--drafts-dir",
            str(tmp_path),
        ],
        check=False,
        cwd=root,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "Reply text is empty." in result.stderr
