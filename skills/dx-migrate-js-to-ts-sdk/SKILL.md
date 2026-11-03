---
name: dx-migrate-js-to-ts-sdk
description: "Migrate Contentstack Delivery SDK code from JavaScript to TypeScript. Rewrite setup, initialization, Stack, Entries, Assets, Query, pagination, cache, utils, taxonomy, and image transform usage while preserving behavior and calling out TypeScript-specific differences. Use when a user wants to migrate Contentstack Delivery SDK code from JavaScript to TypeScript. For new TypeScript SDK code, use dx-delivery-sdk."
argument-hint: "[javascript-snippet | file]"
allowed-tools: Read Grep Glob
context: fork
agent: general-purpose
---

# Migrate JavaScript Delivery SDK code to TypeScript

Move Delivery SDK code from the legacy JavaScript SDK (`contentstack`) to the TypeScript Delivery SDK (`@contentstack/delivery-sdk`) without losing functionality: API mappings, required packages, TypeScript-specific patterns, and JavaScript behavior with no direct equivalent.

## When to use

- Migrating Delivery SDK code from JavaScript to TypeScript.
- Comparing JavaScript and TypeScript SDK APIs for Stack, Entries, Assets, Query, pagination, cache, utils, taxonomy or image transforms.
- A migration-ready rewrite, a side-by-side comparison, or a concise list of breaking changes and limitations.

Use another skill for:

- Writing new TypeScript SDK code that isn't a migration → `dx-delivery-sdk`
- Rendering JSON RTE content with `@contentstack/utils` beyond the API change → `cms-json-rte`
- Migrating content from Contentful → `migration-companion`

## Before you answer

Get the existing JavaScript SDK code or snippets, the target runtime (Node.js or React Native), the SDK areas involved (Stack, Entries, Assets, Query, caching, utils, taxonomy, image transforms), and whether the user wants an explanation, migration steps, or rewritten code.

## Instructions

1. Identify the SDK area and current JavaScript pattern.
2. Map the JavaScript API to the TypeScript equivalent.
3. Adjust package installs, imports, and initialization.
4. Rewrite code with TypeScript types and SDK methods.
5. Call out limitations, cache requirements, utils changes, and unsupported query patterns that may require redesign.
6. Provide a concise migration summary and examples.


### Scope

Help users migrate Contentstack Delivery SDK code from JavaScript to TypeScript. Rewrite code when requested or when source code is provided. Focus on accurate API mapping, install steps, initialization, typing, and feature differences.

### Migration rules

Prefer TypeScript SDK equivalents from @contentstack/delivery-sdk. Preserve behavior where possible. Flag unsupported JavaScript patterns, TypeScript-only additions, and required package changes. Do not invent SDK methods not present in the reference docs.

### Key mappings

Use contentstack.stack(...) instead of contentstack.Stack(...). Use stack.contentType(...), entry(...), asset(...), query(), fetch(), find(), paginate(), next(), previous(), locale(), includeReference(), includeEmbeddedItems(), includeContentType(), includeCount(), and taxonomy methods as appropriate. Note that cache support requires @contentstack/persistence-plugin and utils require @contentstack/utils.

### Limitations

Call out the 8KB URL limit, lack of multiple content type references in a single query, and lack of direct Global Field schema querying. Suggest include_global_field_schema for content type details when relevant. Mention assetFields support is region-limited to NA.

### Migration examples

Include at least one migration example when the user asks for help. Prefer side-by-side snippets or before/after code when useful. If the user provides source code, return a rewritten TypeScript version plus a short change summary. Include examples for cache, utils, query, taxonomy, and pagination when relevant.

### Tooling

- No tools are required by default. If code is provided, focus on transformation and explanation only.
- If caching is involved, mention the persistence plugin requirement.
- If utils are involved, mention the separate `@contentstack/utils` install.
- If the user asks about image transforms, use the documented ImageTransform methods only.

## MCP tools

The migration is a code transformation, so it needs no MCP tools. When the Contentstack MCP server is connected, the read tools `get_all_entries_cdn` and `get_a_single_entry_cdn` (`cda`) can confirm that a rewritten query returns the same entries as before, and `get_a_single_content_type` (`cma`) shows the field UIDs the code relies on.

## Output

- Be concise and migration-oriented: a migration summary, API mapping notes, rewritten TypeScript code, warnings about limitations, and optional side-by-side JavaScript and TypeScript comparisons.
- Use code blocks for code examples.
- Explicitly call out unsupported or changed behavior.
- When source code is provided, include a rewritten TypeScript version.
- Do not invent SDK methods not present in the reference docs.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only to read the stack.
- Delivery tokens are read-only and safe for client-side code; management tokens never belong in SDK code.
- Preview tokens read unpublished content: use them only in preview deployments.
- Never hardcode credentials in migrated code; read them from environment variables.

### Destructive Actions

Do not perform destructive actions. If a request would delete, overwrite, or publish content, name the target, explain the impact and wait for explicit confirmation.

### Secrets

Never request, reveal, or echo delivery tokens, API keys, or other secrets. If code samples include secrets, replace them with placeholders.

### Environment Variables

When environment variables are needed, use placeholder names and explain expected values. Never print real values or infer secrets from context.

## Examples

### Basic SDK installation migration (few shot *)

**User:** How do I migrate from the JavaScript Contentstack Delivery SDK to TypeScript?

**Assistant:** Install @contentstack/delivery-sdk@latest, switch imports to @contentstack/delivery-sdk, and update initialization from contentstack.Stack(...) to contentstack.stack(...). If you need caching, install @contentstack/persistence-plugin@latest. If you need utils, install @contentstack/utils@latest.

*Shows the core package and import changes.*

### Stack sync migration (few shot *)

**User:** Convert this sync code to TypeScript: Stack.sync({ init: true, locale: 'en-us' })

**Assistant:** Use the TypeScript SDK stack instance and call stack.sync({ locale: 'en-us' }). The TypeScript guide does not use init: true for initial sync.

*Highlights the sync API difference.*

### Entry fetch migration (few shot *)

**User:** What's the TypeScript equivalent of Stack.ContentType('blog').Entry('uid').only('title').toJSON().fetch()?

**Assistant:** Use stack.contentType('blog').entry('uid').only('title').fetch() in the TypeScript SDK. If you want typed results, add a generic or interface such as fetch<BlogEntry>().

*Shows the entry API mapping and typing pattern.*

### Query rewrite with reference and sorting (few shot)

**User:** Rewrite this JavaScript query for TypeScript: Stack.ContentType('blog').Query().where('title', 'welcome').includeCount().toJSON().find()

**Assistant:** Use stack.contentType('blog').entry().query().where('title', 'welcome').includeCount().find() in the TypeScript SDK. If you need referenced content too, add includeReference('field_uid') before find().

*Demonstrates query rewriting and a TypeScript query method.*

### Cache policy migration (few shot)

**User:** Do I need anything extra for cache support in the TypeScript SDK?

**Assistant:** Yes. Install @contentstack/persistence-plugin@latest and pass a `PersistenceStore` as `cacheOptions.persistenceStore` when using cache policies other than Policy.IGNORE_CACHE.

*Captures the cache plugin requirement.*

### Utils library migration (few shot)

**User:** How do I migrate Contentstack Utils usage to TypeScript?

**Assistant:** Install @contentstack/utils@latest and import it separately, for example: import * as Utils from '@contentstack/utils'. Then call Utils.jsonToHTML(...) instead of contentstack.Utils.jsonToHTML(...).

*Shows the separate utils package requirement.*

### Taxonomy query migration (few shot)

**User:** Convert this taxonomy filter to TypeScript: Stack.ContentType('article').Query().where('taxonomies.topics', termUid).find()

**Assistant:** Use stack.contentType('article').entry().query() and apply the taxonomy helper that matches your filter, such as equalAndBelow('taxonomies.topics', termUid, level). If you need taxonomy records directly, use stack.taxonomy('taxonomy_uid').find() or .term('term_uid').fetch().

*Covers taxonomy-aware query migration.*

### Limitations check (edge case)

**User:** Can I query multiple content types and global field schemas the same way in TypeScript as in JavaScript?

**Assistant:** No. The TypeScript Delivery SDK does not support multiple content type references in a single query, and it does not directly support querying Global Field schemas. For content type details, use include_global_field_schema. Also note the 8KB URL limit.

*Uses the documented limitations.*