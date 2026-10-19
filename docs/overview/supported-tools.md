---
title: Supported tools & compatibility
description: The tools Contentstack Agent Skills install into, what each install gives you, and how to choose.
---

# Supported tools & compatibility

The same skills install into every tool below. Each one reads the [Agent Skills](https://agentskills.io) format natively, so there's no tool-specific copy: just a different way to install. Pick the row that matches your assistant.

| Tool                         | What you install                                         | Install guide                                                         |
| ---------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------- |
| **Claude Code**              | The `contentstack-skills` plugin from the marketplace    | [Install for Claude Code](../get-started/install-claude-code.md)      |
| **claude.ai / Claude Cowork** | The same plugin, added as a marketplace in Customize     | [Install for claude.ai and Cowork](../get-started/install-claude-ai.md) |
| **Cursor**                   | The plugin, added from the GitHub repository             | [Install for Cursor](../get-started/install-cursor.md)                |
| **Codex**                    | The plugin from the Codex marketplace                    | [Install for Codex](../get-started/install-codex.md)                  |
| **GitHub Copilot**           | The plugin in Copilot CLI or VS Code                     | [Install for GitHub Copilot](../get-started/install-copilot.md)       |
| **Gemini CLI**               | The extension from the GitHub repository                 | [Install for Gemini](../get-started/install-gemini.md)                |
| **`skills` CLI**             | One or more skills you name, into any supported agent    | [Use the skills CLI](../get-started/skills-cli.md)                    |

Every full install gives you every skill with its `references/`, `scripts/` and any sibling guide files (such as `studio`'s specialist guides).

## How to choose

- **You use one assistant for everything** → install the plugin or extension for that tool. The agent picks skills automatically.
- **You only want one capability** (e.g. just the Delivery SDK skill) → use the [`skills` CLI](../get-started/skills-cli.md) to pull that single skill.
- **Your agent isn't listed** → the `skills` CLI also installs into Windsurf, Cline, and other agents that read the Agent Skills format.

## What "auto-selection" means

Agents load only each skill's `name` and `description` at startup. When you make a request, the agent matches it against the "Use when…" part of those descriptions, then loads and follows the matching skill. You don't name skills explicitly, though you can if you want to force a specific one. See [How skill selection works](../how-it-works/router.md).

This works the same whether you installed the whole bundle or a single skill with the `skills` CLI; with one skill there's simply less to choose from.

## Requirements

- An AI coding assistant from the list above.
- For the Launch skills: Launch API access for the target project and environment.
- For Migration Companion: Node 20+, Python 3, the Contentstack CLI (`csdx`), the Contentful CLI, and a shell.
- For Studio: a Contentstack account with Studio enabled, plus OAuth or the Contentstack MCP.
- For Brand Kit API tasks: Brand Kit API credentials and the account's region.

## Keeping skills current

Every tool installs from the same `skills/` folder, so every tool gets the same behavior and the same updates. Each install guide has an **Update** section. Plugin-based tools pick up a new release when the bundle's version number changes. See [Release & versioning](../contributing/release-and-versioning.md).
