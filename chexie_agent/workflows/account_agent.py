"""High-level workflow facade for future account-agent features."""

from __future__ import annotations

from dataclasses import dataclass

from chexie_agent.adapters.base import ForumAdapter
from chexie_agent.domain import ThreadRef
from chexie_agent.safety import ActionKind, ActionRequest, require_live_authorization


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

    def approve_reply(self, thread: ThreadRef, text: str, authorized: bool) -> ActionRequest:
        request = ActionRequest(
            kind=ActionKind.WRITE,
            target=self.adapter.legacy_thread_url(thread),
            summary="Post a reply to a Chexie thread.",
            exact_payload=text,
        )
        require_live_authorization(request, authorized)
        return request
