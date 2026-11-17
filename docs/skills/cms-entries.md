---
title: Entries
description: "Query, localize, version, publish, and structure Contentstack entries for efficient delivery: CDA usage, reference expansion, pagination, bulk ops, and the Sync API."
---

# Entries

**Slug:** `cms-entries` · **Product:** CMS · **Type:** Advisory (acts through MCP tools on request)

Advises on querying, localizing, versioning, publishing, and structuring entries for efficient delivery, with a focus on CDA usage, reference expansion, pagination, bulk operations, and Sync API patterns.

## When it triggers

When you ask about fetching entries, building CDA queries, handling localization, publishing workflows, versioning behavior, bulk operations, or entry-related performance issues.

## What it covers

- **CDA vs CMA**: states up front whether guidance applies to the Content Delivery API (frontend reads) or the Content Management API (authoring). A key guardrail: never use the CMA for frontend reads.
- **Query syntax**: correct operators and response shapes, including filtering by fields inside Modular Blocks.
- **Reference expansion**: including referenced entries in a CDA response.
- **Pagination & performance**: paging through all entries of a content type efficiently.
- **Versioning & publishing**: how versioning works, and the difference between saving and publishing.
- **Localization**: locale-aware entry behavior, including `include_fallback`.
- **Limits**: at most 100 entries per CDA request, up to 100 `include[]` paths, an 8 KB URL limit, bulk publish of up to 100 items, nested reference publishing with the `api_version: 3.2` header, and CMA limits of 10 requests per second (1 per second for bulk actions).
- **Sync API**: an initial full sync plus `sync_token` deltas for mirrors, static builds and search indexes.

For SDK code specifically, this pairs with the [Delivery SDK](dx-delivery-sdk.md) skill.

## Example prompts

- "How do I query entries filtered by a field inside Modular Blocks?"
- "How does entry versioning work in Contentstack?"
- "What's the difference between publishing and saving?"
- "How do I include referenced entries in my CDA response?"
- "How do I paginate through all entries of a content type?"

## MCP tools

With the Contentstack MCP server connected, the agent can read entries, references and versions (`cma`, `cma-extended`), check what the live site receives with `get_all_entries_cdn`, and create, update, publish, unpublish, localize, unlocalize or delete entries when asked. There are no bulk publish or Sync API tools.

## Safety notes

Advisory by default; uses the MCP tools only when you ask for the change. Before any write, publish, unpublish or delete it names the entries, locales and environments and waits for confirmation. Delivery tokens are client-safe; management tokens are not. Use environment variables for credentials in examples.

## Related

- [Delivery SDK](dx-delivery-sdk.md) · [Localization](cms-localization.md) · [Environments & Publishing](cms-environments-publishing.md)
