---
title: Branches & Aliases
description: Use Contentstack branches for isolated content development and aliases for zero-downtime deployments, with CI/CD, merge, and rollback patterns.
---

# Branches & Aliases

**Slug:** `cms-branches-aliases` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on using branches for isolated content/schema development and aliases for zero-downtime deployments: branch strategy, branch-specific vs global modules, CI/CD integration, merge behavior, and rollback.

## When it triggers

When you ask about branches, aliases, CI/CD integration with Contentstack, deployment strategies, or branch-specific vs global module behavior.

## What it covers

- **Branch basics**: branches copy the source branch's content types, global fields, entries, and assets into an isolated workspace. Max 5 branches per stack; one create/delete at a time across an org; only owners, admins, and developers can manage them.
- **Branch-specific vs global modules**: *branch-specific:* content types, global fields, entries, assets, publish queue, releases, languages, extensions, audit logs, labels, search. *Global:* environments, webhooks, workflows, publish rules, users, roles, tokens.
- **Alias-based deployment**: aliases point to branches. Hardcode an alias (e.g. `deploy`) in frontend code instead of a branch UID; switch production by reassigning the alias, and roll back by reassigning it back. Two aliases can point to one branch, but a branch and alias can't share a UID.
- **CI/CD pattern**: branch from main → change schema/content → test on staging → reassign the production alias → reassign back instantly if something breaks.
- **Branch strategy**: keep branches short-lived; prefer trunk-based workflow. Don't use branches as permanent environments (use environments for that).
- **SDK initialization**: pass the branch or alias ID explicitly (e.g. `branch: 'deploy'`); without a branch header, `main` is the default. Always pass it explicitly in scripts.

## Example prompts

- "How do I use branches for content schema development?"
- "What's the difference between branch-specific and global modules?"
- "How do I deploy content changes with zero downtime?"
- "How do branches work with my CI/CD pipeline?"
- "Can I roll back a bad deployment?"

## Safety notes

Read-only advisory: does not create, delete, merge, or reassign branches or aliases. Use environment variables for credentials; keep guidance compatible with branch- and alias-scoped credentials.

## Related

- [Releases](cms-releases.md) · [Environments & Publishing](cms-environments-publishing.md) · [Roles & Permissions](cms-roles-permissions.md)
