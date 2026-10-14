---
title: Install for GitHub Copilot
description: Install Contentstack Agent Skills as a plugin in GitHub Copilot CLI or VS Code.
---

# Install for GitHub Copilot

GitHub Copilot installs the bundle as a **plugin**. Copilot CLI uses the marketplace in `.claude-plugin/`; VS Code uses the root `plugin.json`. Both read the skills in their native format.

## Install

### Copilot CLI

```
copilot plugin marketplace add contentstack/contentstack-agent-skills
copilot plugin install contentstack-skills@contentstack-skills
```

### VS Code

Add the repository to the `chat.plugins.marketplaces` setting:

```json
"chat.plugins.marketplaces": ["contentstack/contentstack-agent-skills"]
```

Then install **contentstack-skills** from the Extensions view.

> Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills)

## What gets installed

All skills under `skills/<slug>/SKILL.md`, with their bundled `references/` and `scripts/`.

## Verify

Ask Copilot (in the CLI or Copilot Chat in agent mode):

> Which Contentstack skills do you have available?

It should list skills from the bundle. See [Verify your setup](verify-setup.md).

## Use it

Ask Contentstack questions in natural language:

> What token should I use to read published content from my frontend?

Copilot loads the **Tokens & Authentication** skill.

## Update

Re-run `copilot plugin install contentstack-skills@contentstack-skills` in the CLI, or update the plugin from the Extensions view in VS Code.

## Troubleshooting

- **Skills don't apply in VS Code** → make sure Copilot Chat is in agent mode and the plugin is enabled, then start a new chat.
- **You want only one capability** → use the [`skills` CLI](skills-cli.md) instead to pull a single skill.
