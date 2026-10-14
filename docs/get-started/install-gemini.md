---
title: Install for Gemini CLI
description: Install Contentstack Agent Skills as a Gemini CLI extension.
---

# Install for Gemini CLI

Gemini CLI installs the bundle as an **extension** described by `gemini-extension.json`.

## Install

```
gemini extensions install contentstack/contentstack-agent-skills
```

> Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills). Replace `contentstack/contentstack-agent-skills` with your fork or local path if needed.

## What gets installed

The extension manifest (`gemini-extension.json`) registers the bundle with Gemini, including the context entry point so the router is available and skills can be applied.

## Verify

Ask Gemini:

> Which Contentstack skills do you have available?

It should list skills from the bundle. See [Verify your setup](verify-setup.md).

## Use it

Ask Contentstack questions in natural language:

> How do I deploy a campaign of 50 entries together without my static site rebuilding hundreds of times?

routes to the **Releases** skill (and references **Webhooks** for the rebuild storm).

## Update

Re-run `gemini extensions install` against the latest version, or update through the Gemini extension workflow.

## Troubleshooting

- **The extension installed but skills don't apply** → confirm the extension is enabled and that Gemini loaded the manifest's context file.
- **You want only one capability** → use the [`skills` CLI](skills-cli.md) instead to pull a single skill.
