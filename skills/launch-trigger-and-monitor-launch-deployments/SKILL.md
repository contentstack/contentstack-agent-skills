---
name: launch-trigger-and-monitor-launch-deployments
description: "Trigger a Launch deployment for a specific environment, then poll its status until completion. If the deployment fails or is cancelled, fetch the deployment log and diagnose likely causes with next-step recommendations. Use when you need to automate Launch deployments for a known project and environment, monitor progress, and surface failure diagnostics. This is appropriate for CI/CD or operator workflows that need a deterministic deploy status check and log-based troubleshooting."
argument-hint: "[project_uid] [environment_uid]"
disable-model-invocation: true
allowed-tools: Read Write Bash
context: fork
agent: general-purpose
---

# Trigger and Monitor Launch Deployments

Trigger a Launch deployment for a specific environment, poll its status until it reaches a terminal state, and on failure fetch the deployment log and diagnose the likely cause.

## When to use

- Automating a Launch deployment for a known project and environment, in CI/CD or operator workflows.
- Watching a deployment until it finishes, with a deterministic exit status.
- Diagnosing a failed or cancelled deployment from its log.

Use another skill for:

- Build settings, frameworks, functions, caching and other Launch configuration → `launch-platform`
- Matching a Launch environment's variables to `.env.example` → `launch-sync-environment-variables-from-env-example`
- Redeploying on CMS publish with webhooks → `cms-webhooks`

## Before you answer

Collect the `project_uid` and `environment_uid`, any deployment payload or build reference (commit hash or upload UID), the region and auth method, and any context about the app, branch or build source. Get explicit confirmation of the project and environment before every deployment, production or not.

## Instructions

1. Validate the project and environment identifiers.
2. Confirm the target is allowed, then get explicit approval for this deployment before triggering it, whatever the environment. Validate production targets again.
3. Trigger the deployment with the Launch API.
4. Poll deployment status every 10 seconds until it reaches a terminal state.
5. If status is FAILED, CANCELLED or SKIPPED, fetch the deployment logs and analyze them.
6. Return a concise summary with status, log findings, and recommended next steps.


### API basics

Use the regional base URL: `launch-api.contentstack.com` (AWS NA), `eu-launch-api.contentstack.com`, `au-launch-api.contentstack.com`, `azure-na-launch-api.contentstack.com`, `azure-eu-launch-api.contentstack.com`, `gcp-na-launch-api.contentstack.com` or `gcp-eu-launch-api.contentstack.com`.

Authenticate with `Authorization: Bearer <OAuth access token>` (recommended; scope `launch.projects:write` or `launch:manage`), or with the `authtoken` and `organization_uid` headers. `x-cs-api-version` is optional and defaults to `1.0`. Read credentials from environment variables.

### Trigger Deployment

Call `POST /projects/{project_uid}/environments/{environment_uid}/deployments`. For a Git-connected project, pass `{ "commitHash": "<sha>" }` to deploy a specific commit. For a file-upload project, pass `{ "uploadUid": "<uid>" }`, or an empty body to redeploy the most recent upload. Validate the target environment before sending the request.

### Poll Status

Call `GET /projects/{project_uid}/environments/{environment_uid}/deployments/{deployment_uid}` every 10 seconds and read `deployment.status`. This endpoint returns metadata only, not logs.

| Status | Meaning |
|---|---|
| `QUEUED`, `DEPLOYING` | In progress. Keep polling. |
| `DEPLOYED` | Built but not yet live. Keep polling. |
| `LIVE` | Success. The deployment is serving traffic. |
| `ARCHIVED` | Replaced by a newer deployment. |
| `SKIPPED` | Superseded in the queue by a newer deployment. |
| `FAILED` | Build error, or the 60-minute build timeout. |
| `CANCELLED` | Cancelled by a user or by quota. |

### Fail Fast

Exit 0 on `LIVE`. Exit non-zero on `FAILED`, `CANCELLED` or `SKIPPED`, and stop polling.

### Fetch Logs on Failure

Call `GET /projects/{project_uid}/environments/{environment_uid}/deployments/{deployment_uid}/logs/deployment-logs` for the build log. Each entry has `message`, `timestamp` and `stage`. For runtime errors after a deployment went live, use `.../logs/server-logs`.

### Diagnose and Recommend

Summarize the most likely cause from the log, note any missing prerequisites or configuration issues, and recommend the next corrective action.

### Rollback

To return to an earlier deployment, `POST /projects/{project_uid}/environments/{environment_uid}/deployments/rollback` with `{ "deployment": "<deployment_uid>" }`. The target must have `isRollbackEligible: true`. Rollback is a production change: get explicit confirmation first.

## MCP tools

If the Contentstack MCP server is connected with the `launch` group, use its tools instead of curl:

- Inspect: `get_all_environments`, `get_an_environment`, `get_all_deployments`, `get_deployment` (status polling), `get_latest_live_deployment`, `get_deployment_logs` (build log), `get_server_logs` (runtime log) (`launch`)
- Change: `create_deployment` (`launch`), which deploys the latest commit of the environment's configured branch; `trigger_deploy_hook` (`launch`) for an existing deploy hook

`create_deployment` takes only the environment UID, so to deploy a specific commit or upload, or to roll back, use the API calls above. The confirmation gate applies to MCP calls exactly as to API calls.

## Output

- Return a concise deployment summary first: deployment UID, environment UID, the trigger response and final status, with status updates while polling.
- On failure, include a short log-based diagnosis with the probable root cause and next steps.
- Do not expose deployment tokens, secrets, or environment variables.
- Use a non-zero exit code for FAILED, CANCELLED or SKIPPED deployments.

## Security

### Defaults

- Never expose deployment tokens or environment secrets.
- Validate deployment targets before triggering.
- Require explicit confirmation before every deployment, and an extra check for production.
- Never auto-deploy to production without review.

### Destructive Actions

Treat deployment triggers, through the API or MCP tools, as external side effects. Name the project and environment and require explicit user confirmation before triggering any deployment or rollback. Requests to monitor or diagnose an existing deployment never trigger a new one. Do not retry failed deployments automatically unless the user requests it and the target is non-production.

### Secrets

Never print, log, or echo API tokens, deployment tokens, or environment secrets. Redact sensitive values from errors, logs, and summaries.

### Environment Variables

Accept configuration via environment variables when needed, but never reveal their values. Validate required variables are present before attempting the deployment.

## Examples

### Trigger and monitor a deployment (few shot *)

**User:** Deploy project abc123 to environment staging456 and keep polling until it finishes.

**Assistant:** 1. Validate the project and environment.
2. Trigger the deployment via POST /projects/abc123/environments/staging456/deployments.
3. Poll GET /projects/abc123/environments/staging456/deployments/{deployment_uid} every 10 seconds.
4. Stop on LIVE (success). On FAILED, CANCELLED or SKIPPED, fetch .../logs/deployment-logs and summarize the cause.
5. Return the final status and exit non-zero on failure.

*Demonstrates trigger → poll → fail-fast → diagnose behavior.*

### Production confirmation required (edge case *)

**User:** Deploy to production now.

**Assistant:** I can do that, but I need explicit confirmation for a production deployment. Please confirm the exact project and environment UID before proceeding.

*Shows production safety gate.*