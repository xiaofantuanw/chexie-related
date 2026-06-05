#!/usr/bin/env python3
"""
Log in interactively and export the current account's chexie signature slots.

This script does not print or persist passwords, cookies, tokens, or session ids.
It saves only sig1/sig2/sig3 HTML/text and type metadata for local editing.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://chexie.net/bbs"
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "data" / "inspect_chexie" / "own_signature_slots.json"


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
    return sess


def checked_radio_value(soup: BeautifulSoup, name: str) -> str:
    checked = soup.find("input", {"name": name, "checked": True})
    return checked.get("value", "") if checked else ""


def parse_account_name(soup: BeautifulSoup) -> str:
    text = soup.get_text("\n", strip=True)
    marker = "用户名："
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split("\n", 1)[0].strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export your own chexie signature slots after interactive login.")
    parser.add_argument("--username", help="chexie username. If omitted, prompt interactively.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    username = args.username or input("chexie username: ").strip()
    password = getpass.getpass("chexie password: ")

    sess = make_session()
    login_resp = sess.post(
        f"{BASE_URL}/login/action.php",
        data={"username": username, "password1": hashlib.md5(password.encode("utf-8")).hexdigest()},
        timeout=20,
    )
    login_resp.raise_for_status()

    edit_resp = sess.get(f"{BASE_URL}/edituser/", timeout=20)
    edit_resp.raise_for_status()
    soup = BeautifulSoup(edit_resp.text, "html.parser")
    account_name = parse_account_name(soup)

    slots = {}
    for slot in ("sig1", "sig2", "sig3"):
        textarea = soup.find("textarea", {"name": slot})
        slots[slot] = {
            "type": checked_radio_value(soup, f"{slot}_type"),
            "html": textarea.decode_contents() if textarea else "",
        }

    output = {
        "account_name": account_name,
        "slots": slots,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"saved: {args.output}")
    print(f"account_name: {account_name}")
    for slot, data in slots.items():
        print(f"{slot}: type={data['type'] or 'unknown'} bytes={len(data['html'].encode('utf-8'))}")


if __name__ == "__main__":
    main()
