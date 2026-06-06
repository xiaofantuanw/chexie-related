---
name: chexie-signature
description: Generate, preview, inspect, and optionally publish chexie.net CAPUBBS signature HTML. Use when Codex needs to inspect an existing user's signature, imitate a specified user's signature style, design/revise personal or group-account signatures, create local draft/preview files, post long signature HTML to a source floor, update a chosen sig1/sig2/sig3 slot, swap or restore signature slots, or use the chexie.net “use a forum floor as a dynamic signature source” pattern.
---

# Chexie Signature

## Purpose

Create maintainable chexie.net BBS signature HTML and a local preview page. Support two main modes:

- **Personal signature**: ride history, seasons, activity names, leaders, roles, times, quotes, links, jokes, and optional interactive/collapsible sections.
- **Group-account signature**: team name, slogan, official route, member roster, role nicknames, member links, image, and polished visual styling.

## First Steps

1. Clarify whether the user wants a personal signature or a group-account signature.
2. Clarify the target account and, for live changes, the exact signature slot: `sig1`, `sig2`, or `sig3`.
3. If the user asks for a numbered slot but inspection only reveals signatures rendered in posts, do not infer that a rendered signature is `sig1`, `sig2`, or `sig3`. Explain that post rendering only shows the signature selected for that post, summarize the variants found, and ask the user which variant/slot to use unless the exact edit-profile field can be read for the target account.
4. Gather current source material from the user or from chexie.net when requested/allowed: profile page, recent posts, existing signature HTML, relevant route/log/team-list posts, image URLs.
5. Produce files first, do not submit changes to chexie.net unless the user explicitly authorizes live modification.
6. Prefer two output files:
   - `*_signature_draft.html`: only the signature snippet intended for chexie.
   - `*_signature_preview.html`: standalone local preview page.
7. If the HTML is long or likely above practical signature limits, recommend the dynamic source-floor method.

Use `scripts/make_preview.py` to wrap a snippet into a local preview page.

## Default Signature Test Thread

For signature source floors, signature loader tests, and signature-related examples, use this thread by default after explicit authorization:

```text
https://chexie.net/bbs/content/?bid=4&tid=19989&p=1
```

This is the signature tutorial/repository thread. Do not use the image-upload test thread for signature source floors unless the user explicitly asks.

## Login And Credential Safety

Some inspection steps may require a logged-in chexie.net session. If credentials or cookies are stored locally in the project, treat them as secrets:

- Never copy usernames, passwords, cookies, tokens, or session ids into this skill, generated drafts, preview files, examples, logs, or user-facing responses.
- Do not ask the user to paste a password into chat. When a password is needed, write or adapt a local script and have the user run it so the password is entered in the terminal via hidden interactive input such as Python `getpass.getpass()`.
- Do not hard-code credentials in scripts. Use the project's existing credential-loading helper, or use an interactive local password prompt after the user authorizes login.
- Prefer read-only inspection first. Do not perform live signature edits, posts, replies, uploads, or account-setting changes unless the user explicitly authorizes that exact action.
- When summarizing findings, describe the account or signature by the user-provided target name only; omit the credential source and all secret values.
- If target-account signature inspection becomes blocked by login/session mismatch, CAPUBBS permissions, or unreliable post archaeology, stop trying to guess. Use or adapt `scripts/export_own_chexie_signatures.py` so the user can log in as the target account and export only the needed `sig1/sig2/sig3` HTML/types to local files. The helper must not print or save passwords, cookies, tokens, or session ids.

## Live Update Workflow

Use this only after explicit authorization for the target account and target slot.

1. Generate and preview the signature snippet locally.
2. Compact final HTML before posting, especially if it contains tags or scripts; source newlines may render as visible `<br>`.
3. Login with a local script using interactive password entry, such as `getpass.getpass()`, or an approved local secret loader. Do not ask for passwords in chat, and do not print or persist secrets.
4. Fetch `/bbs/edituser/` after login and confirm it belongs to the target account before any write.
5. Preserve all profile fields. When parsing `<textarea>` values, use raw inner HTML such as `decode_contents()`, not visible text, so `<script>...</script>` loaders are not stripped.
6. Post the full signature HTML to the configured signature repository thread as a normal reply.
7. When posting that source floor, set the reply `sig` parameter to the same slot number the user wants to replace, not `0`, unless the user explicitly asks to post without a signature.
8. Find the new source floor `pid`, build the loader, and update only the requested `sigN` field plus `sigN_type=html`.
9. Verify by refetching `/bbs/edituser/` and the source floor API. Save before/after snapshots under `data/inspect_chexie/`.
10. For later visual edits, edit the source floor content instead of reposting or changing the loader.

For implementation details and reusable script structure, read `references/live-update.md`.

## Inspect Existing Signatures

When the user says an account already has a signature history, asks to “施工一下”, or asks to imitate another user:

1. Open the target user's profile page: `/bbs/user/?name=USERNAME`.
2. Use the profile's recent posts/replies to open representative thread pages. Prefer:
   - recent replies, because they show the current default signature;
   - self-introduction or long-running archive posts, because they often show older signature variants;
   - the signature tutorial/storage thread if the signature is a dynamic loader.
3. In each thread page, inspect the target user's `tr.floor`, then extract:
   - `.sig` text for visible content;
   - `.sig` HTML for colors, fonts, images, scripts, and loader references.
4. Classify the signature:
   - **Static HTML**: `.sig` directly contains `<font>`, `<br>`, `<img>`, `div/span`, etc.
   - **Dynamic source-floor loader**: `.sig` contains `$.get("/api/bbs/content/floor/?bid=...&tid=...&pid=...")`.
   - **Mixed or multiple variants**: different posts show different `sig1/sig2/sig3`; collect the variants and ask which to modify if unclear.
5. For dynamic signatures, request or fetch the source floor API:

```text
https://chexie.net/api/bbs/content/floor/?bid=BID&tid=TID&pid=PID
```

6. Preserve facts from the original signature unless the user asks to change them: ride names, leaders, route spellings, member nicknames, image URLs, quotes, and inside jokes.
7. When imitating style, copy the pattern, not the private content: layout, density, typography, color rhythm, use of collapsible sections, route emphasis, or image placement.
8. Do not add invented framing, grand summaries, motivational blurbs, or decorative “about this person” headers. A signature is not a profile card: do not add the account ID/name as a prominent title unless it already exists in the source signature or the user asks for it.

If working in this project, `scripts/inspect_chexie.py` can help capture profiles, threads, and floor API responses as local HTML snapshots.

## Chexie Constraints

- Profile edit path: `/bbs/edituser/`.
- Signature fields: `sig1`, `sig2`, `sig3`; each has `raw` or `html` type. Use `html` for styled signatures.
- Reply pages choose signature via `sig=0/1/2/3`; default is usually `1`.
- Old direct signature storage can be truncated around 1375 characters in some flows, even if the UI allows more. Treat direct long HTML as risky.
- The reliable long-signature pattern is:
  1. Put the full signature HTML in a normal forum reply/floor.
  2. Put a short JavaScript loader in the profile signature.
  3. Edit the source floor later to update all rendered signatures.

Dynamic loader template:

```html
<script>$.get("/api/bbs/content/floor/?bid=BID&tid=TID&pid=PID",function(data){sign=data+"<br><br>";$(".sig").each(function(){if($(this).html().search("bid=BID&tid=TID&pid=PID")!=-1){$(this).html(sign);}});});</script>加载签名档中...<br><br><br>
```

Replace both occurrences of `BID`, `TID`, and `PID`. `pid` is the source floor id used by the API, not necessarily the page-local floor number.

## Design Workflow

### Personal Signature

Prefer sections by time or theme:

- Years/seasons: `24秋`, `25春`, `26冬`.
- Activity rows: `活动名【队长/负责人】角色或一句话`.
- Major routes: long-distance private ride, winter/summer tour route, group members.
- Optional self-intro link, quote, or inside joke.

Style guidance:

- Use restrained gradients, colored labels, and compact typography.
- Use `details/summary` or small buttons for very long histories.
- Keep the default view readable without forcing autoplay, alerts, or disruptive popups.
- Prefer polishing the user's existing wording and structure over adding explanatory intros. Do not add a generic lead sentence such as “从某年到某年...” unless the source signature already uses that style or the user asks for summarization.
- Do not put the user ID/account name at the top of a personal signature by default. Only keep it if it is part of the original content, useful as a group roster entry, or explicitly requested.
- Avoid pretending to alter account identity, star count, role, post count, or other user metadata.

### Group-Account Signature

Prefer this structure:

1. Centered group name.
2. Short slogan.
3. Official route, possibly with highlighted anchor cities.
4. Image.
5. Member roster, one person per line unless the user asks for columns.
6. Optional links to member profiles using:

```html
<a class="author" href="../user?name=NAME" target="_blank">@NAME</a>
```

Style guidance:

- Make the team name prominent.
- Keep the route more visible than decoration.
- Use role labels consistently: `团儿`, `大姐`, `小八`, etc.
- Let the user override nicknames, ordering, colors, and whether names link to profiles.

## Implementation Rules

- Default to local files in the current project, such as `data/<slug>_signature_draft.html` and `data/<slug>_signature_preview.html`.
- Use `apply_patch` for file edits.
- Keep generated HTML compatible with older CAPUBBS rendering: inline CSS, simple tags, `font`, `br`, `div`, `span`, `img`, `details`, `summary`, and minimal JavaScript.
- Avoid external JS dependencies beyond jQuery already present on chexie pages when using the loader.
- Keep image URLs as the user provides them unless asked to upload or replace.
- If the user asks to upload, preserve, or replace images rather than only use an existing URL, use the separate `chexie-image-upload` skill.
- Use local preview to verify readability before any live edit.
- Treat `sig1/sig2/sig3` as user-selectable slots. Do not assume slot 1.
- Rendered post signatures are evidence of variants, not proof of slot number. If exact slot mapping cannot be confirmed from `/bbs/edituser/` for the target account, ask the user before labeling a variant as `sig1`, `sig2`, or `sig3`.
- When direct HTML contains scripts, never parse signature fields via rendered text; preserve raw textarea contents.

## References

Read `references/examples.md` when designing concrete signatures, choosing patterns, or needing examples from the signature-tutorial thread. Read `references/live-update.md` before writing or running live update scripts.
