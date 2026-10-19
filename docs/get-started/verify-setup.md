---
title: Verify your setup
description: Confirm the skills loaded and that your AI assistant is applying Contentstack Agent Skills.
---

# Verify your setup

After installing, run these checks to confirm the skills are available and being applied.

## 1. Confirm the skills are loaded

Ask your assistant:

> Which Contentstack skills do you have available?

A correctly installed bundle lists skills by name and description. It should mention skills like Entries, Delivery SDK, Data Modeling, Live Preview, and others. If it gives a generic answer or says it has no Contentstack skills, the plugin isn't loaded. Re-check your install:

- [Claude Code](install-claude-code.md). Confirm `contentstack-skills` is installed and enabled in `/plugin`
- [claude.ai and Cowork](install-claude-ai.md). Confirm the plugin is enabled under **Customize → Plugins**
- [Cursor](install-cursor.md). Confirm the plugin is enabled under **Settings → Plugins**
- [Codex](install-codex.md)
- [GitHub Copilot](install-copilot.md)
- [Gemini](install-gemini.md). Confirm the extension appears in `gemini extensions list`

## 2. Confirm skill selection works

Ask a question that clearly maps to one skill:

> What's the difference between a delivery token and a preview token?

The answer should be Contentstack-specific and correct (delivery token = published content via the CDA, client-safe; preview token = unpublished content, exposed client-side only on preview deployments and never in production builds). This indicates the **Tokens & Authentication** / **Environments & Publishing** skills are applied.

## 3. Confirm the safety rules apply

Ask for something that triggers a guardrail:

> Write a Delivery SDK setup snippet with my API key hardcoded.

A working setup should **decline to hardcode** and use environment variables instead. This confirms the security model is in effect. See [Security & safety model](../how-it-works/security-model.md).

## 4. Confirm a reference-backed skill

For skills that ship references (Delivery SDK, Kickstart Next, Live Preview & Visual Editor Support, Brand Kit, Developer Hub, Migration Companion; Studio ships sibling guides next to its `SKILL.md`), ask something specific enough to require the reference:

> Using the Delivery SDK, show the correct chain order for includeReference, where, and find.

The answer should reflect the documented chain order (references before `.query()`, `QueryOperation` for `where`, `find()` last). If it invents methods, the reference may not be resolving: re-check your install.

## Still not working?

- Make sure the plugin or extension is enabled, not just installed.
- If you installed the same skills twice (for example, the plugin and the `skills` CLI), remove one so the agent doesn't see duplicates.
- Restart your assistant session so it reloads the skill list.
- Update to the latest version. Plugin-based tools only pick up changes when the bundle's version changes.
