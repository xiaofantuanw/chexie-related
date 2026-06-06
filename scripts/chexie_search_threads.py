#!/usr/bin/env python3
"""Search public legacy CAPUBBS threads and print structured JSON.

This command is intentionally read-only. It submits the public search form and
does not use login credentials.
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
    parser = argparse.ArgumentParser(description="Search Chexie threads as structured JSON.")
    parser.add_argument("keyword", help="Search keyword.")
    parser.add_argument("--author", default="", help="Restrict search to a post/thread author.")
    parser.add_argument(
        "--type",
        choices=("thread", "post"),
        default="thread",
        help="Search thread titles or post bodies. Default: thread.",
    )
    parser.add_argument("--bid", type=int, default=-1, help="Restrict search to a board id. Default: -1, all boards.")
    parser.add_argument("--starttime", default="2001-01-01", help="Search start date. Default: 2001-01-01.")
    parser.add_argument("--endtime", default="2100-01-01", help="Search end date. Default: 2100-01-01.")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation. Default: 2.")
    args = parser.parse_args()

    adapter = LegacyCapubbsAdapter()
    results = adapter.search_threads(
        args.keyword,
        author=args.author,
        search_type=args.type,
        bid=args.bid,
        starttime=args.starttime,
        endtime=args.endtime,
    )
    print(json.dumps(to_plain_data(results), ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    main()
