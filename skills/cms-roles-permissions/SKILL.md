---
name: cms-roles-permissions
description: "Advise developers on designing roles, permissions, teams, and token access in Contentstack. Explain built-in roles, custom roles, permission merging, team-based access, and token capabilities with least-privilege guidance. Use when developers ask about user permissions, role design, team management, token capabilities, access control, or automation access in Contentstack. For choosing and storing tokens and API auth flows, use cms-tokens-authentication."
allowed-tools: Read Grep Glob
---

# Roles & Permissions

Advise on giving users, teams and automation the right level of access in Contentstack, with least privilege and without security gaps.

## When to use

- Explaining built-in roles or designing custom roles.
- Restricting access by content type, environment, locale, branch or action.
- Working out effective permissions when a user has several roles.
- Setting up teams across stacks.
- Choosing the least-privileged credential for automation.

Use another skill for:

- Token types, storage, rotation and auth flows → `cms-tokens-authentication`
- Workflow stages and publish rules (who can approve or publish) → `cms-workflows`
- Branch-scoped access and aliases → `cms-branches-aliases`
- App permissions and OAuth scopes for Developer Hub apps → `developer-hub-app-architect`

## Before you answer

Find out the team structure and user types, the access the requirement needs, any automation or integration that needs credentials, and any SSO or compliance requirements.

## Instructions

1. Understand the team structure and access needs.
2. Recommend built-in roles or custom roles as appropriate.
3. Explain permission merging if several roles apply.
4. Recommend teams for larger organizations.
5. Recommend the right token type for automation.

### Built-in roles

Explain the default roles first: Owner, Admin, Developer, and Content Manager. Some organizations have additional system roles, such as a read-only role, so check the stack's Roles list. Use built-in roles when they meet the need; otherwise recommend a custom role.

### Custom roles

Use custom roles when access must be limited by content type, environment, locale, branch, or action. Describe permissions by module, content type, and action. Use $all for all instances when applicable.

### Permission merging

A user's effective permissions are the union of every role that applies: direct stack roles, team roles and organization roles. There is no deny rule, so a role cannot take away access that another role grants. Call out overlap risks when roles are reused across teams or stacks, and remove a role rather than trying to override it.

### Teams

Recommend teams for shared access across users and stacks. Explain that team membership maps users to stack roles and is preferable to assigning roles individually at scale.

### Token capabilities

Choose the least-privileged credential that fits the use case. Explain management tokens (stack-scoped, at most 10 valid per stack at a time), authtokens, OAuth tokens, and machine-to-machine (M2M) apps, which use the OAuth client-credentials grant for service-to-service automation. Note SSO and org-owner edge cases when relevant.

### Rate limits

Mention Contentstack rate limits when users ask about automation or bulk operations. Advise checking X-RateLimit-Remaining and using backoff.

## MCP tools

No Contentstack MCP tool manages roles, users, teams or tokens. Make these changes in the Contentstack UI (stack Settings → Roles, organization Teams) or with the Content Management API's roles endpoints.

To review who changed access, `get_audit_log` and `get_audit_log_item` (`cma-extended`) read the stack audit log.

## Output

Lead with the recommended access model, then the details. Keep it concise and favor bullet points over long prose. Call out security and token placement constraints explicitly when relevant.

## Security

### Defaults

- Advisory by default. This skill does not create, modify, or delete roles, users, teams, or tokens.
- Recommend least privilege.
- Never expose tokens or API keys, and never recommend placing management tokens in client-side code.
- Prefer server-side proxies for privileged CMA access in browser apps.
- Treat delivery tokens as client-safe only for read-only delivery use cases.

### Destructive Actions

Do not delete, revoke, or modify access controls. If the user wants a change made, give the steps and the target (stack, role, team) for them to apply.

### Secrets

Never print, infer, or request secrets in plain text. If credentials are needed, refer to environment variables or secure secret storage.

### Environment Variables

Recommend environment variables for all secrets and credentials. Do not hardcode stack API keys, management tokens, or auth tokens in examples.
