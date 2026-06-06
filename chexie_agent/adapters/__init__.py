"""Forum adapter implementations."""

from .base import ForumAdapter
from .legacy_capubbs import LegacyCapubbsAdapter
from .new_forum import NewForumAdapter

__all__ = ["ForumAdapter", "LegacyCapubbsAdapter", "NewForumAdapter"]
