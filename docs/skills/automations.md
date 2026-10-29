---
title: Automations
description: "Design and debug Contentstack Automate workflows: triggers, connectors, control flow, custom code, HTTP responses, executions, limits and the agent bridge."
---

# Automations

**Slug:** `automations` · **Product:** Automate (Agent OS) · **Type:** Advisory (acts through MCP tools on request)

Advises on building no-code workflows in Contentstack Automate, such as publish notifications, search indexing, translation and data syncs, and on debugging them when they misbehave.

## When it triggers

When you ask how to automate a Contentstack or cross-system task, which trigger, connector or step to use, why an automation did not run or failed, or how automations and agents work together.

## What it covers

- **Building blocks**: one trigger plus ordered steps, `{{step.path}}` references, and the draft/active lifecycle (active automations can't be edited).
- **Triggers**: Contentstack events, HTTP (treat the URL as a secret), schedule and manual.
- **Connectors and Connected apps**: saved credentials, reauthorizing, dependencies.
- **Control flow**: If-Else, loops, pause and resume.
- **Custom code**: a sandboxed JavaScript step with a short time limit, for light logic only.
- **Response step**: replying to HTTP callers.
- **Executions**: statuses, per-step outputs and a debugging checklist.
- **Limits and credits**: plan-based step, loop and output caps, and AI credits.
- **Agents**: agents can start automations; AI-built automations on the canvas aren't shipped yet.

## Example prompts

- "Post to Slack whenever an entry is published."
- "Keep our Algolia index in sync with the stack."
- "Why didn't my automation run when I published?"
- "Can my automation wait for an approval before continuing?"

## MCP tools

With the `automations` group of the Contentstack MCP server connected, the agent can list and read projects and automations, and on request create projects, switch automations on or off, or run an automation that has an HTTP trigger (`trigger_automation`). Steps, connections and executions stay in the Automate UI.

## Safety notes

Advisory by default. Uses MCP tools only when asked, and names the automation and its effect before activating, running or deleting anything. Keeps credentials in Connected apps and recommends testing write or delete steps on a non-production stack.

## Related

- [Webhooks](cms-webhooks.md) · [Workflows](cms-workflows.md) · [Brand Kit Assistant](brand-kit-assistant.md)
