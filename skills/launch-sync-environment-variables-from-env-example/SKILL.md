---
name: launch-sync-environment-variables-from-env-example
description: "Fetch environment variables from a Contentstack Launch project, compare them with a local `.env.example` file, and patch the target environment to add any missing keys."
argument-hint: "[project_uid] [environment_uid] [env_example_path]"
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash
context: fork
agent: general-purpose
---

# Sync Launch environment variables from .env.example

## Description

Fetch environment variables from a Contentstack Launch project, compare them with a local `.env.example` file, and patch the target environment to add any missing keys.

## When to Use

Use when a Launch environment must match the keys defined in a local `.env.example` file.
Use to audit missing environment variables before a deployment.
Use to add missing variable names to a Launch environment without manually editing config.

## User Problem

A Launch environment can drift from the variables expected by a frontend project. This skill checks the environment against `.env.example` and updates Launch when keys are missing.

## Success Criteria

All keys present in `.env.example` exist in the target Launch environment.
Missing keys are added through the Launch Projects/Environments API.
The script reports what was missing and what was updated.
No secrets are printed in logs.

## Expected Inputs

- Launch project UID
- Launch environment UID
- Path to local `.env.example` file
- Launch API credentials or authenticated context
- Optional: dry-run flag

## Expected Outputs

- List of keys found in `.env.example`
- List of keys already present in Launch
- List of missing keys that were patched
- Summary of API calls made
- Exit code indicating success or failure

## Example User Requests

- Generate a Node.js script that syncs Launch environment variables from `.env.example`.
- Compare my Launch environment variables with `.env.example` and add any missing keys.
- Write a script to patch missing Launch environment variables for project abc123 and environment dev456.

## Workflow Summary

Read and parse the local `.env.example` file.
Fetch the target Launch environment and its current variables.
Compare keys from the file against keys in Launch.
Build a minimal patch payload containing only missing keys.
Call PATCH /projects/{project_uid}/environments/{environment_uid}.
Report the changes and stop without exposing values.

## Instructions

### Parse input

Read the local .env.example file and extract variable names. Ignore comments, blank lines, and malformed entries.

### Fetch Launch state

Use the Launch API to get the target project and environment, then read the current environment variables.

### Compare keys

Compare .env.example keys against Launch keys. Identify only missing keys unless the user explicitly asks to update existing values.

### Patch environment

Call PATCH /projects/{project_uid}/environments/{environment_uid} with the minimal update needed to add missing keys.

### Report results

Return a concise summary of missing keys, patched keys, and any errors. Never print secret values or tokens.

## Output Format

Use concise, machine-readable summaries.
Do not print secret values from Launch or local files.
Show missing keys and updated keys separately.
Include the project UID and environment UID in the summary.
If running in dry-run mode, clearly label that no changes were made.

## Tooling Notes

Use the Launch API and Projects/Environments endpoints.
Validate project and environment UIDs before patching.
Avoid logging deployment tokens or environment secrets.
Use the smallest possible PATCH payload.
If the API returns validation errors, surface them without retrying blindly.

## Security

### Defaults

Never expose deployment tokens or environment secrets.
Validate project and environment targets before patching.
Do not print variable values in logs or output.
Require explicit user intent before making any change.
Prefer dry-run behavior unless the user asks to apply changes.

### Destructive Actions

Treat any PATCH that changes Launch configuration as a destructive external action. Confirm the target project and environment before applying changes. Do not broaden the update beyond missing keys unless the user explicitly requests it.

### Secrets

Never reveal secret values from .env.example or Launch. Log only key names and counts. Redact tokens, API keys, and environment values in all output.

### Environment Variables

Read environment variables only as needed for authentication and target selection. Never echo env var values. Support loading from local `.env.example` for comparison only, not for secret disclosure.

## Product Context

- - Product: Launch
- - Description: Contentstack Launch: hosting, deployment, edge delivery, serverless functions, environment management, and CI/CD for Contentstack-powered frontends.
- - Product safety rules: - Never expose deployment tokens or environment secrets.
- Validate deployment targets before triggering.
- Require confirmation for production deployments.
- Never auto-deploy to production without review.
- - Default tools: ["Launch API", "Projects", "Environments", "Deployments", "Serverless Functions", "Edge Delivery", "Custom Domains"]
- - Default connectors: ["Launch Proxy", "GitHub", "CI/CD Pipelines"]