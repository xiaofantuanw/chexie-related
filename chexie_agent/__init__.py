"""Shared scaffolding for Chexie/CAPUBBS account-agent workflows."""

from .domain import BoardRef, ForumVersion, ThreadRef
from .safety import ActionKind, ActionRequest, require_live_authorization

__all__ = [
    "ActionKind",
    "ActionRequest",
    "BoardRef",
    "ForumVersion",
    "ThreadRef",
    "require_live_authorization",
]
