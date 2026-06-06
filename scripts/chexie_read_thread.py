#!/usr/bin/env python3
"""Read a legacy CAPUBBS thread page and print structured JSON.

This command is intentionally read-only. It performs one GET request for one
thread page and does not use login credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chexie_agent.adapters import LegacyCapubbsAdapter
from chexie_agent.serialization import to_plain_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Read one Chexie thread page as structured JSON.")
    parser.add_argument("thread", help="Legacy thread URL, new thread id such as 28-150, or any URL containing bid/tid.")
    parser.add_argument("--page", "-p", type=int, default=1, help="Thread page to read. Default: 1.")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation. Default: 2.")
    args = parser.parse_args()

    adapter = LegacyCapubbsAdapter()
    thread = adapter.parse_thread_ref(args.thread)
    if thread is None:
        raise SystemExit(f"Cannot parse thread reference: {args.thread}")

    result = adapter.fetch_thread(thread, page=max(1, args.page))
    print(json.dumps(to_plain_data(result), ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    main()
