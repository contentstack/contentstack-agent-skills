---
title: Security & safety model
description: How Contentstack Agent Skills handle secrets, destructive actions, and production safety.
---

# Security & safety model

Every skill in the bundle carries an explicit safety contract. This is what makes the skills safe to run against real Contentstack accounts and codebases. The rules come in two layers: **product-level defaults** shared by all skills in a product, and **skill-level rules** in each `SKILL.md`'s Security section.

## Product-level defaults

Each skill is tagged with a product, and each product defines baseline safety rules.

### CMS

- Never expose management tokens or API keys.
- Always use environment variables for credentials.
- Route all CMA calls through server-side proxies in browser apps.
- Never hardcode stack API keys in client-side code.

### Developer Experience

- Never expose deployment tokens or environment secrets.
- Validate deployment targets before triggering.
- Require confirmation for production deployments.
- Never auto-deploy to production without review.

### Launch

- Never expose deployment tokens or environment secrets.
- Validate deployment targets before triggering.
- Require confirmation for production deployments.
- Never auto-deploy to production without review.

### Developer Hub

- Never expose OAuth client secrets or app signing keys.
- Validate all app installation scopes.
- Never grant broader permissions than required.
- Keep app credentials server-side only.

### Brand Kit

- Never expose Brand Kit API tokens.
- Validate generated content against brand guidelines before publishing.
- Treat Knowledge Vault content as brand-governed source material.
- Confirm resource UIDs before any destructive operation.

## The four safety pillars

Every skill's Security section addresses four areas.

### 1. Defaults

The standing rules the skill always applies, for example, "delivery tokens are client-safe; management tokens are not," or "never recommend enabling Live Preview in production builds."

### 2. Destructive actions

Most skills are **advisory and read-only**: they explain and generate code but never mutate your stack. They explicitly refuse to delete, publish, unpublish, or overwrite, and will explain the impact instead.

**Action skills** can cause external side effects and gate them behind explicit confirmation:

- **Trigger & Monitor Launch Deployments**. Requires explicit confirmation for production deployments; never auto-deploys; exits non-zero on failure.
- **Sync Launch env vars**. Treats any PATCH as a destructive external action; confirms the target project/environment; prefers dry-run.
- **Migration Companion**. Gates login, stack creation, and code edits behind confirmation.

### 3. Secrets

No skill ever prints, echoes, infers, or stores secrets. If you paste a token, the skill acknowledges it at a high level and does not repeat it. Examples always use placeholders and environment variables. The Launch skills log only key names and counts, never values.

### 4. Environment variables

Credentials belong in environment variables, never in source or client-visible config. Skills use descriptive placeholders such as `CONTENTSTACK_API_KEY`, `CONTENTSTACK_DELIVERY_TOKEN`, and `CONTENTSTACK_MANAGEMENT_TOKEN`, and recommend server-side injection for privileged credentials.

## Token safety quick reference

A recurring theme across CMS skills:

| Token | Client-safe? | Use |
| --- | --- | --- |
| **Delivery token** | Yes | Read published content via the CDA |
| **Preview token** | Treat as sensitive | Read unpublished draft content for Live Preview |
| **Management token** | No, server-side only | Stack-level read/write (CMA) |
| **Authtoken / OAuth** | No, server-side only | User sessions and automation (OAuth preferred in SSO orgs) |

See [Tokens & Authentication](../skills/cms-tokens-authentication.md) for full guidance.

## What this means for you

- You can ask advisory skills anything. They won't change your stack.
- Action skills will pause and ask before doing anything irreversible or production-facing.
- The agent won't hardcode your credentials, even if you ask it to. It will use environment variables instead. (You can confirm this with the test in [Verify your setup](../get-started/verify-setup.md).)
