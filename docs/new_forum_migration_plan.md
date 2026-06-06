# New Forum Migration Plan

Last reviewed: 2026-06-06

## Current Findings

The production forum remains the legacy CAPUBBS site under:

```text
https://chexie.net/bbs/
```

The new forum test site is available at:

```text
https://test.chexie.net/bbs-new/
```

The announcement thread reviewed on 2026-06-06:

```text
https://chexie.net/bbs/content/?bid=28&tid=150&p=1
```

Key notes from the thread:

- The first public interface demo was posted around 2026-05-27 as a UI preview without a real database.
- A 2026-06-04 update says most APIs have been deployed to the test environment.
- The test database is a snapshot through 2026-05-31.
- Accounts registered before that snapshot can be used for testing.
- Many images are expected to be unavailable on the test environment.
- Current planned/new features include Markdown or HTML editing, local drafts, richer signature support, activity posts with signup metadata, activity admin export, archive/data pages, and user/member data features.

## Access Differences

Legacy CAPUBBS:

- Server-rendered PHP pages.
- Thread URLs use query parameters such as `/bbs/content/?bid=28&tid=150&p=1`.
- Board URLs use `/bbs/main/?bid=...`.
- Profile URLs use `/bbs/user?name=...`.
- Login uses `/bbs/login/action.php` with an MD5 password hash.
- Reply/post/profile forms submit to PHP endpoints.
- Existing scripts parse HTML with BeautifulSoup and rely on CSS selectors such as `tr.floor`, `.textblock`, `.authorbig`, and profile form fields.

New test forum:

- React/Vite single-page app mounted at `/bbs-new/`.
- Route examples include `/threads/:threadId`, `/boards/:boardName`, `/users/:userSlug`, `/login`, `/register`, `/user-center`, `/search`, `/archive`, and `/stats`.
- Thread ids are represented as `bid-tid`, for example `28-150`.
- The frontend includes legacy URL compatibility that maps old `/bbs/content/?bid=&tid=&p=` links into new thread routes.
- The shell page itself is static; data is fetched by JavaScript.
- The bundle still calls many legacy endpoints, including `/api/api.php`, `/api/jiekouapi.php`, `/api/jiekoujson.php`, `/bbs/post`, `/bbs/editpid/action.php`, `/bbs/login/action.php`, `/bbs/content/test.php`, `/bbs/attach`, and related CAPUBBS endpoints.
- Some new capability endpoints appear, including `/api/bbs/activity/create/` and `/bbs/content/utils/postActivity.php`.

## Migration Principles

- Keep production automation on legacy CAPUBBS until the new forum is confirmed stable with real production data.
- Do not rewrite skills around DOM selectors from the new SPA. Prefer API-level adapters where possible.
- Separate forum-independent workflows from forum-specific transport code.
- Keep every live write behind explicit user authorization, regardless of forum version.
- Treat test forum writes as live actions too, because they affect an account and a database snapshot.
- Preserve old URL handling. Many existing forum references will continue to use `bid/tid/pid`.
- Store local snapshots, probes, and migration notes under ignored local directories unless explicitly publishing sanitized docs.

## Adapter Migration Steps

1. Define a shared `ForumAdapter` interface for read, draft, and write operations.
2. Keep `LegacyCapubbsAdapter` as the default adapter.
3. Add `NewForumAdapter` as a probe-only adapter at first.
4. Build read-only parity tests:
   - fetch board summary;
   - fetch thread metadata;
   - fetch floor content;
   - fetch current viewer profile;
   - resolve old URL to canonical thread id.
5. Add authenticated read tests only after explicit user authorization.
6. Add write dry-run objects before live writes:
   - post thread;
   - reply thread;
   - edit floor;
   - upload image;
   - update signature;
   - submit or cancel activity signup.
7. Promote one capability at a time from legacy-only to dual-adapter.
8. Keep old CAPUBBS scripts until each corresponding adapter method has test coverage and at least one verified manual run.

## Skill Migration Order

Recommended order:

1. `chexie-signature` read/preview behavior.
2. Signature source-floor detection and old-link normalization.
3. Image URL normalization and upload probes.
4. Read-only thread/profile inspection.
5. Posting replies and editing existing floors.
6. Activity signup and export workflows.
7. New rich signature editor support, if the new forum removes the old length workaround.

Open risks:

- The new frontend bundle can change without notice.
- The test database is not current production data.
- Image hosting behavior is incomplete on the test environment.
- Some new features are UI-local only, especially drafts and interface settings.
- Activity signup schema needs real endpoint-level confirmation before automation.
