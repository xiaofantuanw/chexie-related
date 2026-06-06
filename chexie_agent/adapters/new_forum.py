"""New forum adapter skeleton.

As of 2026-06-06, the new forum is a React/Vite SPA under /bbs-new/ and should
be treated as a probe target, not the production automation backend.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from chexie_agent.domain import ForumPost, ThreadRef


class NewForumAdapter:
    name = "new-forum-probe"
    base_url = "https://test.chexie.net/bbs-new"

    def legacy_thread_url(self, thread: ThreadRef, page: int = 1) -> str:
        return f"https://chexie.net/bbs/content/?bid={thread.bid}&tid={thread.tid}&p={page}"

    def new_thread_url(self, thread: ThreadRef) -> str:
        return f"{self.base_url}/threads/{thread.new_thread_id}"

    def parse_thread_ref(self, value: str) -> ThreadRef | None:
        parsed = urlparse(value)
        match = re.search(r"/threads/(?:thread-)?(\d+)-(\d+)", parsed.path)
        if match:
            return ThreadRef(bid=int(match.group(1)), tid=int(match.group(2)))

        query = parse_qs(parsed.query)
        bid = _first_int(query.get("bid"))
        tid = _first_int(query.get("tid"))
        if bid and tid:
            return ThreadRef(bid=bid, tid=tid)
        return None

    def fetch_thread_posts(self, thread: ThreadRef, page: int = 1) -> list[ForumPost]:
        raise NotImplementedError("The new forum adapter is probe-only until API behavior is verified.")


def _first_int(values: list[str] | None) -> int | None:
    if not values:
        return None
    try:
        parsed = int(values[0])
    except ValueError:
        return None
    return parsed if parsed > 0 else None
