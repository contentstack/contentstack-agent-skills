---
title: Contentstack MCP
description: "Connect AI agents to Contentstack with the local @contentstack/mcp server or the hosted MCP Profile Hub: choosing, client setup, auth, tool scoping, and safety."
---

# Contentstack MCP

**Slug:** `dx-mcp-server` · **Product:** Developer Experience · **Type:** Advisory (read-only)

Helps you give an AI assistant scoped access to Contentstack over the Model Context Protocol, with either the local MCP server or the hosted MCP Profile Hub.

## When it triggers

When you ask how to give an AI assistant access to Contentstack, set up or debug the Contentstack MCP server or MCP Profile Hub, pick tool groups or profiles, fix MCP auth or missing tools, or build your own MCP integration.

## What it covers

- **Choosing**: the local `@contentstack/mcp` server (stdio, `npx`, best for individual developers) or MCP Profile Hub (hosted, Streamable HTTP, profiles, OAuth, Executions history, best for teams and web clients).
- **Local server**: `GROUPS` (`cma`, `cma-extended`, `cda`, `analytics`, `automations`, `brandkit`, `launch`, `developerhub`, `lytics`, `personalize`), `npx @contentstack/mcp --auth`, management token for CMA only, required IDs per group, stack-aware enrichment, and client config for Claude Code, Claude Desktop and Cursor.
- **Profile Hub**: system and custom profiles, the connector URL, client setup for Claude Code, claude.ai, Cursor, Codex, ChatGPT and stdio clients via `mcp-remote`, URL parameters, Automate automations and Agent OS agents as tools.
- **Safety**: read-only first, separate profiles per job, no tokens in shared config, confirmation before destructive calls.
- **Build your own**: the public tool definitions at `mcp.contentstack.com/<group>/tools`.

## Example prompts

- "How do I connect Claude Code to my Contentstack stack?"
- "Should my team use the MCP server or MCP Profile Hub?"
- "My MCP client shows no Contentstack tools."
- "How do I let an agent deploy to Launch but not delete content?"
- "Can an agent run one of our Automate automations?"

## MCP tools

This skill is about the MCP server itself. It summarizes the tools in each local server group (`cma` 78, `cma-extended` 22, `cda` 4, `analytics` 8, `automations` 9, `brandkit` 12, `launch` 27, `developerhub` 12, `lytics` 10, `personalize` 24), what no group covers (webhooks, roles, users, tokens, labels, extensions), and where to find the published tool definitions.

## Safety notes

Advisory. Recommends OAuth and the smallest tool set, warns before enabling write, delete, publish and deploy tools, and has the agent name the target and wait for confirmation before running one. Never echoes tokens. Profile Hub calls always run with the user's own Contentstack roles.

## Related

- [Tokens & Authentication](cms-tokens-authentication.md) · [Roles & Permissions](cms-roles-permissions.md) · [Contentstack CLI](dx-cli.md)
