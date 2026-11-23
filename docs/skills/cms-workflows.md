---
title: Workflows & Publish Rules
description: "Design Contentstack workflows and publish rules for content governance: stage design, approvals, self-approval prevention, publish governance, and automation."
---

# Workflows & Publish Rules

**Slug:** `cms-workflows` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on designing workflows and publish rules that match your review process without unnecessary complexity or permission gaps.

## When it triggers

When you ask about workflow stage design, approval processes, publish rules, self-approval prevention, transition restrictions, or automation triggered by workflow changes.

## What it covers

- **Keep workflows simple**: 3–5 stages for most cases; add stages only for a clear business need. A content type can have one workflow per branch.
- **Stage design**: each stage defines who can advance entries, allowed next stages, and optional due dates/assignments. Max 20 stages; every transition is recorded in the audit log.
- **Prevent self-advancement**: an option turned on per stage, not a default. When on, the submitter can't also approve, so at least two distinct reviewers are needed.
- **Publish rules are separate**: they govern publish/unpublish conditions independently of workflows, with scope fields (branch, content type, language, environment, action) and conditions (required stage, approver, prevent self-approval).
- **Automation**: webhooks on workflow stage events (a separate workflow module; pick them in the webhook UI); the publish queue tracks pending actions and status.
- **Permission limitations**: only owners, admins, and developers can create workflows and publish rules. Management tokens can't change workflow stages or configure rules requiring user approval; user-scoped auth or OAuth tokens are needed for programmatic transitions.

## Example prompts

- "How many workflow stages should I have?"
- "How do I prevent an author from approving their own content?"
- "How do publish rules differ from workflows?"
- "Can I automate actions when content reaches a workflow stage?"
- "How do workflows work across branches?"

## MCP tools

With the `cma-extended` group, the agent can read workflows, publish rules, publish queue activity and the audit log (`get_all_workflows`, `get_a_single_workflow`, `get_publish_rules`, `get_publish_queue_activity`, `get_audit_log`). No MCP tool changes workflows, stages or publish rules; those changes happen in the UI or the CMA.

## Safety notes

Read-only advisory. Never creates, updates, publishes, unpublishes, or deletes workflows or publish rules. Use environment variables for credentials; route CMA examples through server-side proxies.

## Related

- [Roles & Permissions](cms-roles-permissions.md) · [Webhooks](cms-webhooks.md) · [Releases](cms-releases.md)
