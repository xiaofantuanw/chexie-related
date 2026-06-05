#!/usr/bin/env python3
"""
capu_crawler.py — CAPUBBS (chexie.net) 批量帖子爬取脚本

用法:
  # 爬取所有公开板块的帖子列表（不含正文）
  python capu_crawler.py

  # 爬取所有板块（含正文），需要登录 cookie
  python capu_crawler.py --phpsessid <your_session_id> --token <your_token> --content

  # 只爬取指定板块
  python capu_crawler.py --bids 2 4 6 --content

  # 指定输出数据库路径
  python capu_crawler.py --db /path/to/output.db

数据库表结构:
  boards  — 板块基本信息
  threads — 帖子列表（标题、作者、回复数等）
  posts   — 帖子正文（每一楼的内容）
"""

import argparse
import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ── 常量 ───────────────────────────────────────────────────────────────────────

BASE_URL = "https://chexie.net/bbs"

BOARDS: dict[int, str] = {
    1:  "车协工作区",   # 需要登录
    2:  "行者足音",
    3:  "车友宝典",
    4:  "纯净水",
    5:  "考察与社会",
    6:  "五湖四海",
    7:  "一技之长",
    8:  "历史笔记",
    9:  "竞赛竞技",
    10: "资料整理",
    11: "回收",
    12: "公告栏",
    13: "新闻发布",
    16: "剧组工作",
    20: "游记",
    28: "网站维护",
    30: "测试",
    31: "精品集合",
}

DEFAULT_DELAY = 1.0   # 每次请求间隔（秒），请勿设置太低
DEFAULT_DB    = Path(__file__).parent.parent / "data" / "capu_bbs.db"

# ── 数据库 ─────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS boards (
    bid          INTEGER PRIMARY KEY,
    name         TEXT,
    total_topics INTEGER
);

CREATE TABLE IF NOT EXISTS threads (
    tid              INTEGER PRIMARY KEY,
    bid              INTEGER NOT NULL,
    title            TEXT,
    author           TEXT,
    created_date     TEXT,
    replies          INTEGER DEFAULT 0,
    views            INTEGER DEFAULT 0,
    last_reply       TEXT,
    content_crawled  INTEGER DEFAULT 0,   -- 0=未爬正文, 1=已完成
    FOREIGN KEY (bid) REFERENCES boards(bid)
);

CREATE TABLE IF NOT EXISTS posts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tid       INTEGER NOT NULL,
    bid       INTEGER NOT NULL,
    floor     INTEGER NOT NULL,           -- 楼层号（1 = 楼主）
    author    TEXT,
    post_time TEXT,
    content   TEXT,                       -- 纯文本正文
    UNIQUE (tid, floor),
    FOREIGN KEY (tid) REFERENCES threads(tid)
);

CREATE INDEX IF NOT EXISTS idx_threads_bid ON threads(bid);
CREATE INDEX IF NOT EXISTS idx_posts_tid   ON posts(tid);
"""


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


# ── HTTP 工具 ──────────────────────────────────────────────────────────────────

def make_session(
    phpsessid: Optional[str] = None,
    token: Optional[str] = None,
) -> requests.Session:
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Referer": "https://chexie.net/bbs/index/",
    })
    if phpsessid:
        sess.cookies.set("PHPSESSID", phpsessid, domain=".chexie.net", path="/")
    if token:
        sess.cookies.set("token", token, domain=".chexie.net", path="/")
    return sess


def fetch(sess: requests.Session, url: str, delay: float) -> Optional[BeautifulSoup]:
    try:
        resp = sess.get(url, timeout=20)
        resp.raise_for_status()
        time.sleep(delay)
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        logging.warning(f"请求失败 {url}: {e}")
        return None


# ── 解析：帖子列表 ─────────────────────────────────────────────────────────────

def parse_thread_row(tr) -> Optional[dict]:
    """从帖子列表的 <tr> 中解析一条帖子摘要。"""
    tds = tr.find_all("td", recursive=False)
    if len(tds) < 3:
        return None

    # 标题 & tid
    link = tds[0].find("a", href=re.compile(r"content/.*tid=\d+"))
    if not link:
        return None
    tid_m = re.search(r"tid=(\d+)", link["href"])
    if not tid_m:
        return None
    tid = int(tid_m.group(1))
    title = link.get_text(strip=True)

    # 作者 & 发帖日期（第二列格式："用户名\n日期"）
    author_link = tds[1].find("a")
    author = author_link.get_text(strip=True) if author_link else ""
    raw_date = tds[1].get_text(" ", strip=True).replace(author, "").strip()

    # 回复数 / 阅读数（第三列格式："N / M"）
    rc_text = tds[2].get_text(strip=True)
    rc_parts = re.findall(r"\d+", rc_text)
    replies = int(rc_parts[0]) if len(rc_parts) > 0 else 0
    views   = int(rc_parts[1]) if len(rc_parts) > 1 else 0

    # 最后回复（第四列，可能不存在）
    last_reply = tds[3].get_text(" ", strip=True) if len(tds) > 3 else ""

    return {
        "tid":          tid,
        "title":        title,
        "author":       author,
        "created_date": raw_date,
        "replies":      replies,
        "views":        views,
        "last_reply":   last_reply,
    }


def crawl_board_threads(
    sess: requests.Session,
    bid: int,
    delay: float,
) -> tuple[list[dict], bool]:
    """
    爬取某板块所有帖子的摘要列表。
    返回 (threads_list, login_required)。
    """
    threads: list[dict] = []
    page = 1

    while True:
        url = f"{BASE_URL}/main/?bid={bid}&p={page}"
        soup = fetch(sess, url, delay)
        if soup is None:
            break

        # 检查是否需要登录
        if "后才能查看本版面" in soup.get_text():
            logging.warning(f"[bid={bid}] 需要登录，跳过")
            return [], True

        # 解析帖子行（跳过表头 tr）
        page_threads: list[dict] = []
        for tr in soup.select("table tr"):
            t = parse_thread_row(tr)
            if t:
                page_threads.append(t)

        if not page_threads:
            break
        threads.extend(page_threads)
        logging.info(f"  [bid={bid}] 第{page}页 → {len(page_threads)} 条")

        # 下一页
        if soup.find("a", string="下一页"):
            page += 1
        else:
            break

    return threads, False


# ── 解析：帖子正文 ─────────────────────────────────────────────────────────────

def parse_post_floor(tr) -> Optional[dict]:
    """从 <tr class="floor"> 中解析一楼的内容。"""
    floor_id = tr.get("id", "").strip()
    if not floor_id.isdigit():
        return None
    floor = int(floor_id)

    author = ""
    ab = tr.select_one(".authorbig")
    if ab:
        author = ab.get_text(strip=True)

    post_time = ""
    fi = tr.select_one(".floorinfo")
    if fi:
        # 去掉楼层标记（楼主/N楼），只保留时间
        raw = fi.get_text(" ", strip=True)
        time_m = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", raw)
        post_time = time_m.group(0) if time_m else raw

    content = ""
    tb = tr.select_one(".textblock")
    if tb:
        # 移除引用块（lzltable），避免重复内容
        for lzl in tb.select(".lzltable"):
            lzl.decompose()
        content = tb.get_text("\n", strip=True)

    return {
        "floor":     floor,
        "author":    author,
        "post_time": post_time,
        "content":   content,
    }


def crawl_thread_content(
    sess: requests.Session,
    tid: int,
    bid: int,
    delay: float,
) -> list[dict]:
    """爬取某帖子所有楼层的正文。"""
    posts: list[dict] = []
    page = 1

    while True:
        url = f"{BASE_URL}/content/?bid={bid}&tid={tid}&p={page}"
        soup = fetch(sess, url, delay)
        if soup is None:
            break

        page_posts: list[dict] = []
        for tr in soup.select("tr.floor"):
            p = parse_post_floor(tr)
            if p:
                page_posts.append(p)

        if not page_posts:
            break
        posts.extend(page_posts)

        if soup.find("a", string="下一页"):
            page += 1
        else:
            break

    return posts


# ── 主流程 ─────────────────────────────────────────────────────────────────────

def run(
    bids: list[int],
    db: sqlite3.Connection,
    sess: requests.Session,
    delay: float,
    crawl_content: bool,
    skip_crawled: bool,
) -> None:
    for bid in bids:
        board_name = BOARDS.get(bid, f"bid_{bid}")
        logging.info(f"═══ 板块 [{bid}] {board_name} ═══")

        # 爬取帖子列表
        threads, login_required = crawl_board_threads(sess, bid, delay)
        if login_required:
            db.execute(
                "INSERT OR REPLACE INTO boards (bid, name, total_topics) VALUES (?,?,?)",
                (bid, board_name, -1),
            )
            db.commit()
            continue

        logging.info(f"  共 {len(threads)} 条帖子")

        # 写入 boards
        db.execute(
            "INSERT OR REPLACE INTO boards (bid, name, total_topics) VALUES (?,?,?)",
            (bid, board_name, len(threads)),
        )

        # 写入 threads
        for t in threads:
            db.execute(
                """INSERT OR IGNORE INTO threads
                   (tid, bid, title, author, created_date, replies, views, last_reply)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    t["tid"], bid, t["title"], t["author"],
                    t["created_date"], t["replies"], t["views"], t["last_reply"],
                ),
            )
        db.commit()

        if not crawl_content:
            continue

        # 逐帖爬取正文
        for t in threads:
            tid = t["tid"]

            # 断点续爬：已完成的跳过
            if skip_crawled:
                row = db.execute(
                    "SELECT content_crawled FROM threads WHERE tid=?", (tid,)
                ).fetchone()
                if row and row[0] == 1:
                    logging.debug(f"  跳过已爬取帖子 tid={tid}")
                    continue

            posts = crawl_thread_content(sess, tid, bid, delay)
            for p in posts:
                db.execute(
                    """INSERT OR IGNORE INTO posts
                       (tid, bid, floor, author, post_time, content)
                       VALUES (?,?,?,?,?,?)""",
                    (tid, bid, p["floor"], p["author"], p["post_time"], p["content"]),
                )
            db.execute(
                "UPDATE threads SET content_crawled=1 WHERE tid=?", (tid,)
            )
            db.commit()
            logging.info(f"  tid={tid} 《{t['title'][:30]}》 → {len(posts)} 楼")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CAPUBBS 批量爬取脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--bids", nargs="+", type=int, default=list(BOARDS.keys()),
        help="要爬取的板块 bid 列表，默认全部",
    )
    parser.add_argument(
        "--phpsessid", default=None,
        help="登录 Cookie 的 PHPSESSID 值",
    )
    parser.add_argument(
        "--token", default=None,
        help="登录 Cookie 的 token 值",
    )
    parser.add_argument(
        "--content", action="store_true",
        help="是否同时爬取帖子正文（默认只爬列表）",
    )
    parser.add_argument(
        "--db", type=Path, default=DEFAULT_DB,
        help=f"SQLite 数据库路径（默认 {DEFAULT_DB}）",
    )
    parser.add_argument(
        "--delay", type=float, default=DEFAULT_DELAY,
        help=f"请求间隔秒数（默认 {DEFAULT_DELAY}s，请勿过小）",
    )
    parser.add_argument(
        "--no-skip", action="store_true",
        help="禁用断点续爬，强制重新爬取所有帖子",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="输出 DEBUG 级别日志",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    conn = init_db(args.db)
    sess = make_session(args.phpsessid, args.token)

    logging.info(f"数据库: {args.db}")
    logging.info(f"板块: {args.bids}")
    logging.info(f"爬取正文: {args.content}")
    logging.info(f"请求间隔: {args.delay}s")

    try:
        run(
            bids=args.bids,
            db=conn,
            sess=sess,
            delay=args.delay,
            crawl_content=args.content,
            skip_crawled=not args.no_skip,
        )
    except KeyboardInterrupt:
        logging.info("用户中断，已保存当前进度")
    finally:
        conn.close()

    logging.info("完成")


if __name__ == "__main__":
    main()
