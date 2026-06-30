---
title: Install for Claude Code
description: Install the Contentstack Agent Skills plugin in Claude Code.
---

# Install for Claude Code

Claude Code installs the bundle as a **plugin**. After install, the router is loaded into context and Claude automatically picks the matching skill when you ask a Contentstack question.

## Install

In a Claude Code session, add the marketplace and install the plugin:

```
/plugin marketplace add contentstack/contentstack-agent-skills
/plugin install contentstack-skills
```

> Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills). Replace `contentstack/contentstack-agent-skills` with your fork or local path if you're not installing from GitHub.

## What gets installed

- The plugin manifest from `.claude-plugin/` (`plugin.json` and `marketplace.json`).
- The router at `skills/CLAUDE.md`, loaded into context.
- All 22 skills under `skills/<slug>/SKILL.md`, with their bundled `references/` and `scripts/`.

## Verify

Ask Claude:

> Which Contentstack skills do you have available?

It should list skills from the bundle. For a deeper check, see [Verify your setup](verify-setup.md).

## Use it

Just ask Contentstack questions in natural language: no need to name a skill:

> Write a TypeScript Delivery SDK helper that fetches an entry by URL with pagination and typing.

Claude routes to the **Delivery SDK** skill and follows its rules. To force a specific skill, name it directly (for example, *"use the Data Modeling skill to review this schema"*).

## Update

Re-run the install (or update the marketplace) to pull the latest version of the bundle.

## Troubleshooting

- **Claude doesn't seem to use Contentstack patterns** → confirm the plugin is installed and enabled, then re-check with the verify prompt above.
- **A skill's reference content seems missing** → references are read on demand; ask a question specific enough that the skill needs them.
