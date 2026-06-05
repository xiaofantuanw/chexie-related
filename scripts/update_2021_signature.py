#!/usr/bin/env python3
"""Live updater for the 2021实践团 chexie signature.

Passwords are read interactively with getpass and are never printed or saved.
Stage 1 (prepare) logs in, posts the full signature HTML to the signature
repository thread, and saves the resulting loader locally.
Stage 2 (apply) logs in again and updates sig2 to that saved loader.
Stage 3 (edit) logs in again and edits the already-posted source floor.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE = "https://chexie.net"
BBS = f"{BASE}/bbs"
TARGET_ACCOUNT = "2021实践团"
REPO_BID = 4
REPO_TID = 19989

ROOT = Path(__file__).resolve().parent.parent
DRAFT_PATH = ROOT / "data" / "2021_practice_signature_draft.html"
STATE_PATH = ROOT / "data" / "2021_practice_signature_live_state.json"
SNAPSHOT_DIR = ROOT / "data" / "inspect_chexie"


@dataclass(frozen=True)
class SourceFloor:
    bid: int
    tid: int
    pid: int

    @property
    def api_path(self) -> str:
        return f"/api/bbs/content/floor/?bid={self.bid}&tid={self.tid}&pid={self.pid}"

    @property
    def api_url(self) -> str:
        return f"{BASE}{self.api_path}"


def make_session() -> requests.Session:
    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Referer": f"{BBS}/index/",
        }
    )
    return sess


def login(sess: requests.Session, username: str) -> None:
    password = getpass.getpass(f"Password for {username}: ")
    password1 = hashlib.md5(password.encode("utf-8")).hexdigest()
    password = ""
    resp = sess.post(
        f"{BBS}/login/action.php",
        data={"username": username, "password1": password1},
        timeout=20,
    )
    resp.raise_for_status()
    text = resp.text.strip()
    if text and text not in {"0", "success", "成功"}:
        print(f"login response: {text}")
    assert_logged_in_as(sess, username)


def assert_logged_in_as(sess: requests.Session, username: str) -> None:
    resp = sess.get(f"{BBS}/content/?bid={REPO_BID}&tid={REPO_TID}&p=1", timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    userinfo = soup.select_one(".userinfo")
    text = userinfo.get_text(" ", strip=True) if userinfo else soup.get_text(" ", strip=True)
    if username not in text:
        raise RuntimeError(f"Logged-in account is not {username}; aborting.")
    print(f"confirmed login account: {username}")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value)


def compact_html(html: str) -> str:
    """Keep the source floor on one line so CAPUBBS does not render source newlines."""
    return re.sub(r">\s+<", "><", html.strip())


def read_draft() -> str:
    html = compact_html(DRAFT_PATH.read_text(encoding="utf-8"))
    if TARGET_ACCOUNT not in html or "我们的山楂树之恋" not in html:
        raise RuntimeError(f"Draft does not look like the intended {TARGET_ACCOUNT} signature.")
    return html


def get_thread_max_page(sess: requests.Session) -> int:
    resp = sess.get(f"{BBS}/content/?bid={REPO_BID}&tid={REPO_TID}&p=1", timeout=20)
    resp.raise_for_status()
    pages = [1]
    for value in re.findall(r"[?&]p=(\d+)&bid=4&tid=19989|bid=4&tid=19989&p=(\d+)", resp.text):
        for item in value:
            if item:
                pages.append(int(item))
    for option in BeautifulSoup(resp.text, "html.parser").select("select option[value]"):
        raw = option.get("value", "")
        if raw.isdigit():
            pages.append(int(raw))
    return max(pages)


def post_source_floor(sess: requests.Session, html: str) -> None:
    token = sess.cookies.get("token")
    if not token:
        raise RuntimeError("Missing login token cookie; cannot post.")
    resp = sess.post(
        f"{BBS}/post/",
        data={
            "bid": str(REPO_BID),
            "tid": str(REPO_TID),
            "token": token,
            "title": "Re: 如何像回帖一样自由的编辑签名档【更新若干提醒】",
            "text": encode_post_html(html),
            "sig": "0",
            "attachs": "",
        },
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.text.strip()
    if result != "0":
        raise RuntimeError(f"Post failed; server returned: {result[:200]}")


def encode_post_html(html: str) -> str:
    return html.replace("&", "&amp;")


def find_posted_floor(sess: requests.Session, html: str, start_page: int) -> SourceFloor:
    marker_text = normalize_text(BeautifulSoup(html, "html.parser").get_text("", strip=True))
    pages = list(range(max(1, start_page - 1), start_page + 4))
    candidates: list[tuple[int, int]] = []

    for page in pages:
        resp = sess.get(f"{BBS}/content/?bid={REPO_BID}&tid={REPO_TID}&p={page}", timeout=20)
        if resp.status_code >= 400:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        for floor in soup.select("tr.floor[id]"):
            author = floor.select_one("a.authorbig")
            if not author or author.get_text(strip=True) != TARGET_ACCOUNT:
                continue
            textblock = floor.select_one(".textblock")
            if not textblock:
                continue
            floor_text = normalize_text(textblock.get_text("", strip=True))
            if marker_text and marker_text in floor_text:
                candidates.append((page, int(floor["id"])))

    if not candidates:
        raise RuntimeError("Posted source floor was not found; sig2 was not changed.")
    page, pid = candidates[-1]
    print(f"source floor found: page={page}, pid={pid}")
    return SourceFloor(REPO_BID, REPO_TID, pid)


def make_loader(source: SourceFloor) -> str:
    path = source.api_path
    return (
        f'<script>$.get("{path}",function(data){{sign=data+"<br><br>";'
        f'$(".sig").each(function(){{if($(this).html().search("bid={source.bid}&tid={source.tid}&pid={source.pid}")!=-1)'
        f'{{$(this).html(sign);}}}});}});</script>加载签名档中...<br><br><br>'
    )


def save_state(source: SourceFloor, loader: str) -> None:
    STATE_PATH.write_text(
        json.dumps(
            {
                "account": TARGET_ACCOUNT,
                "bid": source.bid,
                "tid": source.tid,
                "pid": source.pid,
                "api_url": source.api_url,
                "loader": loader,
                "created_at": int(time.time()),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"state saved: {STATE_PATH}")


def load_state() -> tuple[SourceFloor, str]:
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if data.get("account") != TARGET_ACCOUNT:
        raise RuntimeError("State file is not for the target account.")
    source = SourceFloor(int(data["bid"]), int(data["tid"]), int(data["pid"]))
    loader = str(data["loader"])
    if f"pid={source.pid}" not in loader:
        raise RuntimeError("State loader does not match state pid.")
    return source, loader


def extract_edit_form(soup: BeautifulSoup) -> dict[str, str]:
    form = soup.find("form")
    if not form:
        raise RuntimeError("Edit-user form not found.")

    data: dict[str, str] = {}
    for field in form.find_all(["input", "textarea", "select"]):
        name = field.get("name")
        if not name:
            continue
        if field.name == "textarea":
            data[name] = field.decode_contents() or ""
        elif field.name == "select":
            selected = field.find("option", selected=True)
            data[name] = selected.get("value", "") if selected else ""
        elif field.get("type") == "radio":
            if field.has_attr("checked"):
                data[name] = field.get("value", "")
        elif field.get("type") not in {"file", "submit", "button"}:
            data[name] = field.get("value", "")

    html = str(soup)
    icon_match = re.search(r'var\s+iconpath\s*=\s*"([^"]+)"', html)
    if icon_match:
        data["icon"] = icon_match.group(1)
    sex_match = re.search(r"select\((\d+)\);\s*function\s+select", html)
    if sex_match:
        sexes = ["请选择", "男", "女"]
        data["sex"] = sexes[int(sex_match.group(1))]

    for sig in ["sig1", "sig2", "sig3"]:
        data.setdefault(sig, "")
        data.setdefault(f"{sig}_type", "html" if data[sig].lstrip().startswith("<") else "raw")
    for name in ["sex", "icon", "qq", "email", "place", "hobby", "intro"]:
        data.setdefault(name, "")

    if data["sex"] not in {"请选择", "男", "女"} or not data["icon"]:
        raise RuntimeError("Could not safely preserve sex/icon fields from edit page.")
    return data


def fetch_edit_form(sess: requests.Session) -> dict[str, str]:
    resp = sess.get(f"{BBS}/edituser/", timeout=20)
    resp.raise_for_status()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = SNAPSHOT_DIR / "live_edituser_2021_before.html"
    snapshot.write_text(resp.text, encoding="utf-8")

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    if TARGET_ACCOUNT not in text:
        raise RuntimeError(f"Edit page is not for {TARGET_ACCOUNT}; aborting.")
    print(f"saved pre-apply edit page snapshot: {snapshot}")
    return extract_edit_form(soup)


def apply_sig2(sess: requests.Session, loader: str) -> None:
    data = fetch_edit_form(sess)
    old_sig2_len = len(data.get("sig2", ""))
    data["sig2"] = loader
    data["sig2_type"] = "html"

    resp = sess.post(f"{BBS}/edituser/action.php", data=data, timeout=30)
    resp.raise_for_status()
    text = resp.text.strip()
    print(f"edit response: {text[:200] if text else '<empty>'}")

    verify = sess.get(f"{BBS}/edituser/", timeout=20)
    verify.raise_for_status()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = SNAPSHOT_DIR / "live_edituser_2021_after.html"
    snapshot.write_text(verify.text, encoding="utf-8")
    if loader not in verify.text:
        raise RuntimeError("sig2 loader not found after update; please inspect the saved snapshot.")
    print(f"sig2 updated; old length={old_sig2_len}, new length={len(loader)}")
    print(f"saved post-apply edit page snapshot: {snapshot}")


def extract_generic_form(soup: BeautifulSoup) -> tuple[BeautifulSoup, dict[str, str]]:
    form = soup.find("form")
    if not form:
        raise RuntimeError("Edit-pid form not found.")

    data: dict[str, str] = {}
    for field in form.find_all(["input", "textarea", "select"]):
        name = field.get("name")
        if not name:
            continue
        if field.name == "textarea":
            data[name] = field.decode_contents() or ""
        elif field.name == "select":
            selected = field.find("option", selected=True)
            data[name] = selected.get("value", "") if selected else field.get("value", "")
        elif field.get("type") == "radio":
            if field.has_attr("checked"):
                data[name] = field.get("value", "")
        elif field.get("type") not in {"file", "submit", "button"}:
            data[name] = field.get("value", "")
    return form, data


def choose_text_field(form: BeautifulSoup, data: dict[str, str]) -> str:
    preferred = ["text", "content", "msg", "message"]
    for name in preferred:
        if name in data:
            return name
    textarea_names = [tag.get("name") for tag in form.find_all("textarea") if tag.get("name")]
    if len(textarea_names) == 1:
        return str(textarea_names[0])
    raise RuntimeError(f"Could not identify edit-pid text field; found textareas={textarea_names}")


def edit_source_floor(sess: requests.Session, source: SourceFloor, html: str) -> None:
    edit_url = f"{BBS}/editpid/?bid={source.bid}&tid={source.tid}&pid={source.pid}"
    resp = sess.get(edit_url, timeout=20)
    resp.raise_for_status()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    before_snapshot = SNAPSHOT_DIR / f"live_editpid_2021_before_pid_{source.pid}.html"
    before_snapshot.write_text(resp.text, encoding="utf-8")
    print(f"saved pre-edit source-floor snapshot: {before_snapshot}")

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    if "登录" in page_text and TARGET_ACCOUNT not in page_text:
        raise RuntimeError("Edit-pid page appears to require login; aborting.")
    form, data = extract_generic_form(soup)
    text_field = choose_text_field(form, data)
    data[text_field] = encode_post_html(html)
    data.setdefault("bid", str(source.bid))
    data.setdefault("tid", str(source.tid))
    data.setdefault("pid", str(source.pid))
    token = sess.cookies.get("token")
    if token:
        data.setdefault("token", token)

    action = form.get("action") or "action.php"
    action_url = urllib.parse.urljoin(resp.url, action)
    post = sess.post(action_url, data=data, timeout=30)
    post.raise_for_status()
    result = post.text.strip()
    print(f"edit-pid response: {result[:200] if result else '<empty>'}")

    verify = sess.get(source.api_url, timeout=20)
    verify.raise_for_status()
    after_snapshot = SNAPSHOT_DIR / f"live_editpid_2021_after_api_pid_{source.pid}.html"
    after_snapshot.write_text(verify.text, encoding="utf-8")
    if TARGET_ACCOUNT not in verify.text or "line-height:1.18" not in verify.text:
        raise RuntimeError("Source floor API does not show the tightened signature after edit.")
    print(f"source floor updated: {source.api_url}")
    print(f"saved post-edit source-floor API snapshot: {after_snapshot}")


def prepare() -> None:
    html = read_draft()
    sess = make_session()
    login(sess, TARGET_ACCOUNT)
    start_page = get_thread_max_page(sess)
    print(f"repository max page before posting: {start_page}")
    post_source_floor(sess, html)
    source = find_posted_floor(sess, html, start_page)
    loader = make_loader(source)
    save_state(source, loader)
    print("prepare complete; sig2 has not been changed.")
    print(f"source API: {source.api_url}")
    print(f"loader length: {len(loader)}")


def apply() -> None:
    source, loader = load_state()
    sess = make_session()
    login(sess, TARGET_ACCOUNT)
    check = sess.get(source.api_url, timeout=20)
    check.raise_for_status()
    if TARGET_ACCOUNT not in check.text or "我们的山楂树之恋" not in check.text:
        raise RuntimeError("Source floor API does not contain the expected signature content.")
    apply_sig2(sess, loader)
    print("apply complete.")


def edit() -> None:
    source, _ = load_state()
    html = read_draft()
    sess = make_session()
    login(sess, TARGET_ACCOUNT)
    edit_source_floor(sess, source, html)
    print("edit complete.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Live updater for 2021实践团 sig2.")
    parser.add_argument("stage", choices=["prepare", "apply", "edit"])
    args = parser.parse_args()

    try:
        if args.stage == "prepare":
            prepare()
        elif args.stage == "apply":
            apply()
        else:
            edit()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
