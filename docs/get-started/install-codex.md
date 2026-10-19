---
title: Install for Codex
description: Install Contentstack Agent Skills in Codex as a plugin from the marketplace.
---

# Install for Codex

Codex installs the bundle as a **plugin**. The marketplace is defined in `.agents/plugins/marketplace.json` and the plugin itself in the root `plugin.json`. Codex reads the skills in their native format.

## Install

```
codex plugin marketplace add contentstack/contentstack-agent-skills
codex plugin add contentstack-skills@contentstack-skills
```

> Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills)

## What gets installed

All skills under `skills/<slug>/SKILL.md`, with their bundled `references/` and `scripts/`, frontmatter included.

## Verify

Ask Codex:

> Which Contentstack skills do you have available?

It should list skills from the bundle. See [Verify your setup](verify-setup.md).

## Use it

Ask Contentstack questions in natural language. Codex matches your request to a skill description, then follows that skill's `SKILL.md`:

> Review this content model and tell me what to simplify.

loads **Data Modeling Best Practices**.

## Update

Refresh the marketplace, then reinstall to pick up the latest release:

```
codex plugin marketplace upgrade contentstack-skills
codex plugin add contentstack-skills@contentstack-skills
```

## Troubleshooting

- **Codex ignores the skills** → confirm the plugin is installed, then start a new session so Codex reloads the skill list.
- **A bundled script can't be found** → scripts self-locate relative to their own directory; invoke them by absolute path inside the installed skill's `scripts/` folder.
