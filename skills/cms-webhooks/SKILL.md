---
name: cms-webhooks
description: "Advise developers on configuring and consuming Contentstack webhooks for real-time event notifications. Cover event channels, payload structure, signature verification, retry behavior, release-triggered webhook storms, and reliable receiver design. Use when developers need help setting up webhooks, choosing event channels, handling webhook payloads, verifying signatures, debugging delivery issues, or integrating Contentstack with external systems such as site rebuilds, search indexes, Slack, or CI/CD. For no-code event workflows, use automations."
allowed-tools: Read Grep Glob
---

# Contentstack Webhooks

Advise on connecting Contentstack to external systems with webhooks, and on the operational edge cases: duplicate deliveries, retries, release-triggered bursts and failed deliveries.

## When to use

- Setting up a webhook and choosing event channels.
- Handling webhook payloads.
- Verifying webhook signatures.
- Designing a reliable receiver and choosing a retry policy.
- Debugging missed or failing deliveries.
- Triggering site rebuilds, search indexing, Slack or CI/CD from content events.

Use another skill for:

- No-code event workflows with triggers and connectors → `automations`
- Launch deploy hooks and rebuilds → `launch-platform`
- Releases and what deploying one publishes → `cms-releases`
- Workflow stages and publish rules → `cms-workflows`
- Webhooks for Developer Hub app lifecycle events → `developer-hub-app-architect`

## Before you answer

Find out the integration target (site rebuild, search index, Slack, CI/CD), the events needed, reliability and latency requirements, and, when debugging, a sample payload or the execution log details.

## Instructions

1. Identify the integration target and required events.
2. Recommend the narrowest event channels first, and expand only if needed.
3. Explain payload shape, signature verification and secret handling.
4. Describe receiver reliability: fast 2xx response, async processing and idempotency.
5. Warn about release-triggered bursts and suggest debouncing.
6. Use execution logs to diagnose retries, status codes and response bodies.

### Channels

Event channels use the form `{module}.{action}`, such as `entries.create`, `entries.publish`, `assets.publish` and `content_types.update`, or the longer `{module}.{context}.{action}` form, such as `content_types.entries.publish` or `entries.environments.publish`. Workflow stage changes come from a separate workflow module, not from `entries`; select those events in the webhook UI rather than typing a channel name. Use `$all` only when the integration truly needs every event. Start specific and expand later.

### Payloads

The top-level payload fields are `module`, `api_key`, `event` and `data`. Recommend `concise_payload: true` when the receiver only needs identifiers, and full payloads only when the integration needs complete entry or asset data. Do not promise other top-level fields; inspect a real delivery in the execution log if the receiver depends on one.

### Signature verification

Every webhook request carries an `X-Contentstack-Request-Signature` header, an RSA-PSS SHA-256 signature that the receiver verifies with Contentstack's public key. Point users to the current webhook documentation for the public key and the exact verification steps. Where the plan supports it, a webhook can instead be set to HMAC signing: requests then carry `X-Contentstack-HMAC-Signature`, an HMAC-SHA256 of `{timestamp}.{raw body}` computed with the webhook secret. Verify against the raw body, reject old timestamps to block replays, and reject requests with a missing or invalid signature.

### Release-triggered bursts

Deploying a release publishes every item in it, so publish webhooks can fire once per item. Do not rely on a payload field to identify release traffic. Debounce or batch on the receiver so downstream systems such as site rebuilds run once per burst, and use the execution logs to see what actually fired.

### Reliable receiver design

Recommend four receiver behaviors: verify the signature, return 2xx within 30 seconds, process asynchronously after acknowledging, and handle duplicate deliveries idempotently. A non-2xx response or a 30-second timeout counts as a failed delivery.

### Retry policies

The automatic retry policy retries a failed delivery up to 4 times with exponential backoff, at roughly 5 s, 25 s, 125 s and 625 s. With the manual policy, failed events stay in the execution log and can be re-fired from there or through the API. Direct users to the execution logs for attempts, status codes and response bodies.

### Scope and concurrency

Webhooks are a global module, but each webhook can be assigned to one branch at a time. The organization-level Webhook Configuration setting controls the number of concurrent connections to receivers, not a per-second rate.

## MCP tools

No Contentstack MCP tool creates, lists, sends or deletes webhooks. Configure them in stack Settings → Webhooks or with the Content Management API's webhooks endpoints, and read execution logs there.

Related tools: to point a webhook at a Launch rebuild, `get_deploy_hooks` (`launch`) returns a project's deploy hooks. To see what a release deploy will publish, `get_all_items_in_a_release` (`cma`) lists its items.

## Output

Be concise and practical. Prioritize configuration guidance, signature verification and reliability patterns. Call out the release burst issue whenever release-triggered events are involved.

## Security

### Defaults

- Advisory by default. This skill does not create, modify, send or delete webhooks.
- Never expose webhook secrets.
- Always verify the request signature (`X-Contentstack-Request-Signature`, or `X-Contentstack-HMAC-Signature` when HMAC signing is on) in production.
- Use environment variables for all secrets.
- Do not echo raw secrets, tokens, or signatures in examples.
- Prefer server-side verification and processing patterns.

### Destructive Actions

Do not create, update, delete, or send webhooks. If the user wants a change made, give the steps and the target stack and branch for them to apply.

### Secrets

Never reveal webhook secrets or any credential material. If a secret is needed, instruct the user to store it in environment variables and use it only server-side.

### Environment Variables

Store webhook secrets and related credentials in environment variables. Never hardcode secrets in examples or client-side code.
