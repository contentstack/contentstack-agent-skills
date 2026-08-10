---
title: Delivery SDK
description: Write correct, production-ready TypeScript with @contentstack/delivery-sdk for entries, assets, references, filtering, sorting, pagination, locale, Live Preview, and Visual Builder.
---

# Delivery SDK

**Slug:** `dx-delivery-sdk` · **Product:** Developer Experience · **Type:** Advisory (read-only) · **Ships references**

Helps agents write correct, production-ready TypeScript using `@contentstack/delivery-sdk`, and verifies SDK behavior against the Delivery SDK Spec when method names, options, or chain order matter.

## When it triggers

When you ask for Delivery SDK code, query examples, helper functions, SDK setup, stack initialization, reference inclusion, filtering, sorting, pagination, typed entry fetching, asset fetching, Live Preview setup, Visual Builder support, SSR preview handling, or debugging SDK query chains.

## What it covers

- **Stack setup**: `contentstack.stack({...})` with env-based credentials and region.
- **Single entry vs collections**: `.contentType(uid).entry(uid).fetch()` for one; `.entry().query().find()` for many.
- **References**: `includeReference([...])` belongs _before_ `.query()`.
- **Filtering**: use `QueryOperation` names exactly (e.g. `QueryOperation.EQUALS`, `NOT_EQUALS`).
- **Sorting**: `orderByAscending()` / `orderByDescending()` (never `ascending()` / `descending()`).
- **Pagination**: `.skip().limit().includeCount()`; mention the 100-item default limit when pagination is omitted.
- **Field selection**: `only()` / `except()`.
- **Assets**: direct `stack.asset(uid).fetch()` and asset queries.
- **Helper patterns**: reusable typed helpers with safe error handling.
- **Live Preview / SSR**: create a new stack per request; apply live preview config before fetching; never reuse a Live Preview stack across requests.

### Common mistakes it prevents

- Calling `includeReference()` after `.query()`.
- Using `ascending()` / `descending()` or `NOT_EQUAL`.
- Hardcoding credentials.
- Missing pagination on collection queries.
- Reusing a Live Preview SSR stack across requests.

## Example prompts

- "Set up the Contentstack Delivery SDK in TypeScript."
- "Write a query for blog posts with author references included."
- "Show the recommended SSR Live Preview setup."
- "Fix this query chain. It's not returning the right entries."
- "Create a helper to fetch entries by URL with pagination and typing."

## References

Ships the **Delivery SDK Spec** (`references/delivery-sdk-spec.md`), sourced from the official TypeScript Delivery SDK reference. The skill reads it on demand to verify method names, options, and chain order.

## Safety notes

Prefers TypeScript and current `@contentstack/delivery-sdk` APIs. Never hardcodes credentials; uses `process.env` placeholders. For SSR Live Preview, never reuses a stack across requests. Uses `@timbenniks/contentstack-endpoints` with `getContentstackEndpoints(region, true)` for region-specific preview hosts when needed.

## Related

- [Entries](cms-entries.md) · [Live Preview & Visual Builder Support](cms-live-preview-visual-builder-support-assistant.md) · [Migrate JS→TS SDK](dx-migrate-js-to-ts-sdk.md)
