---
title: Releases
description: "Use Contentstack Releases for coordinated, atomic content deployment: creation, item management, staged deployment, webhook-storm prevention, and CI/CD."
---

# Releases

**Slug:** `cms-releases` · **Product:** CMS · **Type:** Advisory (acts through MCP tools on request)

Advises on using Releases to deploy related content changes atomically so campaigns, redesigns, or coordinated updates go live together without manual coordination errors.

## When it triggers

When you ask about deploying multiple content changes together, campaign launches, coordinated content updates, release scheduling, or CI/CD content deployment.

## What it covers

- **Release workflow**: create a release with a descriptive name, add all related entries and assets (across content types and locales), deploy to staging first, validate, then deploy to production. Specify which version of each entry to deploy when needed.
- **Webhook bursts**: deploying a release publishes each item, so per-item publish webhooks can fire. Debounce or batch receivers and check execution logs. See [Webhooks](cms-webhooks.md) for receiver handling.
- **Limitations**: max 25 items per request when adding items; updating items to latest versions does not auto-add new references from updated entries; releases are branch-specific.
- **Releases v2** (plan-gated): multi-locale bulk add, clone, and update-all-items-to-latest; nested references can be included when adding items.
- **CI/CD integration**: create a release → add changed items → deploy to staging → run tests → deploy to production on success. Combine with branches and aliases.
- **When not to use**: not for routine single-entry publishes; use releases when coordinated multi-item deployment is required.

## Example prompts

- "How do I deploy a campaign with 50 entries at once?"
- "Can I schedule a release for a future date?"
- "My static site rebuilds hundreds of times per release deployment."
- "How do I integrate releases with my CI/CD pipeline?"
- "What are the limits on releases?"

## MCP tools

With the Contentstack MCP server connected, the agent can list releases and their items, create and clone releases, add items (25 per request), remove items, and deploy a release. There is no tool to delete a whole release.

## Safety notes

Advisory by default; uses the MCP tools only when you ask for the change. Before creating, changing or deploying a release it names the release, branch, environments, locales and item count and waits for confirmation. Use environment variables for credentials; no client-side access to management credentials.

## Related

- [Webhooks](cms-webhooks.md) · [Branches & Aliases](cms-branches-aliases.md) · [Environments & Publishing](cms-environments-publishing.md)
