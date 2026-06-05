# Live Signature Update Reference

Use this reference when the user authorizes logging into chexie.net and changing a signature slot.

## Inputs

Require explicit values before any write:

- Target account display name.
- Target slot number: `1`, `2`, or `3`.
- Draft HTML path.
- Signature repository thread: `bid` and `tid`.
- Whether to create a new source floor or edit an existing source floor.

## Recommended Stages

### Prepare

1. Read and compact the draft HTML:
   - trim leading/trailing whitespace;
   - collapse whitespace between tags with `>\s+<` -> `><`;
   - keep text content whitespace intact where meaningful.
2. Login without exposing secrets.
3. Confirm `/bbs/edituser/` belongs to the target account.
4. Read the current target slot content and type for backup.
5. Post the full compact HTML to the repository thread.
6. Set reply field `sig` to the target slot number. Do not default to `0`.
7. Locate the new source floor by author and content marker.
8. Save state JSON with account, slot, `bid`, `tid`, `pid`, API URL, loader, old slot length/type, and timestamp.

### Apply

1. Load state JSON.
2. Login and confirm target account.
3. Fetch `/bbs/edituser/` live.
4. Parse the whole profile form and preserve every field.
5. Set only:
   - `sigN` to the loader;
   - `sigN_type` to `html`.
6. Submit `/bbs/edituser/action.php`.
7. Refetch `/bbs/edituser/` and verify the exact loader is present in `sigN`.

### Edit Source Floor

Use this when the loader is already installed and the user only wants visual/content changes.

1. Load state JSON.
2. Login and confirm target account.
3. Open `/bbs/editpid/?bid=BID&tid=TID&pid=PID`.
4. Parse the edit form and replace only the main post body field.
5. Submit to the form action URL.
6. Verify `/api/bbs/content/floor/?bid=BID&tid=TID&pid=PID` contains the updated marker.

## Form Handling Rules

- Use `BeautifulSoup(..., "html.parser")` for structure, but do not use `.text` for signature textareas.
- For every `<textarea>`, read `field.decode_contents()` so embedded `<script>` tags survive.
- Preserve hidden fields, selected radio values, selected options, and JS-initialized profile fields such as icon and sex.
- If the target account cannot be confirmed, stop before writing.
- If the form field for source-floor body cannot be identified unambiguously, stop and save a snapshot.

## Loader Template

```html
<script>$.get("/api/bbs/content/floor/?bid=BID&tid=TID&pid=PID",function(data){sign=data+"<br><br>";$(".sig").each(function(){if($(this).html().search("bid=BID&tid=TID&pid=PID")!=-1){$(this).html(sign);}});});</script>加载签名档中...<br><br><br>
```

Replace both `BID/TID/PID` occurrences.

## Verification

Save snapshots under `data/inspect_chexie/`:

- edit profile page before apply;
- edit profile page after apply;
- source floor edit page before edit;
- source floor API after edit.

A successful update should show:

- source floor API contains the full compact signature HTML;
- selected profile slot contains the full loader, including `<script>`;
- selected profile slot type is `html`;
- unrelated profile fields remain unchanged.
