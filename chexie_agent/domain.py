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
