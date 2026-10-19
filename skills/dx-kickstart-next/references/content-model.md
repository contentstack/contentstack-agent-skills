# Content model guidance for kickstart-next

Use this before changing Contentstack content type UIDs, field UIDs, `lib/types.ts`, modular block rendering, or Visual Builder/CSLP bindings.

## Seed contract

The app assumes content from `contentstack/kickstart-stack-seed`. Verify the actual stack or seed before making schema claims, but preserve this contract unless the user intentionally changes the model.

| Content type | UID | Used by |
| --- | --- | --- |
| Page | `page` | `lib/contentstack.ts` `getPage(url)`, `app/page.tsx`, `components/Page.tsx`, `lib/types.ts` `Page` |

## Page fields

| Field | UID | Type shape in app | Rendered by | Live Preview binding |
| --- | --- | --- | --- | --- |
| Title | `title` | `Page.title: string` | `components/Page.tsx` `h1` | `page.$.title` |
| URL | `url` | `Page.url?: string` | queried by `getPage(url)` | `page.$.url` if rendered later |
| Description | `description` | `Page.description?: string` | `components/Page.tsx` paragraph | `page.$.description` |
| Image | `image` | `Page.image?: File \| null` | `next/image` in `components/Page.tsx` | asset `$` mapping, currently `page.image.$.url` |
| Rich Text | `rich_text` | `Page.rich_text?: string` | sanitized HTML in `components/Page.tsx` | `page.$.rich_text` |
| Blocks | `blocks` | `Page.blocks?: Blocks[]` | modular block loop in `components/Page.tsx` | `page.$.blocks` and indexed `page.$["blocks__${index}"]` |

## Modular block shape

The `blocks` field contains entries shaped like `{ block: Block }`.

| Block field | UID | Type shape in app | Rendered by | Live Preview binding |
| --- | --- | --- | --- | --- |
| Title | `title` | `Block.title?: string` | block `h2` | `block.$.title` |
| Copy | `copy` | `Block.copy?: string` | sanitized HTML | `block.$.copy` |
| Image | `image` | `Block.image?: File \| null` | `next/image` | `block.$.image` |
| Layout | `layout` | `"image_left" \| "image_right" \| null` | flex direction choice | `block.$.layout` if rendered later |
| Metadata | `_metadata.uid` | key fallback for React list items | list item key | not user-editable |

## Asset shape

- Use the local `File` interface for Contentstack assets.
- Render images with `file.url` and descriptive alt text from `file.title` or another safe fallback.
- Keep asset CSLP mappings under `File.$` when the rendered asset field needs Visual Builder editing.

## Change checklist

- If a UID changes, update `getPage`, `lib/types.ts`, renderers, docs, and any Contentstack seed instructions together.
- If a field is added, add the TypeScript shape, render path, fallback behavior for missing content, and `$` mapping only where the field is editable.
- If a modular block is added, preserve empty-block editing support with `VB_EmptyBlockParentClass` on the parent block container.
- If rich text or HTML-like fields are added, sanitize before rendering with `dangerouslySetInnerHTML`.
- If image fields are added, verify `next.config.mjs` allows the image hostname.
