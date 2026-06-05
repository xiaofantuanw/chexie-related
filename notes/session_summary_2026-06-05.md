# Session Summary: Chexie Signature Workflow

Date: 2026-06-05

## Goal

Help understand and operate chexie.net CAPUBBS signatures, design a new signature for a group account, preview it locally, publish it through the forum source-floor method, and turn the learned workflow into a project-level Codex skill.

## Forum Signature Findings

- Chexie profile signature edit path: `/bbs/edituser/`.
- Signature slots: `sig1`, `sig2`, `sig3`; each has a type field: `raw` or `html`.
- Reply pages choose a signature with `sig=0/1/2/3`.
- Long or rich signatures are commonly implemented by:
  1. posting the full signature HTML in a normal forum floor;
  2. setting a short JavaScript loader in a profile signature slot;
  3. later editing the source floor to update the rendered signature.
- Loader pattern:

```html
<script>$.get("/api/bbs/content/floor/?bid=BID&tid=TID&pid=PID",function(data){sign=data+"<br><br>";$(".sig").each(function(){if($(this).html().search("bid=BID&tid=TID&pid=PID")!=-1){$(this).html(sign);}});});</script>加载签名档中...<br><br><br>
```

Important: `pid` is the actual source floor id used by the API, not necessarily the page-local display number.

## Signature Draft And Preview

Created and iterated:

- `data/2021_practice_signature_draft.html`
- `data/2021_practice_signature_preview.html`

Final draft characteristics:

- Centered layout.
- Slogan: `我们的山楂树之恋`.
- Route: `洛阳 - 鸣皋 - 栾川 - 淅川 - 丹江口 - 保康 - 松柏 - 红坪 - 木鱼 - 秭归 - 宜昌实践 - 贺家坪 - 长阳 - 五峰 - 宜昌`.
- Member roster in one column.
- Nickname updates:
  - `六姐` -> `六六`
  - `八哥` -> `小八`
  - `九妹` -> `九奶奶`
  - `与非` -> `与非/小满`
- Image URL reused from the reference signature:
  `https://ftp.bmp.ovh/imgs/2021/06/7ecf0a001d6f30c6.jpg`
- Later tightened line height and compacted the HTML to one line because CAPUBBS can render source newlines as extra `<br>`.

## Live Scripts Created

Created:

- `scripts/update_2021_signature.py`
  - stages: `prepare`, `apply`, `edit`
  - `prepare`: login, post source floor, save loader state
  - `apply`: update chosen profile signature slot to loader
  - `edit`: edit existing source floor content
- `scripts/swap_2021_sig1_sig2.py`
  - swaps `sig1` and `sig2`, including their type fields
- `scripts/restore_2021_sig1_loader.py`
  - restores `sig1` to the saved loader from state

Generated state:

- `data/2021_practice_signature_live_state.json`
  - records account, source `bid/tid/pid`, source API URL, and loader

Saved live-operation snapshots under:

- `data/inspect_chexie/`

## Live Operation Lessons

- Passwords should be entered interactively with `getpass.getpass()`, never pasted into chat or saved in generated files.
- Always confirm `/bbs/edituser/` belongs to the intended target account before writing.
- Preserve the full profile form when submitting `/bbs/edituser/action.php`; only change intended signature fields.
- When parsing `<textarea>` containing loader HTML, use `field.decode_contents()`, not `.text`.
  - `.text` strips embedded `<script>` content and can leave only visible text like `加载签名档中...`.
- When posting the source floor for a signature slot, use the same `sig` number as the slot being replaced.
  - Do not default to `sig=0` unless the user explicitly wants to post without a signature.
- For later style/content tweaks, edit the existing source floor instead of reposting and changing the loader.

## Project-Level Skill

Created/updated project-only skill:

- `.codex/skills/chexie-signature/SKILL.md`
- `.codex/skills/chexie-signature/references/examples.md`
- `.codex/skills/chexie-signature/references/live-update.md`
- `.codex/skills/chexie-signature/scripts/make_preview.py`
- `.codex/skills/chexie-signature/agents/openai.yaml`

Skill scope:

- Generate signature HTML drafts.
- Create local preview pages.
- Inspect existing signatures and source floors.
- Design personal signatures and group-account signatures.
- Publish long signatures via source-floor loader after explicit authorization.
- Update user-selected `sig1/sig2/sig3` slots.
- Edit source floors for later revisions.

Security rule added:

- The skill may mention that login can be required, but must never expose saved forum usernames, passwords, cookies, tokens, or session ids.

## Current Cautions

- The project has sensitive login material under `login_info/`; do not copy it into docs, skills, generated drafts, logs, or responses.
- Some scripts are account-specific prototypes. For future generic use, parameterize account name, slot number, draft path, repository `bid/tid`, and optional existing `pid`.
- The project directory is not currently behaving as a normal git repo from this environment, so use filesystem checks rather than relying on `git status`.

