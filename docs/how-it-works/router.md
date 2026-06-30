---
title: The router
description: How a user request is matched to the right Contentstack skill.
---
# The router

The **router** is how your assistant decides which skill to apply. It's a single table that maps a typical user intent to a skill's `SKILL.md`.

## Where it lives

| Format | Router file |
| --- | --- |
| Source of truth | `skills/CLAUDE.md` |
| Cursor | `cursor/rules/00-router.mdc` (`alwaysApply: true`) |
| Codex | `codex/AGENTS.md` |
| Claude Code / Gemini | loaded from the source via the plugin/extension |

All forms are generated from `skills/CLAUDE.md`. See [Architecture](architecture.md).

## How routing works

1. You make a request in natural language.
2. The agent reads the routing table (always in context for full-bundle installs).
3. It matches your intent to the best-fitting row.
4. It loads that skill's `SKILL.md` and follows it, including reading any `references/` the task needs.

You don't have to name a skill. But you can force one if you want (*"use the Data Modeling skill…"*).

## The routing table

Each row is "when the user asks… → skill." Abbreviated:

| When the user asks about… | Skill |
| --- | --- |
| Brand Kit, Voice Profiles, Knowledge Vault, on-brand AI generation | [Brand Kit Assistant](../skills/brand-kit-assistant.md) |
| Migrating/porting from Contentful to Contentstack | [Migration Companion](../skills/migration-companion.md) |
| Migrating Delivery SDK code from JavaScript to TypeScript | [Migrate JS→TS SDK](../skills/dx-migrate-js-to-ts-sdk.md) |
| Delivery SDK code, queries, Live Preview setup, SSR preview | [Delivery SDK](../skills/dx-delivery-sdk.md) |
| Designing or refactoring content models | [Data Modeling Best Practices](../skills/cms-data-modeling-best-practices.md) |
| Debugging Live Preview or Visual Builder | [Live Preview & Visual Builder Support](../skills/cms-live-preview-visual-builder-support-assistant.md) |
| Fetching entries, CDA queries, pagination, bulk ops | [Entries](../skills/cms-entries.md) |
| Uploading, transforming, delivering assets | [Assets](../skills/cms-assets.md) |
| Classifying content, category hierarchies | [Taxonomy](../skills/cms-taxonomy.md) |
| Workflow stages, approvals, publish rules | [Workflows & Publish Rules](../skills/cms-workflows.md) |
| Environments, publishing, delivery/preview tokens, Sync API | [Environments & Publishing](../skills/cms-environments-publishing.md) |
| Languages, fallback chains, localization | [Localization](../skills/cms-localization.md) |
| Branches, aliases, CI/CD, deployment strategy | [Branches & Aliases](../skills/cms-branches-aliases.md) |
| Roles, permissions, teams, token capabilities | [Roles & Permissions](../skills/cms-roles-permissions.md) |
| Deploying multiple content changes together, campaigns | [Releases](../skills/cms-releases.md) |
| Authentication, token types, API keys, rate limits, SSO | [Tokens & Authentication](../skills/cms-tokens-authentication.md) |
| Webhooks, event channels, payloads, signatures | [Webhooks](../skills/cms-webhooks.md) |
| Matching a Launch env to `.env.example` | [Sync Launch env vars](../skills/launch-sync-environment-variables-from-env-example.md) |
| Triggering and monitoring Launch deployments | [Trigger & Monitor Deployments](../skills/launch-trigger-and-monitor-launch-deployments.md) |
| Personalization, A/B testing, audience segmentation, variants | [Variants & Personalization](../skills/cms-variants-personalization.md) |
| Building a Developer Hub or Marketplace app | [Developer Hub App Architect](../skills/developer-hub-app-architect.md) |

The full, authoritative table is in `skills/CLAUDE.md` and the [skills reference](../skills/index.md).

## When multiple skills fit

Many real tasks span skills. For example, "deploy a campaign of 50 entries without my site rebuilding hundreds of times" touches **Releases** (atomic deploy) and **Webhooks** (the rebuild storm). A good agent routes to the primary skill and pulls in adjacent ones as needed. Skills frequently cross-reference each other for exactly this reason.

## Disambiguating

Some routes ask for clarification first. **Localization**, for instance, behaves differently for the editorial UI versus CDA delivery, so the skill clarifies which you mean before answering. This is by design. See [Anatomy of a SKILL.md](skill-anatomy.md).
