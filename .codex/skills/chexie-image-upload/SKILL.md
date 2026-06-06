---
name: chexie-image-upload
description: Use when Codex needs to help upload, preserve, insert, or reference images for chexie.net CAPUBBS posts or signatures, including choosing between external image URLs, forum-hosted images under /bbs/images/, post attachments via /bbs/attach/, and signature-safe image markup.
---

# Chexie Image Upload

## Purpose

Help with images on chexie.net CAPUBBS posts and signatures. Keep these cases separate:

- **External image link**: the image stays on another site and Chexie only displays it.
- **Forum-hosted post image**: the image is stored on Chexie and rendered from paths like `../images/<hash>.jpg`.
- **Editor image upload**: the reply editor's `上传图片` button stores an image on Chexie and returns a reusable image URL.
- **Post attachment**: a file is uploaded via the reply editor's `添加附件` flow and bound to a post by attachment id.
- **Signature image**: a signature references an image URL or uses a source floor that contains image HTML.

## First Steps

1. Clarify whether the user wants a forum post image, a signature image, or a generic file attachment.
2. Prefer external links or an existing stable Chexie image URL for signatures unless the user specifically asks to upload a new image to the forum.
3. Do not perform live uploads, posts, edits, or deletes unless the user explicitly authorizes that exact operation.
4. Treat credentials, cookies, tokens, and session ids as secrets. Never print or store them in generated output.

## What The Forum Tutorial Says

The public tutorial thread `bid=4&tid=19500` distinguishes two ways to insert images in posts:

- `链接`: the image is displayed from another site and does not consume Chexie storage.
- `上传`: the image is transferred to the forum server, is preserved on Chexie, and consumes forum storage.

The same tutorial recommends:

- Use uploaded/forum-hosted images for pictures with preservation value, such as meaningful ride photos.
- Use linked images for less important images and memes.
- Animated images should use an external link if animation matters.
- Signatures do not have the post toolbar, but can still use tags such as `[img]URL[/img]` or HTML generated in a source floor.

## Signature Image Guidance

For normal signatures, use one of these:

```html
<img src="IMAGE_URL" style="max-width:95%;">
```

```text
[img]IMAGE_URL[/img]
```

For long or styled signatures, prefer the dynamic source-floor pattern from `chexie-signature`: put the full HTML, including `<img>`, in a normal reply and point the profile signature at that floor.

If the image is forum-hosted and appears as a relative path like:

```html
<img src="../images/88b87c284731c1bccc8f20f85691af16997ae7bd.png">
```

use an absolute equivalent when placing it outside its original page context:

```text
https://chexie.net/bbs/images/88b87c284731c1bccc8f20f85691af16997ae7bd.png
```

## Forum Attachment Upload Flow

Use this only for generic files or attachment-style downloads. This is not the same as the editor's `上传图片` button.

The reply page uses the shared script `/bbs/lib/content_shared.js`. The verified attachment flow is:

1. User clicks `添加附件`, which triggers a hidden file input.
2. After file selection, the page asks for `auth` and `price`.
3. The browser sends `multipart/form-data` by `POST` to `../attach/`, equivalent to `/bbs/attach/`, with fields:
   - `auth`: minimum score required to view/download the attachment.
   - `price`: score price, valid range `0` to `200`.
   - `file`: the selected file.
4. On success, the endpoint returns JSON with `code == 0` and `msg` containing the attachment id.
5. The reply submission posts to `../post/` with `attachs` as a space-separated list of attachment ids.
6. Existing unused attachments can be moved into the current reply with the page's `引用` action.
7. Unused attachments can be permanently deleted via `POST ../delattach/` with `id`.

Use this flow for files that should be attached to a post. Do not assume it creates an embeddable image URL for signatures.

## Editor Image Upload Flow

Use this when the user asks to upload an image so it becomes a reusable forum-hosted image URL.

The reply editor loads `/bbs/lib/nic.js`. The verified `上传图片` button flow is:

1. Require explicit authorization before doing this live write operation.
2. Login with an authorized account. Do not print or persist usernames, passwords, cookies, session ids, or tokens.
3. Keep the image under the editor's apparent 1 MB limit. The editor UI says `上传图片（最大允许1M）`.
4. Send `multipart/form-data` by `POST` to:

```text
https://chexie.net/bbs/content/test.php
```

5. Include fields:
   - `image`: the image file.
   - `key`: `b7ea18a4ecbda8e92203fa4968d10660`.
6. Parse the JSON response and read:

```text
upload.links.original
```

7. If the returned URL is relative, usually `../images/<hash>.<ext>`, normalize it to:

```text
https://chexie.net/bbs/images/<hash>.<ext>
```

8. Verify the normalized URL with a GET request before using it in a post or signature.
9. To publish it in a post, insert HTML such as:

```html
<img src="https://chexie.net/bbs/images/<hash>.<ext>" style="max-width:95%;">
```

10. To post a reply programmatically, send `POST /bbs/post/` with `bid`, `tid`, login `token`, `title`, `text`, `sig`, and `attachs`. Set `attachs` to an empty string for an uploaded inline image.

Live validation performed on 2026-06-06:

- Generated a 320x180 white PNG, 453 bytes.
- Uploaded it via `/bbs/content/test.php`.
- Received a forum-hosted URL under `/bbs/images/`.
- Inserted it into a reply in the requested test thread.
- Verified the image URL returned HTTP 200 with `content-type: image/png`.

## Forum-Hosted Image URLs

Posts commonly render uploaded/preserved images as:

```html
<img src="../images/<hash>.<ext>">
```

For reuse in signatures or HTML snippets, normalize to:

```text
https://chexie.net/bbs/images/<hash>.<ext>
```

If the only available result from upload is an attachment id, post or inspect the resulting floor before using it as a signature image. The reliable reusable value is the rendered image URL, not the attachment id.

## Browser Workflow For Users

When guiding a non-technical user:

1. For external images: open the reply editor, use the toolbar's image button or write `[img]IMAGE_URL[/img]`.
2. For image upload/preservation: use the editor's `上传图片` button if visible, choose an image under 1 MB, then submit the post.
3. For generic file attachment: use `添加附件`, choose the file, keep `auth=0` and `price=0` unless there is a reason to restrict access, then submit the post.
4. After the post renders, right-click or inspect the displayed image and copy the final `https://chexie.net/bbs/images/...` URL if it will be reused in a signature.
5. For signatures, place the copied image URL in the signature HTML or the dynamic source floor.

## Implementation Notes

- Use local read-only inspection first. `scripts/inspect_chexie.py --get-url URL` can fetch public pages and save snapshots under `data/inspect_chexie/`.
- Source references that established this workflow:
  - Public tutorial: `https://www.chexie.net/bbs/content/?bid=4&tid=19500&p=1`
  - Image size follow-up: `https://chexie.net/bbs/content/?bid=4&tid=19603&p=1`
  - Editor image upload JavaScript: `https://chexie.net/bbs/lib/nic.js`
  - Shared upload JavaScript: `https://chexie.net/bbs/lib/content_shared.js`
- If live automation is needed, preserve the browser's cookies and CSRF/token behavior. Do not hard-code credentials or tokens.
- Before using a forum-hosted image in a signature, verify the URL loads without requiring the target account's login.
