#!/usr/bin/env python3
"""Set 小饭团w sig2 to the saved 2021实践团 sig1 source-floor loader."""

from __future__ import annotations

import getpass
import hashlib
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE = "https://chexie.net/bbs"
TARGET_ACCOUNT = "小饭团w"
SOURCE_ACCOUNT = "2021实践团"
ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "data" / "2021_practice_signature_live_state.json"
LOGIN_INFO = ROOT / "login_info" / "login.md"
SNAPSHOT_DIR = ROOT / "data" / "inspect_chexie"


def read_login_value(text: str, label: str) -> str | None:
    match = re.search(rf"\*\*{re.escape(label)}\*\*：([^\n]+)", text)
    return match.group(1).strip() if match else None


def read_local_password(username: str) -> str | None:
    if not LOGIN_INFO.exists():
        return None
    text = LOGIN_INFO.read_text(encoding="utf-8")
    stored_username = read_login_value(text, "用户名（ID）")
    if stored_username != username:
        return None
    return read_login_value(text, "密码")


def make_session() -> requests.Session:
    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Referer": f"{BASE}/index/",
        }
    )
    return sess


def login(sess: requests.Session, username: str) -> None:
    password = read_local_password(username)
    if password is None:
        password = getpass.getpass(f"Password for {username}: ")
    password1 = hashlib.md5(password.encode("utf-8")).hexdigest()
    password = ""
    resp = sess.post(
        f"{BASE}/login/action.php",
        data={"username": username, "password1": password1},
        timeout=20,
    )
    resp.raise_for_status()

    check = sess.get(f"{BASE}/edituser/", timeout=20)
    check.raise_for_status()
    soup = BeautifulSoup(check.text, "html.parser")
    if username not in soup.get_text(" ", strip=True):
        raise RuntimeError(f"Logged-in account is not {username}; aborting.")


def extract_edit_form(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        raise RuntimeError("Edit-user form not found.")
    if TARGET_ACCOUNT not in soup.get_text(" ", strip=True):
        raise RuntimeError(f"Edit page is not for {TARGET_ACCOUNT}; aborting.")

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

    icon_match = re.search(r'var\s+iconpath\s*=\s*"([^"]+)"', html)
    if icon_match:
        data["icon"] = icon_match.group(1)

    sex_match = re.search(r"select\((\d+)\);\s*function\s+select", html)
    if sex_match:
        data["sex"] = ["请选择", "男", "女"][int(sex_match.group(1))]

    for sig in ["sig1", "sig2", "sig3"]:
        data.setdefault(sig, "")
        data.setdefault(f"{sig}_type", "html" if data[sig].lstrip().startswith("<") else "raw")
    for name in ["sex", "icon", "qq", "email", "place", "hobby", "intro"]:
        data.setdefault(name, "")

    if data["sex"] not in {"请选择", "男", "女"} or not data["icon"]:
        raise RuntimeError("Could not safely preserve sex/icon fields from edit page.")
    return data


def load_2021_sig1_loader() -> str:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    loader = state.get("loader", "")
    if state.get("account") != SOURCE_ACCOUNT:
        raise RuntimeError("State file is not for 2021实践团.")
    if not isinstance(loader, str) or "<script>" not in loader:
        raise RuntimeError("State file does not contain a valid HTML loader.")
    bid = state.get("bid")
    tid = state.get("tid")
    pid = state.get("pid")
    expected = f"bid={bid}&tid={tid}&pid={pid}"
    if expected not in loader:
        raise RuntimeError("State loader does not match state source floor.")
    return loader


def main() -> int:
    try:
        loader = load_2021_sig1_loader()

        sess = make_session()
        login(sess, TARGET_ACCOUNT)

        before = sess.get(f"{BASE}/edituser/", timeout=20)
        before.raise_for_status()
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        before_path = SNAPSHOT_DIR / "link_xiaofantuanw_sig2_before.html"
        before_path.write_text(before.text, encoding="utf-8")

        data = extract_edit_form(before.text)
        old_sig2_len = len(data["sig2"])
        data["sig2"] = loader
        data["sig2_type"] = "html"

        resp = sess.post(f"{BASE}/edituser/action.php", data=data, timeout=30)
        resp.raise_for_status()
        print(f"edit response: {resp.text.strip()[:200] if resp.text.strip() else '<empty>'}")

        after = sess.get(f"{BASE}/edituser/", timeout=20)
        after.raise_for_status()
        after_path = SNAPSHOT_DIR / "link_xiaofantuanw_sig2_after.html"
        after_path.write_text(after.text, encoding="utf-8")
        after_data = extract_edit_form(after.text)
        if loader not in after.text or after_data["sig2_type"] != "html":
            raise RuntimeError("Verification failed; inspect saved snapshots.")

        print(f"linked {TARGET_ACCOUNT} sig2 to {SOURCE_ACCOUNT} sig1 source floor")
        print(f"old sig2 length={old_sig2_len}, new sig2 length={len(loader)}")
        print(f"saved snapshots: {before_path}, {after_path}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
