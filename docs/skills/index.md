---
title: Skills reference
description: The full catalog of Contentstack Agent Skills, grouped by product.
---

# Skills reference

The bundle includes 22 skills across five Contentstack products. Each links to a dedicated page with what it does, when it triggers, example prompts, and its safety notes.

> Each skill page mirrors its canonical `skills/<slug>/SKILL.md`. The slug is the skill's identifier: use it with the [`skills` CLI](../get-started/skills-cli.md).

## CMS

| Skill | Slug | What it helps with |
| --- | --- | --- |
| [Assets](cms-assets.md) | `cms-assets` | Asset organization, Image Delivery API transforms, publishing lifecycle, CDN behavior, limits. |
| [Branches & Aliases](cms-branches-aliases.md) | `cms-branches-aliases` | Isolated content development, alias-based zero-downtime deploys, CI/CD, merge & rollback. |
| [Data Modeling Best Practices](cms-data-modeling-best-practices.md) | `cms-data-modeling-best-practices` | Choosing content types, references, global fields, groups, modular blocks, JSON RTE, taxonomy. |
| [Entries](cms-entries.md) | `cms-entries` | CDA queries, reference expansion, pagination, versioning, publishing, bulk ops, Sync API. |
| [Environments & Publishing](cms-environments-publishing.md) | `cms-environments-publishing` | Environment design, publishing pipeline, token types, Sync API, CDN, publish queue. |
| [Localization](cms-localization.md) | `cms-localization` | Languages, fallback chains, localized vs unlocalized entries, non-localizable fields. |
| [Releases](cms-releases.md) | `cms-releases` | Atomic multi-item deployment, scheduling, webhook-storm prevention, CI/CD. |
| [Roles & Permissions](cms-roles-permissions.md) | `cms-roles-permissions` | Built-in & custom roles, permission merging, teams, token capabilities, least privilege. |
| [Taxonomy](cms-taxonomy.md) | `cms-taxonomy` | Hierarchical classification, taxonomy vs tags/labels/references, CDA taxonomy queries. |
| [Tokens & Authentication](cms-tokens-authentication.md) | `cms-tokens-authentication` | Choosing the right token, client- vs server-side safety, rate limits, SSO. |
| [Variants & Personalization](cms-variants-personalization.md) | `cms-variants-personalization` | Variants vs separate entries, variant groups, A/B testing, Personalize integration. |
| [Webhooks](cms-webhooks.md) | `cms-webhooks` | Event channels, payloads, signature verification, retries, reliable receiver design. |
| [Workflows & Publish Rules](cms-workflows.md) | `cms-workflows` | Stage design, approvals, self-approval prevention, publish governance, automation. |

## Developer Experience

| Skill | Slug | What it helps with |
| --- | --- | --- |
| [Delivery SDK](dx-delivery-sdk.md) | `dx-delivery-sdk` | Production-ready TypeScript with `@contentstack/delivery-sdk` for entries, assets, queries, Live Preview. |
| [Contentstack Kickstart Next](dx-kickstart-next.md) | `dx-kickstart-next` | Maintaining the Next.js kickstart: App Router, Delivery SDK setup, Live Preview, seed alignment, env vars, validation. |
| [Migrate JS→TS SDK](dx-migrate-js-to-ts-sdk.md) | `dx-migrate-js-to-ts-sdk` | Migrating Delivery SDK code from the JavaScript SDK to the TypeScript SDK. |
| [Live Preview & Visual Builder Support](cms-live-preview-visual-builder-support-assistant.md) | `cms-live-preview-visual-builder-support-assistant` | Diagnosing and implementing Live Preview / Visual Builder across CSR, SSR, SSG, BFF. |
| [Migration Companion](migration-companion.md) | `migration-companion` | Guided Contentful → Contentstack migration: content and application code. |

## Launch

| Skill | Slug | What it helps with |
| --- | --- | --- |
| [Sync Launch env vars from .env.example](launch-sync-environment-variables-from-env-example.md) | `launch-sync-environment-variables-from-env-example` | Comparing a local `.env.example` to a Launch environment and patching missing keys. |
| [Trigger & Monitor Deployments](launch-trigger-and-monitor-launch-deployments.md) | `launch-trigger-and-monitor-launch-deployments` | Triggering a Launch deploy, polling to completion, diagnosing failures from logs. |

## Brand Kit

| Skill | Slug | What it helps with |
| --- | --- | --- |
| [Brand Kit Assistant](brand-kit-assistant.md) | `brand-kit-assistant` | Brand Kit, Voice Profiles, Knowledge Vault, on-brand AI generation, governance, API routing. |

## Developer Hub

| Skill | Slug | What it helps with |
| --- | --- | --- |
| [Developer Hub App Architect](developer-hub-app-architect.md) | `developer-hub-app-architect` | Designing & building Developer Hub / Marketplace apps: UI locations, manifest, SDK, proxy, publishing. |

## How skills get selected

You don't pick skills manually for full-bundle installs: the [router](../how-it-works/router.md) matches your request automatically. Many tasks pull in more than one skill (for example, Releases + Webhooks). To force a specific skill, name it in your prompt.
