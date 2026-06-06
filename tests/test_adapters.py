from chexie_agent.adapters import LegacyCapubbsAdapter, NewForumAdapter
from chexie_agent.domain import ThreadRef


def test_legacy_adapter_parses_old_thread_url():
    adapter = LegacyCapubbsAdapter()
    assert adapter.parse_thread_ref("https://chexie.net/bbs/content/?bid=28&tid=150&p=1") == ThreadRef(28, 150)


def test_new_adapter_parses_new_thread_url():
    adapter = NewForumAdapter()
    assert adapter.parse_thread_ref("https://test.chexie.net/bbs-new/threads/28-150") == ThreadRef(28, 150)


def test_legacy_adapter_parses_thread_html():
    adapter = LegacyCapubbsAdapter()
    html = """
    <html>
      <head><title>Fallback title</title></head>
      <body>
        <a href="../main/?bid=28">网站维护</a>
        <a id="page_title" href="./?bid=28&tid=150&p=1">新版论坛指南</a>
        <span class="page">1</span><a class="page" href="../content/?p=2&bid=28&tid=150">2</a>
        <table>
          <tr class="floor" id="1">
            <td>
              <a name="pid1"></a>
              <p><a class="authorbig" href="../user?name=alice">alice</a></p>
              <div class="floorinfo">发表于 2026-05-27 15:38:31 楼主</div>
              <div class="textblock" id="floor0">
                正文第一行<br>
                <b>正文第二行</b>
              </div>
              <table class="lzltable">
                <tr><td class="lzltd">
                  <div class="lzlicon">icon</div>
                  <a class="author" href="../user?name=bob">bob</a>: 楼中楼内容
                  <span class="lzltime">2026-05-27 15:41:03</span>
                </td></tr>
              </table>
              <button onclick="dolzlreply(1,606652,this);">发表</button>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    thread = adapter.parse_thread_html(html, thread=ThreadRef(28, 150), source_url="https://example.test")

    assert thread.title == "新版论坛指南"
    assert thread.board is not None
    assert thread.board.name == "网站维护"
    assert thread.total_pages == 2
    assert thread.source_url == "https://example.test"
    assert len(thread.posts) == 1
    post = thread.posts[0]
    assert post.floor == 1
    assert post.pid == 606652
    assert post.author == "alice"
    assert post.posted_at == "2026-05-27 15:38:31"
    assert "正文第一行" in post.content_text
    assert "正文第二行" in post.content_text
    assert "楼中楼内容" not in post.content_text
    assert "<b>正文第二行</b>" in post.content_html
    assert len(post.nested_replies) == 1
    assert post.nested_replies[0].author == "bob"
    assert post.nested_replies[0].content_text == "楼中楼内容"


def test_legacy_adapter_parses_search_html():
    adapter = LegacyCapubbsAdapter()
    html = """
    <html>
      <body>
        <table>
          <tr>
            <td>
              <a href="../content/?bid=28&tid=150&p=1">新版论坛指南</a>
              <span>网站维护 2026-05-27 命中摘要</span>
            </td>
          </tr>
          <tr>
            <td>
              <a href="/bbs/content/?bid=4&tid=19989">签名档教程</a>
              <span>纯净水 签名档 source floor</span>
            </td>
          </tr>
          <tr>
            <td>
              <a href="/bbs/content/?bid=4&tid=19989&p=2">签名档教程重复链接</a>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    results = adapter.parse_search_html(html, source_url="https://chexie.net/bbs/search?keyword=论坛")

    assert len(results) == 2
    assert results[0].ref == ThreadRef(28, 150)
    assert results[0].title == "新版论坛指南"
    assert results[0].url == "https://chexie.net/bbs/content/?bid=28&tid=150&p=1"
    assert "命中摘要" in results[0].excerpt
    assert results[1].ref == ThreadRef(4, 19989)


def test_legacy_adapter_search_rejects_empty_keyword_and_author():
    adapter = LegacyCapubbsAdapter()
    assert adapter.search_threads("") == []
