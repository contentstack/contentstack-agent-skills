---
title: Webhooks
description: Configure and consume Contentstack webhooks: event channels, payloads, signature verification, retries, release-triggered storms, and reliable receiver design.
---

# Webhooks

**Slug:** `cms-webhooks` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on configuring and consuming webhooks for real-time event notifications, and on operational edge cases like duplicate deliveries, retries, release-triggered storms, and failed deliveries.

## When it triggers

When you need help setting up webhooks, choosing event channels, handling payloads, verifying signatures, debugging delivery issues, or integrating Contentstack with external systems (site rebuilds, search indexes, Slack, CI/CD).

## What it covers

- **Channels**: `{module}.{action}` form, e.g. `entries.create`, `entries.publish`, `assets.publish`, `content_types.update`, `entries.workflow_stage_change`. Start specific; use `$all` only when truly needed.
- **Payloads**: include module, `api_key`, event, `triggered_at`, data, and branch info. Use `concise_payload: true` when the receiver only needs identifiers.
- **Signature verification**: always validate the `X-Contentstack-Signature` header in production (HMAC-SHA256 over the raw body using the webhook secret). Reject missing/invalid signatures.
- **Release-webhook storm**: a release with many items can produce one event per item. Detect release-triggered events via the `source` key and debounce/batch so downstream systems trigger once per release.
- **Reliable receiver design**: validate signatures, return 2xx within 30 seconds, process asynchronously after acknowledgment, and handle duplicate deliveries idempotently.
- **Retry policies**: manual retries are logged for re-execution; auto retries use exponential backoff. Use execution logs for attempts, status codes, and response bodies.
- **Limits & scope**: max 100 webhooks per stack; webhooks are global but can be scoped to a branch; an org-level setting caps max connections per second.

## Example prompts

- "How do I trigger a site rebuild when content is published?"
- "How do I verify a webhook is genuinely from Contentstack?"
- "My webhook receiver gets hundreds of calls when I deploy a release."
- "What retry policy should I use?"
- "How do I debug missed webhook deliveries?"

## Safety notes

Read-only advisory. Never creates, updates, deletes, or sends webhooks. Always validate `X-Contentstack-Signature` in production; never echo raw secrets, tokens, or signatures; keep secrets in environment variables and verify server-side.

## Related

- [Releases](cms-releases.md) · [Workflows & Publish Rules](cms-workflows.md) · [Environments & Publishing](cms-environments-publishing.md)
