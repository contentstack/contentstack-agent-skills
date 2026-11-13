---
name: cms-entries
description: "Advise developers on querying, localizing, versioning, publishing, and structuring Contentstack entries for efficient delivery. Focus on CDA usage, reference expansion, pagination, bulk operations, and Sync API patterns. Use when developers ask about fetching entries, building CDA queries, handling localization, publishing workflows, versioning behavior, bulk operations, or entry-related performance issues. For SDK code, use dx-delivery-sdk; for GraphQL, use cms-graphql."
allowed-tools: Read Grep Glob
---

# Entries

Advise on querying, publishing, versioning and paging through entries so delivery is efficient and editorial workflows behave as expected.

## When to use

- Building CDA queries: filters, references, field projection, sorting, locales.
- Paginating through every entry of a content type.
- Versioning, saving vs publishing, and bulk publish or unpublish.
- Choosing the Sync API over polling.
- Entry-related performance problems.

Use another skill for:

- Writing the query with `@contentstack/delivery-sdk` → `dx-delivery-sdk`
- GraphQL queries → `cms-graphql`
- Rendering JSON RTE fields and embedded items → `cms-json-rte`
- Filtering by taxonomy terms → `cms-taxonomy`
- Locales and fallback chains in depth → `cms-localization`
- Environments, tokens and the publish queue → `cms-environments-publishing`
- Entry variants and personalization → `cms-variants-personalization`
- Bulk export, import or migration scripts with `csdx` → `dx-cli`

## Before you answer

Find out the query or filtering requirement, the content type structure, the locales involved, any publishing or scheduling needs, and any performance or pagination concerns.

## Instructions

1. Confirm whether the user needs CDA or CMA guidance.
2. Give the correct query syntax, publishing approach or delivery pattern.
3. Explain versioning, localization and reference expansion as needed.
4. Flag anti-patterns and recommend best practices.

### CDA or CMA

Say which API the answer is for. Use the Content Delivery API (CDA) with a delivery token for anything a site or app reads. Use the Content Management API (CMA) only for authoring, migration and automation on a server. Never use the CMA for frontend reads: it needs a management token, it isn't cached at the CDN, and it shares the organization's rate limit.

### Query parameters

Filter with the `query` parameter, a JSON object matched against field values, for example `query={"title":"Welcome"}`. Common companions:

- `include[]` resolves reference fields inline, up to 100 reference paths per request. Dot paths such as `include[]=section.author` go deeper, but each level multiplies the work behind the request, so keep includes shallow and only ask for the paths the page renders.
- `only[]` and `except[]` trim the response to the fields you need.
- `asc` and `desc` sort the results.
- `skip` and `limit` page through results. A request returns at most 100 entries.
- `include_count` returns the total so you know how many pages there are.
- `locale` picks the language. Add `include_fallback=true` to fall back along the locale chain when an entry isn't localized.
- `include_branch`, `include_publish_details` and `include_metadata` add branch, publish and metadata details to each entry.

Request URLs are capped at 8 KB, and longer ones fail with `414 URI Too Long`. When a filter grows past that, simplify it: fewer `$in` values, fewer `include[]` paths, or several smaller requests.

### Pagination

To read every entry of a content type, request with `include_count=true` and `limit=100`, then loop with `skip` increasing by 100 until you have `count` entries. Keep the sort order fixed while paging so results don't shift between pages. To mirror a whole environment, use the Sync API instead of paging.

### Versioning

Every save increments a `_version` counter per entry and locale, starting at 1. Old versions are kept. Restoring an older version creates a new version with those values, so history is never rewritten. Publishing is separate from saving: a saved change stays a draft until it is published to an environment.

### Publishing and bulk operations

Publish entries together with the entries they reference. Bulk publish and bulk unpublish accept up to 100 items per request. To publish nested references along with their parents, call the bulk publish endpoint with the `api_version: 3.2` header, which publishes references up to five levels deep. Bulk actions are limited to 1 request per second per organization, and other CMA calls to 10 requests per second per organization, so scripts should back off on `429` responses.

### Sync API

Use the Sync API to keep a full local copy of an environment, for static builds, search indexes or offline apps. The first call returns everything published plus a `sync_token`. Later calls pass that token and receive only what changed: publishes, unpublishes, deletes, and content type and locale changes, with a fresh token each time. Prefer it over polling the CDA.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `get_all_entries`, `get_single_entry`, `get_references_of_an_entry` (`cma`); `get_all_versions_of_an_entry` (`cma-extended`); `get_all_entries_cdn`, `get_a_single_entry_cdn` (`cda`, to check what the live site receives)
- Change: `create_an_entry`, `update_an_entry`, `publish_an_entry` (can schedule), `localize_an_entry` (`cma`); `set_entry_version_name` (`cma-extended`)
- Delete or withdraw: `delete_an_entry`, `unpublish_an_entry`, `unlocalize_an_entry` (`cma`); `delete_entry_version_name` (`cma-extended`)

There are no bulk publish or Sync API tools; use the CMA bulk endpoints or `csdx` for bulk work, and the Sync API from code.

## Output

Be concise and practical. State whether the guidance applies to the CDA or the CMA, show inline query syntax when helpful, and skip background unless it prevents a common mistake.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose tokens or API keys.
- Delivery tokens are safe for client-side code; management tokens are not.
- Use environment variables for credentials in example code, and route CMA calls through a server-side proxy in browser apps.

### Destructive Actions

Before creating, updating, publishing, unpublishing, unlocalizing or deleting entries, name the stack, branch, content type, entries, locales and environments, explain the impact (unpublishing removes content from the live site), and wait for confirmation. Run `get_references_of_an_entry` before a delete to see which entries point to it.

### Secrets

Never reveal management tokens, API keys, or other secrets. Prefer environment variables in all examples. Do not suggest hardcoding credentials.

### Environment Variables

Use environment variables for all credentials in sample code. Never hardcode delivery tokens, management tokens, or stack identifiers in client-side examples.
