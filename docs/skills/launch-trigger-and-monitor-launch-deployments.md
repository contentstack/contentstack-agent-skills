---
title: Trigger & Monitor Deployments
description: Trigger a Contentstack Launch deployment, poll it to completion, and diagnose failures from the deployment log.
---

# Trigger & Monitor Deployments

**Slug:** `launch-trigger-and-monitor-launch-deployments` · **Product:** Launch · **Type:** Action (gated)

Triggers a Launch deployment for a specific environment, polls its status until completion, and, if it fails or is cancelled, fetches the deployment log and diagnoses likely causes with next-step recommendations. Built for CI/CD or operator workflows that need a deterministic deploy status check.

> This skill has `disable-model-invocation: true`, which Claude Code and Copilot honor: they run it only when you explicitly invoke it. Other tools may still match it automatically, so the skill also confirms the target project and environment before any external call.

## When it triggers

When you need to automate Launch deployments for a known project and environment, monitor progress, and surface failure diagnostics.

## How it works

1. Validate the project and environment identifiers.
2. Confirm the target is allowed. **Require explicit approval for production**.
3. Trigger: `POST /projects/{project_uid}/environments/{environment_uid}/deployments`, optionally with a `commitHash` or `uploadUid`.
4. Poll `GET .../deployments/{deployment_uid}` every 10 seconds. `LIVE` is success; `QUEUED`, `DEPLOYING` and `DEPLOYED` are still in progress.
5. Fail fast. Exit non-zero on `FAILED`, `CANCELLED` or `SKIPPED`; stop polling.
6. On failure, `GET .../deployments/{deployment_uid}/logs/deployment-logs` for the build log (the deployment endpoint itself returns metadata only), then summarize the likely cause and next steps.

## Inputs

- `project_uid`
- `environment_uid`
- Optional deployment payload / build reference
- Confirmation for production deployments
- Any context about the app, branch, or build source

## Example prompts

- "Trigger a deployment for project `abc123` in environment `prod456` and watch it until it finishes."
- "Deploy the latest build to staging and tell me if it fails."
- "Poll a Launch deployment every 10 seconds and exit non-zero on failure."
- "If the deployment fails, check the logs and explain what went wrong."

## MCP tools

If the `launch` group of the Contentstack MCP server is connected, the skill uses `create_deployment` to deploy the latest commit of the environment's branch, `get_deployment` to poll, and `get_deployment_logs` or `get_server_logs` to diagnose. Deploying a specific commit or upload, and rollback, still go through the API.

## Safety notes

Treats deployment triggers, through the API or MCP tools, as external side effects. Requires explicit confirmation of the project and environment before every deployment, with an extra check for production, and never auto-deploys to production without review. Doesn't auto-retry failed deployments unless asked and the target is non-production. Never prints API tokens, deployment tokens, or environment secrets; redacts sensitive values from logs and summaries. Uses a non-zero exit code for failed, cancelled or skipped deployments. Rollback (`POST .../deployments/rollback`) is a production change and needs confirmation.

## Related

- [Sync Launch env vars from .env.example](launch-sync-environment-variables-from-env-example.md) · [Branches & Aliases](cms-branches-aliases.md) · [Releases](cms-releases.md)
