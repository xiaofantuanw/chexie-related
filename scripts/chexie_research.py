#!/usr/bin/env python3
"""Read-only research CLI for Chexie legacy CAPUBBS content."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chexie_agent.adapters import LegacyCapubbsAdapter
from chexie_agent.research import ForumResearchAgent
from chexie_agent.serialization import to_plain_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Chexie forum research helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    read_parser = subparsers.add_parser("read", help="Read one legacy thread.")
    read_parser.add_argument("thread", help="Thread URL or internal thread id.")
    read_parser.add_argument("--all-pages", action="store_true", help="Read and merge all available pages.")
    read_parser.add_argument("--max-pages", type=int, default=None, help="Limit page count when --all-pages is used.")
    read_parser.add_argument("--format", choices=("json", "markdown"), default="markdown")

    search_parser = subparsers.add_parser("search", help="Search legacy public forum content.")
    search_parser.add_argument("keyword", help="Search keyword. Use an empty string with --author for author-only search.")
    search_parser.add_argument("--author", default="", help="Restrict search to a post/thread author.")
    search_parser.add_argument("--type", choices=("thread", "post"), default="thread")
    search_parser.add_argument("--bid", type=int, default=-1)
    search_parser.add_argument("--starttime", default="2001-01-01")
    search_parser.add_argument("--endtime", default="2100-01-01")
    search_parser.add_argument("--format", choices=("json", "markdown"), default="markdown")

    args = parser.parse_args()
    agent = ForumResearchAgent(LegacyCapubbsAdapter())

    if args.command == "read":
        thread = agent.read_thread(args.thread, all_pages=args.all_pages, max_pages=args.max_pages)
        if args.format == "json":
            print(json.dumps(to_plain_data(thread), ensure_ascii=False, indent=2))
        else:
            print(agent.render_thread_markdown(thread), end="")
        return

    if args.command == "search":
        results = agent.search(
            args.keyword,
            author=args.author,
            search_type=args.type,
            bid=args.bid,
            starttime=args.starttime,
            endtime=args.endtime,
        )
        if args.format == "json":
            print(json.dumps(to_plain_data(results), ensure_ascii=False, indent=2))
        else:
            print(agent.render_search_markdown(results), end="")


if __name__ == "__main__":
    main()
