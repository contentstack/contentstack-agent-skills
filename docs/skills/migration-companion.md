---
title: Migration Companion
description: "Guided Contentful → Contentstack migration, content (types, entries, assets, locales) and application code, with prerequisite checks and post-migration validation."
---

# Migration Companion

**Slug:** `migration-companion` · **Product:** Developer Experience · **Type:** Action (gated) · **Ships references & scripts**

Guides a user end-to-end through migrating a project from **Contentful** to **Contentstack**: first the content (content types, entries, assets, locales) via the Contentstack CLI migrate plugin, then the website code that reads from the CMS. It's a sequential workflow where each step's output feeds the next.

## When it triggers

When you want to migrate, move, switch, port, or re-platform to Contentstack: content models, content, assets, locales, application integrations, or website code. Triggers on requests like "migrate to Contentstack," "move my Contentful space," or "migrate from Contentful." Contentful is currently the only supported source.

## The migration at a glance

| Step                      | What happens                                                                              | Produces                               |
| ------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------- |
| 1. Prerequisites & inputs | Prereq checker validates Node 20+, Python 3, `csdx`, `contentful`, logins, region, spaces | Verified env + gathered inputs         |
| 2. Install migrate plugin | Installs/updates `@contentstack/cli-external-migrate`                                     | `csdx migrate:*` available             |
| 3. Content migration      | `csdx migrate:create` exports, converts, and imports into a new stack                     | Populated stack + bundle + credentials |
| 4. Code migration         | Detect → plan → rewrite → eval (13 checks)                                                | Rewritten data layer                   |
| 5. Welcome                | —                                                                                         | Recap + next steps                     |

## What it covers

- **Isolated session workspace** under `${TMPDIR:-/tmp}/migrate-to-cs-<timestamp>-<random>` so concurrent runs never collide.
- **Pinned Node version**. Uses the highest installed Node ≥ 20 the checker validated.
- **Browser-based logins** for Contentstack OAuth and Contentful, handled interactively.
- **Content import** with entity-count verification (locales, content types, assets, entries imported vs exported).
- **Code rewrite** following a source-verified Contentful → Contentstack mapping reference, covering REST Delivery SDK, GraphQL, raw REST/framework plugins, rich text, assets, locales, pagination, and Live Preview.
- **Eval suite** of 13 post-migration checks (residue, field access, SDK init, build and secrets are hard gates that block sign-off; the rest are review or report checks to triage).

## References & scripts

Ships per-step runbooks in `references/` (`step-1-prerequisites.md` through `step-5-welcome-message.md`, loaded only when that step runs), the Contentful → Contentstack mapping file (`CONTENTFUL_TO_CONTENTSTACK_MIGRATION_CONTEXT.md`), and a `scripts/` suite: the prerequisite checker, `read_cf_token.py` (resolves the Contentful token without printing it), the import-summary parser, logging helpers, and per-check eval scripts (`run-all.sh` plus numbered checks).

## Safety notes

Action skill with explicit gates: confirms before logging in, before creating a stack, and before editing your code. The prerequisite checker may install or upgrade global CLIs, and says so. Treats management and Contentful tokens as secrets: never prints or echoes them, and never writes them to workspace files; logs go to `<SESSION_DIR>/migration-log` by default; sets `CS_*` credentials only in the migrated app's gitignored `.env`. Converts reference dereferences to safe array access and flags every guessed field UID with a `TODO(migration)` comment rather than guessing silently.

## Example prompts

- "Migrate my Contentful space to Contentstack."
- "Move my CMS and website code from Contentful to Contentstack."
- "Port my Contentful content models and entries to Contentstack."

## Related

- [Delivery SDK](dx-delivery-sdk.md) · [Migrate JS→TS SDK](dx-migrate-js-to-ts-sdk.md) · [Data Modeling Best Practices](cms-data-modeling-best-practices.md)
