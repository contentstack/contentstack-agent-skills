# Contentful → Contentstack Migration Context (for AI Agents)

> **Purpose of this file.** This is a reference context document for AI coding models tasked
> with migrating a **web application that consumes Contentful** so that it consumes
> **Contentstack** instead. It maps concepts, SDK APIs, query operators, field types,
> rich-text rendering, assets, locales and pagination from the Contentful JS SDKs to the
> Contentstack TypeScript Delivery SDK (`@contentstack/delivery-sdk`) and its helper
> library (`@contentstack/utils`).
>
> **It covers all the common ways a web app consumes Contentful, not just one SDK:**
> the REST Delivery SDK (`contentful`), the **GraphQL** Content API (§17), **Live Preview /
> draft mode** (§18), raw REST / `fetch` access and framework source plugins (§19). Always
> begin by detecting which approach(es) the target app uses (§0.1) and migrate **like-for-like**
> — REST→REST, GraphQL→GraphQL, preview→preview — preserving the app's language and framework.
>
> **Scope:** _application / SDK code migration_ — i.e. rewriting the data-fetching and
> rendering layer of a website. It is **not** a content/data ETL guide (moving entries
> between stacks is a separate task done via the Contentstack Management API / CLI / import
> tooling). Where content-modeling concepts are mentioned, they exist only to help the agent
> map the response shapes correctly.

---

## 0. How an AI agent should use this document

0. **Detect language, framework, and data-access approach first (§0.1).** Migrate in the
   *same* language and framework, and preserve the *same* data-access style (REST SDK →
   Delivery SDK; GraphQL → Contentstack GraphQL; raw fetch → raw fetch). Do not change paradigms.
1. **Identify the Contentful surface in the target app.** Search the codebase for
   `from 'contentful'`, `from 'contentful-management'`, `createClient`, `getEntries`,
   `getEntry`, `getAssets`, `.fields.`, `.sys.`, `@contentful/rich-text-*`, and image URLs
   on `fields.file.url`. Also search for GraphQL (`graphql.contentful.com`, `gql`,
   `@apollo/client`, `urql`, `graphql-request`, `*.graphql`) and Live Preview
   (`preview.contentful.com`, CPA token, `@contentful/live-preview`, `draftMode`).
2. **Classify each call site** using the mapping tables below (client init, read, query,
   reference resolution, rich text, asset/image, locale, pagination) — and the approach-specific
   sections (§17 GraphQL, §18 Live Preview, §19 raw REST / frameworks).
3. **Rewrite each call site** to the Contentstack equivalent, paying special attention to
   the **response-shape differences** (Section 6) — this is the single largest source of
   migration bugs. Contentful nests content under `sys`/`fields`; Contentstack flattens it.
4. **Migrate rendering** (rich text, images) using `@contentstack/utils` (Section 9–10).
5. **Migrate Live Preview / draft mode** (§18) if the source app implements it.
6. **Verify** against the gotchas (Section 13) and the checklist (Section 15).

### 0.1 Detect the data-access approach (decide the migration path)

| Signal found in the source app | Contentful approach | Migrate to | See |
|---|---|---|---|
| `import { createClient } from 'contentful'`, `getEntry(s)`, `getAsset(s)` | REST Delivery SDK (CDA) | `@contentstack/delivery-sdk` builder | §1–§16 |
| `graphql.contentful.com`, `gql`/`*.graphql`, Apollo/urql/graphql-request | GraphQL Content API | Contentstack GraphQL Content Delivery API (same GraphQL client) | §17 |
| `host: 'preview.contentful.com'`, CPA token, `@contentful/live-preview`, `useContentfulLiveUpdates`, Next `draftMode` | Live Preview / draft mode | Contentstack Live Preview (`live_preview` config + `@contentstack/live-preview-utils`) | §18 |
| Raw `fetch`/`axios` to `cdn.contentful.com/...`, or `gatsby-source-contentful` | Direct REST / build-time source plugin | Contentstack REST endpoints / `@contentstack/gatsby-source-contentstack` | §19 |
| `import 'contentful-management'` | Management API (editorial tooling) | `@contentstack/management` (out of scope here; note it) | §1 |

A single app may use **several** of these at once (e.g. GraphQL for reads + Live Preview for
the editor). Migrate each surface in kind.

**Golden rule:** Contentful and Contentstack are both API-first headless CMSs with a similar
mental model (a *space/stack* contains *content types*, *entries*, and *assets*, published to
*environments*). The migration is mostly mechanical *if* the response-shape and
field-addressing differences are handled rigorously.

---

## 1. Package & import mapping

| Concern | Contentful | Contentstack |
|---|---|---|
| Content **delivery** (read) SDK | `contentful` (CDA/CPA) | `@contentstack/delivery-sdk` |
| Content **management** (write) SDK | `contentful-management` (CMA) | `@contentstack/management` (out of scope here) |
| Shared HTTP/core layer (internal) | `contentful-sdk-core` | `@contentstack/core` |
| Rich-text / utility rendering | `@contentful/rich-text-html-renderer`, `@contentful/rich-text-react-renderer`, `@contentful/rich-text-types` | `@contentstack/utils` |

```bash
# remove
npm uninstall contentful contentful-management \
  @contentful/rich-text-html-renderer @contentful/rich-text-react-renderer @contentful/rich-text-types

# add
npm install @contentstack/delivery-sdk @contentstack/utils
# optional, only if cache policies are used:
npm install @contentstack/persistence-plugin
```

```ts
// Contentful
import { createClient } from 'contentful'

// Contentstack
import contentstack from '@contentstack/delivery-sdk'
import * as Utils from '@contentstack/utils'      // rich text, embedded items
```

> A web app that *reads* content uses the Contentful **CDA** SDK (`contentful`). Some apps
> also use `contentful-management` (CMA) for previews or editorial tooling. This document
> focuses on the read path (CDA → Contentstack Delivery). The CMA query/entity model
> (`client.entry.getMany({ spaceId, environmentId, query })`) shares the same query-operator
> and data-model semantics described below.

---

## 2. Terminology mapping

| Contentful | Contentstack | Notes |
|---|---|---|
| Space | Stack | Top-level content container. |
| Space ID | API Key | Identifies the container in client init. |
| Content Delivery API token (CDA) | Delivery Token | Read token. |
| Content Preview API token (CPA) | Delivery Token of a *preview* / Live Preview token | Preview handled via `live_preview` config. |
| Environment (`master`, …) | Environment | Both publish to named environments. Required in Contentstack init. |
| Content Type | Content Type | Same concept. UID identifies it. |
| Entry | Entry | Same concept. |
| Asset | Asset | Media file. |
| Field | Field | Addressed differently (see §6). |
| `sys.id` | `uid` | Stable identifier of an entry/asset/content type. |
| Locale (`en-US`) | Locale (`en-us`) | Contentstack locale codes are lower-cased (`en-us`, `fr-fr`). |
| Tag | Tag | Contentstack also has Taxonomies (richer). |
| Rich Text (RichText document) | JSON RTE / Supercharged RTE | Different JSON shape & renderer (see §9). |
| Reference (Link) | Reference field | Resolved via `includeReference` instead of `include` depth. |
| Modular content (Array of links) | Modular Blocks / Reference | — |
| Region/host | Region/host | Contentstack uses an explicit `Region` enum (US/EU/AU/Azure/GCP). |

---

## 3. Client initialization

### Contentful (CDA)
```ts
import { createClient } from 'contentful'

const client = createClient({
  space: 'SPACE_ID',
  accessToken: 'CDA_TOKEN',
  environment: 'master',          // optional, defaults to 'master'
  host: 'cdn.contentful.com',     // 'preview.contentful.com' for CPA
})
```

### Contentstack (Delivery)
```ts
import contentstack, { Region } from '@contentstack/delivery-sdk'

const stack = contentstack.stack({
  apiKey: 'API_KEY',              // was: space
  deliveryToken: 'DELIVERY_TOKEN',// was: accessToken
  environment: 'production',      // REQUIRED (no default)
  region: Region.US,              // US (default) | EU | AU | AZURE_NA | AZURE_EU | GCP_NA | GCP_EU
  locale: 'en-us',                // optional default locale
  // host: 'custom-cdn.example.com', // optional; overrides region host
  // branch: 'main',                 // optional branch
})
```

**Key init differences (verified against `src/stack/contentstack.ts`):**
- `apiKey`, `deliveryToken`, **and `environment` are all required**; the SDK throws on init if
  any is missing. Contentful only requires `space` + `accessToken`.
- Region is a first-class enum. Don't hardcode hostnames unless you need a custom host.
  Region → host: `US → cdn.contentstack.io`, `EU → eu-cdn.contentstack.com`,
  `AU → au-cdn.contentstack.com`, `AZURE_NA → azure-na-cdn.contentstack.com`,
  `AZURE_EU → azure-eu-cdn.contentstack.com`, `GCP_NA → gcp-na-cdn.contentstack.com`,
  `GCP_EU → gcp-eu-cdn.contentstack.com`.
- Preview: Contentful switches `host` to `preview.contentful.com` with a CPA token.
  Contentstack uses a `live_preview` config object + `stack.livePreviewQuery(...)` instead.
- The Contentstack client is a builder: you start from `stack.contentType(uid)` /
  `stack.asset(uid)` and chain. There is no flat `client.getEntries(...)`.

---

## 4. Reading content — method mapping

Contentstack uses a **fluent builder** rooted at the `stack`. Calls terminate in
`.fetch()` (single object) or `.find()` (collection/query).

| Operation | Contentful (CDA) | Contentstack |
|---|---|---|
| Single entry by id | `client.getEntry(entryId)` | `stack.contentType(ctUid).entry(entryUid).fetch<T>()` |
| Entries of a content type | `client.getEntries({ content_type: 'blog' })` | `stack.contentType('blog').entry().query().find<T>()` |
| All entries (filter on `content_type`) | `client.getEntries({ content_type })` | `stack.contentType(ctUid).entry().query()...find<T>()` |
| Single asset | `client.getAsset(assetId)` | `stack.asset(assetUid).fetch<T>()` |
| All assets | `client.getAssets(query)` | `stack.asset().query()...find<T>()` (or `stack.asset().find()`) |
| Single content type (schema) | `client.getContentType(id)` | `stack.contentType(uid).fetch<T>()` |
| All content types | `client.getContentTypes()` | `stack.contentType().find<T>()` |
| Sync API | `client.sync({ initial: true })` | `stack.sync({ ... })` |
| Global field (Contentstack-only) | — | `stack.globalField(uid).fetch()` / `stack.globalField().find()` |
| Taxonomy query (Contentstack-only) | — | `stack.taxonomy()` |

> **Important:** In Contentful, `content_type` is just a query parameter. In Contentstack,
> the content type UID is **part of the path** (`stack.contentType(uid)…`). A single
> Contentful `getEntries` call that mixed multiple content types must be split per content
> type in Contentstack, **or** use the asset/entry query without a content type only for assets.

### Canonical examples

```ts
// --- Single entry ---
// Contentful
const entry = await client.getEntry('blog123')
// Contentstack
const entry = await stack.contentType('blog_post').entry('blog123').fetch<BlogPost>()

// --- Collection ---
// Contentful
const res = await client.getEntries({ content_type: 'blog_post', limit: 10 })
res.items.forEach(...)
// Contentstack
const res = await stack.contentType('blog_post').entry().query().limit(10).find<BlogPost>()
res.entries?.forEach(...)
```

---

## 5. Query operator & modifier mapping

Contentful expresses queries as a flat params object with bracketed operators
(`'fields.price[gte]': 10`). Contentstack uses a `Query` builder obtained via
`stack.contentType(uid).entry().query()`, with explicit methods **or** the generic
`.where(fieldUid, QueryOperation.X, value)`.

Import the operator enums:
```ts
import { QueryOperation, QueryOperator } from '@contentstack/delivery-sdk'
```

### 5.1 Field comparison operators

| Meaning | Contentful param | Contentstack builder method | Contentstack `.where(...)` | Raw operator |
|---|---|---|---|---|
| Equals | `'fields.x': v` | `.equalTo('x', v)` | `.where('x', QueryOperation.EQUALS, v)` | (bare value) |
| Not equals | `'fields.x[ne]': v` | `.notEqualTo('x', v)` | `.where('x', QueryOperation.NOT_EQUALS, v)` | `$ne` |
| In set | `'fields.x[in]': 'a,b'` | `.containedIn('x', ['a','b'])` | `.where('x', QueryOperation.INCLUDES, ['a','b'])` | `$in` |
| Not in set | `'fields.x[nin]': 'a,b'` | `.notContainedIn('x', ['a','b'])` | `.where('x', QueryOperation.EXCLUDES, ['a','b'])` | `$nin` |
| Greater than | `'fields.x[gt]': v` | `.greaterThan('x', v)` | `.where('x', QueryOperation.IS_GREATER_THAN, v)` | `$gt` |
| Greater or equal | `'fields.x[gte]': v` | `.greaterThanOrEqualTo('x', v)` | `.where('x', QueryOperation.IS_GREATER_THAN_OR_EQUAL, v)` | `$gte` |
| Less than | `'fields.x[lt]': v` | `.lessThan('x', v)` | `.where('x', QueryOperation.IS_LESS_THAN, v)` | `$lt` |
| Less or equal | `'fields.x[lte]': v` | `.lessThanOrEqualTo('x', v)` | `.where('x', QueryOperation.IS_LESS_THAN_OR_EQUAL, v)` | `$lte` |
| Field exists | `'fields.x[exists]': true` | `.exists('x')` / `.notExists('x')` | `.where('x', QueryOperation.EXISTS, true)` | `$exists` |
| Regex / match | `'fields.x[match]': 'foo'` | `.regex('x', '^foo', 'i')` | `.where('x', QueryOperation.MATCHES, 'foo')` | `$regex` (+ `$options`) |
| Tags | `'metadata.tags.sys.id[in]': '...'` | `.tags(['t1','t2'])` | — | `tags` |
| Full-text search | `query: 'term'` | `.search('term')` | — | `typeahead` param |

> Notes:
> - Contentstack `.where(field, QueryOperation.EQUALS, v)` stores the bare value (no operator
>   wrapper), matching Contentful's bare `'fields.x': v`.
> - Contentstack has no direct equivalent to Contentful geo operators `[near]` / `[within]`
>   in the delivery builder; use `.where()`/`.addParams()` with the appropriate raw param if
>   geo querying is required.
> - Contentful `[all]` (array contains all) has no first-class builder method; model with
>   `$and` of `containedIn`/`equalTo` or `.addParams()`.

### 5.2 Logical combination

| Meaning | Contentful | Contentstack |
|---|---|---|
| AND of sub-queries | Multiple params are ANDed implicitly | `.and(q1, q2)` or `.queryOperator(QueryOperator.AND, q1, q2)` |
| OR of sub-queries | Not natively supported in a single CDA call (often multiple calls) | `.or(q1, q2)` or `.queryOperator(QueryOperator.OR, q1, q2)` |

```ts
// Contentstack OR example
const q1 = stack.contentType('blog').entry().query().equalTo('category', 'news')
const q2 = stack.contentType('blog').entry().query().greaterThan('views', 1000)
const res = await stack.contentType('blog').entry().query().or(q1, q2).find<BlogPost>()
```

### 5.3 Sorting, pagination, field selection

| Meaning | Contentful | Contentstack |
|---|---|---|
| Sort ascending | `order: 'fields.title'` | `.orderByAscending('title')` |
| Sort descending | `order: '-fields.title'` | `.orderByDescending('title')` |
| Limit | `limit: 10` | `.limit(10)` |
| Skip / offset | `skip: 20` | `.skip(20)` |
| Total count in result | `res.total` (always present) | `.includeCount()` → `res.count` |
| Select only fields | `select: 'fields.title,fields.slug'` | `.only(['title','slug'])` |
| Exclude fields | (no direct CDA param) | `.except(['body'])` |
| Arbitrary raw param | add key to query object | `.param(key, value)` / `.addParams({...})` |

> Contentstack `only`/`except` use a `BASE` scope under the hood
> (`only[BASE][]=title`); just pass field UIDs to the builder methods.
>
> **Placement (verified against source):** `.only()` / `.except()` live on `.entry()` /
> `.entries()` (and `.asset()`), **not** on the `.query()` object. Call them *before* `.query()`:
> `stack.contentType(ct).entry().only(['title','slug']).query().find<T>()`. Chaining
> `.query().only(...)` will fail.

---

## 6. Response shape mapping (MOST IMPORTANT)

This is where most migration bugs originate. **Contentful wraps content in `sys` + `fields`;
Contentstack returns a flat entry object.**

### 6.1 Single entry

**Contentful:**
```jsonc
{
  "sys": { "id": "blog123", "contentType": { "sys": { "id": "blogPost" } },
           "createdAt": "...", "updatedAt": "...", "locale": "en-US" },
  "fields": {                       // keyed by field id; flattened to one locale by default
    "title": "Hello",
    "slug": "hello",
    "author": { "sys": { "type": "Link", "linkType": "Entry", "id": "auth1" } }
  },
  "metadata": { "tags": [] }
}
// access: entry.fields.title, entry.sys.id, entry.sys.contentType.sys.id
```

**Contentstack (verified against `BaseEntry` in `src/common/types.ts`):**
```jsonc
{
  "uid": "blt...",                 // was sys.id
  "title": "Hello",                // fields are TOP-LEVEL, not under .fields
  "slug": "hello",
  "locale": "en-us",               // was sys.locale
  "created_at": "...",             // was sys.createdAt
  "updated_at": "...",             // was sys.updatedAt
  "_version": 3,
  "tags": [],
  "publish_details": { "environment": "...", "locale": "en-us", "time": "...", "user": "..." },
  "author": [ { /* resolved referenced entry */ } ]   // references are ARRAYS
}
// access: entry.title, entry.uid, entry.locale
```

### 6.2 Field address translation cheatsheet

| Contentful access | Contentstack access |
|---|---|
| `entry.fields.title` | `entry.title` |
| `entry.fields.<any>` | `entry.<any>` (drop the `.fields.` prefix) |
| `entry.sys.id` | `entry.uid` |
| `entry.sys.contentType.sys.id` | known from the path (`contentType(uid)`); or `_content_type_uid` on resolved references |
| `entry.sys.createdAt` / `updatedAt` | `entry.created_at` / `entry.updated_at` |
| `entry.sys.locale` | `entry.locale` |
| `entry.sys.revision` / `version` | `entry._version` |
| `entry.metadata.tags` | `entry.tags` (+ richer Taxonomy support) |

### 6.3 Collection result

| Contentful | Contentstack |
|---|---|
| `res.items` (array) | `res.entries` (array; `res.assets` for asset queries) |
| `res.total` | `res.count` (only when `.includeCount()` was called) |
| `res.skip` / `res.limit` | echoed in request; not returned the same way |
| `res.includes.Entry` / `.Asset` | resolved inline into entry fields via `includeReference` |

Contentstack `find<T>()` returns `FindResponse<T>`:
`{ entries?: T[]; assets?: T[]; content_types?: TContentType[]; count?: number }`.
`fetch<T>()` returns the single object directly (the SDK unwraps `response.entry` /
`response.asset` / `response.content_type` for you).

---

## 7. References / linked entries

**Contentful** auto-resolves links up to a depth using `include` (0–10, default 1) and
returns unresolved links plus an `includes` sidecar that the SDK stitches into `fields`.

**Contentstack** does **not** resolve references by default. You must explicitly request each
reference field by UID via `includeReference`. Resolved references appear **inline as arrays**
on the entry.

| Contentful | Contentstack |
|---|---|
| `getEntries({ content_type, include: 2 })` | `.includeReference('author', 'author.company')` (dot-path for nested) |
| automatic link resolution | explicit per-field `includeReference(...)` |
| `res.includes.Entry/Asset` | inline arrays on the resolved field |
| `links_to_entry` (reverse lookup) | `.whereIn(refUid, subQuery)` / `.referenceIn(field, subQuery)` |
| reference NOT matching | `.whereNotIn(...)` / `.referenceNotIn(...)` |
| include content type uid of refs | `.includeReferenceContentTypeUID()` |

```ts
// Contentful: depth-based
const res = await client.getEntries({ content_type: 'blog', include: 2 })
const authorName = res.items[0].fields.author.fields.name

// Contentstack: explicit, references resolve to arrays
const res = await stack.contentType('blog').entry().query()
  .includeReference('author', 'author.company')
  .find<BlogPost>()
const authorName = res.entries?.[0].author?.[0]?.name   // note the [0] — references are arrays
```

> **Migration pitfall:** A single Contentful reference becomes a **single-element array** in
> Contentstack. Code that did `entry.fields.author.fields.name` becomes
> `entry.author?.[0]?.name`. Audit every dereference.

Related include modifiers (verified in `entries.ts` / `entry.ts`):
`includeContentType()`, `includeEmbeddedItems()` (RTE embedded entries/assets),
`includeFallback()` (locale fallback), `includeMetadata()`, `includeBranch()`,
`includeSchema()`.

---

## 8. Field-type mapping (for response handling)

Contentful field `type` values (verified in `lib/entities/content-type-fields.ts`) map to
Contentstack `data_type` equivalents. Content modeling itself happens in the Contentstack UI /
Management API; this table helps the agent reason about **what a field will look like in the
response** and how to render it.

| Contentful field `type` | Contentstack equivalent (`data_type`) | Response/handling notes |
|---|---|---|
| `Symbol` (short text) | `text` (single line) | plain string |
| `Text` (long text) | `text` (multiline) | plain string |
| `RichText` | `json` (JSON RTE) | different JSON shape → render with `@contentstack/utils` (§9) |
| `Integer` | `number` | number |
| `Number` (decimal) | `number` | number |
| `Date` | `isodate` | ISO date string |
| `Boolean` | `boolean` | boolean |
| `Location` (lat/lon) | `group` (lat/lng) | object shape differs |
| `Object` (JSON) | `json` | arbitrary JSON |
| `Link` → `Entry` | `reference` | array of resolved entries (with `includeReference`) |
| `Link` → `Asset` | `file` | asset object (see §10) |
| `Array` of `Symbol` | `text` (multiple) | array of strings |
| `Array` of `Link<Entry>` | `reference` (multiple) | array of entries |
| `Array` of `Link<Asset>` | `file` (multiple) | array of assets |
| (component/embedded) | `group` / `global_field` / `blocks` (Modular Blocks) | nested object/array |
| `ResourceLink` (cross-space) | reference / external | re-model as needed |
| `metadata.tags` | `tags` / Taxonomy | — |

---

## 9. Rich text rendering

This is a substantial change. **The JSON document shapes are different and the renderers are
different.** Contentful RichText is a `@contentful/rich-text-types` document; Contentstack
uses JSON RTE (Supercharged RTE) rendered via `@contentstack/utils`.

| Concern | Contentful | Contentstack (`@contentstack/utils`) |
|---|---|---|
| Field type | `RichText` (document JSON) | JSON RTE (`json` data_type) |
| HTML string render | `documentToHtmlString(doc, options)` from `@contentful/rich-text-html-renderer` | `Utils.jsonToHTML({ entry, paths, renderOption })` |
| React / component render | `documentToReactComponents(doc, options)` from `@contentful/rich-text-react-renderer` (returns a **component tree**) | `@contentstack/utils` emits **HTML strings only** — there is no React/Vue/Angular component renderer. Inject the HTML (`dangerouslySetInnerHTML` / `v-html` / `[innerHTML]`), or use a dedicated JSON-RTE→component serializer for the framework. `Utils.render` does **not** return JSX. |
| Embedded entries/assets | `BLOCKS.EMBEDDED_ENTRY`, `INLINES.EMBEDDED_ENTRY`, `BLOCKS.EMBEDDED_ASSET` handled in `renderNode` | request with `.includeEmbeddedItems()`, then `Utils.render({ entry, renderOption })` |
| Node/mark customization | `options.renderNode` / `options.renderMark` keyed by `BLOCKS`/`INLINES`/`MARKS` | `renderOption` object keyed by node tag (`p`, `h1`, `a`, …), marks (`bold`), `block`, `inline`, `reference`, `display`, `default` |

```ts
// Contentful
import { documentToHtmlString } from '@contentful/rich-text-html-renderer'
const html = documentToHtmlString(entry.fields.body)

// Contentstack
import * as Utils from '@contentstack/utils'
const renderOption = {
  p:   (node, next) => `<p>${next(node.children)}</p>`,
  h1:  (node, next) => `<h1>${next(node.children)}</h1>`,
  bold:(text) => `<b>${text}</b>`,
  a:   (node) => {
    const txt = node.children.map((c) => c.text || '').join('')
    return `<a href="${node.attrs.url}">${txt}</a>`
  },
}
// For Supercharged/JSON RTE fields (MUTATES `entry` in place; returns void):
Utils.jsonToHTML({ entry, paths: ['body', 'group.rte_field'], renderOption })
// For HTML-RTE embedded items (fetch with .includeEmbeddedItems() first):
// NOTE: the option key is `paths` (plural string[]), NOT `path`. Also mutates `entry` in place.
Utils.render({ entry, paths: ['body'], renderOption })
// To render a raw RTE string/array and RECEIVE the HTML back (no mutation): Utils.renderContent(content, option)
```

> Steps for the agent:
> 1. Add `.includeEmbeddedItems()` to any entry/entries fetch that renders RTE with embeds.
> 2. Replace `documentToHtmlString(entry.fields.body)` with
>    `Utils.jsonToHTML({ entry, paths: ['body'], renderOption })` (note: it mutates/returns
>    HTML keyed onto the field path; pass the whole `entry`, not just the field value).
> 3. Translate `renderNode`/`renderMark` handlers into the `renderOption` shape.

---

## 10. Assets & image transformations

### 10.1 Asset shape

| Contentful | Contentstack |
|---|---|
| `asset.fields.file.url` (often protocol-relative `//...`) | `asset.url` (absolute) |
| `asset.fields.file.fileName` | `asset.filename` |
| `asset.fields.file.contentType` | `asset.content_type` |
| `asset.fields.file.details.size` | `asset.file_size` |
| `asset.fields.file.details.image.{width,height}` | use `.includeDimension()` on asset fetch → `asset.dimension` |
| `asset.fields.title` | `asset.title` |
| `asset.sys.id` | `asset.uid` |

```ts
// Contentful
const url = 'https:' + asset.fields.file.url
// Contentstack
const url = asset.url
```

### 10.2 Image API / transforms

Both support URL-based image manipulation, but param names differ. Contentstack provides an
`ImageTransform` builder (`@contentstack/delivery-sdk`) and a `String.prototype.transform`
helper.

| Transform | Contentful query param | Contentstack `ImageTransform` method |
|---|---|---|
| Width / height / resize | `?w=300&h=200` | `.resize({ width: 300, height: 200 })` |
| Format | `?fm=webp` | `.format(Format.WEBP)` |
| Quality | `?q=80` | `.quality(80)` |
| Fit / crop | `?fit=fill` / `?f=crop` | `.fit(FitBy.CROP)` / `.crop({...})` |
| Auto optimize | `?fm=webp` (manual) | `.auto()` |
| Background | `?bg=...` | `.bgColor('cccccc')` |
| DPR | `?dpr=2` | `.dpr(2)` |
| Blur / sharpen | `?blur=` / — | `.blur(n)` / `.sharpen(a,r,t)` |
| Orientation | `?or=` | `.orient(Orientation.RIGHT)` |
| Trim / pad / overlay / canvas | `?trim=` etc. | `.trim()`, `.padding()`, `.overlay({...})`, `.canvas({...})` |

```ts
import { ImageTransform, Format } from '@contentstack/delivery-sdk'
const t = new ImageTransform().resize({ width: 300, height: 200 }).format(Format.WEBP).quality(80)
const optimized = asset.url.transform(t)   // String.prototype.transform helper (loaded by the SDK)
```

> **Caveat (verified in source):** `Format` is a runtime value export, but at the package root
> `ImageTransform` is currently re-exported **type-only** (`export type { ImageTransform }` in
> `index.ts`). If `new ImageTransform()` from the package root fails at runtime, import the
> value class from the assets module (the SDK's own tests use
> `import { ImageTransform } from '@contentstack/delivery-sdk/dist/.../assets'`), or build the
> transform URL by appending the documented image-delivery query params directly
> (`?width=300&height=200&format=webp&quality=80`). The `String.prototype.transform` helper is
> installed when the SDK is imported (`import './common/string-extensions'`).

---

## 11. Locales / localization

| Concern | Contentful | Contentstack |
|---|---|---|
| Locale code style | `en-US`, `fr-FR` | `en-us`, `fr-fr` (lower-cased) |
| Per-request locale | `getEntries({ locale: 'fr-FR' })` | `.locale('fr-fr')` on entry/entries/asset |
| Default locale | `environment` default / init | `locale` in `stack({...})` or `stack.setLocale('fr-fr')` |
| All locales at once | `locale: '*'` → fields become `{ 'en-US': v }` maps | not the same; query per locale, or use fallback |
| Fallback when unpublished | (CDA returns default-locale content per settings) | explicit `.includeFallback()` |

> **Pitfall:** With Contentful `locale: '*'`, `entry.fields.title` becomes an object keyed by
> locale. Apps relying on this multi-locale shape must be re-architected to query per locale
> in Contentstack (Contentstack returns single-locale flat entries).

---

## 12. Pagination

| Concern | Contentful | Contentstack |
|---|---|---|
| Offset pagination | `skip` + `limit`, read `res.total` | `.skip(n).limit(m)`, `.includeCount()` → `res.count` |
| Cursor pagination | `getEntriesWithCursor` (CMA) / `res.pages.next` | use sync API / offset; cursor not in delivery builder |
| Delta sync | `client.sync({ initial, nextSyncToken })` | `stack.sync({ ... })`; **TS keys are camelCase** (`paginationToken` / `syncToken`); `init: true` is auto-added when neither is present. Response uses snake_case (`sync_token`, `pagination_token`). |

```ts
// Contentstack offset pagination with total
const page = await stack.contentType('blog').entry().query()
  .includeCount().skip(20).limit(20).find<BlogPost>()
const total = page.count
```

---

## 13. Common gotchas / migration pitfalls

1. **`.fields.` removal.** Every `entry.fields.X` → `entry.X`. This is the most frequent edit.
2. **`sys` → flat metadata.** `entry.sys.id` → `entry.uid`; `sys.createdAt` → `created_at`; etc.
3. **References become arrays.** `entry.fields.ref.fields.x` → `entry.ref?.[0]?.x`. Even a
   single reference resolves to a one-element array.
4. **References are not auto-resolved.** Replace `include: N` with explicit
   `.includeReference('field', 'field.nested')`. Forgetting this leaves you with unresolved
   reference stubs (`{ uid, _content_type_uid }`).
5. **Content type is in the path.** No `content_type` query param; use
   `stack.contentType(uid)`. Multi-type Contentful queries must be split per type.
6. **`environment` is mandatory** in Contentstack init (Contentful defaults to `master`).
7. **Collection key rename.** `res.items` → `res.entries` (or `res.assets`). `res.total` →
   `res.count` and only when `.includeCount()` is set.
8. **`.find()` vs `.fetch()`.** Collections/queries end in `.find()`; single objects end in
   `.fetch()`. Mixing them up is a common error.
9. **Rich text is a different JSON dialect.** You cannot pass a Contentful RichText document to
   `@contentstack/utils`; the underlying content must live in a Contentstack JSON RTE field.
   The renderer API also differs (tag-keyed `renderOption` vs `BLOCKS`/`INLINES` `renderNode`).
10. **Locale casing.** Lower-case all locale codes (`en-US` → `en-us`).
11. **Asset URLs.** Contentful URLs are often protocol-relative (`//images.ctfassets.net/...`)
    and need an added scheme; Contentstack URLs are absolute.
12. **Image transform params differ.** Don't carry over `?w=&h=&fit=` query strings verbatim;
    rebuild with `ImageTransform` or the correct Contentstack image param names.
13. **OR queries.** Contentstack supports `.or(...)` natively; Contentful CDA often required
    multiple requests — you can consolidate during migration.
14. **Typed responses.** Pass an interface to `fetch<T>()` / `find<T>()`. Extend `BaseEntry`
    (from `@contentstack/delivery-sdk`) for entry types so `uid`, `locale`, `created_at`, etc.
    are typed.
15. **`Utils.render` uses `paths` (plural array), not `path`.** And `jsonToHTML`/`render`
    **mutate the entry in place** (return `void`) — pass the whole entry and read the field
    afterward; use `Utils.renderContent(content, option)` if you need a returned HTML string.
16. **`@contentstack/utils` produces HTML strings, never components.** Code using
    `documentToReactComponents` (a component tree) needs an HTML-injection strategy or a
    JSON-RTE→component serializer — not a 1:1 swap.
17. **`ImageTransform` is type-only at the package root.** `new ImageTransform()` from
    `@contentstack/delivery-sdk` may fail at runtime; build the image query string manually
    (`?width=300&height=200&format=webp&quality=80`) or deep-import the value class.
18. **`stack.sync` keys are camelCase in TypeScript** (`paginationToken`, `syncToken`), even
    though the response and some JSDoc examples use snake_case.
19. **Match the data-access approach.** Don't rewrite a GraphQL app to the REST SDK (or vice
    versa). GraphQL → Contentstack GraphQL (§17); preview → Contentstack Live Preview (§18).

---

## 14. Worked before/after example

### Contentful (e.g. a Next.js / React data layer)
```ts
import { createClient } from 'contentful'
import { documentToHtmlString } from '@contentful/rich-text-html-renderer'

const client = createClient({
  space: process.env.CF_SPACE!,
  accessToken: process.env.CF_CDA_TOKEN!,
  environment: 'master',
})

export async function getPost(slug: string) {
  const res = await client.getEntries({
    content_type: 'blogPost',
    'fields.slug': slug,
    include: 2,
    limit: 1,
  })
  const post = res.items[0]
  return {
    title: post.fields.title,
    author: post.fields.author.fields.name,
    coverUrl: 'https:' + post.fields.coverImage.fields.file.url,
    bodyHtml: documentToHtmlString(post.fields.body),
  }
}
```

### Contentstack (migrated)
```ts
import contentstack, { Region, BaseEntry } from '@contentstack/delivery-sdk'
import * as Utils from '@contentstack/utils'

const stack = contentstack.stack({
  apiKey: process.env.CS_API_KEY!,
  deliveryToken: process.env.CS_DELIVERY_TOKEN!,
  environment: process.env.CS_ENVIRONMENT!,   // required
  region: Region.US,
})

interface BlogPost extends BaseEntry {
  slug: string
  author: Array<{ name: string }>             // references resolve to arrays
  cover_image: { url: string }                // asset (file) field
  body: any                                   // JSON RTE
}

const renderOption = {
  p:    (node, next) => `<p>${next(node.children)}</p>`,
  bold: (text) => `<b>${text}</b>`,
}

export async function getPost(slug: string) {
  const res = await stack
    .contentType('blog_post')
    .entry()
    .query()
    .equalTo('slug', slug)
    .includeReference('author')               // explicit reference resolution
    .includeEmbeddedItems()                   // needed for RTE embeds
    .limit(1)
    .find<BlogPost>()

  const post = res.entries?.[0]
  if (!post) return null

  Utils.jsonToHTML({ entry: post, paths: ['body'], renderOption })  // mutates post.body → HTML

  return {
    title: post.title,                        // no .fields
    author: post.author?.[0]?.name,           // reference is an array
    coverUrl: post.cover_image?.url,          // absolute URL
    bodyHtml: post.body,                       // rendered by jsonToHTML
  }
}
```

---

## 15. Migration checklist (agent run order)

0. **Detect** language, framework, and data-access approach(es) (§0.1). Confirm prerequisites:
   the target stack already has the matching content model + published content, and you have a
   Contentful-field-ID → Contentstack-field-UID map. If reads are GraphQL, follow §17; if the app
   has Live Preview / draft mode, also follow §18.
1. **Dependencies:** remove `contentful*` + `@contentful/rich-text-*`; add
   `@contentstack/delivery-sdk` + `@contentstack/utils` (+ `@contentstack/persistence-plugin`
   only if cache policies are used).
2. **Env vars:** `CF_SPACE`/`CF_CDA_TOKEN` → `CS_API_KEY`/`CS_DELIVERY_TOKEN`/`CS_ENVIRONMENT`
   (+ region/branch as needed).
3. **Client init:** `createClient(...)` → `contentstack.stack({...})`.
4. **Reads:** rewrite each `getEntry`/`getEntries`/`getAsset`/`getAssets`/`getContentType(s)`
   to the builder form ending in `.fetch()`/`.find()` (§4).
5. **Queries:** translate every operator/sort/pagination/select param (§5).
6. **References:** replace `include: N` with explicit `includeReference(...)`; convert single
   references to `?.[0]` access (§7).
7. **Field access:** strip `.fields.`; map `sys.*` → flat metadata (`uid`, `created_at`, …) (§6).
8. **Collections:** `res.items` → `res.entries`/`res.assets`; `res.total` →
   `.includeCount()` + `res.count`.
9. **Rich text:** move RTE rendering to `@contentstack/utils` (`jsonToHTML`/`render`) with a
   `renderOption`; add `.includeEmbeddedItems()` where embeds are rendered (§9).
10. **Assets/images:** `fields.file.url` → `url`; rebuild image transforms with
    `ImageTransform` (§10).
11. **Locales:** lower-case codes; `locale` param → `.locale(...)`; add `.includeFallback()`
    where Contentful relied on default-locale fallback (§11).
12. **Types:** introduce interfaces extending `BaseEntry` for `fetch<T>()`/`find<T>()`.
13. **Verify:** typecheck/build; smoke-test each migrated query against a real Contentstack
    stack; confirm reference arrays, RTE HTML output, and image URLs render correctly.

---

## 16. Quick API equivalence (condensed)

```
Contentful (contentful / CDA)                 Contentstack (@contentstack/delivery-sdk)
------------------------------------------     ---------------------------------------------------
createClient({ space, accessToken, env })  ->  contentstack.stack({ apiKey, deliveryToken, environment, region })
client.getEntry(id)                         ->  stack.contentType(ct).entry(id).fetch<T>()
client.getEntries({ content_type: ct })     ->  stack.contentType(ct).entry().query().find<T>()
client.getAsset(id)                         ->  stack.asset(id).fetch<T>()
client.getAssets(q)                         ->  stack.asset().query()...find<T>()
client.getContentType(id)                   ->  stack.contentType(id).fetch<T>()
client.getContentTypes()                    ->  stack.contentType().find<T>()
client.sync({ initial: true })              ->  stack.sync({ ... })
'fields.x': v                               ->  .equalTo('x', v) | .where('x', QueryOperation.EQUALS, v)
'fields.x[gte]': v                          ->  .greaterThanOrEqualTo('x', v)
order: '-fields.x'                          ->  .orderByDescending('x')
skip / limit                                ->  .skip(n) / .limit(m)
select: 'fields.a,fields.b'                 ->  .only(['a','b'])
include: N                                  ->  .includeReference('a','a.b')
res.items / res.total                       ->  res.entries / (res.count via .includeCount())
entry.fields.x / entry.sys.id               ->  entry.x / entry.uid
documentToHtmlString(entry.fields.body)     ->  Utils.jsonToHTML({ entry, paths:['body'], renderOption })
asset.fields.file.url                       ->  asset.url
```

---

## 17. GraphQL migration (Contentful GraphQL → Contentstack GraphQL)

If the app reads via the **Contentful GraphQL Content API** (signals: `graphql.contentful.com`,
`gql` tagged templates, `*.graphql` files, `@apollo/client` / `urql` / `graphql-request`,
GraphQL Code Generator), migrate to the **Contentstack GraphQL Content Delivery API** — do **not**
rewrite it to the REST Delivery SDK. **Keep the same GraphQL client library**; only the endpoint,
auth, schema, and query/fragment text change. The response-shape principles in §6 still apply
(flattened fields, `uid`/`created_at` metadata, references as nested objects).

> The Contentstack GraphQL API is a separate service and is **not** part of `@contentstack/delivery-sdk`.
> The endpoint hosts, header names, and pagination/filter argument names below should be **verified
> against current Contentstack GraphQL documentation** for the target region before finalizing.

### 17.1 Endpoint & auth

| Concern | Contentful GraphQL | Contentstack GraphQL |
|---|---|---|
| Endpoint | `https://graphql.contentful.com/content/v1/spaces/{SPACE}/environments/{ENV}` | `https://graphql.contentstack.com/stacks/{API_KEY}?environment={ENV}` (regional hosts: `eu-graphql…`, `azure-na-graphql…`, `azure-eu-graphql…`, `gcp-na-graphql…`, `gcp-eu-graphql…`) |
| Auth | `Authorization: Bearer {CDA_or_CPA_TOKEN}` | header `access_token: {DELIVERY_TOKEN}` (API key is in the path; `environment` is a query param) |
| Preview | `graphql.contentful.com` + CPA Bearer token | preview host + `live_preview` hash / `preview_token` header (see §18) |

### 17.2 Query shape

Field/type names follow the **Contentstack content-type & field UIDs** (snake_case, e.g.
`blog_post`, `cover_image`), not Contentful's camelCase ids.

```graphql
# Contentful
query {
  blogPostCollection(limit: 10, where: { slug: "hello" }) {
    total
    items { title slug author { name } }
  }
}

# Contentstack (verify exact arg/field names against the stack's GraphQL schema)
query {
  all_blog_post(limit: 10, where: { slug: "hello" }) {
    total
    items {
      title
      slug
      author { ... on SysAssetOrEntry { /* reference: nest the referenced type's fields */ } }
    }
  }
}
```

| Concept | Contentful GraphQL | Contentstack GraphQL |
|---|---|---|
| Collection query | `xxxCollection` → `{ items, total }` | `all_<content_type_uid>` → `{ items, total }` |
| Single entry | `xxx(id: "...")` | `<content_type_uid>(uid: "...")` |
| References | nested `linkedFrom` / inline link selections | **nest the referenced type's fields** in the selection (the GraphQL analog of `includeReference`) |
| Filtering | `where: { field: value, field_gt: n }` | `where: { ... }` (operator/arg names differ — verify) |
| Pagination | `limit` + `skip` (`total`) | `limit` + `skip` (`total`) |
| Localization | `locale: "en-US"` arg | `locale: "en-us"` arg (lower-cased) |
| RTE field | `json` in response | `json` in response → render with `@contentstack/utils` (§9) |

### 17.3 Steps for the agent
1. Repoint the GraphQL client (Apollo/urql/graphql-request) at the Contentstack endpoint and swap
   `Authorization: Bearer` → `access_token` header + `environment` query param.
2. Rewrite every query/fragment to the Contentstack schema (collection names, field UIDs, reference
   nesting, filter args, lower-cased locales).
3. Update response handling for the new shape (`items` arrays, flat fields, `uid`/`created_at`).
4. If **GraphQL Code Generator** is used, repoint it at the Contentstack schema/introspection and
   regenerate types; fix call sites against the new generated types.
5. Render RTE/JSON fields with `@contentstack/utils` (§9), same as the REST path.

---

## 18. Live Preview / draft mode migration

If the source app implements **Contentful Preview** or **Live Preview**, reimplement equivalent
behavior with **Contentstack Live Preview**, matching the source's scope (which routes/components,
SSR vs client, click-to-edit vs. read-only preview).

**Detect in the source:** `host: 'preview.contentful.com'`, a CPA / Content Preview token, a second
"preview" client, `@contentful/live-preview` (`ContentfulLivePreview.init`, `useContentfulLiveUpdates`,
`useContentfulInspectorMode`), Next.js `draftMode()` / preview API routes, or a `?preview=` route gate.

### 18.1 SDK config & per-request hash (verified against `@contentstack/delivery-sdk` source)

`live_preview` is a first-class field on `StackConfig` (`src/common/types.ts`), and the stack exposes
`livePreviewQuery(...)`:

```ts
const stack = contentstack.stack({
  apiKey: process.env.CS_API_KEY!,
  deliveryToken: process.env.CS_DELIVERY_TOKEN!,
  environment: process.env.CS_ENVIRONMENT!,
  live_preview: {
    enable: true,                         // REQUIRED on the LivePreview type
    preview_token: process.env.CS_PREVIEW_TOKEN!,  // preferred (management_token is legacy)
    host: 'rest-preview.contentstack.com',// regional preview host (verify per region)
  },
})

// Per request, apply the preview hash (from the URL / live-preview-utils) before fetching:
stack.livePreviewQuery({
  live_preview: hash,            // the live_preview hash for the edited entry
  contentTypeUid: 'blog_post',   // also accepts content_type_uid
  entryUid: 'blt...',            // also accepts entry_uid
  // preview_timestamp, release_id, include_applied_variants are also supported
})
```

`LivePreview` type fields (verified): `enable: boolean` (required), `preview_token?`,
`management_token?` (legacy), `host?`, `live_preview?`, `contentTypeUid?`, `entryUid?`,
`include_applied_variants?`. In the **browser**, the SDK auto-reads `live_preview`, `release_id`,
and `preview_timestamp` from the page URL's query string during `stack(...)` init.

### 18.2 Front-end real-time updates & click-to-edit (`@contentstack/live-preview-utils`)

> Not part of the Delivery SDK and **not vendored in this workspace** — verify the exact API against
> current `@contentstack/live-preview-utils` docs. Add it as a dependency.

| Contentful | Contentstack |
|---|---|
| `ContentfulLivePreview.init({...})` | `ContentstackLivePreview.init({ stackDetails: { apiKey, environment }, enable: true, ssr: false /* or true */ })` |
| `useContentfulLiveUpdates(entry)` (real-time merge) | `ContentstackLivePreview.onEntryChange(cb)` → re-run the fetch in `cb` |
| live-update hash plumbing | `ContentstackLivePreview.hash` (REST) / GraphQL hash helper → pass to `stack.livePreviewQuery({ live_preview: hash, ... })` |
| `useContentfulInspectorMode()` / `data-contentful-*` field tags (click-to-edit) | `Utils.addEditableTags(entry, contentTypeUid, true, locale)` from `@contentstack/utils` → emits `data-cslp` attributes the Live Preview UI uses for click-to-edit |
| CPA token | `preview_token` (+ `live_preview` host) |

### 18.3 Steps for the agent
1. Add `live_preview` to the stack init (`enable: true` + `preview_token` + regional preview host).
2. Add `@contentstack/live-preview-utils`; call `ContentstackLivePreview.init(...)` where the source
   called `ContentfulLivePreview.init(...)`.
3. Replace the source's live-update hook with `onEntryChange(...)` re-fetching, calling
   `stack.livePreviewQuery({ live_preview, contentTypeUid, entryUid })` before each preview fetch.
4. If the source had click-to-edit (inspector mode), add `Utils.addEditableTags(...)` and render the
   resulting `data-cslp` attributes on the same elements.
5. Preserve the existing preview gating/routing (e.g. Next.js `draftMode`, `?preview=` guard); only
   swap the backend. Keep preview tokens server-side.

---

## 19. Raw REST / `fetch` and framework source plugins

Not every app uses an SDK. Migrate these in kind:

- **Raw `fetch`/`axios` to `cdn.contentful.com`.** Repoint to the Contentstack Content Delivery
  REST API: base `https://{region-cdn-host}/v3` (US `cdn.contentstack.io`; see §3 for regional hosts),
  headers `api_key`, `access_token`, and `environment` as a query param. Endpoints:
  `/v3/content_types/{ct_uid}/entries` (list), `/v3/content_types/{ct_uid}/entries/{uid}` (single),
  `/v3/assets`. Query params map per §5 (`include[]=author`, `only[BASE][]=title`, `limit`, `skip`,
  `include_count=true`, `locale`, `include_fallback=true`). Response keys per §6 (`entries`/`entry`,
  `assets`/`asset`, `count`). Prefer adopting `@contentstack/delivery-sdk` if it doesn't fight the
  app's architecture, but a like-for-like raw-fetch migration is valid.
- **Gatsby (`gatsby-source-contentful`).** Migrate to `@contentstack/gatsby-source-contentstack`:
  swap the plugin + its options (`api_key`, `delivery_token`, `environment`, `regions`) in
  `gatsby-config`, and rewrite GraphQL queries from `allContentfulXxx` to the Contentstack source
  plugin's node types (verify node-type naming against the plugin docs).
- **Framework data-fetching idioms — keep them.** Migrate the data-layer call *inside* the app's
  existing pattern; don't change where/how data is fetched:
  - Next.js: `getStaticProps`/`getServerSideProps`/`generateStaticParams`/RSC `fetch` — keep the
    same function, swap the client call. Keep ISR/caching tags.
  - Remix `loader`, SvelteKit `load`, Nuxt `useAsyncData`/`asyncData`, Vue composables, Angular
    services/resolvers — same: swap only the CMS call body.
  - Module-singleton vs per-request client: instantiate the Contentstack stack the same way the
    Contentful client was instantiated (one shared client module is the common case).
