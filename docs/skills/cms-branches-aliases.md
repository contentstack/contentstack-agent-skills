---
title: Branches & Aliases
description: Use Contentstack branches for isolated content development and aliases for zero-downtime deployments, with CI/CD, merge, and rollback patterns.
---

# Branches & Aliases

**Slug:** `cms-branches-aliases` · **Product:** CMS · **Type:** Advisory (acts through MCP tools on request)

Advises on using branches for isolated content/schema development and aliases for zero-downtime deployments: branch strategy, branch-specific vs global modules, CI/CD integration, merge behavior, and rollback.

## When it triggers

When you ask about branches, aliases, CI/CD integration with Contentstack, deployment strategies, or branch-specific vs global module behavior.

## What it covers

- **Branch basics**: a branch inherits the source branch's content types, global fields, entries, assets, languages, webhooks and extensions as an isolated workspace. The branch count per stack depends on your plan; only owners, admins, and developers can create and delete branches.
- **Branch-specific vs global modules**: *branch-specific:* content types, global fields, entries, assets, workflows, publish queue, releases, languages, extensions, audit logs, global search, labels. *Global:* taxonomy, environments, users, roles, webhooks, workflows, publish rules, tokens, Marketplace apps. A webhook can be assigned to one branch at a time; workflows, publish rules and tokens can be scoped to specific branches (tokens also to aliases).
- **Compare & merge**: content types and global fields only, via CMA or CLI. Strategies: `merge_prefer_base`, `merge_prefer_compare`, `overwrite_with_compare` (destructive), `merge_new_only`, `merge_modified_only_prefer_base`, `merge_modified_only_prefer_compare`, `ignore`. A backup branch is created first; the merge runs asynchronously. Entries and assets need scripted reconciliation.
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

## MCP tools

With the Contentstack MCP server connected, the agent can list branches and aliases, compare branches and specific content types or global fields, create and merge branches, poll merge jobs, assign aliases, and delete branches or aliases (all in the `cma` group).

## Safety notes

Advisory by default; uses the MCP tools only when you ask for the change. Before creating, merging or deleting a branch, or assigning or deleting an alias, it names the branches, aliases and merge strategy, explains the impact, and waits for confirmation. Use environment variables for credentials; keep guidance compatible with branch- and alias-scoped credentials.

## Related

- [Releases](cms-releases.md) · [Environments & Publishing](cms-environments-publishing.md) · [Roles & Permissions](cms-roles-permissions.md)
