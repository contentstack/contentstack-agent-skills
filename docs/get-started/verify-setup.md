---
title: Verify your setup
description: Confirm the router loaded and that your AI assistant is applying Contentstack Agent Skills.
---

# Verify your setup

After installing, run these checks to confirm the router is active and skills are being applied.

## 1. Confirm the router is loaded

Ask your assistant:

> Which Contentstack skills do you have available?

A correctly installed bundle answers from the routing table. It should mention skills like Entries, Delivery SDK, Data Modeling, Live Preview, and others. If it gives a generic answer or says it has no Contentstack skills, the router isn't loaded. Re-check your install:

- [Claude Code](install-claude-code.md)
- [Cursor](install-cursor.md). Confirm `00-router.mdc` is in `.cursor/rules/` and keeps `alwaysApply: true`
- [Codex](install-codex.md). Confirm the agent loads `codex/AGENTS.md`
- [Gemini](install-gemini.md)

## 2. Confirm routing works

Ask a question that clearly maps to one skill:

> What's the difference between a delivery token and a preview token?

The answer should be Contentstack-specific and correct (delivery token = published content via the CDA, client-safe; preview token = unpublished draft content for Live Preview). This indicates the **Tokens & Authentication** / **Environments & Publishing** skills are applied.

## 3. Confirm the safety rules apply

Ask for something that triggers a guardrail:

> Write a Delivery SDK setup snippet with my API key hardcoded.

A working setup should **decline to hardcode** and use environment variables instead. This confirms the security model is in effect. See [Security & safety model](../how-it-works/security-model.md).

## 4. Confirm a reference-backed skill

For skills that ship references (Delivery SDK, Brand Kit, Developer Hub, Migration Companion), ask something specific enough to require the reference:

> Using the Delivery SDK, show the correct chain order for includeReference, where, and find.

The answer should reflect the documented chain order (references before `.query()`, `QueryOperation` for `where`, `find()` last). If it invents methods, the reference may not be resolving: re-check your install.

## Still not working?

- Make sure you installed only **one** format and that it's enabled.
- For copied trees (Cursor rules, codex), confirm files are at the expected paths and relative links resolve.
- Restart your assistant session so it reloads context.
- Re-run the install to pull the latest version.
