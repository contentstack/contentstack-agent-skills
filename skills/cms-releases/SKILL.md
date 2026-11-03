---
name: cms-releases
description: "Advise developers on using Contentstack Releases for coordinated, atomic content deployment. Cover release creation, item management, staged deployment, webhook storm prevention, and CI/CD integration. Use when developers ask about deploying multiple content changes together, campaign launches, coordinated content updates, release scheduling, or CI/CD content deployment. For single-entry publishing, use cms-environments-publishing."
allowed-tools: Read Grep Glob
---

# Releases

Advise on Releases for deploying related entries and assets together, so campaigns and coordinated updates go live at once without manual coordination errors.

## When to use

- Deploying many entries and assets together, such as a campaign launch.
- Scheduling a release.
- A static site rebuilding many times during one release deployment.
- Release limits, and Releases in a CI/CD pipeline.

Use another skill for:

- Routine single-entry publishing and scheduling → `cms-environments-publishing`
- Debouncing webhook receivers → `cms-webhooks`
- Branches and alias-based deployment → `cms-branches-aliases`
- Approvals before publishing → `cms-workflows`

## Before you answer

Find out what has to go live together, how many items and of which types and locales, the CI/CD pipeline, and any scheduling need.

## Instructions

1. Understand the coordination requirements.
2. Recommend release creation and item grouping.
3. Advise staging validation before production.
4. Warn about webhook bursts and receiver debouncing.
5. Cover CI/CD integration if applicable.
6. State release limitations and when not to use releases.

### Release workflow

Create a release with a descriptive name. Add all related entries and assets, including items from multiple content types and locales. Deploy to staging first, validate, then deploy to production. Specify which version of each entry to deploy when needed.

### Webhook bursts

Deploying a release publishes each item, so per-item publish webhooks can fire. Warn users to debounce or batch on the receiver so a rebuild runs once per deployment, and to check the webhook execution logs for what actually fired. Refer to the Webhooks skill for receiver-specific handling.

### Limitations

Add at most 25 items (entries or assets) per request when adding items to a release. Updating release items to their latest versions does not automatically add new references from the updated entries. Releases are branch-specific: a release deploys items from the branch it was created on.

### Releases v2

Releases v2 is plan-gated. It adds multi-locale bulk add of items, cloning a release, and updating all items to their latest versions in one call. Nested references can be included when items are added.

### CI/CD integration

Use a pipeline that creates a release, adds changed items, deploys to staging, runs tests, then deploys to production on success. Combine with branches and aliases for automated content deployment.

### When not to use releases

Do not recommend releases for routine single-entry publishes. Use them when coordinated deployment across multiple content pieces is required.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `get_all_releases`, `get_a_single_release`, `get_all_items_in_a_release` (`cma`)
- Change: `create_a_release`, `add_items_to_a_release`, `clone_a_release`, `deploy_a_release` (`cma`)
- Delete: `delete_items_from_a_release` (`cma`)

`add_items_to_a_release` follows the 25-items-per-request limit, so batch larger releases. There is no tool to delete a whole release; use the UI or the CMA.

## Output

Be concise and practical. Emphasize the webhook burst gotcha when relevant, prefer bullets or short steps, and state limitations when they affect the recommendation.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose tokens or API keys.
- Use environment variables for credentials in example code.
- Do not suggest client-side access to management credentials; route CMA calls through a server-side proxy in browser apps.

### Destructive Actions

Before creating, changing or deploying a release, name the release, the branch, the target environments and locales, and the number of items, and wait for confirmation. Deploying to production changes the live site and can fire a webhook for every item.

### Secrets

Never reveal management tokens, API keys, or other secrets. If code is shown, use placeholders and environment variables only.

### Environment Variables

Use environment variables for all credentials in examples and integration guidance. Never hardcode secrets in sample code.
