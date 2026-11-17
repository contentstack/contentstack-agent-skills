---
name: cms-graphql
description: "Advise developers on querying published Contentstack content with the GraphQL Content Delivery API. Cover regional endpoints, required headers, the generated schema, reference connections, modular blocks, JSON RTE embedded items, assets, filtering, pagination, query limits, rate limits, and Live Preview with GraphQL. Use when developers write or debug Contentstack GraphQL queries, see schema build errors or partial errors, hit GraphQL limits or 429s, paginate references, or wire GraphQL into Live Preview or Visual Editor. For REST CDA queries use cms-entries; for Delivery SDK code use dx-delivery-sdk; for preview failures use cms-live-preview-visual-editor-support-assistant."
allowed-tools: Read Grep Glob
---

# GraphQL Content Delivery API

Advise on querying published content with the GraphQL Content Delivery API: endpoints, headers, schema shape, references, modular blocks, JSON RTE, assets, filtering, pagination, limits and Live Preview, without silently losing data to limits or partial errors.

## When to use

- Writing or fixing a GraphQL query against the generated schema.
- `SCHEMA_BUILD_ERROR`, partial errors on HTTP 200, 414s or 429s.
- Paginating references and staying inside query limits.
- Querying modular blocks, JSON RTE embedded items and assets.
- Wiring a GraphQL fetch layer into Live Preview or Visual Editor.

Use another skill for:

- REST Content Delivery API queries → `cms-entries`
- Delivery SDK code → `dx-delivery-sdk`
- Rendering the JSON RTE document the query returns → `cms-json-rte`
- Live Preview or Visual Editor failures → `cms-live-preview-visual-editor-support-assistant`
- Designing the content types the schema is generated from → `cms-data-modeling-best-practices`

## Before you answer

Find out the stack region, the content type and field UIDs, the query or the error returned, and whether the request runs in the browser, on a server or in a preview session.

## Instructions

1. Confirm the region, environment and branch.
2. Build the query against the generated schema.
3. Check depth, record and size limits; paginate where needed.
4. Check `errors` as well as `data`.
5. For preview sessions, switch host and add preview headers.

### Endpoints and headers

Send queries to `https://<host>/stacks/{api_key}?environment={environment}`. Hosts: `graphql.contentstack.com` (AWS NA), `eu-graphql.contentstack.com`, `au-graphql.contentstack.com`, `azure-na-graphql.contentstack.com`, `azure-eu-graphql.contentstack.com`, `gcp-na-graphql.contentstack.com`, `gcp-eu-graphql.contentstack.com`. Dedicated infrastructure uses its own host.

Headers: `access_token` with the environment's delivery token (required), optional `branch` (branch UID or alias; `main` when omitted), and `Content-Type: application/json`. POST a JSON body with `query`, optional `variables` and `operationName`. GET works too, but the URL must stay under 2,000 bytes or the server returns 414. The API supports queries only: no mutations or subscriptions.

### Schema shape

Each content type becomes a type with a single-entry field and an `all_<content_type_uid>` collection field. Type names are the PascalCase form of the UID, so UIDs must not start with a number, must match `[_A-Za-z][_0-9A-Za-z]*`, and must not collide after PascalCase conversion. Collisions and invalid names cause `SCHEMA_BUILD_ERROR`. Use introspection in GraphiQL to see the generated schema, and `skip_content_type_uids` to exclude a content type that breaks the build.

### References

Query a reference through its connection field: append `Connection` to the field UID and select `totalCount` and `edges { node { ... } }`. For a reference to several content types, use inline fragments on the PascalCase type names and select `__typename`. `skip` and `limit` on a connection only work for fields marked Multiple. Referenced items are paginated whether or not they are published.

### Modular blocks, JSON RTE and assets

- **Modular blocks** are unions. Select `__typename` and use inline fragments named `<ContentType><Field><Block>`, for example `... on PageSectionsHero { hero { title } }`.
- **JSON RTE** returns the document in `json`. Fetch embedded entries and assets through `embedded_itemsConnection` with inline fragments, using `... on SysAsset` for assets. Embedded items can't be filtered, and references inside embedded entries can't be fetched.
- **Assets** are `SysAsset`. Use `all_assets` for lists. Image fields accept transform arguments such as `width`, `height`, `format`, `fit` and `quality`.

### Filtering, sorting and pagination

Filter with `where`: equality plus `_ne`, `_exists`, `_in`, `_nin`, `_gt`, `_gte`, `_lt`, `_lte`, combined with `AND` and `OR`. Regular expressions aren't supported. `order_by` accepts `created_at` and `updated_at`, ascending or descending. Paginate root collections with `skip` and `limit` (default 25, max 100) and request `total` to know when to stop.

### Query limits

- Up to 3 levels of nested references, and 3 levels for reference filters in `where`.
- Up to 7,500 records per query, counting root and referenced entries.
- Up to 100 referenced records per reference connection.
- Up to 100 embedded items per JSON RTE field.
- Responses up to 7 MB, and one operation per request: use aliases instead of batching.
- Up to 3 variant UIDs in `x-cs-variant-uid`.

When a page needs more, split it into several queries, or fetch the deep part with a separate query keyed by UID.

### Rate limits and errors

Uncached requests to the origin are limited per organization (80 per second by default, depending on plan). Requests served from the CDN cache aren't rate-limited but still count toward usage. A 429 means back off; read `X-RateLimit-Limit` and `X-RateLimit-Remaining`. HTTP 200 doesn't guarantee success: partial failures return in `errors` alongside `data`, so always check `errors` before using the result.

### Live Preview with GraphQL

When a preview hash is present, swap the host for the region's preview host (`graphql-preview.contentstack.com`, `eu-graphql-preview.contentstack.com` and so on) and add the `live_preview` (the hash) and `preview_token` headers. Keep `access_token`. Under CSR read the hash from `ContentstackLivePreview.hash`; under SSR read it from the `live_preview` query parameter on the request. Never cache preview responses. Edit tags (`data-cslp`) need the response normalized first, because `Connection`, `edges` and `node` wrappers break tag paths. Route anything that still fails to `cms-live-preview-visual-editor-support-assistant`.

## MCP tools

The Contentstack MCP server has no GraphQL tool; run queries in GraphiQL or from code. To check the underlying data when a query returns less than expected, use these read-only tools (local server group in brackets):

- Inspect: `get_all_entries_cdn`, `get_a_single_entry_cdn`, `get_all_assets_cdn` (`cda`, the same published data over REST); `get_a_single_content_type` (`cma`, to check UIDs against the GraphQL naming rules)

## Output

Lead with the working query or the fix. Show the endpoint and headers when they matter. State which limit applies when splitting a query. Keep explanations short.

## Security

### Defaults

- Advisory by default. Don't send queries with real credentials or change stack settings unless the user asks.
- Delivery tokens are read-only and environment-scoped; they can be used client-side.
- Preview tokens belong only on preview deployments.
- Never use management tokens with GraphQL or in client code, and never hardcode stack API keys in client-side code.

### Destructive Actions

None. This skill only reads published content and advises.

### Secrets

Never echo tokens or live preview hashes. Use placeholders in examples.

### Environment Variables

Use variables such as `CONTENTSTACK_API_KEY`, `CONTENTSTACK_DELIVERY_TOKEN`, `CONTENTSTACK_ENVIRONMENT` and `CONTENTSTACK_PREVIEW_TOKEN` in examples.

## References

- https://www.contentstack.com/docs/developers/apis/graphql-content-delivery-api
