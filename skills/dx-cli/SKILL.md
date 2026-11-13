---
name: dx-cli
description: "Guide developers through the Contentstack CLI (csdx, @contentstack/cli 2.x): install, region setup, login with password or OAuth/SSO, token aliases, stack export, import, seed and clone, bulk publish and unpublish with cm:stacks:bulk-entries/bulk-assets/bulk-taxonomies, migration scripts, branch diff and merge, audit, and installable plugins such as tsgen, apps-cli and the Launch plugin. Use when developers ask which csdx command to run, how to authenticate the CLI, move content between stacks or branches, bulk publish, write cm:stacks:migration scripts, generate TypeScript types, upgrade from CLI 1.x, or troubleshoot CLI errors. For Contentful-to-Contentstack migrations, use migration-companion; for automated Launch deployments over the API, use the launch-* skills."
allowed-tools: Read Grep Glob
---

# Contentstack CLI

Guide developers through the Contentstack CLI (`csdx`): setup and authentication, moving content between stacks and branches, bulk operations, migration scripts, branch merges, and the installable plugins.

## When to use

- Which `csdx` command to run, and with which flags.
- Logging in, regions and token aliases.
- Exporting, importing, seeding or cloning a stack.
- Bulk publishing and unpublishing.
- Scripting content type changes, diffing and merging branches, generating TypeScript types.
- Moving from CLI 1.x to 2.x, or troubleshooting CLI errors.

Use another skill for:

- Contentful migrations → `migration-companion`
- Launch deployments driven through the Launch API → `launch-trigger-and-monitor-launch-deployments`, `launch-sync-environment-variables-from-env-example`
- Launch hosting concepts → `launch-platform`
- Branch strategy and aliases → `cms-branches-aliases`
- Building Developer Hub apps → `developer-hub-app-architect`
- Converting HTML RTE content and rendering JSON RTE → `cms-json-rte`

## Before you answer

Find out the task (export, import, seed, clone, bulk publish, migration, branch merge, types, Launch), the region, the stack API key or token alias, the source and target branch or environment, and the CLI version (`csdx --version`). The CLI has many plugins and flags, and several changed between 1.x and 2.x.

## Instructions

1. Check the CLI version and Node version.
2. Set the region, then authenticate.
3. Pick a command that exists in the current CLI and fill in stack, branch and environment explicitly.
4. Point out what the command overwrites and how to undo it.
5. Give the command and one verification step.


### Install and version

Install with `npm install -g @contentstack/cli`. CLI 2.x needs Node.js 22 or later. Check with `csdx --version`, and list commands with `csdx --help`. Install extra plugins with `csdx plugins:install <package>`.

### Region and authentication

Set the region first: `csdx config:set:region AWS-NA` (also `AWS-EU`, `AWS-AU`, `AZURE-NA`, `AZURE-EU`, `GCP-NA`, `GCP-EU`, or custom hosts with `--cma`, `--cda`, `--ui-host` and `--name`). Sessions are tied to a region, so changing it means logging in again.

Log in with `csdx auth:login` (alias `csdx login`). In SSO organizations use `csdx auth:login --oauth`, which opens the browser. Check the session with `csdx auth:whoami`.

For scripts and CI, store tokens as aliases instead of using a personal session: `csdx auth:tokens:add --management -a <alias> -k <stack_api_key>` or `--delivery -e <environment>`. Most commands accept `-a <alias>` or `-k <stack_api_key>`. List aliases with `csdx auth:tokens:list`.

### Export, import, seed and clone

- `csdx cm:stacks:export -k <key> --data-dir ./export --branch <branch>` exports a stack. Use `--module` for one module and `--content-types` to limit entries. Pass `--branch` explicitly.
- `csdx cm:stacks:import -k <key> --data-dir ./export --branch <branch>` imports into an existing stack. `--module` imports one module. `--replace-existing` overwrites matching modules, so warn before using it. `--skip-entries-publish` and `--skip-assets-publish` skip publishing. `--import-webhook-status disable` keeps imported webhooks off.
- Export and import cover Personalize projects and variant entries (`--module personalize`, `variant-entries`) and Studio compositions alongside the CMS modules.
- `csdx cm:stacks:seed --repo <github_repo>` creates or fills a stack from a starter repository.
- `csdx cm:stacks:clone` copies a stack or branch to another stack: type `a` copies structure only, type `b` copies structure and content.
- `csdx cm:stacks:audit` finds content type and entry issues; `csdx cm:stacks:audit:fix` repairs them. Run it before large imports.

### Bulk operations

CLI 2.x replaces the 1.x `cm:stacks:bulk-publish` commands with the bundled bulk-operations plugin:

- `csdx cm:stacks:bulk-entries --operation publish|unpublish --content-types blog --environments prod --locales en-us -a <alias>`
- `csdx cm:stacks:bulk-assets --operation publish|unpublish ...`, which also moves and deletes Assets (DAM) items with `--space-uid`
- `csdx cm:stacks:bulk-taxonomies`

`--publish-mode bulk` (default) uses the Bulk Publish API; `single` publishes one item at a time. `--source-env` cross-publishes what is live in one environment to others. Operations write a log folder: rerun failures with `--retry-failed <folder>` and undo with `--revert <folder>`. The CMA allows 1 bulk request per second per organization, so large runs take time.

### Migration scripts

`csdx cm:stacks:migration -k <key> --file-path ./migrations/001-add-field.js --branch <branch>` runs a JavaScript migration script that creates or edits content types and transforms entries. `--multiple` runs every script in a folder. Keep scripts in version control and run them on a branch before main. The command executes the script's code, so only run scripts you trust.

### Branches

- `csdx cm:branches:create` and `csdx cm:branches:delete` manage branches.
- `csdx cm:branches:diff --base-branch main --compare-branch feature -k <key>` shows content type and global field differences.
- `csdx cm:branches:merge --base-branch main --compare-branch feature -k <key>` merges them. Merge covers content types and global fields only. By default it creates a revert branch first; `--no-revert` skips that, so discourage it. Use `--export-summary-path` to review the plan and `--use-merge-summary` to apply it.
- `csdx cm:branches:merge-status -k <key> --merge-uid <uid>` checks a merge job.

### Installable plugins

- **TypeScript types:** `csdx plugins:install contentstack-cli-tsgen`, then `csdx tsgen -a <delivery_alias> --output types/contentstack.d.ts`. Add `--api-type graphql` for GraphQL types and `--include-referenced-entry` for references.
- **Apps:** `@contentstack/apps-cli` adds `csdx app:create`, `app:deploy`, `app:install` and related commands for Developer Hub apps.
- **Launch:** `@contentstack/cli-launch` adds `csdx launch` (deploy from GitHub or a file upload), `csdx launch:logs` (`--type d` for deployment logs) and `csdx launch:functions` (run cloud functions locally).
- Also available: `@contentstack/cli-cm-export-query` (query-based export), `contentstack-cli-content-type` (inspect content types), `@contentstack/cli-cm-regex-validate` and `@contentstack/cli-cm-migrate-rte` (HTML RTE to JSON RTE, opt-in in 2.x).

See [references/commands.md](references/commands.md) for the command list by plugin.

### Upgrading from 1.x

- Node.js 22 or later is required.
- `cm:stacks:bulk-publish` and the related 1.x bulk commands are gone; use `bulk-entries`, `bulk-assets` and `bulk-taxonomies`.
- The HTML-to-JSON RTE migration plugin is no longer bundled; install it if needed.
- Re-check scripts that pass removed flags.

## MCP tools

The CLI is the tool for bulk and stack-wide jobs; the MCP server has no export, import, seed, clone, bulk publish or migration-script tools. When the Contentstack MCP server is connected, it covers the single-item and branch operations (local server group in brackets):

- Inspect: `get_all_branches`, `compare_branches`, `compare_content_types_between_branches`, `compare_global_fields_between_branches`, `get_all_merge_jobs`, `get_a_single_merge_job`, `get_all_content_types`, `export_content_type` (`cma`)
- Change: `create_a_branch`, `merge_branch`, `publish_an_entry`, `unpublish_an_entry` (`cma`)
- Delete: `delete_a_branch` (`cma`)

Use them to check the state of a stack before and after a CLI run, for example to compare branches before `csdx cm:branches:merge`.

## Output

Give the command first, then the setup it needs (region, login, token alias, plugin install), then what it changes and how to verify or undo it. Offer a dry run or read-only check where available, such as `csdx auth:whoami`, `csdx config:get:region` or `csdx cm:branches:diff`. Use placeholders for keys, tokens and aliases.

## Security

### Defaults

- Advisory by default: suggest commands for the user to run, and don't run commands that write to a stack. Use the MCP tools above only when the user asks for the change.
- Prefer token aliases or OAuth over passing tokens on the command line.
- Use management tokens only on trusted machines and in CI secrets.
- Always pass the branch explicitly in write commands.
- Back up or export before destructive operations.

### Destructive Actions

Imports with `--replace-existing`, bulk unpublish, branch merges, branch deletion and migration scripts change live data. State the target stack, branch and environment, recommend an export or backup branch first, and require the user to confirm. The same applies before any MCP write, merge or delete.

### Secrets

Never print management tokens or authtokens. `csdx auth:tokens:list` shows token values, so don't ask users to paste its output.

### Environment Variables

In CI, inject tokens from the secret store and add them with `csdx auth:tokens:add ... --token "$CONTENTSTACK_MANAGEMENT_TOKEN"`.

## References

- [Command list by plugin](references/commands.md)
- https://www.contentstack.com/docs/developers/cli
