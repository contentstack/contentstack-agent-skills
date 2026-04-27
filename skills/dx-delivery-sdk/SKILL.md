---
name: dx-delivery-sdk
description: "Help agents write correct, production-ready TypeScript using `@contentstack/delivery-sdk` for Contentstack entries, assets, references, filtering, sorting, pagination, locale, Live Preview, and Visual Builder support. Verify SDK behavior against the Delivery SDK Spec when method names, options, or chain order matter."
allowed-tools: Read Grep Glob
---

# dx-delivery-sdk

## Description

Help agents write correct, production-ready TypeScript using `@contentstack/delivery-sdk` for Contentstack entries, assets, references, filtering, sorting, pagination, locale, Live Preview, and Visual Builder support. Verify SDK behavior against the Delivery SDK Spec when method names, options, or chain order matter.

## When to Use

Use when a user asks for Contentstack Delivery SDK code, query examples, helper functions, SDK setup, stack initialization, reference inclusion, filtering, sorting, pagination, typed entry fetching, asset fetching, Live Preview setup, Visual Builder support, SSR preview handling, or debugging SDK query chains.

## User Problem

Users need current, correct Contentstack Delivery SDK code with the right method names, chain order, and query patterns. The skill should prevent subtle SDK mistakes and default to production-ready TypeScript.

## Success Criteria

- Uses current `@contentstack/delivery-sdk` method names and correct chain order.
- Verifies API details against the Delivery SDK Spec when behavior is uncertain.
- Produces TypeScript-first examples with safe environment-based credentials.
- Handles references, filters, sorting, pagination, field selection, assets, locale, and Live Preview correctly.
- Flags or avoids common mistakes such as wrong query methods, missing pagination, or shared SSR Live Preview stacks.

## Expected Inputs

- Content type UID
- Entry UID or asset UID when applicable
- Field UIDs for filters, sorting, selection, or references
- Locale when localized content is needed
- Desired return shape or helper function behavior
- SSR or Visual Builder context when Live Preview is involved

## Expected Outputs

- TypeScript code snippets
- Reusable helper functions
- Correct SDK query chains
- Live Preview or SSR-safe stack setup
- Debugging guidance for incorrect Contentstack SDK usage

## Example User Requests

- Write a Contentstack Delivery SDK query for blog posts with author references included.
- Show me the correct TypeScript setup for Contentstack Live Preview in Next.js SSR.
- Fix this Contentstack query chain; it is not returning the right entries.
- Create a helper to fetch entries by URL with pagination and typing.
- How do I fetch assets and filter by content type in `@contentstack/delivery-sdk`?

## Workflow Summary

1. Identify the target object: entry, asset, content type, taxonomy, or helper.
2. Check the Delivery SDK Spec when method names, options, or chain order matter.
3. Ask only for missing inputs needed to build the query correctly.
4. Choose the correct SDK chain and method order.
5. Add pagination, locale, field selection, and references as needed.
6. Use safe TypeScript types and reusable helpers.
7. Include error handling and common-mistake warnings when relevant.

## Instructions

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

## Output Format

Prefer TypeScript.
Use concise, production-ready code blocks.
Verify method-order constraints against the Delivery SDK Spec when they matter.
Do not hardcode credentials.
Call out pagination limits when returning multiple entries.
Include brief notes for Live Preview or SSR safety when relevant.

## Tooling Notes

Prefer `@contentstack/delivery-sdk` as the primary SDK.
Use `@timbenniks/contentstack-endpoints` for region-specific preview hosts when needed.
Use `getContentstackEndpoints(region, true)` so SDK host values omit `https://`.
For SSR Live Preview or Visual Builder, create a new stack per request.

## Security

### Defaults

Never expose deployment tokens or environment secrets.
Validate deployment targets before triggering.
Require confirmation for production deployments.
Never auto-deploy to production without review.
Never hardcode Contentstack credentials in examples.
Avoid sharing preview tokens or other secrets in responses.
For SSR Live Preview, do not reuse a stack instance across requests.

### Destructive Actions

This skill does not perform destructive actions. If a request implies deleting, publishing, or mutating production content, require explicit confirmation and verify the target before proceeding.

### Secrets

Use environment variables for all credentials and tokens. Never print, infer, or echo secrets. If a secret is missing, request the variable name or show a placeholder only.

### Environment Variables

Use `process.env` placeholders in examples. Prefer required non-null assertions only when the surrounding code clearly validates configuration. Do not suggest committing secrets to source control.

## Product Context

- - Product: Developer Experience
- - Description: Developer experience tooling
- - Product safety rules: - Never expose deployment tokens or environment secrets.
- Validate deployment targets before triggering.
- Require confirmation for production deployments.
- Never auto-deploy to production without review.

## References

This skill ships reference material in the `references/` folder. Read those files on demand when their content is relevant to the task — do not assume their contents from the summaries below.

### [Delivery SDK Spec](references/delivery-sdk-spec.md) (product doc, required)
- Source: Official Docs (https://www.contentstack.com/docs/developers/sdks/content-delivery-sdk/typescript/reference.md)
- Summary: Contentstack offers the TypeScript Delivery SDK for building applications. Below, is an in-depth guide and valuable resources to initiate your journey with our TypeScript Delivery SDK. Additionally, the SDK supports the creating applications for Node.js and React Native environments.
- Read: `references/delivery-sdk-spec.md`

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