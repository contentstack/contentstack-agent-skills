---
name: cms-tokens-authentication
description: "Advise developers on choosing the right Contentstack authentication method and token type for frontend, backend, automation, and third-party app use cases. Include security guidance, rate-limit awareness, and SSO considerations. Use when developers ask about authentication, token types, API keys, rate limits, SSO integration, or credential security. For role and team design, use cms-roles-permissions."
allowed-tools: Read Grep Glob
context: fork
agent: general-purpose
---

# Tokens & Authentication

Recommend the right Contentstack authentication method and token type for the use case, and the safest way to use it.

## When to use

- Choosing a token for a frontend, backend script, CI/CD pipeline, migration, third-party app or interactive session.
- Comparing management tokens, authtokens, delivery and preview tokens, OAuth and machine-to-machine (M2M) apps.
- Handling rate limits and 429 responses.
- Authenticating in an SSO-enforced organization.
- Keeping credentials safe.

Use another skill for:

- Roles, custom roles, teams and effective permissions → `cms-roles-permissions`
- Environments, delivery tokens per environment and publishing → `cms-environments-publishing`
- Live Preview setup and preview token troubleshooting → `cms-live-preview-visual-editor-support-assistant`
- OAuth scopes and M2M setup inside a Developer Hub app → `developer-hub-app-architect`
- Authenticating the `csdx` CLI → `dx-cli`; authenticating MCP clients → `dx-mcp-server`

## Before you answer

Find out the use case and where the code runs (browser, server, CI, script), whether the organization enforces SSO, any rate-limit concerns, and security requirements.

## Instructions

1. Identify the use case and runtime environment.
2. Recommend the authentication method or token type.
3. State what is safe for client-side versus server-side use.
4. Add security and credential-handling guidance.
5. Explain rate limits and backoff if relevant.
6. Include SSO constraints when applicable.

### Token decision rules

Frontend reads of published content: use a delivery token. Live preview of draft content: use a preview token. Backend automation, CI/CD, and migration scripts: use a management token. Interactive user sessions: use an authtoken only when appropriate. Third-party apps: prefer OAuth with scoped access. Service-to-service automation: prefer a machine-to-machine (M2M) app.

### Key limits

A stack can have at most 10 valid management tokens at a time. A management token can expire on a set date or never, so prefer an expiry date and rotate. Authtokens are user-specific and have their own limits. Responses carry `x-ratelimit-limit` and `x-ratelimit-remaining` headers; mention them and a retry strategy when the user asks about throughput or 429 errors.

### Machine-to-machine apps

For service-to-service automation with no human session, recommend a machine-to-machine (M2M) app. It uses the OAuth client-credentials grant, is created at the organization level, and can be scoped to specific stacks. Prefer it over long-lived personal credentials for new integrations.

### Preview tokens

The preview token is a separate credential that only the Preview Service accepts. It reads draft content for Live Preview and only works together with the short-lived `live_preview` hash. Keep it out of production builds.

### SSO organizations

When an organization enforces SSO, password-based login is blocked for its users, so scripts can't obtain authtokens that way. For automation in SSO orgs, recommend management tokens, OAuth or an M2M app.

### Security rules

Never expose management tokens or authtokens in client-side code. Use environment variables for credentials. Never hardcode secrets in source code. Recommend rotation and least-privilege access.

### Rate limit handling

Recommend exponential backoff with jitter for 429 responses. Advise checking rate-limit headers before retrying. Keep guidance practical and concise.

## MCP tools

No Contentstack MCP tool creates, rotates or deletes tokens. Manage delivery, preview and management tokens in the stack's Settings → Tokens, and M2M apps in Developer Hub.

The MCP server itself authenticates with OAuth (`npx @contentstack/mcp --auth`, or the Profile Hub sign-in) or, for the `cma` groups only, a management token; see `dx-mcp-server`. For OAuth app scopes, `get_oauth_scopes` and `get_app_oauth` (`developerhub`) read what an app requests.

## Output

Be concise and direct. Always state whether a credential is safe for client-side or server-side use. Use bullets when comparing token types. Do not include raw secrets or example real tokens.

## Security

### Defaults

- Advisory by default. This skill does not create, modify, rotate or delete tokens.
- Never expose management tokens, authtokens, API keys, or OAuth secrets.
- Use placeholders and environment variables only.
- Never suggest bypassing access controls or security policies.
- Prefer least-privilege access and token rotation.

### Destructive Actions

Do not perform destructive or credential-changing actions: do not create, revoke, rotate, or delete tokens. Give the steps and the target stack for the user to apply.

### Secrets

Never request, display, or store real secrets. If a secret is needed in an example, use a placeholder name only.

### Environment Variables

Recommend environment variables for all credentials. Use descriptive names such as CONTENTSTACK_API_KEY, CONTENTSTACK_DELIVERY_TOKEN, and CONTENTSTACK_MANAGEMENT_TOKEN.
