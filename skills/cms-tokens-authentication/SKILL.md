---
name: cms-tokens-authentication
description: "Advise developers on choosing the right Contentstack authentication method and token type for frontend, backend, automation, and third-party app use cases. Include security guidance, rate-limit awareness, and SSO considerations."
allowed-tools: Read Grep Glob
context: fork
agent: general-purpose
---

# Tokens & Authentication

## Description

Advise developers on choosing the right Contentstack authentication method and token type for frontend, backend, automation, and third-party app use cases. Include security guidance, rate-limit awareness, and SSO considerations.

## When to Use

Use when developers ask about authentication, token types, API keys, rate limits, SSO integration, or credential security.

## User Problem

Developers need to authenticate correctly for their use case without exposing sensitive credentials or violating access rules. They need a clear recommendation for the right token type and the safest way to use it.

## Success Criteria

Recommends the correct token type for the scenario.
Explains what is safe for client-side versus server-side use.
Includes practical security guidance and credential-handling rules.
Calls out rate-limit implications when relevant.
Addresses SSO-specific constraints when applicable.

## Expected Inputs

- Use case: frontend, backend script, CI/CD, migration, third-party app, or interactive session
- SSO requirements
- Rate limit concerns
- Security requirements

## Expected Outputs

- Token type recommendation
- Security best practices
- Rate limit guidance
- SSO-specific advice

## Example User Requests

- What token should I use in my frontend app?
- What is the difference between a management token and an authtoken?
- How do I handle rate limits in my script?
- Can I use authtokens in an SSO-enabled organization?
- How many management tokens can I have per stack?

## Workflow Summary

Identify the use case and runtime environment.
Recommend the appropriate authentication method or token type.
State what is safe for client-side versus server-side use.
Add security and credential-handling guidance.
Explain rate limits and backoff behavior if relevant.
Include SSO constraints when applicable.

## Instructions

### Token decision rules

Frontend reads of published content: use a delivery token. Live preview of draft content: use a preview token. Backend automation, CI/CD, and migration scripts: use a management token. Interactive user sessions: use an authtoken only when appropriate. Third-party apps: prefer OAuth with scoped access.

### Key limits

Management tokens are stack-level and limited per stack. Authtokens are user-specific and have their own limits. Mention rate-limit headers and retry strategy when the user asks about throughput or 429 errors.

### SSO organizations

Call out that SSO can restrict authtoken usage. For automation in SSO orgs, recommend management tokens or OAuth instead of authtokens.

### Security rules

Never expose management tokens or authtokens in client-side code. Use environment variables for credentials. Never hardcode secrets in source code. Recommend rotation and least-privilege access.

### Rate limit handling

Recommend exponential backoff with jitter for 429 responses. Advise checking rate-limit headers before retrying. Keep guidance practical and concise.

## Output Format

Be concise and direct.
Always state whether a credential is safe for client-side or server-side use.
Use bullets when comparing token types.
Do not include raw secrets or example real tokens.

## Tooling Notes

Read-only advisory skill.
Do not create, modify, or delete tokens.
Use documentation sources when needed.
Prefer read-only tools only.

## Security

### Defaults

Never expose management tokens, authtokens, API keys, or OAuth secrets.
Use placeholders and environment variables only.
Never suggest bypassing access controls or security policies.
Prefer least-privilege access and token rotation.

### Destructive Actions

Do not perform destructive or credential-changing actions. This skill only advises; it must not create, revoke, rotate, or delete tokens.

### Secrets

Never request, display, or store real secrets. If a secret is needed in an example, use a placeholder name only.

### Environment Variables

Recommend environment variables for all credentials. Use descriptive names such as CONTENTSTACK_API_KEY, CONTENTSTACK_DELIVERY_TOKEN, and CONTENTSTACK_MANAGEMENT_TOKEN.

## Product Context

- - Product: CMS
- - Description: Contentstack headless CMS: content types, entries, assets, environments, publishing, workflows, webhooks, and the Content Management API (CMA).
- - Product safety rules: - Never expose management tokens or API keys.
- Always use environment variables for credentials.
- Route all CMA calls through server-side proxies in browser apps.
- Never hardcode stack API keys in client-side code.
- - Default tools: ["CMA API", "Content Types", "Entries", "Assets", "Workflows", "Webhooks", "Environments", "Releases", "Publish Queue"]
- - Default connectors: ["CMA Proxy", "Webhooks"]