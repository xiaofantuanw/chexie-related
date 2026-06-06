# Account Agent Plan

## Preferred First Phase

Build a conservative account agent that can:

- read public boards and threads;
- read authenticated pages after explicit authorization;
- draft posts and replies locally;
- submit a post or reply only after exact user approval;
- inspect activity posts and help prepare signup information;
- submit an activity signup only after exact user approval;
- save sanitized local summaries and structured data for later use.

The first phase should not attempt to become a general association knowledge system. It should make account operations reliable, auditable, and reversible where possible.

## Capability Stages

Stage 0: foundation

- Shared domain models for boards, threads, floors, users, signatures, attachments, and activity signup forms.
- Forum adapters for legacy CAPUBBS and future new forum.
- Safety layer that distinguishes read, draft, and live write actions.
- Local-only config and state under ignored directories.

Initial read-only thread parsing is implemented through:

```bash
python3 scripts/chexie_research.py read "https://chexie.net/bbs/content/?bid=28&tid=150&p=1"
python3 scripts/chexie_research.py read "PASTE_THREAD_URL_HERE" --all-pages --format markdown
python3 scripts/chexie_research.py search "暑期" --author "蓝" --type post
python3 scripts/chexie_read_thread.py "https://chexie.net/bbs/content/?bid=28&tid=150&p=1"
python3 scripts/chexie_search_threads.py "新版论坛"
python3 scripts/chexie_search_threads.py "暑期" --author "蓝" --type post
```

`chexie_research.py` is the preferred first-stage read-only agent entry point. It wraps the adapter in `ForumResearchAgent`, supports all-page thread reads, and renders user-facing Markdown that refers to content by title, board, author, time, and floor number rather than raw `bid/tid/pid` ids. The lower-level scripts remain useful for JSON-only inspection.

These should remain public read-only workflows unless an explicitly authorized authenticated read mode is added later.

Stage 1: account control

- Login through local scripts or terminal input, never chat.
- Session validation that confirms the current account before writes.
- Read threads, profiles, messages, own signature slots, and own drafts.
- Draft post/reply/edit content with a preview.
- Execute exact approved writes: post, reply, edit own floor, upload image, update signature.

Stage 2: activity helper

- Detect activity posts and signup fields.
- Extract signup requirements into structured data.
- Prepare a signup answer draft.
- Submit signup only with explicit user approval.
- Export or summarize signup data when the account has permission.

Stage 3: reminders and monitoring

- Track watched threads and expected update windows.
- Produce reminders for summer trip logs, self-introductions, training updates, and unfilled reserved floors.
- Keep notification state local and avoid posting reminders automatically unless explicitly authorized.

Stage 4: knowledge workflows

- Summarize leader reports.
- Compare leader reports across teams and years.
- Extract reusable leader training guidance.
- Build retrieval datasets from public or explicitly authorized materials.

Stage 5: operational dashboards

- Aggregate activity participation, medical/support roles, training attendance, and retention signals.
- Keep manual verification in the loop because historical data can be incomplete or inconsistent.

## Project Architecture

Recommended module boundaries:

- `chexie_agent.domain`: forum-independent data types.
- `chexie_agent.safety`: permission and action classification.
- `chexie_agent.adapters`: forum-specific clients.
- `chexie_agent.workflows`: user-facing workflows composed from adapters.
- `chexie_agent.services`: reusable parsing, summarization, storage, and notification services.
- `scripts`: thin CLI entry points and legacy prototypes.
- `.codex/skills`: Codex-facing instructions and reusable skill workflows.
- `docs`: public, sanitized design notes and migration plans.
- `data`, `notes`, `login_info`: local-only state and private materials.

## Live Action Rule

Every operation should be classified before execution:

- `read`: GET-only inspection or local file read.
- `draft`: local transformation, preview, or proposed payload.
- `write`: anything that changes the forum, account, profile, signature, upload store, activity signup, or messages.

Write actions require an exact target and explicit approval. Examples:

- "Reply to `bid=4&tid=20131` with this exact text."
- "Update `sig1` for this account to this loader."
- "Upload this image to the editor image endpoint."
- "Submit this signup to this activity thread."

## Data Handling

- Never put credentials, cookies, tokens, or session ids into docs, logs, generated examples, or Git commits.
- Keep raw crawls and private summaries under ignored local directories.
- Redact private account names and sensitive personal data before publishing public notes.
- Prefer source links and structured references over copying large forum content into committed files.
- Treat `bid`, `tid`, `pid`, and `BID-TID` values as internal references. User-facing summaries should normally name帖子标题、版面、楼层、作者和时间；raw ids belong in JSON, commands, logs, and implementation details.
