"""Legacy CAPUBBS adapter skeleton.

Existing scripts remain the source of truth for concrete behavior. This class is
the future home for shared, tested operations now scattered across scripts.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from chexie_agent.domain import BoardRef, ForumPost, ForumSearchResult, ForumThread, NestedReply, ThreadRef


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
        return list(self.fetch_thread(thread, page).posts)

    def fetch_thread(self, thread: ThreadRef, page: int = 1) -> ForumThread:
        url = self.legacy_thread_url(thread, page)
        resp = requests.get(url, headers=_headers(), timeout=20)
        resp.raise_for_status()
        return self.parse_thread_html(resp.text, thread=thread, page=page, source_url=resp.url)

    def fetch_thread_pages(
        self,
        thread: ThreadRef,
        *,
        start_page: int = 1,
        max_pages: int | None = None,
    ) -> ForumThread:
        first_page = max(1, start_page)
        first = self.fetch_thread(thread, first_page)
        total_pages = first.total_pages or first_page
        last_page = total_pages if max_pages is None else min(total_pages, first_page + max_pages - 1)

        pages = [first]
        for page in range(first_page + 1, last_page + 1):
            pages.append(self.fetch_thread(thread, page))

        posts: list[ForumPost] = []
        for thread_page in pages:
            posts.extend(thread_page.posts)

        return ForumThread(
            ref=first.ref,
            title=first.title,
            board=first.board,
            page=first_page,
            total_pages=first.total_pages,
            posts=tuple(posts),
            source_url=first.source_url,
            login_required=any(thread_page.login_required for thread_page in pages),
        )

    def search_threads(
        self,
        keyword: str,
        *,
        author: str = "",
        search_type: str = "thread",
        bid: int = -1,
        starttime: str = "2001-01-01",
        endtime: str = "2100-01-01",
    ) -> list[ForumSearchResult]:
        cleaned = keyword.strip()
        cleaned_author = author.strip()
        if not cleaned and not cleaned_author:
            return []
        normalized_type = search_type if search_type in {"thread", "post"} else "thread"
        url = f"{self.base_url}/search/"
        resp = requests.post(
            url,
            data={
                "keyword": cleaned,
                "type": normalized_type,
                "bid": str(bid),
                "show": "1",
                "starttime": starttime,
                "endtime": endtime,
                "author": cleaned_author,
            },
            headers=_headers(),
            timeout=20,
        )
        resp.raise_for_status()
        return self.parse_search_html(resp.text, source_url=resp.url)

    def parse_thread_html(
        self,
        html: str,
        *,
        thread: ThreadRef,
        page: int = 1,
        source_url: str = "",
    ) -> ForumThread:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        login_required = "登录" in text and (
            "后回复此贴" in text or "后才能查看本版面帖子内容" in text
        ) and not soup.select("tr.floor")
        return ForumThread(
            ref=thread,
            title=_parse_title(soup),
            board=_parse_board(soup, thread.bid),
            page=page,
            total_pages=_parse_total_pages(soup),
            posts=tuple(_parse_post_floors(soup, thread)),
            source_url=source_url,
            login_required=login_required,
        )

    def parse_search_html(self, html: str, *, source_url: str = "") -> list[ForumSearchResult]:
        soup = BeautifulSoup(html, "html.parser")
        return _parse_search_results(soup, source_url or self.base_url)


def _first_int(values: list[str] | None) -> int | None:
    if not values:
        return None
    try:
        parsed = int(values[0])
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Referer": f"{LegacyCapubbsAdapter.base_url}/index/",
    }


def _parse_title(soup: BeautifulSoup) -> str:
    page_title = soup.select_one("#page_title")
    if page_title:
        return page_title.get_text(" ", strip=True)
    if soup.title:
        return soup.title.get_text(" ", strip=True)
    return ""


def _parse_board(soup: BeautifulSoup, bid: int) -> BoardRef | None:
    for link in soup.find_all("a", href=True):
        if f"bid={bid}" not in link["href"]:
            continue
        name = link.get_text(" ", strip=True)
        if name:
            return BoardRef(bid=bid, name=name)
    return BoardRef(bid=bid)


def _parse_total_pages(soup: BeautifulSoup) -> int | None:
    pages: list[int] = []
    for item in soup.select(".page"):
        raw = item.get_text(" ", strip=True)
        if raw.isdigit():
            pages.append(int(raw))
    return max(pages) if pages else None


def _parse_post_floor(row: Tag, thread: ThreadRef) -> ForumPost | None:
    floor = _parse_floor_number(row)
    if floor is None:
        return None

    author_node = row.select_one(".authorbig")
    author = author_node.get_text(" ", strip=True) if author_node else ""
    posted_at = _parse_posted_at(row)
    content_node = row.select_one(".textblock")
    nested_replies = _parse_nested_replies(row)
    pid = _parse_pid(row)

    content_html = ""
    content_text = ""
    if content_node:
        content_copy = BeautifulSoup(str(content_node), "html.parser")
        for nested in content_copy.select(".lzltable"):
            nested.decompose()
        body = content_copy.select_one(".textblock") or content_copy
        content_html = body.decode_contents().strip() if isinstance(body, Tag) else str(body).strip()
        content_text = body.get_text("\n", strip=True)

    return ForumPost(
        thread=thread,
        floor=floor,
        author=author,
        posted_at=posted_at,
        content_text=content_text,
        content_html=content_html,
        pid=pid,
        nested_replies=tuple(nested_replies),
    )


def _parse_post_floors(soup: BeautifulSoup, thread: ThreadRef) -> list[ForumPost]:
    posts: list[ForumPost] = []
    for row in soup.select("tr.floor"):
        post = _parse_post_floor(row, thread)
        if post:
            posts.append(post)
    return posts


def _parse_floor_number(row: Tag) -> int | None:
    floor_id = row.get("id", "").strip()
    if floor_id.isdigit():
        return int(floor_id)
    anchor = row.find_previous("a", attrs={"name": re.compile(r"pid\d+")})
    if not anchor:
        return None
    match = re.search(r"pid(\d+)", anchor.get("name", ""))
    return int(match.group(1)) if match else None


def _parse_pid(row: Tag) -> int | None:
    for button in row.find_all(attrs={"onclick": True}):
        onclick = button.get("onclick", "")
        match = re.search(r"dolzlreply\(\s*\d+\s*,\s*(\d+)", onclick)
        if match:
            return int(match.group(1))
    return None


def _parse_posted_at(row: Tag) -> str:
    floor_info = row.select_one(".floorinfo")
    if not floor_info:
        return ""
    raw = floor_info.get_text(" ", strip=True)
    match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", raw)
    return match.group(0) if match else raw


def _parse_nested_replies(row: Tag) -> list[NestedReply]:
    replies: list[NestedReply] = []
    local_row = _clone_without_nested_floor_rows(row)
    for item in local_row.select(".lzltable .lzltd"):
        author_node = item.select_one("a.author")
        time_node = item.select_one(".lzltime")
        author = author_node.get_text(" ", strip=True) if author_node else ""
        posted_at = time_node.get_text(" ", strip=True) if time_node else ""

        clone = BeautifulSoup(str(item), "html.parser")
        for tag in clone.select("a.author, .lzltime, .lzlicon"):
            tag.decompose()
        content_text = clone.get_text(" ", strip=True).lstrip(":：").strip()
        if not author:
            continue
        if not content_text or content_text in {"发表", "我也说一句 发表"}:
            continue
        replies.append(NestedReply(author=author, content_text=content_text, posted_at=posted_at))
    return replies


def _clone_without_nested_floor_rows(row: Tag) -> Tag:
    clone = BeautifulSoup(str(row), "html.parser")
    root = clone.select_one("tr.floor")
    if root is None:
        return clone
    for nested_floor in root.find_all("tr", class_="floor"):
        nested_floor.decompose()
    return root


def _parse_search_results(soup: BeautifulSoup, source_url: str) -> list[ForumSearchResult]:
    results: list[ForumSearchResult] = []
    seen: set[ThreadRef] = set()
    base_url = _as_directory_url(source_url)
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "content" not in href or "tid=" not in href or "bid=" not in href:
            continue
        absolute_url = urljoin(base_url, href)
        ref = _parse_thread_ref_from_url(absolute_url)
        if ref is None or ref in seen:
            continue
        seen.add(ref)
        raw_title = link.get_text(" ", strip=True)
        container = _nearest_result_container(link)
        excerpt = _extract_excerpt(container, raw_title)
        title = _derive_search_title(container, raw_title)
        results.append(
            ForumSearchResult(
                ref=ref,
                title=title,
                url=absolute_url,
                excerpt=excerpt,
                board=_parse_board(container, ref.bid) if container else None,
            )
        )
    return results


def _as_directory_url(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    path = parsed.path or "/"
    if not path.endswith("/"):
        path = f"{path}/"
    return parsed._replace(path=path, query="", fragment="").geturl()


def _parse_thread_ref_from_url(value: str) -> ThreadRef | None:
    parsed = urlparse(value)
    query = parse_qs(parsed.query)
    bid = _first_int(query.get("bid"))
    tid = _first_int(query.get("tid"))
    if bid and tid:
        return ThreadRef(bid=bid, tid=tid)
    return None


def _nearest_result_container(link: Tag) -> Tag | None:
    for parent_name in ("tr", "li", "div", "p"):
        parent = link.find_parent(parent_name)
        if parent:
            return parent
    return None


def _extract_excerpt(container: Tag | None, title: str) -> str:
    if container is None:
        return ""
    text = container.get_text(" ", strip=True)
    if title and text.startswith(title):
        text = text[len(title) :].strip(" -:：")
    return text


def _derive_search_title(container: Tag | None, raw_title: str) -> str:
    if raw_title and raw_title != "查看原帖":
        return raw_title
    if container is None:
        return raw_title
    text = container.get_text(" ", strip=True)
    match = re.search(r"(?:Re:\s*)?(.+?)\s+查看原帖\s+---\s+", text)
    if match:
        return match.group(1).strip()
    return raw_title
