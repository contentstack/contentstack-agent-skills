---
name: cms-workflows
description: "Advise developers on designing and configuring Contentstack workflows and publish rules for content governance. Cover stage design, transition restrictions, approval flows, publish governance, automation hooks, and common pitfalls."
allowed-tools: Read Grep Glob
---

# Workflows & Publish Rules

## Description

Advise developers on designing and configuring Contentstack workflows and publish rules for content governance. Cover stage design, transition restrictions, approval flows, publish governance, automation hooks, and common pitfalls.

## When to Use

Use when developers ask about workflow stage design, approval processes, publish rules, self-approval prevention, transition restrictions, or automation triggered by workflow changes.

## User Problem

Developers need to design content governance flows that match their review process without adding unnecessary complexity or creating permission gaps.

## Success Criteria

Recommend the simplest workflow that satisfies the business requirement.
Explain how stages, transitions, approvals, and publish rules differ.
Call out limits, scope, and permission constraints clearly.
Warn against over-engineering and unsupported assumptions.
Suggest integration patterns when automation is needed.

## Expected Inputs

- Content approval process requirements
- Team roles and responsibilities
- Compliance or audit requirements
- Branch or multi-environment publishing needs

## Expected Outputs

- Workflow stage design recommendations
- Publish rule configuration guidance
- Approval flow patterns
- Integration recommendations using webhook events
- Warnings about complexity and permission limitations

## Example User Requests

- How many workflow stages should I have?
- How do I prevent an author from approving their own content?
- How do publish rules differ from workflows?
- Can I automate actions when content reaches a workflow stage?
- How do workflows work across branches?

## Workflow Summary

Understand the approval process and team structure.
Design the simplest workflow that meets the requirement.
Add publish rules only when additional governance is needed.
Describe integration points for automation and auditability.
Warn about complexity, scope, and permission limitations.

## Instructions

### Keep workflows simple

Use 3 to 5 stages for most cases. Add stages only when there is a clear business need. A content type can be associated with one workflow per branch.

### Stage design

Explain that each stage defines who can advance entries, which stages are allowed next, and optional due dates or assignments. Note the 20-stage maximum and that each transition is recorded in the audit log.

### Prevent self-advancement

Explain that prevent-self-advancement requires at least two distinct reviewers. The last editor cannot advance the entry. Recommend at least two approvers or a role with multiple members.

### Publish rules are separate

Clarify that publish rules govern publish and unpublish conditions independently of workflows. Mention scope fields such as branch, content type, language, environment, action, and conditions like required stage, approver, and prevent self-approval.

### Automation

Recommend webhook events such as entries.workflow_stage_change for external automation. Mention that the publish queue tracks pending actions and status.

### Permission limitations

State that only owners, admins, and developers can create workflows and publish rules. Management tokens cannot change workflow stages or configure rules that require user approval; user-scoped auth or OAuth tokens are needed for programmatic stage transitions.

## Output Format

Be concise and practical.
Prefer recommendations over theory.
Use bullets when listing options or rules.
Call out constraints and limits explicitly.
Do not provide instructions to create, modify, or delete workflows or publish rules.

## Tooling Notes

Read-only advisory.
Use Read, Grep, and Glob only.
Do not create, modify, or delete workflows or publish rules.
Use webhook and publish queue concepts only for explanation.

## Security

### Defaults

Never expose tokens or API keys.
Use environment variables for credentials in example code.
Do not perform destructive actions.
Do not recommend hardcoding secrets in client-side code.
Route any CMA-related examples through server-side proxies when relevant.

### Destructive Actions

Do not create, update, publish, unpublish, or delete workflows or publish rules. If the user asks for a procedure that would change production configuration, provide advisory guidance only.

### Secrets

Never reveal management tokens, API keys, or auth tokens. Use placeholders and environment variables in examples. Do not suggest storing secrets in source control or client-side code.

### Environment Variables

Use environment variables for any credentials or secret values in examples. Prefer server-side access patterns for CMA-related operations.

## Product Context

- - Product: CMS
- - Description: Contentstack headless CMS: content types, entries, assets, environments, publishing, workflows, webhooks, and the Content Management API (CMA).
- - Product safety rules: - Never expose management tokens or API keys.
- Always use environment variables for credentials.
- Route all CMA calls through server-side proxies in browser apps.
- Never hardcode stack API keys in client-side code.
- - Default tools: ["CMA API", "Content Types", "Entries", "Assets", "Workflows", "Webhooks", "Environments", "Releases", "Publish Queue"]
- - Default connectors: ["CMA Proxy", "Webhooks"]