---
title: GraphQL Content Delivery
description: "Query published Contentstack content with the GraphQL Content Delivery API: endpoints, schema, references, modular blocks, JSON RTE, limits, and Live Preview."
---

# GraphQL Content Delivery

**Slug:** `cms-graphql` · **Product:** CMS · **Type:** Advisory (read-only)

Helps you write and debug queries against the GraphQL Content Delivery API without running into its limits or losing data to partial errors.

## When it triggers

When you write or debug Contentstack GraphQL queries, see schema build errors or partial errors, hit GraphQL limits or 429s, paginate references, or connect a GraphQL fetch layer to Live Preview or Visual Editor.

## What it covers

- **Endpoints and headers**: regional hosts (`graphql.contentstack.com`, `eu-graphql…`, `au-graphql…`, Azure and GCP), `/stacks/{api_key}?environment=…`, `access_token`, optional `branch`. Queries only, no mutations.
- **Schema shape**: generated types per content type, `all_<uid>` collections, PascalCase naming rules and `SCHEMA_BUILD_ERROR`.
- **References**: `<field>Connection` with `totalCount`, `edges` and `node`; inline fragments for multi-type references.
- **Modular blocks, JSON RTE, assets**: unions with inline fragments, `embedded_itemsConnection`, `SysAsset` and image transforms.
- **Filtering and pagination**: `where` operators, `order_by` on `created_at`/`updated_at`, `skip`/`limit` (max 100).
- **Limits**: 3 levels of nested references, 7,500 records per query, 100 per reference connection, 7 MB responses, one operation per request.
- **Rate limits and errors**: per-organization origin limit, `X-RateLimit-*` headers, and checking `errors` even on HTTP 200.
- **Live Preview**: preview hosts, `live_preview` and `preview_token` headers, no caching, normalizing connection wrappers for edit tags.

## Example prompts

- "How do I query referenced entries with GraphQL in Contentstack?"
- "My GraphQL response is 200 but some data is missing."
- "How do I query modular blocks and JSON RTE embedded entries?"
- "What are the GraphQL query limits?"
- "How do I make Live Preview work with my GraphQL client?"

## MCP tools

The Contentstack MCP server has no GraphQL tool. To check the underlying data, the agent can use the read-only `cda` tools (`get_all_entries_cdn`, `get_a_single_entry_cdn`, `get_all_assets_cdn`) and `get_a_single_content_type` to check UIDs against GraphQL naming rules.

## Safety notes

Read-only advisory. Uses delivery tokens only; management tokens never belong in GraphQL calls or client code. Preview tokens stay on preview deployments.

## Related

- [Entries](cms-entries.md) · [Delivery SDK](dx-delivery-sdk.md) · [Live Preview & Visual Editor](cms-live-preview-visual-editor-support-assistant.md)
