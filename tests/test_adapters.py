from chexie_agent.adapters import LegacyCapubbsAdapter, NewForumAdapter
from chexie_agent.domain import ThreadRef


def test_legacy_adapter_parses_old_thread_url():
    adapter = LegacyCapubbsAdapter()
    assert adapter.parse_thread_ref("https://chexie.net/bbs/content/?bid=28&tid=150&p=1") == ThreadRef(28, 150)


def test_new_adapter_parses_new_thread_url():
    adapter = NewForumAdapter()
    assert adapter.parse_thread_ref("https://test.chexie.net/bbs-new/threads/28-150") == ThreadRef(28, 150)
