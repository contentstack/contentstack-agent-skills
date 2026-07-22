# register-json-rte


## When to use

Register a unified RTE renderer via `registerRTERenderer` so Studio can serialize json_rte fields, embedded entries, embedded assets, and custom element types to HTML for component props.

Use when a CT schema has a JSON RTE field bound to a component prop (Studio exposes it as JsonRTEProp), when the JSON tree contains custom element types the default serializer doesn't know, when the RTE field embeds entries that should render as components/cards, or when overriding default HTML output for a standard tag. Register once at app bootstrap.

# Register a JSON RTE renderer

## Context

Contentstack's **JSON RTE** field stores rich text as a structured JSON tree (nodes with a `type` and `attrs`), not as an HTML string. When Studio resolves a component prop bound to a `json_rte` field, it serializes that JSON tree to an HTML string and passes it as a `JsonRTEProp` value.

The default serializer already handles paragraphs, headings, lists, links, marks, images, and tables. Use **`registerRTERenderer`** — the unified, canonical API — when any of these apply:

- The JSON tree contains **custom element types** (anything outside the default tag map)
- The RTE field **embeds entries** that should render as components/cards (e.g. a blog body that embeds a Product card)
- The RTE field **embeds assets** that need custom markup (override the default `<img>` / `<video>` / `<a download>` fallback)
- You want to **override** the default rendering of a standard tag

`registerRTERenderer` covers all four in a single call.

Registration is a side-effect on the SDK singleton. It must happen **once, at app bootstrap, before any `<StudioComposition />` (or `<StudioComponent />`) mounts**. Late registration won't retroactively re-render props that have already resolved.

**`registerJSONRTE` is deprecated.** It still works (preserves previously-registered `embeddedEntry`/`embeddedAsset`) but the SDK marks it `@deprecated`. New code uses `registerRTERenderer`; migrate existing calls when you next touch them. `registerEmbeddedEntryRenderer` is also deprecated for the same reason.

See: `docs/20-bring-your-own-components/json-rte-custom-element-rendering.md`.

## Task

1. **Import `registerRTERenderer`** from `@contentstack/studio-react` (re-exported from `@contentstack/studio-client`):

   ```ts
   import { registerRTERenderer } from "@contentstack/studio-react";
   ```

2. **Call it at app bootstrap, once**, in the same module where you call `studioSdk.init(...)` (typically `src/lib/contentstack.ts`). Place it alongside any `registerComponent(...)` calls.

3. **Pass an `RTEConfig`** — extends `IJsonToHtmlOptions` with `embeddedEntry` + `embeddedAsset`. Each call **REPLACES** the full config; merge yourself if you call it more than once.

   ```ts
   registerRTERenderer({
     // Render embedded entries as components/cards. The SDK auto-resolves
     // the embedded entry and passes the full entry object — no extra fetch.
     embeddedEntry: ({ entry, contentTypeUid, displayType }) => {
       // displayType is one of "block", "link", or other editor-defined kinds
       if (displayType === "block") {
         return `<article class="card">
           <h3>${entry.title}</h3>
           <p>${entry.summary ?? ""}</p>
         </article>`;
       }
       if (displayType === "link") {
         return `<a href="${entry.url ?? "#"}">${entry.title}</a>`;
       }
       return `<span>${entry.title}</span>`;
     },

     // Render embedded assets. Omit to use the built-in default
     // (img for image/*, video/audio for those MIMEs, <a download> otherwise).
     embeddedAsset: ({ asset }) => {
       if (asset.content_type?.startsWith("image/")) {
         return `<img src="${asset.url}" alt="${asset.title ?? ""}" loading="lazy" />`;
       }
       return `<a href="${asset.url}" download>${asset.filename}</a>`;
     },

     // Custom JSON RTE element types (handlers return HTML strings)
     customElementTypes: {
       callout: (attrs, child, jsonBlock) => {
         const variant = jsonBlock?.attrs?.variant ?? "info";
         return `<aside class="callout callout--${variant}"${attrs}>${child}</aside>`;
       },
       // Override default heading rendering:
       h2: (attrs, child) => `<h2 class="prose-h2"${attrs}>${child}</h2>`,
     },

     // Other IJsonToHtmlOptions keys passed through:
     allowNonStandardTypes: true,
   });
   ```

4. **`embeddedEntry` args** — full signature: `{ entry, contentTypeUid, displayType, ...metadata }`. The `entry` is the **complete resolved entry object** (Studio fetches it) — read any field on it directly. `displayType` carries the editor's chosen display variant ("block", "link", or any custom string the editor exposes). Branch on it to render the same entry differently.

5. **`embeddedAsset` args** — `{ asset, ...metadata }`. The `asset` is the complete asset object including `url`, `content_type`, `filename`, `title`, `dimension` etc. Both JSON RTE (`attrs.type: "asset"`) and HTML RTE (`<figure class="embedded-asset" data-sys-asset-uid="…">`) paths invoke this handler.

6. **`customElementTypes` handler signature**: `(attrs: string, child: string, jsonBlock: IAnyObject, extraProps?: object) => string`
   - `attrs` — pre-serialized HTML attribute string
   - `child` — pre-serialized inner HTML of children
   - `jsonBlock` — raw node; read `jsonBlock.attrs`, `jsonBlock.type`, custom metadata
   - **Return an HTML string**, not a React element

7. **Match keys to node `type` exactly.** Keys in `customElementTypes` must equal the `type` string on the JSON RTE node emitted by Contentstack, byte-for-byte. `callout` will not match `"Callout"` or `"custom-callout"`. Use a standard tag name (`h2`, `a`, `ul`) to override the default rendering for that tag.

8. **Declare the prop in your component schema as `json_rte`.** Studio creates a `JsonRTEProp` and binds it to the field like any other prop — your component code stays JSON-RTE-agnostic.

9. **Render the resulting HTML** in your component via `dangerouslySetInnerHTML`, since the serializer emits an HTML string:

   ```tsx
   export function Article({ body }: { body: string }) {
     return <div className="prose" dangerouslySetInnerHTML={{ __html: body }} />;
   }
   ```

10. **(Optional) Inspect current config** — three internal readers used by hooks:
    - `getJSONRTE()` — returns `IJsonToHtmlOptions` (without `embeddedEntry`/`embeddedAsset`)
    - `getEmbeddedEntryRenderer()` — returns the registered entry renderer or `null`
    - `getEmbeddedAssetRenderer()` — returns the registered asset renderer or `null` (falls back to the SDK default if not registered)

    All three import from `@contentstack/studio-client` (not `@contentstack/studio-react`, which only re-exports the registration functions).

## Inputs needed from the user

1. `embeddedContentTypes` — list of CTs the RTE field can embed (so the `embeddedEntry` callback can branch on `contentTypeUid` per CT).
2. `customElementTypes` — list of custom node `type` values you need to render. Pull these from the actual entry JSON, not from guesses.
3. `overrideTags` — optional list of standard tags whose default HTML you want to replace.

If none of the three is provided, ask the user whether they actually need this skill — the default serializer + default asset renderer may already cover their JSON RTE.

## Acceptance

This skill succeeds only when ALL of the following are true:

- [ ] `registerRTERenderer({...})` is called once, in the bootstrap module, before any `<StudioComposition />` or `<StudioComponent />` mounts.
- [ ] If embedded entries are in scope: the `embeddedEntry` handler branches on `contentTypeUid` and/or `displayType` and returns an HTML string per case.
- [ ] If embedded assets need custom markup: the `embeddedAsset` handler returns an HTML string; otherwise the default is acceptable.
- [ ] Every declared custom element type has a handler returning an HTML string (not React).
- [ ] Handler keys match the raw `type` values in the entry JSON exactly.
- [ ] Components consuming the prop render it via `dangerouslySetInnerHTML` (no escaped HTML visible on the page).
- [ ] `getJSONRTE()` returns the serializer options; `getEmbeddedEntryRenderer()` returns the entry renderer.
- [ ] Rendering a composition bound to the `json_rte` field shows custom node markup AND embedded-entry markup AND custom-asset markup in the DOM; standard nodes still render via their defaults.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Using `registerJSONRTE` for new code | Deprecated; `registerRTERenderer` is the unified canonical API | Use `registerRTERenderer`. Existing `registerJSONRTE` calls still work — migrate when you next touch the file. |
| Embedded entry renders blank or as a placeholder | No `embeddedEntry` handler is registered (default renders nothing for entry embeds) | Register `embeddedEntry: ({ entry, contentTypeUid, displayType }) => html` |
| `embeddedEntry` returns a React element / JSX | Serializer is HTML-string based; React objects stringify to `[object Object]` | Return a plain HTML string from the handler |
| Calling `registerRTERenderer` more than once | Each call REPLACES the full config; later calls drop earlier `customElementTypes` / `embeddedEntry` | Build a single merged config and call once at bootstrap. Or use `registerJSONRTE` for serializer-only updates (it preserves existing `embeddedEntry`/`embeddedAsset`) — but the right answer is "register everything in one call." |
| Registering too late | After props resolve, re-registering does not retroactively re-render | Always register at bootstrap, before any composition mount |
| Wrong key name in `customElementTypes` | Keys must match the raw `type` in entry JSON, not the editor's display label | Verify against the actual entry JSON |
| Forgetting `dangerouslySetInnerHTML` | The page renders escaped HTML as visible text | Render the prop via `dangerouslySetInnerHTML` |
| Registering standard types unnecessarily | Paragraphs, headings, lists, links, marks, images, tables already render | Only register to override or add |
| Branching `embeddedEntry` on entry shape instead of `contentTypeUid` | Fragile — entries may share field names across CTs | Use `contentTypeUid` as the primary branch key |
| API-authoring an entry with a `json_rte` embed reference node whose `attrs` omits `locale` | CMA rejects the write with `"Reference must contain content-type-uid, entry-uid, locale and display-type."` — the SDK's read path never surfaces this because it's a write-time validation | Every embedded-entry `reference` node under `json_rte` needs the full attr set: `{ type: "entry", "entry-uid": "…", "content-type-uid": "…", "display-type": "block"\|"inline"\|"link", "locale": "en-us" }`. Applies both to node-level RTE fields and `static_value.json_rte[*].value` embeds (mirrors `provision-studio-project` § *`static_value` sub-schema* JSON-RTE row) |

## See also

- Pair with `install-studio` (must run first so `studioSdk.init` exists).
- `docs/20-bring-your-own-components/json-rte-custom-element-rendering.md` for the full prop / serializer reference.
