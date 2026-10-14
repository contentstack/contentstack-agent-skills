---
title: Developer Hub App Architect
description: Turn Contentstack Developer Hub and Marketplace app ideas into concrete implementations: UI location choice, architecture, React/TypeScript scaffolding, manifest, proxy, and publishing.
---

# Developer Hub App Architect

**Slug:** `developer-hub-app-architect` · **Product:** Developer Hub · **Type:** Advisor + Builder · **Ships references**

Turns Developer Hub and Marketplace app ideas into concrete implementations: it chooses the right UI location, maps the architecture, generates boilerplate-aligned React/TypeScript code, and troubleshoots setup, SDK, manifest, proxy, and publishing issues.

## When it triggers

When designing or building a Contentstack Developer Hub or Marketplace app, choosing a UI location for a feature, generating app code from the boilerplate, explaining manifest/setup/proxy/OAuth/publishing steps, or debugging app loading, SDK, iframe, route, or location issues.

## Operating modes

- **Advisor mode**: chooses the best UI location(s) with tradeoffs, reviews architecture, and debugs issues.
- **Builder mode**: generates implementation-ready React + TypeScript with loading/error states, typed helpers, and iframe resize behavior, aligned to the user's boilerplate.

## What it covers

- **Location selection**: always identifies the best Contentstack UI location before writing code; prefers the smallest location that fits; compares candidates by user context, SDK surface, and complexity.
- **Developer Hub setup**: manifest, base URL, route mapping, location enabling, advanced settings variables, proxy/rewrite, install, and deploy steps.
- **SDK & integration**: `@contentstack/app-sdk` patterns for location access, config read/write, field updates, asset replacement, iframe sizing, and typed guards; proxy/API rewrites for external integrations with secrets kept server-side.
- **Troubleshooting**: checks route, manifest, location, SDK init, iframe context, config persistence, proxy behavior, and install scope, in that order, leading with the most likely cause.
- **Publishing & safety**: readiness checks for scopes, permissions, credentials, versioning, and install flow.

## References

Ships a Developer Hub coding reference (`references/developer-hub-coding-reference.md`) used for location selection, boilerplate conventions, SDK patterns, setup, troubleshooting, and publishing.

## Example prompts

- "Build a private app that adds AI suggestions in the entry sidebar."
- "Which UI location should I use for a product taxonomy picker?"
- "Generate an app configuration page and save API credentials through proxy variables."
- "Why is my app loading but `appSdk.location.CustomField` is undefined?"
- "Turn this app idea into manifest config, route plan, and starter code."

## Safety notes

Never exposes OAuth client secrets or app signing keys; keeps app credentials server-side via proxy variables or secure env vars. Validates installation scopes and never grants broader permissions than required. For publish/delete/revoke/uninstall flows, explains the impact first and requires confirmation of the target app/environment/installation.

## Related

- [Roles & Permissions](cms-roles-permissions.md) · [Tokens & Authentication](cms-tokens-authentication.md) · [Webhooks](cms-webhooks.md)
