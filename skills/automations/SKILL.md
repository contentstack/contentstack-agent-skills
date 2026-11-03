---
name: automations
description: "Advise on Contentstack Automate (Automations, formerly Automation Hub), the no-code workflow product in Agent OS: designing automations from a trigger and steps, Contentstack, HTTP, scheduled and manual triggers, connectors and connected apps, If-Else and loop control flow, pause and resume, custom code steps, the HTTP Response step, executions and debugging failed runs, limits and credits, and how agents and automations call each other. Use when users ask how to automate a Contentstack task such as notifying Slack on publish, syncing entries to a search index, translating on workflow change, or calling an external API; why an automation did not run or failed; or which trigger, connector or step to use. For CMS webhook configuration itself, use cms-webhooks."
allowed-tools: Read Grep Glob
---

# Automations

Advise on Contentstack Automate (Automations, formerly Automation Hub), the no-code workflow product in Agent OS: triggers, steps and connectors, control flow, custom code, HTTP responses, executions and debugging, limits, and the bridge between automations and agents.

## When to use

- Automating a Contentstack or cross-system task: publish notifications, search indexing, translation, approvals, data syncs, calling an external API.
- Choosing a trigger, connector or step.
- Working out why an automation didn't run or failed.
- Connecting automations with agents.

Use another skill for:

- Configuring CMS webhooks that point at your own receiver → `cms-webhooks`
- Workflow stages and publish rules inside the CMS → `cms-workflows`
- Exposing automations to AI clients through MCP Profile Hub → `dx-mcp-server`
- Ready-made Marketplace integrations such as search or translation apps → `marketplace-apps`

## Before you answer

Find out the task to automate and the systems involved, what starts it (content event, HTTP call, schedule, manual), the data the steps need and where it comes from, and for failures the execution status and the failing step's output.

## Instructions

1. Clarify the outcome and the event that should start it.
2. Pick one trigger, then the connector actions in order, keeping the chain short and readable.
3. Add control flow only where the logic needs it.
4. Use a custom code step only when no connector action fits.
5. Activate, test, and debug from the execution record, not guesses. State limits and unshipped features honestly.


### Building blocks

An automation is one trigger plus an ordered list of steps. Each step usually runs one connector action and can use outputs from earlier steps with `{{step.path}}` references. A new automation is a draft and runs only after it is activated. An active automation can't be edited: switch it off, change it, and switch it on again.

### Triggers

- **Contentstack (CMS) events:** pick the stack and the event, such as an entry being published. The automation registers its trigger URL when activated. Events that arrive while it is inactive are accepted but nothing runs.
- **HTTP:** an incoming request to the automation's trigger URL starts a run. The URL has no documented authentication, so treat it as a secret, and check a shared header or token in an early If-Else step when the caller can send one.
- **Schedule:** runs on a timetable for syncs and reports.
- **Manual:** a person or an agent starts it on demand.

### Connectors and connected apps

Connectors package actions for outside services: Contentstack products, Slack, Microsoft Teams, Jira, Salesforce, AWS Lambda, translation and search services, email, HTTP and more. Saved credentials live in **Connected apps**, which shows which automations use each connection. Reauthorize expired OAuth connections there. A connection can't be deleted while an active automation uses it.

### Control flow

- **If-Else:** route on a condition; the branches merge afterwards.
- **Loop:** repeat steps for each item in a list from an earlier step. Loops have a per-plan iteration cap; steps over the cap are skipped.
- **Pause:** stop and wait for an approval, a callback or a timed event, then resume. A paused run can be resumed a limited number of times and carries a limited payload.

### Custom code

Use a code step when no connector action fits. It runs JavaScript in an isolated sandbox with no access to the host process or other runs. Only the return value is passed on, and there is a short time limit (about 5 seconds), so keep it to data shaping and light logic. Do heavy work in an external service through the HTTP connector. Code steps count against a monthly allowance; a step over it is skipped.

### HTTP responses

For HTTP-triggered automations, a **Response** step returns a reply to the caller. There can be only one, and it must be the last top-level step, outside loops and branches. Use it when the automation acts as a small API.

### Executions and debugging

Each run creates an execution with a status (pending, queued, running, paused, success, partially-executed, failed, rejected) and per-step outputs. When something goes wrong:

1. Check the automation is active and the trigger points at the right stack and event.
2. Open Executions and find the run. No run means the trigger didn't fire or the automation was inactive.
3. Read the first failing step's input and output, then fix the mapping, credentials or connector settings.
4. Re-run the failed execution once the cause is fixed.

Password fields are masked in logs. Runs over the organization's per-minute limit are rejected with 429.

### Limits and credits

Limits depend on the plan. Typical defaults: about 15 steps per automation (the trigger counts), 100 loop iterations, 1 MB output per step, and an HTTP connector cap of 5 minutes or 2 MB per response. Runs with AI work use AI credits reserved before the run starts; a run without enough credits is refused. Check the organization's plan for exact values.

### Agents and automations

Agents (Polaris and Custom Agents) can start an automation as a tool call, so a conversation can trigger an existing workflow. Running a custom agent as a step inside an automation is in progress and may not be available. Building an automation by prompting Polaris on the canvas is not shipped yet; don't present it as available.

## MCP tools

When the Contentstack MCP server is connected with the `automations` group, these tools act on Automate:

- Inspect: `list_automation_projects`, `get_automation_project`, `list_automations`, `get_automation` (optionally with its steps and triggers) (`automations`)
- Change: `create_automation_project`, `update_automation_project`, `set_automation_active`, `trigger_automation` (runs an automation with an HTTP trigger) (`automations`)
- Delete: `delete_automation_project` (`automations`)

There are no tools for building steps, editing connections or reading executions; use the Automate UI for those. When debugging, read the automation with `get_automation` to check it is active and see its trigger, then check Executions. MCP Profile Hub can also expose active HTTP-triggered automations as tools of their own.

## Output

Lead with the recommended design as a numbered trigger-and-steps outline. Show `{{step.path}}` mappings and code snippets only where needed. For debugging, name the execution status and the failing step first.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose connector credentials, OAuth tokens, API keys or trigger URLs.
- Store service credentials in Connected apps, never inline in steps or code.
- Validate input from HTTP triggers before acting on it.
- Don't present unshipped features as available.

### Destructive Actions

Before deleting automation projects, activating or deactivating an automation, or running one, name the project and automation and what the run will change, and wait for confirmation. Before suggesting steps that delete or overwrite content in Contentstack or other systems, state what will change and recommend testing on a non-production stack.

### Secrets

Never print or echo secrets, trigger URLs or masked values. Use placeholders in examples.

### Environment Variables

Use placeholder names for any credential in examples. Keep secrets in Connected apps or project variables, not in code steps.
