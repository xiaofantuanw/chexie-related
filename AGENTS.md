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
- `chexie_agent/`
- `docs/`
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
- Treat test.chexie.net actions as live forum actions too. Even when the test forum uses a database snapshot, writes can still affect an account and should require explicit authorization.

## Default Agent Workflow

Use this workflow when a new AI agent enters this project:

1. Read `AGENTS.md`, `README.md`, and the relevant skill `SKILL.md` before acting.
2. Check the worktree with `git status --short --branch`; do not overwrite unrelated user changes.
3. Inspect existing scripts and local notes before inventing a new approach. Prefer `rg` and existing helper scripts.
4. Classify the requested operation:
   - `read`: GET-only inspection or local file reading.
   - `draft`: local generation, preview, parsing, summarization, or proposed payload.
   - `write`: anything that changes Chexie/forum state, including posts, replies, uploads, profile edits, signature edits, messages, activity signups, or test-forum writes.
5. For `read`, use public pages first. Use authenticated reads only when needed and avoid printing sensitive account data.
6. For `draft`, save drafts/previews under ignored local directories such as `data/` unless the user asks for a tracked artifact.
7. For `write`, require exact user authorization for the target and payload. Confirm the logged-in account before writing.
8. After changes, run the narrowest useful verification. For Python scaffolding, `python3 -m pytest` or `python3 -m compileall` is usually enough.
9. Before committing, run the commands in the Development section and verify that `data`, `notes`, and `login_info` are not tracked.

## Forum Versions

Primary production target:

- Legacy CAPUBBS at `https://chexie.net/bbs/`.
- Server-rendered PHP pages.
- Thread URLs use `/bbs/content/?bid=BID&tid=TID&p=PAGE`.
- Existing scripts parse legacy HTML and call legacy PHP/API endpoints.

New forum test target:

- Test SPA at `https://test.chexie.net/bbs-new/`.
- As checked on 2026-06-06, it is a React/Vite frontend with routes such as `/threads/:threadId`, `/boards/:boardName`, `/users/:userSlug`, `/login`, `/register`, `/user-center`, `/search`, `/archive`, and `/stats`.
- Thread ids are represented as `BID-TID`, for example `28-150`.
- The announcement thread says the test database is current through 2026-05-31 and many images are unavailable in the test environment.
- The new frontend still calls many legacy endpoints, including `/api/api.php`, `/api/jiekouapi.php`, `/api/jiekoujson.php`, `/bbs/post`, `/bbs/editpid/action.php`, `/bbs/login/action.php`, `/bbs/content/test.php`, and `/bbs/attach`, plus newer activity endpoints.
- Keep production workflows on the legacy forum until the new forum is verified against production data and stable APIs.

Migration planning lives in:

- `docs/new_forum_migration_plan.md`
- `docs/account_agent_plan.md`

## Project Architecture

Use this organization for future account-agent work:

- `chexie_agent/domain.py`: forum-independent references and data models.
- `chexie_agent/safety.py`: action classification and live-write authorization gates.
- `chexie_agent/adapters/`: forum-specific adapters. Keep legacy CAPUBBS as the default; keep the new forum adapter probe-only until verified.
- `chexie_agent/workflows/`: user-facing workflows composed from adapters and safety checks.
- `chexie_agent/services/`: reusable parsing, storage, reminder, and summarization services.
- `scripts/`: thin CLI entry points, prototypes, and compatibility helpers.
- `.codex/skills/`: Codex-facing operational instructions.
- `docs/`: public, sanitized design and migration notes.

Do not move working legacy scripts into the package until the equivalent adapter method has tests or a clear manual verification path.

## Account-Agent Roadmap

Recommended first phase:

- Read public and authorized forum pages.
- Draft posts, replies, edits, signatures, and activity signup answers locally.
- Execute exact approved writes only after confirming account and target.
- Preserve local state for drafts, snapshots, and summaries without committing private data.

Later phases can add reminders, activity management, leader-report summarization, report comparison, and training-agent datasets. These are valuable but should come after reliable account-control primitives.

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
