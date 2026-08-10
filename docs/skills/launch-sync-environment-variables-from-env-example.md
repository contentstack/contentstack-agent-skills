---
title: Sync Launch env vars from .env.example
description: Compare a local .env.example with a Contentstack Launch environment and patch the environment to add any missing keys: without exposing secrets.
---

# Sync Launch env vars from .env.example

**Slug:** `launch-sync-environment-variables-from-env-example` · **Product:** Launch · **Type:** Action (gated)

Fetches environment variables from a Contentstack Launch project, compares them with a local `.env.example` file, and patches the target environment to add any missing keys. Useful for auditing missing variables before a deployment and keeping a Launch environment aligned with what a frontend project expects.

> This skill has `disable-model-invocation: true`. It runs only when you explicitly invoke it, not via automatic routing.

## When it triggers

When a Launch environment must match the keys defined in a local `.env.example`, when auditing missing variables before a deployment, or when adding missing variable names without manually editing config.

## How it works

1. Read and parse `.env.example`, extracting variable names (ignoring comments, blanks, malformed entries).
2. Fetch the target Launch project and environment and read its current variables.
3. Compare keys: identify only missing keys unless you explicitly ask to update existing values.
4. Build a minimal patch payload with only the missing keys.
5. `PATCH /projects/{project_uid}/environments/{environment_uid}`.
6. Report missing keys, patched keys, and any errors: without exposing values.

## Inputs

- Launch project UID
- Launch environment UID
- Path to local `.env.example`
- Launch API credentials / authenticated context
- Optional dry-run flag

## Example prompts

- "Generate a Node.js script that syncs Launch environment variables from `.env.example`."
- "Compare my Launch environment variables with `.env.example` and add any missing keys."
- "Patch missing Launch environment variables for project `abc123` and environment `dev456`."

## Safety notes

Treats any PATCH as a destructive external action. Validates and confirms the target project/environment, and never broadens the update beyond missing keys unless asked. Prefers dry-run. Logs only key names and counts; never prints secret values from Launch or local files. Uses the smallest possible PATCH payload.

## Related

- [Trigger & Monitor Deployments](launch-trigger-and-monitor-launch-deployments.md) · [Environments & Publishing](cms-environments-publishing.md)
