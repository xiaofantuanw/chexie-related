#!/usr/bin/env python3
"""
Read-only inspector for chexie.net BBS profile signatures.

This script intentionally performs only HTTP GET requests. It saves raw HTML
snapshots and prints concise text/structure summaries for offline analysis.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://chexie.net/bbs"
ROOT = Path(__file__).resolve().parent.parent
LOGIN_INFO = ROOT / "login_info" / "login.md"
OUTPUT_DIR = ROOT / "data" / "inspect_chexie"
DEFAULT_NAMES = ["2026飞九团", "2025骑行团", "2026飞青团", "2025实践团", "晚风渡"]


def read_cookie_value(text: str, label: str) -> str | None:
    match = re.search(rf"\*\*{re.escape(label)}\*\*：([^\n]+)", text)
    return match.group(1).strip() if match else None


def read_login_info() -> tuple[str | None, str | None, str | None, str | None]:
    if not LOGIN_INFO.exists():
        return None, None, None, None
    text = LOGIN_INFO.read_text(encoding="utf-8")
    username = read_cookie_value(text, "用户名（ID）")
    password = read_cookie_value(text, "密码")
    phpsessid = read_cookie_value(text, "PHPSESSID")
    token = read_cookie_value(text, "token")
    return username, password, phpsessid, token


def make_session() -> requests.Session:
    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Referer": f"{BASE_URL}/index/",
        }
    )

    _, _, phpsessid, token = read_login_info()
    if phpsessid:
        sess.cookies.set("PHPSESSID", phpsessid, domain=".chexie.net", path="/")
    if token:
        sess.cookies.set("token", token, domain=".chexie.net", path="/")

    return sess


def login(sess: requests.Session) -> None:
    username, password, _, _ = read_login_info()
    if not username or not password:
        raise RuntimeError(f"Missing username/password in {LOGIN_INFO}")
    password1 = hashlib.md5(password.encode("utf-8")).hexdigest()
    resp = sess.post(
        f"{BASE_URL}/login/action.php",
        data={"username": username, "password1": password1},
        timeout=20,
    )
    resp.raise_for_status()
    print(f"login user: {username}")
    print(f"login response: {resp.text.strip()}")


def save_html(kind: str, name: str, html: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", name)
    path = OUTPUT_DIR / f"{kind}_{safe_name}.html"
    path.write_text(html, encoding="utf-8")
    return path


def visible_text(soup: BeautifulSoup, limit: int = 2500) -> str:
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return text[:limit]


def print_forms(soup: BeautifulSoup) -> None:
    forms = soup.find_all("form")
    print(f"forms: {len(forms)}")
    for idx, form in enumerate(forms, 1):
        action = form.get("action", "")
        method = form.get("method", "get")
        inputs = []
        for field in form.find_all(["input", "textarea", "select"]):
            inputs.append(
                {
                    "tag": field.name,
                    "name": field.get("name", ""),
                    "type": field.get("type", ""),
                    "id": field.get("id", ""),
                }
            )
        print(f"  form {idx}: method={method} action={action} fields={inputs}")


def inspect_profile(sess: requests.Session, name: str, delay: float) -> None:
    encoded = urllib.parse.quote(name)
    url = f"{BASE_URL}/user?name={encoded}"
    resp = sess.get(url, timeout=20)
    resp.raise_for_status()
    path = save_html("profile", name, resp.text)
    soup = BeautifulSoup(resp.text, "html.parser")

    print(f"\n===== profile: {name} =====")
    print(f"url: {resp.url}")
    print(f"saved: {path}")
    print_forms(soup)
    print("--- text ---")
    print(visible_text(soup))
    time.sleep(delay)


def inspect_search(sess: requests.Session, keyword: str, delay: float) -> None:
    url = f"{BASE_URL}/search?keyword={urllib.parse.quote(keyword)}"
    resp = sess.get(url, timeout=20)
    resp.raise_for_status()
    path = save_html("search", keyword, resp.text)
    soup = BeautifulSoup(resp.text, "html.parser")

    print(f"\n===== search: {keyword} =====")
    print(f"url: {resp.url}")
    print(f"saved: {path}")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        if "content" in href or keyword in text:
            links.append((text, urllib.parse.urljoin(resp.url, href)))
    for text, href in links[:20]:
        print(f"- {text}: {href}")
    print("--- text ---")
    print(visible_text(soup, 1800))
    time.sleep(delay)


def inspect_thread(sess: requests.Session, url: str, delay: float) -> None:
    resp = sess.get(url, timeout=20)
    resp.raise_for_status()
    name = re.sub(r"[^0-9A-Za-z_-]+", "_", urllib.parse.urlparse(resp.url).query) or "thread"
    path = save_html("thread", name, resp.text)
    soup = BeautifulSoup(resp.text, "html.parser")

    print(f"\n===== thread =====")
    print(f"url: {resp.url}")
    print(f"saved: {path}")
    print_forms(soup)
    for selector in [".signature", ".sign", ".sig", ".textblock", "tr.floor"]:
        matches = soup.select(selector)
        print(f"selector {selector!r}: {len(matches)}")
        for item in matches[:3]:
            print(item.get_text("\n", strip=True)[:1000])
            print("---")
    time.sleep(delay)


def inspect_floor_api(sess: requests.Session, bid: int, tid: int, pid: int, delay: float) -> None:
    url = f"https://chexie.net/api/bbs/content/floor/?bid={bid}&tid={tid}&pid={pid}"
    resp = sess.get(url, timeout=20)
    resp.raise_for_status()
    name = f"bid_{bid}_tid_{tid}_pid_{pid}"
    path = save_html("api_floor", name, resp.text)
    soup = BeautifulSoup(resp.text, "html.parser")

    print(f"\n===== api floor: {name} =====")
    print(f"url: {resp.url}")
    print(f"saved: {path}")
    print("--- text ---")
    print(visible_text(soup, 2500))
    print("--- html ---")
    print(resp.text[:3500])
    time.sleep(delay)


def inspect_get_url(sess: requests.Session, url: str, delay: float) -> None:
    resp = sess.get(url, timeout=20)
    parsed = urllib.parse.urlparse(resp.url)
    name = re.sub(r"[^0-9A-Za-z_-]+", "_", f"{parsed.path}_{parsed.query}") or "url"
    path = save_html("url", name, resp.text)
    soup = BeautifulSoup(resp.text, "html.parser")

    print(f"\n===== url =====")
    print(f"url: {resp.url}")
    print(f"status: {resp.status_code}")
    print(f"saved: {path}")
    if resp.status_code >= 400:
        print("--- text ---")
        print(visible_text(soup, 1000))
        time.sleep(delay)
        return
    print_forms(soup)
    print("--- links ---")
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = urllib.parse.urljoin(resp.url, a["href"])
        if text or any(key in href for key in ["user", "edit", "profile", "login", "logout", "setting"]):
            print(f"- {text}: {href}")
    print("--- text ---")
    print(visible_text(soup, 2200))
    time.sleep(delay)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only chexie.net BBS inspector")
    parser.add_argument("--names", nargs="*", default=DEFAULT_NAMES)
    parser.add_argument("--search", nargs="*", default=[])
    parser.add_argument("--thread-url", nargs="*", default=[])
    parser.add_argument(
        "--floor-api",
        nargs="*",
        default=[],
        help="Floor references as bid,tid,pid. Example: 4,19989,70",
    )
    parser.add_argument("--get-url", nargs="*", default=[])
    parser.add_argument("--login", action="store_true", help="Login using login_info/login.md before GET requests")
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    sess = make_session()
    if args.login:
        login(sess)
    for name in args.names:
        inspect_profile(sess, name, args.delay)
    for keyword in args.search:
        inspect_search(sess, keyword, args.delay)
    for url in args.thread_url:
        inspect_thread(sess, url, args.delay)
    for item in args.floor_api:
        bid_text, tid_text, pid_text = item.split(",", 2)
        inspect_floor_api(sess, int(bid_text), int(tid_text), int(pid_text), args.delay)
    for url in args.get_url:
        inspect_get_url(sess, url, args.delay)


if __name__ == "__main__":
    main()
