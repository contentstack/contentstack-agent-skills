---
name: author-composition-entry
---

## When to use

Write the composition entry itself: the CMA body, and the `url` + `url_metadata` matched pair. Read before the first POST. `static_value` resolution is in [`author-composition-static-values`](author-composition-static-values.md).

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## The composition entry: what you actually write to the CMA

A composition is a single entry on the compositions CT. The fields (see [`author-composition-templates`](author-composition-templates.md) § Complete example for a real published Freeform composition):

| Field | Type | Holds |
|---|---|---|
| `title` | string | Display name in the Compositions list |
| `url` | string | URL pattern (e.g. `/products/{{entry.slug}}` for Connected. A fixed path like `/campaigns/spring-2026` for Freeform). Populated for both kinds |
| `composable_uid` | string | Composable identity for the composition. Must be **unique across the compositions CT**. Studio's UI fills it from the name as a readable slug (`"spring_2026_landing"`). The entry uid also works. The runtime resolves pages and embeds by `composable_uid`. **It never places a section:** a template's `section-composition` node references the section by its entry uid (`metadata.compositionUID: "blt…"`), and a `composable_uid` there fails with `Component with type '<it>' is not registered`. A mismatch produces "Composition Not Found" |
| `connected_content_type` | string | The CT this template binds to (Connected only). Empty string `""` for Freeform / sections |
| `place_composition_as` | string | `"page"` for a template composition (Connected or Freeform). `"section"` for a section composition. `"template"` also legal but not what Studio writes for the top-level template composition. The Compositions tab lists `"page"` entries under Templates |
| `schema_version` | string | Composition schema version stamped by Studio (`"1.0.0"`, `"1"`, `"2"`, …), a **string**, not a number |
| `ui` | string | The compressed composition tree, `zlib:<base64>` (see `troubleshoot-canvas` § Diagnostic tooling) |
| `data_sources` | JSON string | The stringified `resolvedReferences` map + pinned data-source list. Wire shape is `"[]"` when empty, not `[]` |
| `static_value` | group | Per-key literal store. Every `binding.type: "static_value"` on a node references a **key** here. The actual literal lives in `static_value.<subtype>[]` under that key. See [`author-composition-static-values`](author-composition-static-values.md) |
| `url_metadata` | group | **Required on every template composition** (`place_composition_as: "page"`): `url_source` + `url_queries`. Never write `url` without it. See § `url` + `url_metadata`: a matched pair below. Sections carry neither `url` nor `url_metadata` |
| `linked_schemas` | **group-multiple** | Sections only. Declares parent CT + `selectedField` the section scopes to. `[]` for templates / freeform |
| `linked_sections` | reference (multiple) | Template's references to section-composition entries placed in its `ui` tree. `[]` for freeform / sections |
| `ui_preview` | file (asset uid) | **Required on every section composition** (`place_composition_as: "section"`). The editor writes this for itself by screenshotting the canvas on save. **The CMA never populates it**, so an API-created Section stays blank in the Sections palette forever and nothing errors. Supply an asset uid. See [`author-composition-thumbnails`](author-composition-thumbnails.md) § Fix C for the calls. Templates don't need it |

After write, publish the entry. Studio queries by `composable_uid` + published status. An unpublished entry won't appear in the project's Compositions list or load in the canvas.

**A section write is not finished until `ui_preview` is set.** It fails the way publish state does (silently, with a correct-looking `200` and a page that renders), so it is invisible until an author opens the palette and finds unlabeled gray tiles. Set it in the same pass as the create, per [`author-composition-thumbnails`](author-composition-thumbnails.md): screenshot or generate the image, `POST /v3/assets`, then `PUT { entry: { ui_preview: <assetUid> } }`. Batching it to "later" is how a whole project ends up with none. Measured: 254 API-authored Sections in one project, zero thumbnails, while the UI-authored Sections beside them all had one.

**Reading publish state back requires an explicit flag.** A plain `GET /v3/content_types/<ct>/entries/<uid>` returns **no `publish_details`**. The field is simply absent, which reads identically to "not published" and makes the verification step above unfalsifiable. Ask for it:

```bash
curl -s "https://<cma-host>/v3/content_types/<ct-uid>/entries/<entry-uid>?include_publish_details=true" \
  -H "api_key: <stack-api-key>" -H "$CS_AUTH" | jq '.entry.publish_details'
```

A published entry returns an array with one object per environment/locale. `[]` or `null` means not published to anything. Same flag applies when listing entries.

<a id="url-metadata-matched-pair"></a>

### `url` + `url_metadata`: a matched pair, never one without the other

**Rule: any entry you write with `place_composition_as: "page"` gets BOTH `url` and `url_metadata`. No exceptions, no "minimal envelope" shortcut.**

`url` is the pattern. `url_metadata.url_source` is how the pattern is derived. Write the pattern alone and Studio has no derivation to read, so the composition behaves as the `legacy_url` source (the pre-variable wildcard mode) regardless of what the pattern actually contains.

**Why this matters.** Omitting `url_metadata` doesn't fail the CMA write and often doesn't break delivery either: a Connected template with `url: "{{entry.url}}"` can return 200 on the live route off the pattern alone. That green page is exactly what makes the omission expensive. It's discovered later, in the editor, not at write time:

- **Studio's URL panel loses the derivation.** The editor can't show that the URL comes from the connected CT's `url_pattern`, so the Edit-URL modal renders it as an opaque hand-typed string. First author who touches it re-authors the pattern by hand and the CT link is gone for good.
- **Candidate-set risk.** The SDK's composition-candidate query filters on `url_metadata.$exists: true` (see [`troubleshoot-composition-resolution` § Symptom-to-stage matrix](troubleshoot-composition-resolution.md)). A composition with no `url_metadata` at all is not guaranteed to enter the candidate set. One code path resolving it today is not the same as every path resolving it.
- **`legacy_url` semantics are stricter.** They match against a `url` field populated on every entry, with a leading slash. A pattern written for `content_type_url_pattern` semantics but resolved under `legacy_url` fails the moment the entry set grows past the one you tested.

#### Which `url_source` to write

| Composition | `url` | `url_source` | Notes |
|---|---|---|---|
| **Connected** template, CT is a page type (`is_page: true` + CT `url_pattern`) | `/<route>/{{entry.title}}` | `content_type_url_pattern` | **The default for the API path.** The CT pattern is the derivation, so Studio re-derives correctly on every editor load. Pair with CT `url_prefix: "/<route>/"`. See [`build-connected-template` § Single-entry vs multi-entry URL pattern rule](build-connected-template.md#single-entry-vs-multi-entry-url-pattern-rule) |
| **Connected** template, CT **has** a `url_pattern` (entries get a real `url`) | `/<route>/{{entry.title}}` | `content_type_url_pattern` | Resolution keys on **`entry.url`**: the SDK finds the entry whose stored `url` equals the request path, so write the template `url` in the shape of a real entry's `url` (read one first; a CT `url_prefix` the stored `url` lacks misses with `PREVIEW_ENTRY_NOT_FOUND`). The composition `url` is NOT variable-substituted under this source (see below). Requires every entry to carry a populated `url` |
| **Connected** template, **singleton** CT with no `url_pattern` (homepage, pricing, a one-entry rewards page) | `/rewards` (literal) | `content_type_url_pattern`, **but only if you populate `url` on the entry by hand** | The source's real requirement is a non-empty `url` field on at least one entry, not a CT `url_pattern`. A singleton has no pattern to generate one, so set `url: "/rewards"` on the entry yourself. Skip that and the editor fails with `MISSING_CT_PATTERN_URL_FIELD`, shown as "No entry has a URL field populated yet", while SSR renders the page fine |
| **Connected** template whose URL derives from a field **other than** `url` (`{{entry.slug}}`, `{{entry.author.slug}}`) | `/blog/{{entry.slug}}` | `user_specified_pattern` | This is the only source that extracts and matches on pattern variables. `content_type_url_pattern` would ignore the pattern and look for `url` instead |
| **Freeform** template, identity URL | `/<compositions-CT-uid>/<composable_uid>` | `default_url_pattern` | The Studio-generated default. Use this unless the path was deliberately hand-chosen |
| **Freeform** template, hand-chosen path | `/campaigns/spring-2026` | `user_specified_pattern` | Semantically correct: there's no CT to derive from. Write `url_queries` explicitly. Nothing else generates it on the API path |
| **Connected** template, hand-typed **variable** pattern on a CT that does have a `url_pattern` | - | Avoid, prefer `content_type_url_pattern` | Here `user_specified_pattern` reverts: `url_queries` is generated by the UI's Edit-URL then Save flow and Studio re-derives from the CT pattern on load. Use `content_type_url_pattern`. See [`build-connected-template` § URL traps (c)](build-connected-template.md). **This is not a blanket ban on `user_specified_pattern` for Connected**. It's the correct source when the CT has no pattern to derive from (row above) |
| **Section** (`place_composition_as: "section"`) | (omit) | (omit) | Sections have no URL. Don't invent one |

`custom_preview_url` (in Stack, under Visual Experience) and `legacy_url` (match a `url` field on every entry) are the two remaining values. Neither is something you write by hand on the API path: `custom_preview_url` is stack config, `legacy_url` is the state you fall into by accident.

#### What each `url_source` actually does: and the editor error it produces

Observed behavior in the Studio editor: the editor picks a **preview entry** by querying the connected CT, and the query shape depends entirely on `url_source`:

| `url_source` | Editor's query | Variable substitution? | Error when nothing matches |
|---|---|---|---|
| `content_type_url_pattern` | Fixed: **`url` field existence** (`requiredVariables: ["url"]`), no field predicates | **No** | `MISSING_CT_PATTERN_URL_FIELD`, shown as "No entry has a URL field populated yet" |
| `legacy_url` | Same fixed `url`-existence query | **No** | `MISSING_LINKED_URL_FIELD` |
| `user_specified_pattern` | Extracts `{{entry.x}}` variables from the pattern and matches entries on those fields | **Yes** | `NO_ENTRY_WITH_ALL_VARIABLES` |

Two consequences that bite in practice:

1. **`content_type_url_pattern` does not substitute your pattern.** `{{entry.title}}` in the composition `url` is display/matching metadata. The editor resolves purely off the entry's **`url` field**. The requirement is therefore "at least one entry has a non-empty `url`", **not** "the CT has a `url_pattern`". Two ways to satisfy it: a CT `url_pattern` (the usual route for multi-entry CTs), or setting `url` by hand (the route for a singleton). Satisfy neither and the editor dead-ends on "No entry has a URL field populated yet" while SSR keeps rendering. The mismatch reads as a Studio bug and isn't one.
2. **`user_specified_pattern` is the substituting branch.** Pick it when the URL derives from fields other than `url` (`{{entry.slug}}`, a reference field) or for a freeform hand-chosen path. It's wrong for a multi-entry CT that already has a `url_pattern`. Studio re-derives and the hand-set metadata reverts.

<a id="editor-vs-ssr-url-derivation"></a>

#### Editor vs SSR: an API-authored template can render live and still refuse to open

`prepareResolution` bails with `no-fetch` / reason `no-composition` when the composition has **no `url_metadata` at all**. The editor then has nothing to derive a preview URL from, so the template won't open, while SSR resolves the same composition off the `url` pattern and the entry's `url` and serves the page perfectly.

Same asymmetry family as `linked_sections` and `ui_preview`: the editor depends on metadata the UI writes for itself and the API path silently omits. **A passing SSR render is not evidence the template opens in Studio.** Verify both: load the route AND open the template in the editor. Cross-reference [`troubleshoot-composition-resolution` § Editor vs SSR: URL derivation](troubleshoot-composition-resolution.md#editor-vs-ssr-url-derivation).

#### Two authoring hazards worth avoiding up front

- **Bare `{{entry.url}}` with no literal prefix** matches every path. Fine with one template. The moment a second exists it wins or ties on specificity and swallows the other's URLs (ties break by `composable_uid`, deterministic but arbitrary). Give every template a literal segment. See [`setup-template-preview-routes` § Bare `{{entry.url}}` catch-all](setup-template-preview-routes.md#bare-entry-url-hazard).
- **Don't put a locale in the composition `url`.** Locale is a context variable (`{{locale}}`), not part of the stored path. Studio composes `<env base URL> + <composition url>`. On a locale-prefixed app (`next-intl`, `localePrefix: "always"`) the unprefixed path 307-redirects and the preview iframe dies on the redirect. Carry locale via the env base URL or the SDK `locale` option instead.

#### The wire shape

`url_metadata` is a **group with two text sub-fields**. `url_queries` is a **JSON string, not an object**. Send an object and the CMA rejects with a 422 type mismatch:

```jsonc
// Connected template — CT is a page type
"url": "/blog/{{entry.title}}",
"url_metadata": {
  "url_source": "content_type_url_pattern",
  "url_queries": "{\"include\":[],\"only\":{},\"where\":{}}"
}
```

```jsonc
// Freeform template — identity URL
"url": "/compositions/spring_2026_landing",
"url_metadata": {
  "url_source": "default_url_pattern",
  "url_queries": "{\"include\":[],\"only\":{},\"where\":{}}"
}
```

Leave `include` as `[]`. Reference expansion for URL variables like `{{entry.author.slug}}` is driven by `data_sources[template].resolvedReferences`, not by `url_queries.include`. A bare `""` for `url_queries` is also accepted alongside `content_type_url_pattern` (that's the shape in the verified multi-entry recipe). Prefer the explicit `{include, only, where}` JSON string, which is what the UI writes.

**Precondition: the CT must model the field.** If the project's compositions CT has no `url_metadata` group with `url_source` + `url_queries` sub-fields, the CMA **silently drops** the object on write: the POST returns 201, the entry reads back with no `url_metadata`, and you're in the `legacy_url` case with no error anywhere. Verify the CT first. See [`provision-studio-project`](provision-studio-project.md). Read the field back after your first write.

### `static_value` bindings: write two places

A `static_value` binding stores a key. The literal lives in the entry's `static_value.<subtype>[]` under that key, so write both, in the subtype matching the prop's `type`. Full rules: [`author-composition-static-values`](author-composition-static-values.md).
