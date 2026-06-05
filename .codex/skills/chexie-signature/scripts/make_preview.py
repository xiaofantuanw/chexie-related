#!/usr/bin/env python3
"""Wrap a chexie signature snippet into a standalone preview HTML file."""

from __future__ import annotations

import argparse
from pathlib import Path


TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{
      margin: 0;
      padding: 32px;
      background: #eef3f0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      color: #333;
    }}
    .post {{
      max-width: 860px;
      margin: 0 auto;
      background: #fff;
      border: 1px solid #d8e1dd;
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(31, 55, 47, 0.08);
      overflow: hidden;
    }}
    .content {{
      padding: 24px 28px;
      line-height: 1.7;
      min-height: 90px;
    }}
    .sigtip {{
      display: block;
      padding: 0 28px;
      color: #999;
      font-family: serif;
    }}
    .sig {{
      padding: 12px 28px 28px;
    }}
  </style>
</head>
<body>
  <div class="post">
    <div class="content">{body_text}</div>
    <span class="sigtip">--------</span>
    <div class="sig">
{snippet}
    </div>
  </div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snippet", type=Path)
    parser.add_argument("preview", type=Path)
    parser.add_argument("--title", default="Chexie signature preview")
    parser.add_argument("--body-text", default="这里是帖子正文预览。")
    args = parser.parse_args()

    snippet = args.snippet.read_text(encoding="utf-8").rstrip()
    indented = "\n".join("      " + line for line in snippet.splitlines())
    html = TEMPLATE.format(title=args.title, body_text=args.body_text, snippet=indented)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.preview.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
