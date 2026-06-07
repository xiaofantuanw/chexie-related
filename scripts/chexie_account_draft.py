#!/usr/bin/env python3
"""Create local-only Chexie account-agent drafts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chexie_agent.adapters import LegacyCapubbsAdapter
from chexie_agent.workflows import AccountAgentWorkflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Create local Chexie forum drafts without posting.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    reply_parser = subparsers.add_parser("reply", help="Draft a reply to a legacy CAPUBBS thread.")
    reply_parser.add_argument("thread", help="Thread URL or internal thread id.")
    reply_parser.add_argument("--text", help="Exact reply text.")
    reply_parser.add_argument("--text-file", type=Path, help="Read exact reply text from a UTF-8 file.")
    reply_parser.add_argument(
        "--drafts-dir",
        type=Path,
        default=ROOT / "data" / "drafts",
        help="Directory for local draft files. Default: data/drafts.",
    )
    reply_parser.add_argument(
        "--print-preview",
        action="store_true",
        help="Print the generated Markdown preview to stdout.",
    )

    args = parser.parse_args()

    if args.command == "reply":
        text = _resolve_text(args.text, args.text_file)
        workflow = AccountAgentWorkflow(LegacyCapubbsAdapter())
        draft = workflow.create_reply_draft(args.thread, text)
        json_path, markdown_path = workflow.save_reply_draft(draft, args.drafts_dir)
        print(f"Saved JSON draft: {json_path}")
        print(f"Saved Markdown preview: {markdown_path}")
        print("Status: local draft only; no forum post was submitted.")
        if args.print_preview:
            print()
            print(workflow.render_reply_draft_markdown(draft), end="")


def _resolve_text(text: str | None, text_file: Path | None) -> str:
    if text and text_file:
        raise SystemExit("Use either --text or --text-file, not both.")
    if text_file:
        value = text_file.read_text(encoding="utf-8")
    elif text is not None:
        value = text
    else:
        value = sys.stdin.read()

    if not value.strip():
        raise SystemExit("Reply text is empty.")
    return value


if __name__ == "__main__":
    main()
