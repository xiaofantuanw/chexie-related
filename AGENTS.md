# Agent Instructions

## Language

- 默认用简体中文回复。
- 代码、命令、日志、API、文件名、错误信息保持原文。
- 技术术语、产品名、框架名、协议名通常保留 English，除非中文表达更自然。

## Repository Scope

This repository contains Chexie/CAPUBBS automation helpers and local Codex skills.

Important tracked areas:

- `.codex/skills/chexie-signature/`
- `.codex/skills/chexie-image-upload/`
- `scripts/`

Important local-only areas:

- `login_info/`
- `data/`
- `notes/`

Do not commit local-only areas unless the user explicitly asks and confirms the privacy risk.

## Safety

- Never print, copy, commit, or hard-code Chexie usernames, passwords, cookies, session ids, or tokens.
- Prefer read-only inspection before any live forum action.
- Do not perform live Chexie uploads, posts, replies, profile edits, or signature edits unless the user explicitly authorizes that exact action.
- Keep generated public docs free of private account data and scraped personal details.

## Skills

- Use `chexie-signature` for CAPUBBS signature design, preview, inspection, dynamic source-floor signatures, and live signature update workflows.
- Use `chexie-image-upload` for forum image upload, image URL normalization, signature image references, and distinguishing external image links from forum-hosted images or attachments.

## Development

- Prefer small, maintainable changes.
- Use existing helper scripts before rewriting equivalent logic.
- Use `rg` for searching.
- Use `apply_patch` for manual file edits.
- Before committing, run:

```bash
git status --short --branch
git ls-files data notes login_info
```

The second command should normally print nothing.

