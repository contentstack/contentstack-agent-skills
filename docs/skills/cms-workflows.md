---
title: Workflows & Publish Rules
description: Design Contentstack workflows and publish rules for content governance: stage design, approvals, self-approval prevention, publish governance, and automation.
---

# Workflows & Publish Rules

**Slug:** `cms-workflows` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on designing workflows and publish rules that match your review process without unnecessary complexity or permission gaps.

## When it triggers

When you ask about workflow stage design, approval processes, publish rules, self-approval prevention, transition restrictions, or automation triggered by workflow changes.

## What it covers

- **Keep workflows simple**: 3–5 stages for most cases; add stages only for a clear business need. A content type can have one workflow per branch.
- **Stage design**: each stage defines who can advance entries, allowed next stages, and optional due dates/assignments. Max 20 stages; every transition is recorded in the audit log.
- **Prevent self-advancement**: requires at least two distinct reviewers; the last editor can't advance the entry. Use at least two approvers or a role with multiple members.
- **Publish rules are separate**: they govern publish/unpublish conditions independently of workflows, with scope fields (branch, content type, language, environment, action) and conditions (required stage, approver, prevent self-approval).
- **Automation**: use webhook events like `entries.workflow_stage_change`; the publish queue tracks pending actions and status.
- **Permission limitations**: only owners, admins, and developers can create workflows and publish rules. Management tokens can't change workflow stages or configure rules requiring user approval; user-scoped auth or OAuth tokens are needed for programmatic transitions.

## Example prompts

- "How many workflow stages should I have?"
- "How do I prevent an author from approving their own content?"
- "How do publish rules differ from workflows?"
- "Can I automate actions when content reaches a workflow stage?"
- "How do workflows work across branches?"

## Safety notes

Read-only advisory. Never creates, updates, publishes, unpublishes, or deletes workflows or publish rules. Use environment variables for credentials; route CMA examples through server-side proxies.

## Related

- [Roles & Permissions](cms-roles-permissions.md) · [Webhooks](cms-webhooks.md) · [Releases](cms-releases.md)
