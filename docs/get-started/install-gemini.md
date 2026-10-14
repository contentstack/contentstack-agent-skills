---
title: Install for Gemini CLI
description: Install Contentstack Agent Skills as a Gemini CLI extension.
---

# Install for Gemini CLI

Gemini CLI installs the bundle as an **extension** described by `gemini-extension.json`.

## Install

```
gemini extensions install https://github.com/contentstack/contentstack-agent-skills
```

> Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills). Replace the URL with your fork or local path if needed.

## What gets installed

The extension manifest (`gemini-extension.json`) registers the bundle as the `contentstack-skills` extension. Gemini picks up the extension's `skills/` folder automatically, so every skill is available with their `references/` and `scripts/`.

## Verify

Ask Gemini:

> Which Contentstack skills do you have available?

It should list skills from the bundle. See [Verify your setup](verify-setup.md).

## Use it

Ask Contentstack questions in natural language:

> How do I deploy a campaign of 50 entries together without my static site rebuilding hundreds of times?

loads the **Releases** skill (and **Webhooks** for the rebuild storm).

## Update

```
gemini extensions update contentstack-skills
```

## Troubleshooting

- **The extension installed but skills don't apply** → run `gemini extensions list` to confirm `contentstack-skills` is enabled, then restart Gemini.
- **You want only one capability** → use the [`skills` CLI](skills-cli.md) instead to pull a single skill.
