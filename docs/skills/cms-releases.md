---
title: Releases
description: Use Contentstack Releases for coordinated, atomic content deployment: creation, item management, staged deployment, webhook-storm prevention, and CI/CD.
---

# Releases

**Slug:** `cms-releases` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on using Releases to deploy related content changes atomically so campaigns, redesigns, or coordinated updates go live together without manual coordination errors.

## When it triggers

When you ask about deploying multiple content changes together, campaign launches, coordinated content updates, release scheduling, or CI/CD content deployment.

## What it covers

- **Release workflow**: create a release with a descriptive name, add all related entries and assets (across content types and locales), deploy to staging first, validate, then deploy to production. Specify which version of each entry to deploy when needed.
- **Webhook storm**: a release deployment triggers one webhook event per item. Debounce receivers and inspect the `source` key in payloads. See [Webhooks](cms-webhooks.md) for receiver handling.
- **Limitations**: max 100 items per API call when adding items; release titles max 50 characters; updating items to latest versions does not auto-add new references from updated entries; releases are branch-specific.
- **CI/CD integration**: create a release → add changed items → deploy to staging → run tests → deploy to production on success. Combine with branches and aliases.
- **When not to use**: not for routine single-entry publishes; use releases when coordinated multi-item deployment is required.

## Example prompts

- "How do I deploy a campaign with 50 entries at once?"
- "Can I schedule a release for a future date?"
- "My static site rebuilds hundreds of times per release deployment."
- "How do I integrate releases with my CI/CD pipeline?"
- "What are the limits on releases?"

## Safety notes

Read-only advisory. Never creates, deploys, updates, or deletes releases. Use environment variables for credentials; no client-side access to management credentials.

## Related

- [Webhooks](cms-webhooks.md) · [Branches & Aliases](cms-branches-aliases.md) · [Environments & Publishing](cms-environments-publishing.md)
