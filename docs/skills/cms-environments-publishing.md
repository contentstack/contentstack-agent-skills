---
title: Environments & Publishing
description: Configure environments, publish content, use delivery and preview tokens, leverage the Sync API, and understand CDN and publish-queue behavior in Contentstack.
---

# Environments & Publishing

**Slug:** `cms-environments-publishing` · **Product:** CMS · **Type:** Advisory (acts through MCP tools on request)

Advises on configuring environments, publishing content, using delivery and preview tokens, leveraging the Sync API, and understanding CDN and publish-queue behavior.

## When it triggers

When you ask about environment setup, publishing behavior, delivery or preview tokens, the Sync API, scheduling, or CDN and caching configuration.

## What it covers

- **Environment design**: treat environments as deployment targets (development, staging, production). Environments are global modules, shared across branches.
- **Publishing fundamentals**: content is a draft until published to an environment; publishing can target multiple environments and locales. For nested references, use bulk publish with the `api_version: 3.2` header, which publishes references up to five levels deep with their parents. Always publish entries with their references.
- **Token types**: *Delivery Token:* published content via the CDA, environment-scoped, client-safe. *Preview Token:* unpublished content for Live Preview; client-side only on preview deployments, never in production builds. *Management Token:* stack-level read/write, server-side only, never in the browser.
- **SDK initialization**: stack API key + delivery token + environment, optionally branch/alias. CDA base URLs are region-specific (`cdn.contentstack.io` for AWS NA, `eu-cdn.contentstack.com` for AWS EU, `au-cdn.contentstack.com` for AWS AU, plus `azure-na-cdn`, `azure-eu-cdn`, `gcp-na-cdn` and `gcp-eu-cdn` on `.contentstack.com`).
- **Sync API**: recommended for static sites, offline apps, or local caches. First request returns all published content plus a `sync_token`; later requests return only changes. Prefer it over polling.
- **Publish queue**: tracks publish/unpublish status; each branch has its own queue; scheduled publishes can be cancelled before execution.
- **Rate limits**: CMA 10 req/s and bulk 1 req/s per org; CDA reads are mostly CDN-served. Responses carry `X-RateLimit-Limit`/`X-RateLimit-Remaining`. Use exponential backoff with jitter; the CLI bulk publish plugin handles rate limiting automatically.

## Example prompts

- "How many environments should I set up?"
- "What's the difference between a delivery token and a preview token?"
- "My content isn't showing on the live site after publishing."
- "How does the Sync API work?"
- "Can I schedule content to publish at a future time?"

## MCP tools

With the Contentstack MCP server connected, the agent can inspect environments, the publish queue and publish rules, confirm what an environment serves with the `cda` tools, publish or unpublish entries and assets, and create, update or delete environments. There are no tools for tokens, the Sync API or cancelling a scheduled publish.

## Safety notes

Advisory by default; uses the MCP tools only when you ask for the change. Before publishing, unpublishing or changing an environment it names the environments, locales and items and waits for confirmation. Delivery tokens are client-safe; management tokens must never be exposed client-side. Use environment variables for all token examples.

## Related

- [Tokens & Authentication](cms-tokens-authentication.md) · [Releases](cms-releases.md) · [Entries](cms-entries.md) · [Branches & Aliases](cms-branches-aliases.md)
