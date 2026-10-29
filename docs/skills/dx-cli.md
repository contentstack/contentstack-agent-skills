---
title: Contentstack CLI
description: "Use the Contentstack CLI (csdx): region and login, token aliases, export/import/seed/clone, bulk operations, migration scripts, branch merges, and plugins such as tsgen."
---

# Contentstack CLI

**Slug:** `dx-cli` · **Product:** Developer Experience · **Type:** Advisory (acts through MCP tools on request)

Helps you pick and run the right `csdx` command against the right region, stack and branch, and avoid overwriting content by accident.

## When it triggers

When you ask which `csdx` command to run, how to authenticate the CLI, how to move content between stacks or branches, bulk publish, write migration scripts, generate TypeScript types, upgrade from CLI 1.x, or troubleshoot CLI errors.

## What it covers

- **Setup**: `npm install -g @contentstack/cli` (Node.js 22+), `csdx config:set:region`, `csdx auth:login` (`--oauth` for SSO), token aliases with `csdx auth:tokens:add`.
- **Moving content**: `cm:stacks:export`, `cm:stacks:import` (modules, `--replace-existing`, skip-publish flags), `cm:stacks:seed`, `cm:stacks:clone`, and `cm:stacks:audit`.
- **Bulk operations**: `cm:stacks:bulk-entries`, `bulk-assets` and `bulk-taxonomies` replace the 1.x bulk-publish commands, with cross-publish, retry and revert.
- **Migration scripts**: `cm:stacks:migration` for scripted content type and entry changes.
- **Branches**: `cm:branches:diff`, `cm:branches:merge` (revert branch by default), `cm:branches:merge-status`.
- **Plugins**: `tsgen` for TypeScript types, `apps-cli` for Developer Hub apps, `cli-launch` for Launch, and more. See the bundled command list.

## Example prompts

- "How do I log in to the CLI with SSO?"
- "Export one stack and import it into another."
- "Bulk publish all blog entries to production."
- "Merge my feature branch content types into main."
- "Generate TypeScript types for my content types."

## MCP tools

The CLI handles bulk and stack-wide jobs; MCP has no export, import, seed, clone, bulk publish or migration-script tools. With the `cma` group connected, the agent can compare branches, check merge jobs and publish single entries (`compare_branches`, `merge_branch`, `get_a_single_merge_job`, `publish_an_entry`) before and after a CLI run.

## Safety notes

Advisory: suggests commands for you to run, and uses MCP tools only when you ask. Warns before imports that replace content, bulk unpublishes, merges, branch deletion and migration scripts, and recommends an export or backup branch first. Never prints tokens.

## Related

- [Migration Companion](migration-companion.md) · [Branches & Aliases](cms-branches-aliases.md) · [Launch deployments](launch-trigger-and-monitor-launch-deployments.md)
