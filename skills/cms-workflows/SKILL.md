---
name: cms-workflows
description: "Advise developers on designing and configuring Contentstack workflows and publish rules for content governance. Cover stage design, transition restrictions, approval flows, publish governance, automation hooks, and common pitfalls. Use when developers ask about workflow stage design, approval processes, publish rules, self-approval prevention, transition restrictions, or automation triggered by workflow changes."
allowed-tools: Read Grep Glob
---

# Workflows & Publish Rules

Advise on content governance with workflows and publish rules: stage design, transition restrictions, approvals, publish governance, automation hooks and common pitfalls.

## When to use

- Designing workflow stages and transitions.
- Setting up approval flows and preventing self-approval.
- Choosing between workflows and publish rules.
- Automating actions when content reaches a stage.
- Understanding how workflows behave across branches.

Use another skill for:

- Roles and who can do what → `cms-roles-permissions`
- Webhook receivers for workflow events → `cms-webhooks`
- No-code automation on workflow events → `automations`
- Scheduling and bundling publishes → `cms-releases`
- Environments and publishing mechanics → `cms-environments-publishing`

## Before you answer

Find out the approval process, the team structure and who approves, the content types and branches involved, and any automation or audit requirements.

## Instructions

1. Understand the approval process and team structure.
2. Design the simplest workflow that meets the requirement.
3. Add publish rules only when more governance is needed.
4. Describe integration points for automation and auditability.
5. Warn about complexity, scope and permission limitations.

### Keep workflows simple

Use 3 to 5 stages for most cases. Add stages only when there is a clear business need. A content type can be associated with one workflow per branch.

### Stage design

Explain that each stage defines who can advance entries, which stages are allowed next, and optional due dates or assignments. Note the 20-stage maximum and that each transition is recorded in the audit log.

### Prevent self-advancement

Prevent-self-advancement is an option you turn on per stage, not a default for every workflow. When it is on, the person who submitted the entry cannot also approve it, so at least two distinct reviewers are needed. Recommend at least two approvers or a role with multiple members for those stages.

### Publish rules are separate

Clarify that publish rules govern publish and unpublish conditions independently of workflows. Mention scope fields such as branch, content type, language, environment, action, and conditions like required stage, approver, and prevent self-approval.

### Automation

Recommend webhooks on workflow stage events for external automation. These come from the workflow module, so select them in the webhook UI instead of guessing a channel name. Mention that the publish queue tracks pending actions and status.

### Permission limitations

State that only owners, admins, and developers can create workflows and publish rules. Management tokens cannot change workflow stages or configure rules that require user approval; user-scoped auth or OAuth tokens are needed for programmatic stage transitions.

## MCP tools

When the Contentstack MCP server is connected, these tools read the governance setup (local server group in brackets):

- Inspect: `get_all_workflows`, `get_a_single_workflow`, `get_publish_rules`, `get_publish_queue_activity`, `get_audit_log` (`cma-extended`); `get_publish_queue` (`cma`)

No MCP tool creates or changes workflows, stages or publish rules, or moves an entry between stages. Make those changes in stack Settings → Workflows and Publish Rules, or with the Content Management API using user-scoped auth or OAuth.

## Output

Be concise and practical, with recommendations over theory. Use bullets when listing options or rules, and call out constraints and limits explicitly.

## Security

### Defaults

- Advisory by default. This skill does not create, modify, or delete workflows or publish rules.
- Never expose tokens or API keys.
- Use environment variables for credentials in example code.
- Do not recommend hardcoding secrets in client-side code.
- Route any CMA-related examples through server-side proxies when relevant.

### Destructive Actions

Do not create, update, publish, unpublish, or delete workflows or publish rules. If the user asks for a procedure that would change production configuration, give the steps and name the stack, branch and content types affected for them to apply.

### Secrets

Never reveal management tokens, API keys, or auth tokens. Use placeholders and environment variables in examples. Do not suggest storing secrets in source control or client-side code.

### Environment Variables

Use environment variables for any credentials or secret values in examples. Prefer server-side access patterns for CMA-related operations.
