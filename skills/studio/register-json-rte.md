---
name: register-json-rte
---

## When to use

Register the unified RTE renderer via `registerRTERenderer` so Studio can render rich text (**JSON RTE, HTML RTE and Markdown alike**) plus embedded entries, embedded assets and custom element types.

Use for **any** rich-text field bound to a component prop, whatever its storage format. Phrases: "JSON RTE", "HTML RTE", "rich text field", "markdown field", "RichText component", "rich text renders as raw HTML", "RTE shows `<p>` tags as literal text", "rich text renders blank", "embed a card inside rich text", "embedded entries/assets in RTE", "custom element type in RTE", "registerRTERenderer", "registerJSONRTE is deprecated". Also when the JSON tree contains element types the default serializer doesn't know, or you want to override the default HTML for a standard tag. Register once at app bootstrap.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them), and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Register an RTE renderer

> **The name says `json-rte` for historical reasons. The API is not JSON-RTE-only.** `registerRTERenderer` is a single call covering **JSON RTE, HTML RTE and Markdown**. If you arrived here with an HTML RTE or a Markdown field, you are in the right place: everything below applies unchanged.

## Context

Contentstack stores rich text in more than one shape, and Studio renders all of them through one renderer:

| Field | Stored as | Notes |
|---|---|---|
| **JSON RTE** | a structured JSON tree (nodes with `type` + `attrs`) | serialized to HTML for the prop |
| **HTML RTE** | an HTML string | embedded refs extracted from the markup |
| **Markdown** | a Markdown string | converted, then rendered |

The built-in **`RichText`** component is typed `any` and **auto-detects** which of these it received, so a JSON tree, an HTML string, Markdown, or a plain string all render without the author choosing a variant.

When Studio resolves a component prop bound to a rich-text field, it serializes the value to HTML and passes it to your component.

The default serializer already handles paragraphs, headings, lists, links, marks, images, and tables. Use **`registerRTERenderer`** (the unified, canonical API) when any of these apply:

- The JSON tree contains **custom element types** (anything outside the default tag map)
- The RTE field **embeds entries** that should render as components/cards (e.g. a blog body that embeds a Product card)
- The RTE field **embeds assets** that need custom markup (override the default `<img>` / `<video>` / `<a download>` fallback)
- You want to **override** the default rendering of a standard tag

`registerRTERenderer` covers all four in a single call.

Registration is a side-effect on the SDK singleton. It must happen **once, at app bootstrap, before any `<StudioComposition />` (or `<StudioComponent />`) mounts**. Late registration won't retroactively re-render props that have already resolved.

**`registerJSONRTE` is deprecated.** It still works (preserves previously-registered `embeddedEntry`/`embeddedAsset`) but the SDK marks it `@deprecated`. New code uses `registerRTERenderer`. Migrate existing calls when you next touch them. `registerEmbeddedEntryRenderer` is also deprecated for the same reason.

## Task

1. **Import `registerRTERenderer`** from `@contentstack/studio-react` (re-exported from `@contentstack/studio-client`):

   ```ts
   import { registerRTERenderer } from "@contentstack/studio-react";
   ```

2. **Call it at app bootstrap, once**, in the same module where you call `studioSdk.init(...)` (typically `src/lib/contentstack.ts`). Place it alongside any `registerComponent(...)` calls.

3. **Pass an `RTEConfig`**: extends `IJsonToHtmlOptions` with `embeddedEntry` + `embeddedAsset`. Each call **REPLACES** the full config. Merge yourself if you call it more than once.

   ```ts
   // Handlers return HTML strings, so escape every author-controlled value
   // and only emit http(s)/relative URLs.
   const esc = (v: unknown) =>
     String(v ?? "").replace(/[&<>"']/g, (c) =>
       ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));
   const safeUrl = (u: unknown) => {
     const s = String(u ?? "").trim();
     return /^(https?:\/\/|\/(?!\/)|#)/i.test(s) ? esc(s) : "#";
   };
   const CALLOUT_VARIANTS = new Set(["info", "warning", "success", "danger"]);

   registerRTERenderer({
     // Render embedded entries as components/cards. The SDK auto-resolves
     // the embedded entry and passes the full entry object — no extra fetch.
     embeddedEntry: ({ entry, contentTypeUid, displayType }) => {
       // displayType is one of "block", "link", or other editor-defined kinds
       if (displayType === "block") {
         return `<article class="card">
           <h3>${esc(entry.title)}</h3>
           <p>${esc(entry.summary)}</p>
         </article>`;
       }
       if (displayType === "link") {
         return `<a href="${safeUrl(entry.url)}">${esc(entry.title)}</a>`;
       }
       return `<span>${esc(entry.title)}</span>`;
     },

     // Render embedded assets. Omit to use the built-in default
     // (img for image/*, video/audio for those MIMEs, <a download> otherwise).
     embeddedAsset: ({ asset }) => {
       if (asset.content_type?.startsWith("image/")) {
         return `<img src="${safeUrl(asset.url)}" alt="${esc(asset.title)}" loading="lazy" />`;
       }
       return `<a href="${safeUrl(asset.url)}" download>${esc(asset.filename)}</a>`;
     },

     // Custom JSON RTE element types (handlers return HTML strings)
     customElementTypes: {
       callout: (attrs, child, jsonBlock) => {
         const v = jsonBlock?.attrs?.variant;
         const variant = CALLOUT_VARIANTS.has(v) ? v : "info"; // allowlist, never interpolate raw
         return `<aside class="callout callout--${variant}"${attrs}>${child}</aside>`;
       },
       // Override default heading rendering:
       h2: (attrs, child) => `<h2 class="prose-h2"${attrs}>${child}</h2>`,
     },

     // Other IJsonToHtmlOptions keys passed through:
     allowNonStandardTypes: true,
   });
   ```

4. **`embeddedEntry` args**, full signature: `{ entry, contentTypeUid, displayType, ...metadata }`. The `entry` is the **complete resolved entry object** (Studio fetches it). Read any field on it directly. `displayType` carries the editor's chosen display variant ("block", "link", or any custom string the editor exposes). Branch on it to render the same entry differently.

5. **`embeddedAsset` args**: `{ asset, ...metadata }`. The `asset` is the complete asset object including `url`, `content_type`, `filename`, `title`, `dimension` etc. Both JSON RTE (`attrs.type: "asset"`) and HTML RTE (`<figure class="embedded-asset" data-sys-asset-uid="…">`) paths invoke this handler.

6. **`customElementTypes` handler signature**: `(attrs: string, child: string, jsonBlock: IAnyObject, extraProps?: object) => string`
   - `attrs`: pre-serialized HTML attribute string
   - `child`: pre-serialized inner HTML of children
   - `jsonBlock`: raw node, read `jsonBlock.attrs`, `jsonBlock.type`, custom metadata
   - **Return an HTML string**, not a React element

7. **Match keys to node `type` exactly.** Keys in `customElementTypes` must equal the `type` string on the JSON RTE node emitted by Contentstack, byte-for-byte. `callout` will not match `"Callout"` or `"custom-callout"`. Use a standard tag name (`h2`, `a`, `ul`) to override the default rendering for that tag.

8. **Declare the prop in your component schema as `json_rte`.** Studio creates a `JsonRTEProp` and binds it to the field like any other prop: your component code stays JSON-RTE-agnostic.

9. **Render it: check which path the installed SDK supports.** Two options, and the newer one removes most of this work:

   ```bash
   grep -rq "useStudioRichText" node_modules/@contentstack/studio-react/dist \
     && echo "hook available" || echo "hook ABSENT — use the manual path"
   ```

   **`hook available` means one call.** `useStudioRichText` runs the same pipeline as the built-in `RichText`: it detects JSON RTE / HTML RTE / Markdown, resolves embedded entries and assets, and sanitizes before rendering. No `dangerouslySetInnerHTML`, no DOMPurify, no format branching.

   ```tsx
   import { useStudioRichText } from "@contentstack/studio-react";

   export function Article({ body, $body, entry }) {
     return <div className="prose">{useStudioRichText(body, $body, entry)}</div>;
   }
   ```

   Pass `entry` when you have it: embedded items are then read from `entry._embedded_items` instead of being refetched, free if the caller already used `.includeEmbeddedItems()`.

   **`hook ABSENT` means the manual path.** The prop hands over the raw value, so the component serializes and sanitizes it itself, and embedded entries/assets will NOT render:

   ```tsx
   import { jsonToHtml } from "@contentstack/json-rte-serializer";
   import DOMPurify from "isomorphic-dompurify";

   export function Article({ body }: { body: object }) {
     const html = DOMPurify.sanitize(jsonToHtml(body));
     return <div className="prose" dangerouslySetInnerHTML={{ __html: html }} />;
   }
   ```

   **Sanitize on this path.** RTE content is author-supplied. Rendering it unsanitized is an XSS vector. The hook does this for you. The manual path does not.

   On an SDK without the hook, `json_rte` also accepts **only** JSON RTE (an object). HTML RTE and Markdown are strings and cannot bind to it. Bind those to an `any` prop, or use the built-in `RichText`, until the SDK is upgraded.

10. **(Optional) Inspect current config**: three internal readers used by hooks:
    - `getJSONRTE()` returns `IJsonToHtmlOptions` (without `embeddedEntry`/`embeddedAsset`)
    - `getEmbeddedEntryRenderer()` returns the registered entry renderer or `null`
    - `getEmbeddedAssetRenderer()` returns the registered asset renderer or `null` (falls back to the SDK default if not registered)

    All three import from `@contentstack/studio-client` (not `@contentstack/studio-react`, which only re-exports the registration functions).

## Inputs needed from the user

1. `embeddedContentTypes`: list of CTs the RTE field can embed (so the `embeddedEntry` callback can branch on `contentTypeUid` per CT).
2. `customElementTypes`: list of custom node `type` values you need to render. Pull these from the actual entry JSON, not from guesses.
3. `overrideTags`: optional list of standard tags whose default HTML you want to replace.

If none of the three is provided, ask the user whether they actually need this skill: the default serializer + default asset renderer may already cover their JSON RTE.

## Acceptance

This skill succeeds only when ALL of the following are true:

- [ ] `registerRTERenderer({...})` is called once, in the bootstrap module, before any `<StudioComposition />` or `<StudioComponent />` mounts.
- [ ] If embedded entries are in scope: the `embeddedEntry` handler branches on `contentTypeUid` and/or `displayType` and returns an HTML string per case.
- [ ] If embedded assets need custom markup: the `embeddedAsset` handler returns an HTML string. Otherwise the default is acceptable.
- [ ] Every declared custom element type has a handler returning an HTML string (not React).
- [ ] Handler keys match the raw `type` values in the entry JSON exactly.
- [ ] Components consuming the prop render it via `useStudioRichText` where the installed SDK exports it, or via sanitized `dangerouslySetInnerHTML` where it does not (no escaped HTML visible on the page).
- [ ] `getJSONRTE()` returns the serializer options. `getEmbeddedEntryRenderer()` returns the entry renderer.
- [ ] Rendering a composition bound to the `json_rte` field shows custom node markup AND embedded-entry markup AND custom-asset markup in the DOM. Standard nodes still render via their defaults.

## Which component for which field {#rte-field-to-component}

Rich text is never a `Heading`/`Paragraph` job. Map the CT field to the right component, then register what that component needs:

| Contentstack field | Component | Prop type | Must register |
|---|---|---|---|
| **JSON RTE** | `RichText` | `json_rte` | `registerRTERenderer`: always, if it embeds entries/assets or custom nodes |
| **HTML RTE** (multiline + rich text editor) | `RichText` | `any` | same call: embedded refs are extracted from the markup |
| **Markdown** (multiline + markdown) | `RichText` | `any` | same call |
| Rich text that must **collapse / "read more"** | `CollapsibleText` | same as above | same call: it accepts the full RTE matrix |
| Single-line / multiline **plain** text | built-in `Text` / `Header` | `plaintext` | nothing |

**The line between them:** if an author can apply any formatting (bold, a link, a list, an embed) it is rich text and needs `RichText`. Only genuinely unformatted strings belong on `Text`/`Header`, which render `String(text)` and show markup as literal characters.

`CollapsibleText` is not a different content model: it is `RichText` plus expand/collapse. Choose it whenever the design truncates long copy behind "read more", an accordion, or a "show details" toggle.

## Embedded entries and embedded assets: the reason this API exists

These two are what `registerRTERenderer` is for. A rich-text field that only holds paragraphs needs no registration at all. The moment an author embeds an entry or an asset, unregistered rendering degrades badly:

| | Without registration | With a handler |
|---|---|---|
| **Embedded entry** | renders as a raw delivery-API span: title only, no field access, no markup | your card / component markup, with full entry fields |
| **Embedded asset** | `defaultAssetRender` fallback by MIME | your markup (captions, lazy-loading, art direction, CDN transforms) |

**Embedded entries** are stored as references, so their content must be resolved (see the next section). The handler receives the **full delivery-API entry**, plus `contentTypeUid` and `displayType`. Branch on `contentTypeUid` first, never on entry shape, because different content types often share field names.

`displayType` tells you how the author placed it, and each wants different markup:

| `displayType` | Author intent | Typical markup |
|---|---|---|
| `block` | a standalone card in the flow of text | full card: image, heading, summary, link |
| `inline` | a mention inside a sentence | a short inline span. Never a block-level element |
| `link` | text linking to the entry | an `<a>` with the entry's resolved URL |

Returning block markup for an `inline` embed breaks the paragraph it sits in, the most common visual bug here.

**Embedded assets** need no fetch: their metadata travels inline in the RTE markup. Register `embeddedAsset` only when the default markup can't express what you need.

Both handlers return **HTML strings**, not React: a returned JSX object stringifies to `[object Object]`.

## Embedded items: let the fetch you already did do the work

Embedded **entries** are stored in the RTE as references, so their content must be fetched. Embedded **assets** are not: their metadata travels inline in the markup and never costs a request.

Two ways the entries get resolved, and the cheaper one is easy to miss:

| Route | What happens | Cost |
|---|---|---|
| Pass the **`entry`** prop to `RichText` | Resolves `entry._embedded_items[<field>]` via the `$text` CSLP tag | **no extra request** |
| Pass only the RTE value | Refs are extracted, grouped by content type, and fetched in parallel | one query per content type |

So if the caller already fetched with **`.includeEmbeddedItems()`**, pass `entry` through: the embedded items are in the payload and re-fetching them is pure waste. Reach for the fetching route only when the RTE value arrives without its parent entry.

## Embedded assets: the default is usually enough, and it is guarded

`defaultAssetRender` branches on the asset's MIME type, so a custom `embeddedAsset` handler is only needed for markup the default cannot express:

| MIME | Rendered as |
|---|---|
| `image/*` | `<img>` |
| `video/*` | `<video controls>` |
| `audio/*` | `<audio controls>` |
| anything else | `<a download>` |

**If you replace it, keep the URL guard.** The default blocks `javascript:`, `vbscript:` and non-image `data:` URLs and falls back to a plain-text placeholder. An asset URL is author-supplied content, so rendering one unfiltered into an `href`/`src` is an XSS vector. A hand-written `embeddedAsset` handler that interpolates the URL straight into markup silently drops that protection.

## Deprecated built-ins: do not reach for these

`Number`, `JSONRTE` and `Section` are deprecated and no longer appear in `getBasicComponents` / `BASIC_COMPONENTS`. For rich text use **`RichText`** (or `CollapsibleText`, which accepts the same RTE matrix). The built-in `Text` and `Header` now type their text prop as `plaintext` rather than `string`. `Text` renders `String(text)` and no longer parses HTML, so markup passed to it shows as literal characters: that is what `RichText` is for.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Assuming this is JSON-RTE-only because of the name | `registerRTERenderer` covers JSON RTE, HTML RTE **and** Markdown in one call. Treating HTML RTE as unsupported leads to hand-rolled parsing | One registration serves every rich-text field, whatever its storage format |
| Putting rich text through the built-in `Text` | `Text` renders `String(text)` and no longer parses HTML, so tags appear as literal `<p>` characters | Use the `RichText` component (typed `any`, auto-detects the payload) |
| Re-fetching embedded entries the caller already loaded | Without the `entry` prop the refs are fetched again, one query per content type, on every render path | Pass `entry` so `_embedded_items` is used. Pair with `.includeEmbeddedItems()` at fetch time |
| Custom `embeddedAsset` handler that interpolates the URL directly | Drops the default's scheme guard: `javascript:` / `vbscript:` / non-image `data:` URLs become an XSS vector | Keep the scheme check, or extend `defaultAssetRender` rather than replacing it |
| Using the deprecated `Number` / `JSONRTE` / `Section` basics | Removed from `BASIC_COMPONENTS`. The `@deprecated` marker sits on the declarations so IDEs warn | Use `RichText` for rich text. `Number`/`Section` have no replacement in the basics palette |
| Using `registerJSONRTE` for new code | Deprecated. `registerRTERenderer` is the unified canonical API | Use `registerRTERenderer`. Existing `registerJSONRTE` calls still work, migrate when you next touch the file. |
| Embedded entry renders blank or as a placeholder | No `embeddedEntry` handler is registered (default renders nothing for entry embeds) | Register `embeddedEntry: ({ entry, contentTypeUid, displayType }) => html` |
| `embeddedEntry` returns a React element / JSX | Serializer is HTML-string based. React objects stringify to `[object Object]` | Return a plain HTML string from the handler |
| Calling `registerRTERenderer` more than once | Each call REPLACES the full config. Later calls drop earlier `customElementTypes` / `embeddedEntry` | Build a single merged config and call once at bootstrap. Or use `registerJSONRTE` for serializer-only updates (it preserves existing `embeddedEntry`/`embeddedAsset`), but the right answer is "register everything in one call." |
| Registering too late | After props resolve, re-registering does not retroactively re-render | Always register at bootstrap, before any composition mount |
| Wrong key name in `customElementTypes` | Keys must match the raw `type` in entry JSON, not the editor's display label | Verify against the actual entry JSON |
| Forgetting `dangerouslySetInnerHTML` on the manual path | The page renders escaped HTML as visible text | Use `useStudioRichText` if the SDK exports it. Otherwise render via `dangerouslySetInnerHTML` |
| Rendering the manual path without sanitizing | RTE content is author-supplied, so unsanitized HTML is an XSS vector. `useStudioRichText` sanitizes, hand-rolled rendering does not | Run DOMPurify before `dangerouslySetInnerHTML`, or upgrade to an SDK exporting the hook |
| Expecting embedded entries/assets to appear on the manual path | Only the built-in components and `useStudioRichText` resolve embeds: a hand-serialized `jsonToHtml` call drops them silently | Use the hook, or accept that embedded cards/media will not render |
| Registering standard types unnecessarily | Paragraphs, headings, lists, links, marks, images, tables already render | Only register to override or add |
| Branching `embeddedEntry` on entry shape instead of `contentTypeUid` | Fragile: entries may share field names across CTs | Use `contentTypeUid` as the primary branch key |
| API-authoring an entry with a `json_rte` embed reference node whose `attrs` omits `locale` | CMA rejects the write with `"Reference must contain content-type-uid, entry-uid, locale and display-type."`. The SDK's read path never surfaces this because it's a write-time validation | Every embedded-entry `reference` node under `json_rte` needs the full attr set: `{ type: "entry", "entry-uid": "…", "content-type-uid": "…", "display-type": "block"\|"inline"\|"link", "locale": "en-us" }`. Applies both to node-level RTE fields and `static_value.json_rte[*].value` embeds (mirrors `provision-studio-project` § `static_value` sub-schema JSON-RTE row) |

## See also

- Pair with `install-studio` (must run first so `studioSdk.init` exists).
