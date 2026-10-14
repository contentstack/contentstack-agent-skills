---
title: Roles & Permissions
description: Design roles, permissions, teams, and token access in Contentstack with least-privilege guidance.
---

# Roles & Permissions

**Slug:** `cms-roles-permissions` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on designing roles, permissions, teams, and token access: built-in roles, custom roles, permission merging, team-based access, and token capabilities: with least-privilege guidance.

## When it triggers

When you ask about user permissions, role design, team management, token capabilities, access control, or automation access.

## What it covers

- **Built-in roles**: Owner, Admin, Developer, Content Manager. Use them when they fit; otherwise create a custom role.
- **Custom roles**: limit access by content type, environment, locale, branch, or action. Describe permissions by module, content type, and action; use `$all` for all instances when applicable.
- **Permission merging**: multiple roles combine allowed actions permissively, but explicit denials override grants. Watch overlap risks when roles are reused across teams/stacks.
- **Teams**: recommended for shared access across users and stacks; team membership maps users to stack roles and scales better than assigning roles individually.
- **Token capabilities**: choose the least-privileged token (management tokens, authtokens, OAuth) with SSO/org-owner edge cases noted.
- **Rate limits**: check `X-RateLimit-Remaining` and use backoff for automation/bulk operations.

## Example prompts

- "What built-in roles does Contentstack have?"
- "How do I restrict editors to only certain content types?"
- "What can management tokens do vs authtokens?"
- "How do I set up teams for multiple stacks?"
- "What happens when a user has multiple roles?"

## Safety notes

Read-only advisory. Never creates, modifies, or deletes roles, users, teams, or tokens. Never recommends management tokens in client-side code; prefers server-side proxies for privileged CMA access. Delivery tokens are client-safe for read-only delivery only.

## Related

- [Tokens & Authentication](cms-tokens-authentication.md) · [Workflows & Publish Rules](cms-workflows.md) · [Branches & Aliases](cms-branches-aliases.md)
