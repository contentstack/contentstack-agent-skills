---
name: cms-branches-aliases
description: "Advise developers on using Contentstack branches for isolated content development and aliases for zero-downtime content deployments. Cover branch strategy, branch-specific vs global modules, CI/CD integration, merge behavior, and rollback patterns. Use when developers ask about branches, aliases, CI/CD integration with Contentstack, deployment strategies, or branch-specific vs global module behavior. For running csdx branch commands, use dx-cli."
---

# Branches & Aliases

Advise on branches for isolated schema and content work, and aliases for zero-downtime deployment and rollback.

## When to use

- Choosing a branch strategy for schema and content development.
- Which modules are branch-specific and which are global.
- Comparing and merging branches.
- Alias-based deployment, rollback and CI/CD pipelines.

Use another skill for:

- Running `csdx` branch, export and import commands → `dx-cli`
- Deploying a set of entries together → `cms-releases`
- Environments, publishing and token scoping → `cms-environments-publishing`
- Designing the content types you change on a branch → `cms-data-modeling-best-practices`

## Before you answer

Find out the development workflow or CI/CD pipeline, the deployment and rollback requirements, and how the team collaborates.

## Instructions

1. Understand the development and deployment workflow.
2. Recommend a branch strategy.
3. Explain branch-specific vs global modules.
4. Guide alias-based deployment.
5. Cover merge, rollback and CI/CD integration.

### Branch basics

A new branch inherits the source branch's content types, global fields, entries, assets, languages, webhooks and extensions as an isolated workspace. The number of branches per stack depends on the plan. Only owners, admins and developers can create and delete branches.

### Branch-specific vs global modules

Branch-specific: content types, global fields, entries, assets, workflows, publish queue, releases, languages, extensions, audit logs, global search and labels. Global: taxonomy, environments, users, roles, webhooks, workflows, publish rules, tokens and Marketplace apps. Some global modules can be scoped: a webhook can be assigned to one branch at a time, workflows and publish rules can apply to all branches or specific ones, and delivery and management tokens can be limited to specific branches or aliases. A content type on a development branch does not exist on main until merged.

### Compare and merge

Compare and merge covers only content types and global fields, and runs through the CMA or the CLI. Merge strategies are `merge_prefer_base`, `merge_prefer_compare`, `overwrite_with_compare`, `merge_new_only`, `merge_modified_only_prefer_base`, `merge_modified_only_prefer_compare` and `ignore` (per item). Warn that `overwrite_with_compare` replaces the base and loses anything that exists only there. A backup branch is created before the merge runs, and the merge is asynchronous, so poll the merge queue for its status. Entries, assets and other modules have no merge tool; reconcile them with scripts.

### Alias-based deployment

Aliases point to branches. Hardcode an alias such as `deploy` in frontend code instead of a branch UID. To switch production to a new branch, reassign the alias. Frontend code does not change. For rollback, reassign the alias back. Two aliases can point to the same branch, but a branch and alias cannot share the same UID.

### CI/CD pattern

Create a branch from main, make schema and content changes, test on staging, reassign the production alias to the new branch, and reassign back immediately if something goes wrong.

### Branch strategy

Keep branch lifetimes short. Long-lived branches drift and create merge conflicts. Prefer a trunk-based workflow with short-lived feature branches merged back to main quickly. Do not use branches as permanent environments; use environments for that.

### SDK initialization

Pass the branch or alias ID explicitly, for example `branch: 'deploy'`. If no branch header is passed, main is used by default. Always pass the branch header explicitly in scripts, even when targeting main.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `get_all_branches`, `get_a_single_branch`, `get_all_branch_aliases`, `get_a_single_branch_alias`, `compare_branches`, `compare_content_types_between_branches`, `compare_global_fields_between_branches`, `compare_specific_ct_between_branches`, `compare_specific_gf_between_branches`, `get_all_merge_jobs`, `get_a_single_merge_job` (`cma`)
- Change: `create_a_branch`, `merge_branch`, `assign_a_branch_alias` (`cma`)
- Delete: `delete_a_branch`, `delete_a_branch_alias` (`cma`)

Run a compare before `merge_branch`, and poll `get_a_single_merge_job` until the merge finishes. Set `CONTENTSTACK_BRANCH` (or the Profile Hub `branch` URL parameter) so other tools act on the intended branch.

## Output

Provide concise branch and deployment guidance. Favor practical CI/CD patterns over abstract explanations.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose tokens or API keys.
- Use environment variables for credentials in example code, and route CMA calls through a server-side proxy in browser apps.
- Do not recommend hardcoding secrets in client-side code.
- Keep guidance compatible with branch- and alias-scoped credentials.

### Destructive Actions

Before creating, merging or deleting a branch, or assigning or deleting an alias, name the stack, the branches and aliases involved and the merge strategy, explain the impact (reassigning a production alias switches the live site; `overwrite_with_compare` loses base-only items; deleting a branch deletes its content), and wait for confirmation.

### Secrets

Never expose management tokens, delivery tokens, API keys, or other credentials. If code examples are needed, use environment variables and placeholder names only.

### Environment Variables

Use environment variables for all credentials and secret values. Never hardcode stack API keys, tokens, or branch-scoped credentials in examples.
