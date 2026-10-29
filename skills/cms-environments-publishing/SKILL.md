---
name: cms-environments-publishing
description: "Advise developers on configuring environments, publishing content, using delivery and preview tokens, leveraging the Sync API, and understanding CDN and publish queue behavior in Contentstack. Use when developers ask about environment setup, publishing behavior, delivery or preview tokens, the Sync API, scheduling, or CDN and caching configuration in Contentstack. For Launch hosting environments, use launch-platform."
allowed-tools: Read Grep Glob
---

# Contentstack Environments & Publishing

Advise on how content moves from draft to live: environments, publishing and scheduling, the token for each job, the Sync API, the publish queue and CDN behavior.

## When to use

- Designing environments for a deployment pipeline.
- Content that doesn't appear on the live site after publishing.
- Choosing between delivery, preview and management tokens.
- Scheduling publishes and reading the publish queue.
- Setting up the Sync API, regional CDA hosts and rate limits.

Use another skill for:

- Launch hosting environments, builds and deploys → `launch-platform`
- Token types, scopes and auth in depth → `cms-tokens-authentication`
- Publishing many entries together on a schedule → `cms-releases`
- Approval stages and publish rules → `cms-workflows`
- Rebuilding a site when content publishes → `cms-webhooks`
- Entry queries and bulk publish details → `cms-entries`
- Branch and alias deployment → `cms-branches-aliases`

## Before you answer

Find out the deployment pipeline and environments, the frontend framework or static site generator, the token or auth question, and any scheduling or publish queue concern.

## Instructions

1. Understand the deployment pipeline.
2. Recommend the environment structure.
3. Explain the token types and which one applies.
4. Guide publishing, scheduling and reference publishing.
5. Recommend the Sync API for static sites or local caches.
6. When content is missing after a publish, troubleshoot step by step.

### Environment design

Treat environments as deployment targets such as development, staging and production. Keep them aligned with the real deployment pipeline. Environments are global modules, shared across branches.

### Publishing fundamentals

Content is a draft until explicitly published to an environment. Publishing can target one or more environments and locales. For nested references, use the bulk publish API with the `api_version: 3.2` header, which publishes referenced entries up to five levels deep together with their parents. Always publish entries with their references.

### Token types

Use the correct token in every answer: Delivery Token for published content via the CDA, environment-scoped and safe for client-side use; Preview Token for unpublished draft content in Live Preview; Management Token for stack-level read/write access, server-side only, never exposed client-side.

### SDK initialization

When relevant, mention stack API key plus delivery token plus environment name, and optionally branch or alias ID. CDA base URLs are region-specific: `cdn.contentstack.io` (AWS NA), `eu-cdn.contentstack.com` (AWS EU), `au-cdn.contentstack.com` (AWS AU), `azure-na-cdn.contentstack.com` (Azure NA), `azure-eu-cdn.contentstack.com` (Azure EU), `gcp-na-cdn.contentstack.com` (GCP NA) and `gcp-eu-cdn.contentstack.com` (GCP EU).

### Sync API

Recommend the Sync API for static sites, offline apps, or local content caches. The first request returns all published content plus a `sync_token`, and later requests return only changes such as created, updated, deleted, published, and unpublished items. Prefer it over polling when near-real-time updates are needed without excessive API usage.

### Publish queue

The publish queue tracks publish and unpublish operations and their status. Each branch has its own queue, and scheduled publishes can be cancelled before execution.

### Rate limits

The CMA allows 10 requests per second per organization, and bulk operations 1 request per second. CDA reads are mostly served from the CDN cache and don't count against the origin limit. Responses carry `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers. Recommend exponential backoff with jitter for scripts, and note that the CLI bulk publish plugin handles rate limiting automatically.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `get_all_environments`, `get_an_environment`, `get_publish_queue` (`cma`); `get_publish_queue_activity`, `get_publish_rules` (`cma-extended`); `get_all_entries_cdn`, `get_a_single_entry_cdn` (`cda`, to confirm what an environment serves)
- Change: `create_an_environment`, `update_an_environment`, `publish_an_entry` (can schedule), `publish_an_asset`, `publish_variants_of_an_entry` (`cma`)
- Delete or withdraw: `delete_an_environment`, `unpublish_an_entry`, `unpublish_an_asset` (`cma`)

There are no tools for tokens, the Sync API or cancelling a scheduled publish; use the UI or the CMA. For "published but not live", check `get_publish_queue` for the job's status, then `get_a_single_entry_cdn` with the environment's delivery token.

## Output

Be concise and practical. Always say which token type applies, never recommend client-side use of management tokens, and troubleshoot step by step when content is missing after a publish.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Delivery tokens are safe for client-side code.
- Management tokens must never be exposed client-side; route CMA calls through a server-side proxy in browser apps.
- Use environment variables for all token examples, and never hardcode tokens in frontend code.

### Destructive Actions

Before publishing, unpublishing, or creating, updating or deleting an environment, name the stack, branch, environments, locales and items, explain the impact (publishing to production changes the live site; deleting an environment affects every branch, since environments are global), and wait for confirmation.

### Secrets

Never expose management tokens, API keys, or other secrets. Use environment variables in all examples. Never hardcode tokens in frontend or client-side code.

### Environment Variables

Use environment variables for all token and API key examples. Prefer server-side injection for management credentials and client-safe delivery token usage only where appropriate.
