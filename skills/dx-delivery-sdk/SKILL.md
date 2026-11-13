---
name: dx-delivery-sdk
description: "Help agents write correct, production-ready TypeScript using `@contentstack/delivery-sdk` for Contentstack entries, assets, references, filtering, sorting, pagination, locale, Live Preview, and Visual Builder support. Verify SDK behavior against the Delivery SDK Spec when method names, options, or chain order matter. Use when a user asks for Contentstack Delivery SDK code, query examples, helper functions, SDK setup, stack initialization, reference inclusion, filtering, sorting, pagination, typed entry fetching, asset fetching, Live Preview setup, Visual Builder support, SSR preview handling, or debugging SDK query chains. For GraphQL, use cms-graphql; for rendering JSON RTE fields, use cms-json-rte; for Live Preview troubleshooting, use cms-live-preview-visual-editor-support-assistant."
allowed-tools: Read Grep Glob
---

# Contentstack Delivery SDK

Write correct, production-ready TypeScript with `@contentstack/delivery-sdk`: entries, assets, references, filtering, sorting, pagination, locale, Live Preview and Visual Builder support. The SDK reads published content, assets and taxonomy from the Content Delivery API.

## When to use

- Delivery SDK setup and stack initialization.
- Query examples and helper functions: references, filtering, sorting, pagination, field selection, locale.
- Typed entry and asset fetching.
- Live Preview, Visual Builder and SSR preview setup in SDK code.
- Debugging SDK query chains.

Use another skill for:

- Migrating JavaScript SDK code to TypeScript → `dx-migrate-js-to-ts-sdk`
- GraphQL queries → `cms-graphql`
- Rendering JSON RTE fields and embedded items → `cms-json-rte`
- Diagnosing broken Live Preview or Visual Editor setups → `cms-live-preview-visual-editor-support-assistant`
- Work inside the Next.js kickstart repo → `dx-kickstart-next`
- CDA query semantics beyond the SDK (raw REST, Sync API) → `cms-entries`

## Before you answer

Identify the content type UID, any entry or asset UID, the field UIDs for filters, sorting, selection or references, the locale, the return shape the user wants, and whether SSR or Visual Builder is involved. Ask only for what is missing to build the query correctly.

## Instructions

1. Identify the target object: entry, asset, content type, taxonomy, or helper.
2. Check the Delivery SDK Spec when method names, options, or chain order matter.
3. Ask only for missing inputs needed to build the query correctly.
4. Choose the correct SDK chain and method order.
5. Add pagination, locale, field selection, and references as needed.
6. Use safe TypeScript types and reusable helpers.
7. Include error handling and common-mistake warnings when relevant, such as wrong query methods, missing pagination, or shared SSR Live Preview stacks.


### Identify the target

Determine whether the request is for entries, assets, taxonomy, references, Live Preview, or a reusable helper. Ask only for missing UIDs, locale, references, or return shape when needed.

### Verify SDK behavior

Use the Delivery SDK Spec as the source of truth for method names, supported options, and chain order. If the request depends on SDK behavior, confirm the exact API before answering.

### Use current SDK patterns

Prefer TypeScript and the current `@contentstack/delivery-sdk` API. Use safe environment-based credentials and avoid hardcoded tokens or host values unless they are documented defaults.

### Build correct queries

Apply references before `.query()`, use `QueryOperation` for filters, use `orderByAscending()` / `orderByDescending()` for sorting, and add pagination for collection queries.

### Handle Live Preview safely

For SSR or Visual Builder, create a new stack per request and apply live preview configuration before fetching. Do not reuse a Live Preview stack across requests.

### Packages and hosts

- Prefer `@contentstack/delivery-sdk` as the primary SDK.
- Use `@timbenniks/contentstack-endpoints` for region-specific preview hosts when needed. It is a community package (not published under `@contentstack/`) that the official kickstarts use to resolve region hosts.
- Use `getContentstackEndpoints(region, true)` so SDK host values omit `https://`.
- For SSR Live Preview or Visual Editor (formerly Visual Builder), create a new stack per request.
- Cache policies other than `Policy.IGNORE_CACHE` need `@contentstack/persistence-plugin`: pass a `PersistenceStore` as `cacheOptions.persistenceStore`.

## MCP tools

When the Contentstack MCP server is connected, use read tools to ground SDK code in the real stack instead of guessing UIDs (local server group in brackets):

- Inspect the model: `get_all_content_types`, `get_a_single_content_type`, `get_all_global_fields`, `get_all_languages`, `get_all_environments` (`cma`)
- Check what the SDK will return: `get_all_entries_cdn`, `get_a_single_entry_cdn`, `get_all_assets_cdn`, `get_a_single_asset_cdn` (`cda`)

The `cda` tools read published content with a delivery token, the same data the SDK sees. This skill needs no write tools.

## Output

- Prefer TypeScript, in concise, production-ready code blocks.
- Verify method-order constraints against the Delivery SDK Spec when they matter.
- Do not hardcode credentials.
- Call out pagination limits when returning multiple entries.
- Include brief notes for Live Preview or SSR safety when relevant.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only to read the stack.
- Delivery tokens are read-only and safe for client-side code.
- Preview tokens read unpublished content: use them only in preview deployments, never in production builds.
- Never put management tokens in SDK or client code.
- Never hardcode Contentstack credentials in examples, and avoid sharing preview tokens or other secrets in responses.
- For SSR Live Preview, do not reuse a stack instance across requests.

### Destructive Actions

This skill does not perform destructive actions. If a request implies deleting, publishing, or mutating content, name the target and get explicit confirmation before proceeding.

### Secrets

Use environment variables for all credentials and tokens. Never print, infer, or echo secrets. If a secret is missing, request the variable name or show a placeholder only.

### Environment Variables

Use `process.env` placeholders in examples. Prefer required non-null assertions only when the surrounding code clearly validates configuration. Do not suggest committing secrets to source control.

## References

Read these on demand when their content is relevant; don't assume their contents from the summaries.

- [Delivery SDK Spec](references/delivery-sdk-spec.md) (required): the TypeScript Delivery SDK reference for Node.js and React Native. Source: https://www.contentstack.com/docs/developers/sdks/content-delivery-sdk/typescript/reference.md

## Examples

### Stack setup (few shot *)

**User:** Set up the Contentstack Delivery SDK in TypeScript.

**Assistant:** ```ts
import contentstack, { QueryOperation } from "@contentstack/delivery-sdk";

const stack = contentstack.stack({
  apiKey: process.env.CONTENTSTACK_API_KEY!,
  deliveryToken: process.env.CONTENTSTACK_DELIVERY_TOKEN!,
  environment: process.env.CONTENTSTACK_ENVIRONMENT!,
  region: process.env.CONTENTSTACK_REGION || "us",
});
```

*Default stack setup with env vars and current import style.*

### Live Preview stack factory (few shot *)

**User:** Show the recommended SSR Live Preview setup.

**Assistant:** ```ts
import contentstack from "@contentstack/delivery-sdk";

export function createStack() {
  return contentstack.stack({
    apiKey: process.env.CONTENTSTACK_API_KEY!,
    deliveryToken: process.env.CONTENTSTACK_DELIVERY_TOKEN!,
    environment: process.env.CONTENTSTACK_ENVIRONMENT!,
    region: process.env.CONTENTSTACK_REGION || "us",
    live_preview: {
      enable: true,
      preview_token: process.env.CONTENTSTACK_PREVIEW_TOKEN,
      host: "rest-preview.contentstack.com",
    },
  });
}
```

*Per-request factory for SSR or Visual Builder.*

### Single entry fetch (few shot *)

**User:** Fetch one blog post by UID.

**Assistant:** ```ts
const entry = await stack.contentType("blog_post").entry("entry_uid").fetch();
```

*Use direct fetch for single entries.*

### Entry query (few shot *)

**User:** Fetch multiple blog posts.

**Assistant:** ```ts
const result = await stack.contentType("blog_post").entry().query().find();
const entries = result.entries;
```

*Use query().find() for collections.*

### References (few shot *)

**User:** Include author and category references.

**Assistant:** ```ts
const result = await stack
  .contentType("blog_post")
  .entry()
  .includeReference(["author", "category"])
  .query()
  .find();
```

*`includeReference()` belongs before `.query()`.*

### Filtering (few shot *)

**User:** Filter by title.

**Assistant:** ```ts
const result = await stack
  .contentType("blog_post")
  .entry()
  .query()
  .where("title", QueryOperation.EQUALS, "My Post")
  .find();
```

*Use `QueryOperation` names exactly.*

### Sorting (few shot *)

**User:** Sort by publish date descending.

**Assistant:** ```ts
const result = await stack
  .contentType("blog_post")
  .entry()
  .query()
  .orderByDescending("published_date")
  .find();
```

*Never use `.descending()`.*

### Pagination (few shot *)

**User:** Return page 1 with 10 items and total count.

**Assistant:** ```ts
const result = await stack
  .contentType("blog_post")
  .entry()
  .query()
  .skip(0)
  .limit(10)
  .includeCount()
  .find();
```

*Mention the 100-item default limit when pagination is omitted.*

### Field selection (few shot *)

**User:** Only fetch title and url.

**Assistant:** ```ts
const result = await stack
  .contentType("blog_post")
  .entry()
  .query()
  .only(["title", "url"])
  .find();
```

*Use `only()` and `except()` for payload control.*

### Asset fetch and query (few shot *)

**User:** Fetch an asset and query JPEG assets.

**Assistant:** ```ts
const asset = await stack.asset("asset_uid").fetch();

const result = await stack
  .asset()
  .query()
  .where("content_type", QueryOperation.EQUALS, "image/jpeg")
  .find();
```

*Support both direct fetch and asset queries.*

### Helper function pattern (few shot *)

**User:** Create reusable helpers for fetching entries.

**Assistant:** ```ts
export async function getEntryByUrl(contentTypeUid: string, url: string) {
  try {
    const result = await stack
      .contentType(contentTypeUid)
      .entry()
      .query()
      .where("url", QueryOperation.EQUALS, url)
      .includeCount()
      .find();

    return result.entries[0] || null;
  } catch (error) {
    if (error instanceof Error) {
      console.error("Failed to fetch entry by url:", error.message);
    }
    return null;
  }
}
```

*Include safe error handling in reusable helpers.*

### Common mistakes checklist (edge case *)

**User:** What mistakes should I avoid with the Delivery SDK?

**Assistant:** - Do not call `includeReference()` after `.query()`.
- Use `orderByAscending()` / `orderByDescending()`, not `ascending()` / `descending()`.
- Use `QueryOperation.NOT_EQUALS`, not `NOT_EQUAL`.
- Do not hardcode credentials.
- Add pagination for collection queries.
- Do not reuse a Live Preview SSR stack across requests.

*Use as a compact guardrail response.*