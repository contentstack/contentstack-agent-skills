---
name: launch-sync-environment-variables-from-env-example
description: "Fetch environment variables from a Contentstack Launch project, compare them with a local `.env.example` file, and update the target environment to add any missing keys. Use when a Launch environment must match the keys defined in a local `.env.example` file."
argument-hint: "[project_uid] [environment_uid] [env_example_path]"
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash
context: fork
agent: general-purpose
---

# Sync Launch environment variables from .env.example

Fetch a Contentstack Launch environment's variables, compare them with a local `.env.example` file, and add any missing keys without changing any other environment setting.

## When to use

- A Launch environment must match the keys defined in a local `.env.example` file.
- Auditing missing environment variables before a deployment.
- Adding missing variable names to a Launch environment without editing the config by hand.

Use another skill for:

- General Launch hosting, build settings and environment variable limits → `launch-platform`
- Triggering a deployment and watching it → `launch-trigger-and-monitor-launch-deployments`
- Setting up the Contentstack MCP server → `dx-mcp-server`

## Before you answer

Collect the Launch project UID, environment UID, the path to `.env.example`, the region, and how the user authenticates (OAuth token or authtoken plus organization UID). Ask whether to run as a dry run; default to one.

## Instructions

1. Read and parse the local `.env.example` file.
2. Fetch the target Launch environment and its current variables.
3. Compare keys from the file against keys in Launch.
4. Append only the missing keys to the environment's `environmentVariables` array.
5. Send the full environment back with `PUT /projects/{project_uid}/environments/{environment_uid}`.
6. Report the changes and stop without exposing values.


### Parse input

Read the local .env.example file and extract variable names. Ignore comments, blank lines, and malformed entries.

### Fetch Launch state

Call `GET /projects/{project_uid}/environments/{environment_uid}` and keep the whole `environment` object. Its `environmentVariables` array holds `{ "key", "value" }` pairs.

Use the regional base URL: `launch-api.contentstack.com` (AWS NA), `eu-launch-api.contentstack.com`, `au-launch-api.contentstack.com`, `azure-na-launch-api.contentstack.com`, `azure-eu-launch-api.contentstack.com`, `gcp-na-launch-api.contentstack.com` or `gcp-eu-launch-api.contentstack.com`.

Authenticate with `Authorization: Bearer <OAuth access token>` (recommended; scope `launch.projects:write` or `launch:manage`), or with the `authtoken` and `organization_uid` headers. `x-cs-api-version` is optional and defaults to `1.0`. Read credentials from environment variables.

### Compare keys

Compare .env.example keys against Launch keys. Identify only missing keys unless the user explicitly asks to update existing values.

### Update environment

There is no PATCH endpoint. Use `PUT /projects/{project_uid}/environments/{environment_uid}` and treat it as a full replacement:

1. Start from the environment object you fetched.
2. Append the missing keys to `environmentVariables` with empty or placeholder values. Leave existing entries untouched.
3. Send the whole object back, keeping every other field (`name`, `gitBranch`, `frameworkPreset`, `buildCommand`, `outputDirectory`, `autoDeployOnPush`, `passwordProtection` and the rest) exactly as fetched.

Never send a body with only `environmentVariables`: settings you leave out can be reset. If the GET response masks existing values, stop and tell the user, because sending masked values back would overwrite the real ones. An environment holds at most 128 variables.

### Report results

Return a concise summary of missing keys, added keys, and any errors. Never print secret values or tokens.

### API behaviour

Validate the project and environment UIDs before updating. Change only the `environmentVariables` array, and only by adding missing keys. If the API returns validation errors, surface them without retrying blindly.

## MCP tools

If the Contentstack MCP server is connected with the `launch` group, use its tools instead of writing a script or calling the API with curl:

- Inspect: `get_all_projects`, `get_all_environments`, `get_an_environment` (`launch`)
- Change: `update_an_environment` (`launch`), which takes `project_uid`, `environment_uid` and the full `environment_data` object

The same rules apply: fetch with `get_an_environment`, append only missing keys, send the whole object back, and stop if values come back masked. Confirm before calling `update_an_environment`, as below.

## Output

- Use concise, machine-readable summaries, with the project UID and environment UID.
- Show the keys found in `.env.example`, the keys already in Launch, and the missing keys added, separately, plus a summary of API calls and the exit status.
- Do not print secret values from Launch or local files.
- In dry-run mode, clearly label that no changes were made.

## Security

### Defaults

- Never expose deployment tokens or environment secrets.
- Validate project and environment targets before updating.
- Do not print variable values in logs or output.
- Require explicit user intent before making any change, and prefer dry-run behavior unless the user asks to apply changes.
- Require confirmation for production environments, and never auto-deploy to production without review.

### Destructive Actions

Treat any PUT that changes Launch configuration, through the API or `update_an_environment`, as a destructive external action. Name the target project and environment and the keys to add, and wait for confirmation before applying changes. Do not broaden the update beyond missing keys unless the user explicitly requests it.

### Secrets

Never reveal secret values from .env.example or Launch. Log only key names and counts. Redact tokens, API keys, and environment values in all output.

### Environment Variables

Read environment variables only as needed for authentication and target selection. Never echo env var values. Support loading from local `.env.example` for comparison only, not for secret disclosure.
