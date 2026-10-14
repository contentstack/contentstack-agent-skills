---
title: Install for Claude Code
description: Install the Contentstack Agent Skills plugin in Claude Code.
---

# Install for Claude Code

Claude Code installs the bundle as a **plugin**. Claude sees each skill's name and description, and loads the matching skill when you ask a Contentstack question.

## Install

In a Claude Code session, add the marketplace and install the plugin:

```
/plugin marketplace add contentstack/contentstack-agent-skills
/plugin install contentstack-skills@contentstack-skills
```

> Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills). Replace `contentstack/contentstack-agent-skills` with your fork or local path if you're not installing from GitHub.

If you already added the marketplace in claude.ai, the plugin syncs to Claude Code automatically. See [Install for claude.ai and Claude Cowork](install-claude-ai.md).

## What gets installed

- The plugin and marketplace manifests from `.claude-plugin/`.
- All skills under `skills/<slug>/SKILL.md`, with their bundled `references/` and `scripts/`.

## Verify

Ask Claude:

> Which Contentstack skills do you have available?

It should list skills from the bundle. You can also run `/plugin` to confirm `contentstack-skills` is installed and enabled. For a deeper check, see [Verify your setup](verify-setup.md).

## Use it

Just ask Contentstack questions in natural language, no need to name a skill:

> Write a TypeScript Delivery SDK helper that fetches an entry by URL with pagination and typing.

Claude loads the **Delivery SDK** skill and follows its rules. To force a specific skill, name it directly (for example, *"use the Data Modeling skill to review this schema"*). Skills that only run on request, like the Launch action skills, are invoked as slash commands. Plugin installs namespace them, for example `/contentstack-skills:launch-trigger-and-monitor-launch-deployments` or `/contentstack-skills:cms-entries` (or `/cms-entries` if installed with the `skills` CLI).

## Update

Claude Code updates an installed plugin only when the bundle's version number changes. Refresh the marketplace to pick up a new release:

```
/plugin marketplace update contentstack-skills
```

You can also turn on auto-update for the marketplace from the `/plugin` menu.

## Troubleshooting

- **Claude doesn't seem to use Contentstack patterns** → confirm the plugin is installed and enabled in `/plugin`, start a new session, then re-check with the verify prompt above.
- **You don't see a recent change** → the version may not have been bumped yet; plugins only update on a new version.
- **A skill's reference content seems missing** → references are read on demand; ask a question specific enough that the skill needs them.
