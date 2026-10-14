---
title: Install for claude.ai and Claude Cowork
description: Add Contentstack Agent Skills to claude.ai and Claude Cowork as a plugin marketplace.
---

# Install for claude.ai and Claude Cowork

claude.ai installs the bundle as a **plugin** from a marketplace. Once added, the skills are available in claude.ai, Claude Cowork, and Claude Code.

## Install

1. In claude.ai, go to **Customize → Plugins → Add marketplace**.
2. Enter `contentstack/contentstack-agent-skills`.
3. Install the **contentstack-skills** plugin from that marketplace.

> Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills)

## What gets installed

The same plugin Claude Code uses (`.claude-plugin/`): all skills under `skills/<slug>/SKILL.md`, with their bundled `references/` and `scripts/`.

## Verify

Start a new conversation and ask:

> Which Contentstack skills do you have available?

It should list skills from the bundle. See [Verify your setup](verify-setup.md).

## Use it

Ask Contentstack questions in natural language:

> Should product categories be a taxonomy, tags, or a referenced content type?

Claude loads the **Taxonomy** and **Data Modeling** skills as needed.

## Update

The marketplace stays linked to the repository, so the plugin updates when a new version is released. No reinstall needed.

## Troubleshooting

- **Skills don't show up** → confirm the plugin is installed and enabled under **Customize → Plugins**, then start a new conversation.
- **Bundled scripts don't run** → scripts need an environment that can execute code, such as Cowork or Claude Code. Advisory skills work everywhere.
