---
title: Concepts & terminology
description: "The core building blocks of Contentstack Agent Skills: skills, descriptions, references, bundled scripts, and plugin manifests."
---

# Concepts & terminology

This page defines the vocabulary used throughout the documentation.

## Skill

A **skill** is a single Contentstack capability packaged as instructions for an AI agent. Each skill lives at `skills/<slug>/SKILL.md` and describes one focused area, for example, querying entries or designing a content model. A skill tells the agent *when* it applies, *what* good output looks like, *how* to produce it, and *which* safety rules to enforce.

See [Anatomy of a SKILL.md](../how-it-works/skill-anatomy.md) for the full structure.

## Slug

The **slug** is a skill's directory name and stable identifier, for example `cms-entries` or `dx-delivery-sdk`. It must match the `name` field in the skill's frontmatter. Slugs are used by the `skills` CLI, for explicit invocation, and as the page names in the [skills reference](../skills/index.md).

## Description

Every skill's frontmatter has a **description**: what the skill does plus a "Use when…" sentence listing the requests that should trigger it. Agents see only each skill's `name` and `description` up front, and load the full `SKILL.md` when your request matches. The description is the routing; there is no separate router file.

See [How skill selection works](../how-it-works/router.md) for details.

## References

Some skills ship extra **reference material** in a `references/` folder next to the skill, for example the Delivery SDK spec or the Brand Kit API reference. The agent reads these on demand only when the task needs them, rather than loading everything up front. Reference-backed skills include `dx-delivery-sdk`, `dx-kickstart-next`, `cms-live-preview-visual-editor-support-assistant`, `brand-kit-assistant`, `developer-hub-app-architect`, and `migration-companion`. `studio` instead ships its specialist guides as sibling files next to `SKILL.md`.

## Bundled scripts

A few skills ship executable **scripts** in a `scripts/` folder. The Migration Companion, for example, bundles prerequisite checkers and post-migration evaluation scripts. The agent invokes these by absolute path during a workflow.

## Source of truth

`skills/<slug>/SKILL.md` is the **source of truth** and the only place skills are edited. It follows the open [Agent Skills](https://agentskills.io) format, which every supported tool reads natively, so there are no per-tool copies to generate or keep in sync.

## Plugin manifests

Each tool discovers the bundle through its own small manifest at the repository root: `.claude-plugin/` (Claude Code, claude.ai, Copilot CLI), `plugin.json` (Codex, VS Code), `.agents/plugins/marketplace.json` (Codex), `.cursor-plugin/` (Cursor), and `gemini-extension.json` (Gemini CLI). They all point at the same `skills/` folder, and every manifest that declares a version shares the same one. See [Architecture](../how-it-works/architecture.md).

## Product

Each skill is tagged with a **product** area: `CMS`, `Developer Experience`, `Studio`, `Launch`, `Brand Kit`, or `Developer Hub`. Products carry shared safety defaults, for example, every CMS skill enforces "never expose management tokens" and "route CMA calls through a server-side proxy."

## Advisory vs action skills

- **Advisory skills** (the majority) are read-only. They explain, design, review, and generate code but never mutate your Contentstack stack. Examples: Entries, Data Modeling, Webhooks.
- **Action skills** can perform external operations and therefore gate them behind confirmation. Examples: the Launch deployment skills (trigger a deploy, patch environment variables) the Migration Companion (creates a stack, edits your repo), and Studio (provisions projects, creates content types and entries).

The distinction matters for trust. See the [Security & safety model](../how-it-works/security-model.md).
