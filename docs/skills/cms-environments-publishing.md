---
title: Environments & Publishing
description: Configure environments, publish content, use delivery and preview tokens, leverage the Sync API, and understand CDN and publish-queue behavior in Contentstack.
---

# Environments & Publishing

**Slug:** `cms-environments-publishing` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on configuring environments, publishing content, using delivery and preview tokens, leveraging the Sync API, and understanding CDN and publish-queue behavior.

## When it triggers

When you ask about environment setup, publishing behavior, delivery or preview tokens, the Sync API, scheduling, or CDN and caching configuration.

## What it covers

- **Environment design**: treat environments as deployment targets (development, staging, production). Default max 5 per stack. Environments are global modules, shared across branches.
- **Publishing fundamentals**: content is a draft until published to an environment; publishing can target multiple environments and locales. Use `api_version: 3.2` for nested reference publishing so the full reference tree resolves automatically. Always publish entries with their references.
- **Token types**: *Delivery Token:* published content via the CDA, environment-scoped, client-safe. *Preview Token:* unpublished draft content for Live Preview. *Management Token:* stack-level read/write, server-side only.
- **SDK initialization**: stack API key + delivery token + environment, optionally branch/alias. CDA base URLs are region-specific (`cdn.contentstack.io` for AWS NA, `eu-cdn.contentstack.com` for AWS EU, `au-cdn.contentstack.com` for AWS AU).
- **Sync API**: recommended for static sites, offline apps, or local caches. First request returns all published content plus a `sync_token`; later requests return only changes. Prefer it over polling.
- **Publish queue**: tracks publish/unpublish status; each branch has its own queue; scheduled publishes can be cancelled before execution.
- **Rate limits**: 10 req/s individual, 1 req/s bulk per org. Use exponential backoff with jitter; the CLI bulk publish plugin handles rate limiting automatically.

## Example prompts

- "How many environments should I set up?"
- "What's the difference between a delivery token and a preview token?"
- "My content isn't showing on the live site after publishing."
- "How does the Sync API work?"
- "Can I schedule content to publish at a future time?"

## Safety notes

Read-only advisory. Never publishes, unpublishes, or modifies environments. Delivery tokens are client-safe; management tokens must never be exposed client-side. Use environment variables for all token examples.

## Related

- [Tokens & Authentication](cms-tokens-authentication.md) · [Releases](cms-releases.md) · [Entries](cms-entries.md) · [Branches & Aliases](cms-branches-aliases.md)
