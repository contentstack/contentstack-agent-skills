---
title: Contentstack Studio
description: Build with Contentstack Studio end to end, routed to one of 109 bundled specialist guides per task.
---

# Contentstack Studio

**Slug:** `studio` · **Product:** Studio · **Type:** Action (gated) · **Ships specialist guides**

A router skill for Contentstack Studio and the stack behind it. It reads `skills-index.md`, loads the one specialist guide that matches the task, and follows it. The guides cover SDK install, project provisioning, component registration, section and template authoring, data binding, canvas and preview routes, publishing, verification, troubleshooting and migration.

## When it triggers

When a request touches Contentstack Studio: the Studio SDK, canvas, compositions, Connected or Freeform templates, sections and section slots, repeaters, registering components, BYOC, Studio preview routes, or making a project Studio-ready.

## How it works

1. Match the request against the trigger table in `skills-index.md`, or fall back to its topic map.
2. Load the matched specialist guide and follow it. Setup requests ("make this project Studio-ready") run the full convert-and-verify flow.
3. On every turn, apply two standing rules: decompose into atomic, reusable components before registering anything, and meet the definition of done so marketers, not just developers, can use the result.

It prefers Contentstack MCP tools when they are connected and falls back to OAuth-authenticated API calls for missing operations.

## Example prompts

- "Make this Next.js project Studio-ready."
- "Register my hero component with Studio."
- "Why does my repeater render nothing on the canvas?"
- "Add a Studio preview route."

## Related

- [Live Preview & Visual Editor Support](cms-live-preview-visual-editor-support-assistant.md) · [Data Modeling Best Practices](cms-data-modeling-best-practices.md) · [Delivery SDK](dx-delivery-sdk.md)
