"""Safety gates for account-agent actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionKind(str, Enum):
    READ = "read"
    DRAFT = "draft"
    WRITE = "write"


@dataclass(frozen=True)
class ActionRequest:
    kind: ActionKind
    target: str
    summary: str
    exact_payload: str = ""


def require_live_authorization(request: ActionRequest, authorized: bool) -> None:
    """Raise unless a live forum-changing action has explicit authorization."""

    if request.kind is not ActionKind.WRITE:
        return
    if authorized:
        return
    raise PermissionError(
        "Live Chexie write action requires explicit authorization for the exact target and payload: "
        f"{request.target}"
    )
