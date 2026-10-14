---
title: How skill selection works
description: How a user request is matched to the right Contentstack skill using skill descriptions and progressive disclosure.
---

# How skill selection works

There is no router file. Each skill's **description** tells the agent when to use it, and the agent loads skills only when your request needs them.

## Progressive disclosure

Agents that read the [Agent Skills](https://agentskills.io) format load skills in three stages:

1. **At startup**, only each skill's `name` and `description` from the frontmatter go into context. For 22 skills that's a few thousand tokens.
2. **When a request matches** a description, the agent loads that skill's full `SKILL.md` and follows it.
3. **When the task needs more detail**, the skill points the agent to files in its `references/` folder or runs a bundled script.

This keeps context lean: you get all 22 skills available without paying for 22 full instruction sets in every conversation.

## How a request is matched

1. You make a request in natural language.
2. The agent compares it with the descriptions it has in context, especially the "Use when…" part.
3. It loads the best-fitting skill (or several, if the task spans them).
4. It follows that skill's instructions, reading any `references/` the task needs.

You don't have to name a skill. But you can force one if you want (*"use the Data Modeling skill…"*). In Claude Code, you can also invoke a skill directly as a slash command, for example `/cms-entries`.

## What triggers each skill

Each description's "Use when…" clause lists the requests that should load it. In short:

| When the user asks about… | Skill |
| --- | --- |
| Brand Kit, Voice Profiles, Knowledge Vault, on-brand AI generation | [Brand Kit Assistant](../skills/brand-kit-assistant.md) |
| Migrating/porting from Contentful to Contentstack | [Migration Companion](../skills/migration-companion.md) |
| Migrating Delivery SDK code from JavaScript to TypeScript | [Migrate JS→TS SDK](../skills/dx-migrate-js-to-ts-sdk.md) |
| Delivery SDK code, queries, Live Preview setup, SSR preview | [Delivery SDK](../skills/dx-delivery-sdk.md) |
| Maintaining or extending the Next.js kickstart | [Contentstack Kickstart Next](../skills/dx-kickstart-next.md) |
| Designing or refactoring content models | [Data Modeling Best Practices](../skills/cms-data-modeling-best-practices.md) |
| Debugging Live Preview or Visual Builder | [Live Preview & Visual Editor Support](../skills/cms-live-preview-visual-editor-support-assistant.md) |
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

The exact wording lives in each skill's frontmatter. See the [skills reference](../skills/index.md).

## Skills that only run on request

Skills with `disable-model-invocation: true` in their frontmatter are never picked automatically, because they perform external actions. Both Launch skills work this way: you invoke them by name (in Claude Code, as `/launch-trigger-and-monitor-launch-deployments` or `/launch-sync-environment-variables-from-env-example`).

## When multiple skills fit

Many real tasks span skills. For example, "deploy a campaign of 50 entries without my site rebuilding hundreds of times" touches **Releases** (atomic deploy) and **Webhooks** (the rebuild storm). A good agent loads the primary skill and pulls in adjacent ones as needed. Skills frequently cross-reference each other for exactly this reason.

## Disambiguating

Some skills ask for clarification first. **Localization**, for instance, behaves differently for the editorial UI versus CDA delivery, so the skill clarifies which you mean before answering. This is by design. See [Anatomy of a SKILL.md](skill-anatomy.md).

## Writing descriptions that trigger well

Because the description is the only thing the agent sees before loading a skill, it has to carry the routing cues. See [Authoring conventions](../contributing/authoring-conventions.md).
