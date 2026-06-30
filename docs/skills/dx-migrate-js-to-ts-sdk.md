---
title: Migrate JS to TS SDK
description: Migrate Contentstack Delivery SDK code from the JavaScript SDK to the TypeScript @contentstack/delivery-sdk, preserving behavior and flagging differences.
---

# Migrate JS to TS SDK

**Slug:** `dx-migrate-js-to-ts-sdk` · **Product:** Developer Experience · **Type:** Advisory (read-only)

Migrates Contentstack Delivery SDK code from JavaScript to TypeScript: setup, initialization, Stack, Entries, Assets, Query, pagination, cache, utils, taxonomy, and image transforms: preserving behavior and calling out TypeScript-specific differences.

## When it triggers

When you want to migrate Delivery SDK code from JavaScript to TypeScript, compare the two SDK APIs, or get a migration-ready rewrite, side-by-side comparison, or list of breaking changes.

## What it covers

- **Packages & imports**: install `@contentstack/delivery-sdk@latest`; switch imports; add `@contentstack/persistance-plugin` for cache and `@contentstack/utils` for utils.
- **Key API mappings**: `contentstack.stack(...)` (not `Stack(...)`); `stack.contentType(...).entry(...).asset(...).query().fetch().find()`, plus `paginate()`, `next()`, `previous()`, `locale()`, `includeReference()`, `includeEmbeddedItems()`, `includeContentType()`, `includeCount()`, and taxonomy methods.
- **Typed results**: generics on `fetch<BlogEntry>()`.
- **Cache**: install the persistence plugin and pass `cacheOptions` for policies other than `Policy.IGNORE_CACHE`.
- **Utils**: install `@contentstack/utils` separately and call `Utils.jsonToHTML(...)`.
- **Sync**: TypeScript uses `stack.sync({ locale })` without `init: true`.
- **Limitations**: 8KB URL limit; no multiple content-type references in a single query; no direct Global Field schema querying (use `include_global_field_schema`); `assetFields` support is region-limited to NA.

## Example prompts

- "Migrate this JavaScript Delivery SDK code to TypeScript."
- "What changes do I need moving from `contentstack` to `@contentstack/delivery-sdk`?"
- "Show me the TypeScript equivalent for this JavaScript snippet."
- "How do I rewrite cache policy usage for the TypeScript SDK?"
- "Convert this taxonomy query from the JavaScript SDK to TypeScript."

## Safety notes

Never invents SDK methods not present in the reference docs. Replaces any secrets in samples with placeholders; uses environment variables for credentials.

## Related

- [Delivery SDK](dx-delivery-sdk.md) · [Entries](cms-entries.md) · [Taxonomy](cms-taxonomy.md)
