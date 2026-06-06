"""Forum-independent data types.

These models are intentionally small. They define the shape of information that
workflows can use without depending on legacy CAPUBBS HTML or the new SPA.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ForumVersion(str, Enum):
    LEGACY = "legacy"
    NEW = "new"


@dataclass(frozen=True)
class BoardRef:
    bid: int
    name: str = ""


@dataclass(frozen=True)
class ThreadRef:
    bid: int
    tid: int

    @property
    def legacy_query(self) -> str:
        return f"bid={self.bid}&tid={self.tid}"

    @property
    def new_thread_id(self) -> str:
        return f"{self.bid}-{self.tid}"


@dataclass(frozen=True)
class FloorRef:
    thread: ThreadRef
    floor: int | None = None
    pid: int | None = None


@dataclass(frozen=True)
class UserRef:
    username: str


@dataclass(frozen=True)
class ForumPost:
    thread: ThreadRef
    floor: int
    author: str
    posted_at: str
    content_text: str
    content_html: str = ""
    pid: int | None = None
    nested_replies: tuple["NestedReply", ...] = ()


@dataclass(frozen=True)
class NestedReply:
    author: str
    content_text: str
    posted_at: str = ""


@dataclass(frozen=True)
class ForumThread:
    ref: ThreadRef
    title: str
    board: BoardRef | None = None
    page: int = 1
    total_pages: int | None = None
    posts: tuple[ForumPost, ...] = ()
    source_url: str = ""
    login_required: bool = False


@dataclass(frozen=True)
class ForumSearchResult:
    ref: ThreadRef
    title: str
    url: str
    excerpt: str = ""
    board: BoardRef | None = None
