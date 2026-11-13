---
title: Contentstack Studio (preview)
description: Build with Contentstack Studio end to end, through the Studio MCP first and the bundled specialist guides when it can't be used.
---

# Contentstack Studio (preview)

**Slug:** `studio` · **Product:** Studio · **Type:** Action (gated) · **Ships specialist guides**

> **Preview.** `studio` ships as a preview in 0.2.0; some guides are still being reconciled with the Studio team.

A router skill for Contentstack Studio and the stack behind it. When the Studio MCP (built on Flux) is connected, it does the work through that server, which tracks each goal, previews every change and asks before applying it. Otherwise it reads `skills-index.md`, loads the one specialist guide that matches the task, and follows it. The guides cover SDK install, project provisioning, component registration, section and template authoring, data binding, canvas and preview routes, publishing, verification, troubleshooting and migration.

## When it triggers

When a request touches Contentstack Studio: the Studio SDK, canvas, compositions, Connected or Freeform templates, sections and section slots, repeaters, registering components, BYOC, Studio preview routes, or making a project Studio-ready. It also triggers when Live Preview, Visual Editor, Launch hosting, content types and entries, or Personalize audiences and variants are part of Studio work. It deliberately does not trigger for general CMS, Live Preview, Visual Editor, Launch or Personalize questions that don't involve Studio.

## How it works

1. If the Studio MCP's tools are callable, start with `list_goals` and `next_step` and follow it. Every change is previewed and applied only after the author says yes.
2. It switches to the bundled guides only for five named reasons (the server isn't there, doesn't respond, can't sign in, has no goal for the request, or the author asks), and says so. `fallback-map.md` says which guide continues a goal the Studio MCP stopped part-way through.
3. From the guides: match the request against the trigger table in `skills-index.md`, or fall back to its topic map, then load the matched guide and follow it. Setup requests ("make this project Studio-ready") run the full convert-and-verify flow.
4. When working from the guides, apply two standing rules on every turn: decompose into atomic, reusable components before registering anything, and meet the definition of done so marketers, not just developers, can use the result.

It prefers Contentstack MCP tools when they are connected and falls back to OAuth-authenticated API calls for missing operations.

## MCP tools

The Studio MCP (`list_goals`, `next_step`, `preview`, `apply`, `check`, `get_guide`) is preferred for all Studio work. When working from the guides, the Contentstack MCP is used for the operations it supports: content types, entries and publishing through the `cma` group. Its `install-contentstack-mcp` guide discovers and verifies the server. The Studio API project list and configuration, and some token and Live Preview operations, still need OAuth HTTP or the Studio UI.

## Safety notes

Resolves credentials OAuth-first: it asks before reading or refreshing a stored OAuth session from another tool, and uses a session `authtoken` only as a last resort. Verifies the target stack with a read call before MCP work. Confirms before creating or changing stacks, content types, entries, compositions or Studio projects, whether through MCP or HTTP. Never prints tokens or `.env` contents, never weakens TLS verification, and never ships permissive frame headers outside the canvas route.

## Example prompts

- "Make this Next.js project Studio-ready."
- "Register my hero component with Studio."
- "Why does my repeater render nothing on the canvas?"
- "Add a Studio preview route."

## Related

- [Live Preview & Visual Editor Support](cms-live-preview-visual-editor-support-assistant.md) · [Data Modeling Best Practices](cms-data-modeling-best-practices.md) · [Delivery SDK](dx-delivery-sdk.md)
