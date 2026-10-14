---
title: Supported tools & compatibility
description: The five formats Contentstack Agent Skills ship in, what each install produces, and how to choose.
---

# Supported tools & compatibility

The same 22 skills are packaged in five formats. You only need to install one: pick the row that matches your assistant.

| Tool                      | What you install                                                                     | What it produces                                                          | Install guide                                                    |
| ------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Claude Code**           | A plugin from the marketplace                                                        | The router is loaded into context; Claude auto-selects the matching skill | [Install for Claude Code](../get-started/install-claude-code.md) |
| **Cursor**                | The plugin, or `cursor/rules/*.mdc` copied into `.cursor/rules/`                     | An always-on router rule plus one rule per skill                          | [Install for Cursor](../get-started/install-cursor.md)           |
| **Codex / OpenAI agents** | The `codex/` markdown tree                                                           | `codex/AGENTS.md` router plus `codex/<slug>/SKILL.md` per skill           | [Install for Codex](../get-started/install-codex.md)             |
| **Gemini CLI**            | The extension via `gemini extensions install contentstack/contentstack-agent-skills` | The extension manifest wires the skills into Gemini                       | [Install for Gemini](../get-started/install-gemini.md)           |
| **`skills` CLI**          | A single skill on demand                                                             | Just the one skill you name                                               | [Use the skills CLI](../get-started/skills-cli.md)               |

## How to choose

- **You use one assistant for everything** → install the bundle for that tool (Claude Code, Cursor, Codex, or Gemini). The router ships with it, so the agent picks skills automatically.
- **You only want one capability** (e.g. just the Delivery SDK skill) → use the [`skills` CLI](../get-started/skills-cli.md) to pull that single skill.
- **Your team standardizes on a repo** → vendor the relevant tree (`cursor/rules/` or `codex/`) into your project so every contributor gets the same behavior.

## What "auto-selection" means

For the four full-bundle formats, the **router** is included and loaded into the agent's context. When you make a request, the agent reads the routing table, matches your intent to a skill, then loads and follows that skill. You don't name skills explicitly, though you can, if you want to force a specific one.

The `skills` CLI is different: it installs exactly the skill you name and nothing else, so there's no router and no auto-selection.

## Requirements

- An AI coding assistant from the list above.
- For the Launch skills: Launch API access for the target project and environment.

## Keeping skills current

Because all formats are generated from a single source, every tool gets the same behavior and the same updates. When the bundle is updated, re-running your tool's install (or pulling the latest repo) brings the generated trees up to date. See [Architecture](../how-it-works/architecture.md) for how the trees are kept in sync.
