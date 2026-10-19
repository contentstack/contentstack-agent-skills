---
title: Install for Cursor
description: Install Contentstack Agent Skills in Cursor as a plugin from the GitHub repository.
---

# Install for Cursor

Cursor installs the bundle as a **plugin** described by `.cursor-plugin/plugin.json`. Cursor reads the skills in their native format; there are no rule files to copy.

## Install

1. Open **Settings → Plugins**.
2. Choose **Add from GitHub repository**.
3. Enter `https://github.com/contentstack/contentstack-agent-skills`.

## What gets installed

- All skills under `skills/<slug>/SKILL.md`, with their bundled `references/` and `scripts/`.
- The plugin and marketplace manifests from `.cursor-plugin/`.

## Verify

Open the Cursor chat and ask:

> Which Contentstack skills do you have available?

It should list skills from the bundle. See [Verify your setup](verify-setup.md) for more.

## Use it

Ask Contentstack questions normally:

> How do I set up Contentstack Live Preview for SSR in Next.js?

Cursor matches the request to a skill description and applies it (here, **Live Preview & Visual Editor Support**).

## Update

Update the plugin from **Settings → Plugins**. A new release is picked up when the bundle's version number changes.

## Troubleshooting

- **Skills don't seem to apply** → confirm the plugin is listed and enabled under **Settings → Plugins**, then start a new chat.
- **You want to change a skill** → edits belong in `skills/<slug>/SKILL.md` in the repository, not in your local install. See [Add or edit a skill](../contributing/add-or-edit-a-skill.md).
