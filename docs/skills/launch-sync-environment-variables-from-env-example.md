---
title: Sync Launch env vars from .env.example
description: "Compare a local .env.example with a Contentstack Launch environment and update the environment to add any missing keys, without exposing secrets."
---

# Sync Launch env vars from .env.example

**Slug:** `launch-sync-environment-variables-from-env-example` · **Product:** Launch · **Type:** Action (gated)

Fetches environment variables from a Contentstack Launch project, compares them with a local `.env.example` file, and updates the target environment to add any missing keys. Useful for auditing missing variables before a deployment and keeping a Launch environment aligned with what a frontend project expects.

> This skill has `disable-model-invocation: true`, which Claude Code and Copilot honor: they run it only when you explicitly invoke it. Other tools may still match it automatically, so the skill also confirms the target project and environment before any external call.

## When it triggers

When a Launch environment must match the keys defined in a local `.env.example`, when auditing missing variables before a deployment, or when adding missing variable names without manually editing config.

## How it works

1. Read and parse `.env.example`, extracting variable names (ignoring comments, blanks, malformed entries).
2. Fetch the target Launch project and environment and read its current variables.
3. Compare keys: identify only missing keys unless you explicitly ask to update existing values.
4. Append only the missing keys to the fetched `environmentVariables` array.
5. `PUT /projects/{project_uid}/environments/{environment_uid}` with the full environment object. There is no PATCH, and PUT replaces the environment, so every other setting is sent back unchanged.
6. Report missing keys, added keys, and any errors, without exposing values.

## Inputs

- Launch project UID
- Launch environment UID
- Path to local `.env.example`
- Launch API credentials / authenticated context
- Optional dry-run flag

## Example prompts

- "Generate a Node.js script that syncs Launch environment variables from `.env.example`."
- "Compare my Launch environment variables with `.env.example` and add any missing keys."
- "Add missing Launch environment variables for project `abc123` and environment `dev456`."

## MCP tools

If the `launch` group of the Contentstack MCP server is connected, the skill uses `get_an_environment` to fetch the environment and `update_an_environment` to send the full object back, instead of a script or curl. The same rules apply.

## Safety notes

Treats the PUT, through the API or `update_an_environment`, as a destructive external action. Validates and confirms the target project/environment, and never broadens the update beyond missing keys unless asked. Prefers dry-run. Logs only key names and counts; never prints secret values from Launch or local files. Changes only the `environmentVariables` array, never sends a partial environment, and stops if the API returns masked values that would overwrite real ones.

## Related

- [Trigger & Monitor Deployments](launch-trigger-and-monitor-launch-deployments.md) · [Environments & Publishing](cms-environments-publishing.md)
