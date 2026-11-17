---
title: Tokens & Authentication
description: "Choose the right Contentstack authentication method and token type for frontend, backend, automation, and third-party apps, with security, rate-limit, and SSO guidance."
---

# Tokens & Authentication

**Slug:** `cms-tokens-authentication` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on choosing the right authentication method and token type, with clear client-side vs server-side safety guidance, rate-limit awareness, and SSO considerations.

## When it triggers

When you ask about authentication, token types, API keys, rate limits, SSO integration, or credential security.

## What it covers

**Token decision rules:**

| Use case | Token |
| --- | --- |
| Frontend reads of published content | Delivery token |
| Live Preview of draft content | Preview token (client-side only on preview deployments, never in production builds) |
| Backend automation, CI/CD, migration scripts | Management token |
| Interactive user sessions | Authtoken (only when appropriate) |
| Third-party apps | OAuth with scoped access |
| Service-to-service automation | Machine-to-machine (M2M) app with OAuth client credentials |

Plus:

- **Key limits**: a stack can have at most 10 valid management tokens at a time, and each can expire on a date or never. Authtokens are user-specific with their own limits. Watch the `x-ratelimit-limit` and `x-ratelimit-remaining` headers and 429s.
- **Preview tokens**: a separate credential that only the Preview Service accepts, used together with the short-lived `live_preview` hash.
- **SSO organizations**: SSO blocks password login, so scripts can't get authtokens that way. For automation in SSO orgs, use management tokens, OAuth or an M2M app.
- **Security rules**. Never expose management tokens or authtokens client-side; use environment variables; rotate credentials; least privilege.
- **Rate-limit handling**: exponential backoff with jitter for 429s; check rate-limit headers before retrying.

## Example prompts

- "What token should I use in my frontend app?"
- "What's the difference between a management token and an authtoken?"
- "How do I handle rate limits in my script?"
- "Can I use authtokens in an SSO-enabled organization?"
- "How many management tokens can I have per stack?"

## MCP tools

No Contentstack MCP tool creates, rotates or deletes tokens; manage them in stack Settings → Tokens and M2M apps in Developer Hub. The skill explains how the MCP server itself authenticates (OAuth, or a management token for the `cma` groups) and can read an app's OAuth scopes with `get_oauth_scopes` and `get_app_oauth` (`developerhub`).

## Safety notes

Read-only advisory. Never creates, modifies, or deletes tokens. Never displays real secrets or example real tokens; always states whether a credential is client-safe or server-side only. Uses placeholders like `CONTENTSTACK_API_KEY`, `CONTENTSTACK_DELIVERY_TOKEN`, `CONTENTSTACK_MANAGEMENT_TOKEN`.

## Related

- [Roles & Permissions](cms-roles-permissions.md) · [Environments & Publishing](cms-environments-publishing.md) · [Security & safety model](../how-it-works/security-model.md)
