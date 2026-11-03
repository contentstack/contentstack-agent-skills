---
title: Webhooks
description: "Configure and consume Contentstack webhooks: event channels, payloads, signature verification, retries, release-triggered storms, and reliable receiver design."
---

# Webhooks

**Slug:** `cms-webhooks` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on configuring and consuming webhooks for real-time event notifications, and on operational edge cases like duplicate deliveries, retries, release-triggered storms, and failed deliveries.

## When it triggers

When you need help setting up webhooks, choosing event channels, handling payloads, verifying signatures, debugging delivery issues, or integrating Contentstack with external systems (site rebuilds, search indexes, Slack, CI/CD).

## What it covers

- **Channels**: `{module}.{action}` form (e.g. `entries.create`, `assets.publish`, `content_types.update`) or `{module}.{context}.{action}` (e.g. `content_types.entries.publish`). Workflow stage events come from a separate workflow module; pick them in the webhook UI. Start specific; use `$all` only when truly needed.
- **Payloads**: top-level `module`, `api_key`, `event` and `data`. Use `concise_payload: true` when the receiver only needs identifiers.
- **Signature verification**: every request carries `X-Contentstack-Request-Signature` (RSA-PSS SHA-256), verified with Contentstack's public key. With HMAC signing enabled (plan feature), requests carry `X-Contentstack-HMAC-Signature`, an HMAC-SHA256 of `{timestamp}.{raw body}` with the webhook secret. Reject missing/invalid signatures and stale timestamps.
- **Release-triggered bursts**: deploying a release publishes each item, so publish webhooks can fire per item. Debounce or batch on the receiver so downstream systems trigger once per burst; check execution logs for what fired.
- **Reliable receiver design**: validate signatures, return 2xx within 30 seconds, process asynchronously after acknowledgment, and handle duplicate deliveries idempotently.
- **Retry policies**: automatic retries up to 4 times with exponential backoff (about 5 s, 25 s, 125 s, 625 s); manual failures stay in the execution log to re-fire. Use execution logs for attempts, status codes, and response bodies.
- **Scope & concurrency**: webhooks are global but each can be assigned to one branch at a time; the org-level Webhook Configuration setting caps concurrent connections.

## Example prompts

- "How do I trigger a site rebuild when content is published?"
- "How do I verify a webhook is genuinely from Contentstack?"
- "My webhook receiver gets hundreds of calls when I deploy a release."
- "What retry policy should I use?"
- "How do I debug missed webhook deliveries?"

## MCP tools

No Contentstack MCP tool manages webhooks, so they are configured in stack Settings → Webhooks or through the CMA. The agent can use `get_deploy_hooks` (`launch`) to find a Launch deploy hook to target, and `get_all_items_in_a_release` (`cma`) to size a release burst.

## Safety notes

Read-only advisory. Never creates, updates, deletes, or sends webhooks. Always verify the request signature in production; never echo raw secrets, tokens, or signatures; keep secrets in environment variables and verify server-side.

## Related

- [Releases](cms-releases.md) · [Workflows & Publish Rules](cms-workflows.md) · [Environments & Publishing](cms-environments-publishing.md)
