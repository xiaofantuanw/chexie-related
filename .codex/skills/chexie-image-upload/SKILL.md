---
name: chexie-image-upload
description: Use when Codex needs to help upload, preserve, insert, or reference images for chexie.net CAPUBBS posts or signatures, including choosing between external image URLs, forum-hosted images under /bbs/images/, post attachments via /bbs/attach/, and signature-safe image markup.
---

# Chexie Image Upload

## Purpose

Help with images on chexie.net CAPUBBS posts and signatures. Keep these cases separate:

- **External image link**: the image stays on another site and Chexie only displays it.
- **Forum-hosted post image**: the image is stored on Chexie and rendered from paths like `../images/<hash>.jpg`.
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
2. For upload/preservation: use the editor's image upload or attachment control if visible, choose the file, keep `auth=0` and `price=0` unless there is a reason to restrict access, then submit the post.
3. After the post renders, right-click or inspect the displayed image and copy the final `https://chexie.net/bbs/images/...` URL if it will be reused in a signature.
4. For signatures, place the copied image URL in the signature HTML or the dynamic source floor.

## Implementation Notes

- Use local read-only inspection first. `scripts/inspect_chexie.py --get-url URL` can fetch public pages and save snapshots under `data/inspect_chexie/`.
- Source references that established this workflow:
  - Public tutorial: `https://www.chexie.net/bbs/content/?bid=4&tid=19500&p=1`
  - Image size follow-up: `https://chexie.net/bbs/content/?bid=4&tid=19603&p=1`
  - Shared upload JavaScript: `https://chexie.net/bbs/lib/content_shared.js`
- If live automation is needed, preserve the browser's cookies and CSRF/token behavior. Do not hard-code credentials or tokens.
- Before using a forum-hosted image in a signature, verify the URL loads without requiring the target account's login.
