#!/usr/bin/env python3
"""Swap sig1 and sig2 for the 2021实践团 chexie account."""

from __future__ import annotations

import getpass
import hashlib
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE = "https://chexie.net/bbs"
TARGET_ACCOUNT = "2021实践团"
ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = ROOT / "data" / "inspect_chexie"


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


def login(sess: requests.Session) -> None:
    password = getpass.getpass(f"Password for {TARGET_ACCOUNT}: ")
    password1 = hashlib.md5(password.encode("utf-8")).hexdigest()
    password = ""
    resp = sess.post(
        f"{BASE}/login/action.php",
        data={"username": TARGET_ACCOUNT, "password1": password1},
        timeout=20,
    )
    resp.raise_for_status()

    check = sess.get(f"{BASE}/edituser/", timeout=20)
    check.raise_for_status()
    if TARGET_ACCOUNT not in check.get_text(" ", strip=True) if hasattr(check, "get_text") else TARGET_ACCOUNT not in check.text:
        raise RuntimeError(f"Logged-in account is not {TARGET_ACCOUNT}; aborting.")


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


def main() -> int:
    try:
        sess = make_session()
        login(sess)

        before = sess.get(f"{BASE}/edituser/", timeout=20)
        before.raise_for_status()
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        before_path = SNAPSHOT_DIR / "swap_2021_sig_before.html"
        before_path.write_text(before.text, encoding="utf-8")

        data = extract_edit_form(before.text)
        old_sig1_len = len(data["sig1"])
        old_sig2_len = len(data["sig2"])

        data["sig1"], data["sig2"] = data["sig2"], data["sig1"]
        data["sig1_type"], data["sig2_type"] = data["sig2_type"], data["sig1_type"]

        resp = sess.post(f"{BASE}/edituser/action.php", data=data, timeout=30)
        resp.raise_for_status()
        print(f"edit response: {resp.text.strip()[:200] if resp.text.strip() else '<empty>'}")

        after = sess.get(f"{BASE}/edituser/", timeout=20)
        after.raise_for_status()
        after_path = SNAPSHOT_DIR / "swap_2021_sig_after.html"
        after_path.write_text(after.text, encoding="utf-8")
        after_data = extract_edit_form(after.text)
        if after_data["sig1"] != data["sig1"] or after_data["sig2"] != data["sig2"]:
            raise RuntimeError("Swap verification failed; inspect saved snapshots.")

        print(f"swapped sig1/sig2 for {TARGET_ACCOUNT}")
        print(f"old sig1 length={old_sig1_len}, old sig2 length={old_sig2_len}")
        print(f"saved snapshots: {before_path}, {after_path}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
