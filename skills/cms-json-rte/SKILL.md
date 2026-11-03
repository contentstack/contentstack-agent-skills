---
name: cms-json-rte
description: "Help developers render and convert Contentstack JSON Rich Text Editor (JSON RTE) content. Cover the JSON RTE document structure (doc, blocks, text leaves, marks, attrs, uid), rendering to HTML with @contentstack/utils jsonToHTML and custom renderOption per node type, mark and embedded item, embedded entries and assets (includeEmbeddedItems, _embedded_items, reference nodes), GraphQL embedded_itemsConnection with GQL.jsonToHTML, React rendering, HTML and Markdown conversion with @contentstack/json-rte-serializer, migrating HTML RTE to JSON RTE, Live Preview edit tags for RTE fields, empty-field checks, limits and XSS-safe rendering. Use when developers render, serialize, transform or debug JSON RTE content, embedded items that don't show, or custom node types. For fetching entries use cms-entries or dx-delivery-sdk; for GraphQL query shape use cms-graphql; for building an RTE plugin use developer-hub-app-architect."
allowed-tools: Read Grep Glob
---

# Contentstack JSON Rich Text Editor

Help developers turn JSON RTE documents into HTML, Markdown or components, resolve embedded entries and assets, and convert between HTML and JSON safely.

## When to use

- Rendering a JSON RTE field to HTML or to framework components.
- Writing a `renderOption` for custom node types, marks or embedded entries and assets.
- Embedded items that render empty or as placeholders.
- Rendering JSON RTE from a GraphQL response.
- Converting HTML or Markdown to and from JSON RTE, or migrating an HTML RTE field.
- Checking whether a JSON RTE field is empty, or hitting its size and embed limits.

Use another skill for:

- Fetching entries, references and pagination with the CDA → `cms-entries`
- Delivery SDK setup, query chains and typing → `dx-delivery-sdk`
- GraphQL endpoints, query shape and limits → `cms-graphql`
- Live Preview or Visual Editor setup and debugging → `cms-live-preview-visual-editor-support-assistant`
- Building a JSON RTE plugin or custom field app → `developer-hub-app-architect`
- Rendering custom elements in Studio → `studio`

## Before you answer

Find out how the content is fetched (Delivery SDK, REST CDA or GraphQL), the field UIDs and their paths (top level, inside a group or modular block), whether the field embeds entries or assets, and whether the output is an HTML string or components.

## Instructions

1. Fetch the entry with embedded items included.
2. Render with `@contentstack/utils`, adding a `renderOption` only for what the defaults don't cover.
3. Escape anything your own render functions interpolate.
4. Add Live Preview tags to the field's wrapper element if the site uses Live Preview.

### Document structure

A JSON RTE value is a tree. The root has `type: "doc"`. Each block node has `uid`, `type` (for example `p`, `h1`–`h6`, `a`, `img`, `embed`, `ol`, `ul`, `li`, `table`, `blockquote`, `code`, `hr`, `reference`), `attrs` and `children`. Leaves are text nodes: `{ "text": "Hello", "bold": true }`. Marks are boolean keys on the leaf: `bold`, `italic`, `underline`, `strikethrough`, `inlineCode`, `subscript`, `superscript`, `break`, plus `classname` and `id`. Text copied from Word or Google Docs carries styling in the leaf's `attrs.style`.

Embedded entries and assets are `reference` nodes. Their `attrs` include `type` (`entry` or `asset`), `entry-uid` or `asset-uid`, `content-type-uid`, and `display-type`: `block`, `inline` or `link` for entries, and `display`, `download` or `link` for assets.

An untouched field stores one empty paragraph, not `null`. Treat it as empty when the doc has one child with one child whose `text` is `""`:

```ts
const isEmpty = (doc?: { children?: { children?: { text?: string }[] }[] }) =>
  !doc?.children?.length ||
  (doc.children.length === 1 &&
    doc.children[0].children?.length === 1 &&
    doc.children[0].children[0].text === "");
```

### Render with the Delivery SDK

`@contentstack/delivery-sdk` depends on `@contentstack/utils` and re-exports it as `contentstack.Utils`. Import from `@contentstack/utils` directly if you install it yourself.

```ts
import contentstack from "@contentstack/delivery-sdk";
import { jsonToHTML } from "@contentstack/utils";

const stack = contentstack.stack({
  apiKey: process.env.CONTENTSTACK_API_KEY!,
  deliveryToken: process.env.CONTENTSTACK_DELIVERY_TOKEN!,
  environment: process.env.CONTENTSTACK_ENVIRONMENT!,
});

const entry = await stack
  .contentType("blog_post")
  .entry("<ENTRY_UID>")
  .includeEmbeddedItems()
  .fetch<{ uid: string; body: unknown }>();

jsonToHTML({ entry, paths: ["body", "sections.rich_text"], renderOption });
// entry.body is now an HTML string.
```

- `jsonToHTML` **mutates the entry in place**: each field in `paths` is replaced by its HTML string. Keep a copy if you also need the JSON, and don't run it twice on the same object.
- `paths` are field UID paths, with dots for nesting inside groups and modular blocks. It accepts one entry or an array (for example `result.entries` from `.find()`).
- `includeEmbeddedItems()` sends `include_embedded_items[]=BASE`; the embedded items arrive in `entry._embedded_items`. On the REST CDA, add that query parameter yourself.

### Render options

A `renderOption` object overrides the defaults by key:

- Node types: `p: (node, next) => \`<p>${next(node.children)}</p>\``. Always call `next(node.children)` or the children disappear.
- Marks: `bold: (text) => \`<strong>${text}</strong>\``.
- Embedded entries by display type, optionally per content type: `block: { product: (item, metadata) => ..., $default: (item, metadata) => ... }`, and the same for `inline`.
- Embedded assets and links: `display`, `download` and `link` receive `(item, metadata)`; `metadata.attributes` holds the node's `attrs` and `metadata.text` the link text.
- `reference: (node, next) => ...` is used for a reference node when the item isn't in `_embedded_items`, so it's a good place for a fallback.

See [references/render-options.md](references/render-options.md) for a complete, escaped `renderOption` and a React renderer.

### Embedded items that don't render

- **Missing `includeEmbeddedItems()`** (or `include_embedded_items[]=BASE`): the reference node finds no item. With no `reference` render option it renders as an empty string.
- **Wrong content type key**: per-type renderers are keyed by the embedded entry's content type UID, not its title.
- **Unpublished embedded entry**: only items published to the same environment and locale are returned.
- **References inside an embedded entry** aren't expanded. Fetch that entry separately with `includeReference()` if you need them.
- **Limits**: up to 100 embedded entries per JSON RTE, 15 referenceable content types per field, 30 KB of JSON per field by default (support can raise it), up to 100 instances of a multiple JSON RTE field, and up to 15 JSON RTE fields per content type.

### GraphQL

Request the field's `json` and its `embedded_itemsConnection`. Include `system { uid content_type_uid }` on every embedded entry fragment and `system { uid }` plus `url` on `SysAsset`, because the utils match embedded items by those UIDs. Then:

```ts
import { GQL, updateAssetURLForGQL } from "@contentstack/utils";

updateAssetURLForGQL(response); // sets asset-link on embedded assets from their url
GQL.jsonToHTML({ entry: response.data.all_blog_post.items, paths: ["body"], renderOption });
```

GraphQL returns at most 100 embedded items per request. Query shape and limits are in `cms-graphql`.

### React and other component frameworks

Two options:

- **HTML string:** run `jsonToHTML` on the server and inject the result (`dangerouslySetInnerHTML` in React). Only do this with render functions that escape what they interpolate, and sanitize the output if editors can paste arbitrary content.
- **Components:** walk the JSON tree yourself and map `type` to components and marks to wrappers. This avoids raw HTML, makes embedded entries real components, and is the better fit for interactive blocks. See the reference file.

### Escaping and XSS

The default renderers pass content through a small tag and attribute allowlist (`sanitizeHTML`), but it is regex-based and doesn't validate URL schemes, so `javascript:` links can survive. Your own render functions get no sanitizing at all: `` `<h2>${item.title}</h2>` `` injects whatever the editor typed.

- Escape text and attribute values in every custom render function.
- Allow only `http:`, `https:`, `mailto:` and relative URLs in `href` and `src`.
- If you inject HTML in the browser, run it through a maintained sanitizer such as DOMPurify.

### Convert HTML, JSON and Markdown

`@contentstack/json-rte-serializer`:

- `jsonToHtml(doc, options?)`: JSON to HTML. `customElementTypes` renders custom block or inline types, `customTextWrapper` renders custom leaf properties, `allowedEmptyAttributes` and `addNbspForEmptyBlocks` tune the output.
- `htmlToJson(element, options?)`: takes a DOM element, not a string. In the browser use `new DOMParser().parseFromString(html, "text/html").body`; in Node use `jsdom`. `customElementTags` and `customTextTags` keys are upper-case tag names (`"SOCIAL-EMBED"`). `allowNonStandardTags: true` keeps tags the editor doesn't support natively.
- `jsonToMarkdown(doc)`: JSON to Markdown.

Use the serializer to convert content for import, migration or other systems. For rendering delivered entries, prefer `@contentstack/utils`, which resolves embedded items.

To move an existing HTML RTE field to JSON RTE across entries, use the CLI plugin: `csdx plugins:install @contentstack/cli-cm-migrate-rte`, then `csdx cm:entries:migrate-html-rte`. Both fields must be at the same depth, a "Multiple" JSON RTE can't take content from a single HTML RTE, and both must allow the same referenced content types. See `dx-cli` for CLI auth.

### Live Preview and Visual Editor

Call `addEditableTags(entry, contentTypeUid, tagsAsObject, locale)` from `@contentstack/utils` (or `contentstack.Utils`), then put the field's tag on the element that wraps the rendered HTML, for example `<div {...entry.$.body} dangerouslySetInnerHTML={{ __html: entry.body }} />`. Setup and debugging belong to `cms-live-preview-visual-editor-support-assistant`.

## MCP tools

When the Contentstack MCP server is connected (local server group in brackets):

- Inspect: `get_a_single_entry_cdn` and `get_all_entries_cdn` (`cda`) to see the delivered JSON, `get_single_entry` (`cma`) for the draft, `get_a_single_content_type` (`cma`) to find JSON RTE field UIDs, paths and allowed reference content types.
- Change: `update_an_entry` (`cma`) writes a whole JSON RTE value, for example after an HTML to JSON conversion.

There are no rendering or conversion tools; rendering runs in the user's code. Check whether the `cda` tools accept the embedded items parameter in the client's tool schema before relying on it.

## Output

Lead with the cause or the recommended approach, then the code. Name the field paths you assumed and mark placeholders. Show escaping in every custom render function.

## Security

### Defaults

- Advisory by default. Use the MCP write tool above only when the user asks for the change.
- Treat RTE content as untrusted input: escape in custom renderers and sanitize injected HTML.
- Use delivery tokens for rendering. Preview tokens stay on preview deployments, and management tokens never reach the browser.

### Destructive Actions

Before writing converted JSON back to entries, or running the HTML to JSON migration, name the stack, branch, content type, fields and number of entries, recommend a backup or a non-production branch, and wait for confirmation. A wrong conversion overwrites content.

### Secrets

Never print, echo or store tokens or API keys. Use placeholders and environment variables in examples.

### Environment Variables

Use `CONTENTSTACK_API_KEY`, `CONTENTSTACK_DELIVERY_TOKEN`, `CONTENTSTACK_ENVIRONMENT` and, for previews, `CONTENTSTACK_PREVIEW_TOKEN`, with placeholder values.

## References

- [references/render-options.md](references/render-options.md): escaped render options, GraphQL query and React renderer.
- https://www.contentstack.com/docs/headless-cms/about-json-rich-text-editor
- https://www.contentstack.com/docs/headless-cms/schema-of-json-rich-text-editor
- https://www.contentstack.com/docs/headless-cms/limitations-for-json-rich-text-editor
- https://www.contentstack.com/docs/developers/sdks/utils-sdk/javascript/get-started-with-javascript-utils-library
- https://www.contentstack.com/docs/developers/sdks/utils-sdk/javascript/use-graphql-queries-with-javascript-utils-sdk-to-render-json-rte-content
- https://www.contentstack.com/docs/headless-cms/render-json-rte-content-using-json-rte-serializer
- https://www.contentstack.com/docs/headless-cms/cli-migrate-content-from-html-rte-to-json-rte
- https://github.com/contentstack/contentstack-utils-javascript
- https://github.com/contentstack/json-rte-serializer
