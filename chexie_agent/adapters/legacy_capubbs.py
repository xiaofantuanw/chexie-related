"""Legacy CAPUBBS adapter skeleton.

Existing scripts remain the source of truth for concrete behavior. This class is
the future home for shared, tested operations now scattered across scripts.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from chexie_agent.domain import ForumPost, ThreadRef


class LegacyCapubbsAdapter:
    name = "legacy-capubbs"
    base_url = "https://chexie.net/bbs"

    def legacy_thread_url(self, thread: ThreadRef, page: int = 1) -> str:
        return f"{self.base_url}/content/?bid={thread.bid}&tid={thread.tid}&p={page}"

    def new_thread_url(self, thread: ThreadRef) -> str:
        return f"https://test.chexie.net/bbs-new/threads/{thread.new_thread_id}"

    def parse_thread_ref(self, value: str) -> ThreadRef | None:
        parsed = urlparse(value)
        query = parse_qs(parsed.query)
        bid = _first_int(query.get("bid"))
        tid = _first_int(query.get("tid"))
        if bid and tid:
            return ThreadRef(bid=bid, tid=tid)

        match = re.search(r"(?:thread-)?(\d+)-(\d+)", value)
        if not match:
            return None
        return ThreadRef(bid=int(match.group(1)), tid=int(match.group(2)))

    def fetch_thread_posts(self, thread: ThreadRef, page: int = 1) -> list[ForumPost]:
        raise NotImplementedError("Use scripts/inspect_chexie.py or scripts/capu_crawler.py until this is implemented.")


def _first_int(values: list[str] | None) -> int | None:
    if not values:
        return None
    try:
        parsed = int(values[0])
    except ValueError:
        return None
    return parsed if parsed > 0 else None
