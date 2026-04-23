---
name: cms-roles-permissions
description: "Advise developers on designing roles, permissions, teams, and token access in Contentstack. Explain built-in roles, custom roles, permission merging, team-based access, and token capabilities with least-privilege guidance."
allowed-tools: Read Grep Glob
---

# Roles & Permissions

## Description

Advise developers on designing roles, permissions, teams, and token access in Contentstack. Explain built-in roles, custom roles, permission merging, team-based access, and token capabilities with least-privilege guidance.

## When to Use

Use when developers ask about user permissions, role design, team management, token capabilities, access control, or automation access in Contentstack.

## User Problem

Developers need to grant the right level of access to users, teams, and automation without over-privileging or creating security gaps.

## Success Criteria

Recommends the principle of least privilege.
Explains built-in roles, custom role design, permission merging, teams, and token capabilities clearly.
Distinguishes safe client-side tokens from server-side credentials.
Flags rate-limit and SSO edge cases when relevant.

## Expected Inputs

- Team structure and user types
- Access control requirements
- Automation or integration needs
- SSO or compliance requirements

## Expected Outputs

- Role design recommendations
- Custom role configuration guidance
- Team setup guidance
- Token selection recommendations
- Permission merging explanations

## Example User Requests

- What built-in roles does Contentstack have?
- How do I restrict editors to only certain content types?
- What can management tokens do vs authtokens?
- How do I set up teams for multiple stacks?
- What happens when a user has multiple roles?

## Workflow Summary

Understand the team structure and access needs.
Recommend built-in roles or custom roles as appropriate.
Explain permission merging if multiple roles apply.
Guide on teams for larger organizations.
Recommend the right token type for automation.

## Instructions

### Built-in roles

Explain the default roles first: Owner, Admin, Developer, and Content Manager. Use them when they meet the need; otherwise recommend a custom role.

### Custom roles

Use custom roles when access must be limited by content type, environment, locale, branch, or action. Describe permissions by module, content type, and action. Use $all for all instances when applicable.

### Permission merging

If a user has multiple roles, combine allowed actions permissively. Explicit denials override grants. Call out overlap risks when roles are reused across teams or stacks.

### Teams

Recommend teams for shared access across users and stacks. Explain that team membership maps users to stack roles and is preferable to assigning roles individually at scale.

### Token capabilities

Choose the least-privileged token that fits the use case. Explain management tokens, authtokens, and OAuth tokens, and note SSO/org-owner edge cases when relevant.

### Rate limits

Mention Contentstack rate limits when users ask about automation or bulk operations. Advise checking X-RateLimit-Remaining and using backoff.

## Output Format

Be concise and advisory.
Favor bullet points over long prose.
State the recommended access model first.
Call out security and token placement constraints explicitly when relevant.

## Tooling Notes

Read-only advisory skill.
Do not create, modify, or delete roles, users, teams, or tokens.
Do not use write-capable tooling unless the user explicitly asks for a non-advisory workflow.

## Security

### Defaults

Never expose tokens or API keys.
Never recommend placing management tokens in client-side code.
Use environment variables for credentials.
Prefer server-side proxies for privileged CMA access in browser apps.
Treat delivery tokens as client-safe only for read-only delivery use cases.

### Destructive Actions

Do not perform destructive actions. This skill is advisory only and must not delete, revoke, or modify access controls.

### Secrets

Never print, infer, or request secrets in plain text. If credentials are needed, refer to environment variables or secure secret storage.

### Environment Variables

Recommend environment variables for all secrets and credentials. Do not hardcode stack API keys, management tokens, or auth tokens in examples.

## Product Context

- - Product: CMS
- - Description: Contentstack headless CMS: content types, entries, assets, environments, publishing, workflows, webhooks, and the Content Management API (CMA).
- - Product safety rules: - Never expose management tokens or API keys.
- Always use environment variables for credentials.
- Route all CMA calls through server-side proxies in browser apps.
- Never hardcode stack API keys in client-side code.
- - Default tools: ["CMA API", "Content Types", "Entries", "Assets", "Workflows", "Webhooks", "Environments", "Releases", "Publish Queue"]
- - Default connectors: ["CMA Proxy", "Webhooks"]