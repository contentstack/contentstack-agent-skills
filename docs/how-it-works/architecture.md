---
title: Architecture
description: How Contentstack Agent Skills are authored once and installed into every tool through small plugin manifests.
---

# Architecture

Contentstack Agent Skills follow a **single-source, no-copies** model. Each skill is authored once in the open [Agent Skills](https://agentskills.io) format, and every supported tool reads that format directly. Nothing is generated, so installed skills can't drift from source. The `docs/skills/` pages are hand-written, so keep them in step when a skill changes.

## Source of truth

Everything starts in `skills/`:

```
skills/
  <slug>/
    SKILL.md                 # the canonical skill definition
    references/              # optional, read-on-demand docs
    scripts/                 # optional, executable helpers
    *.md                     # optional sibling guides (e.g. studio's specialist files)
```

`skills/` is the **only** place you edit. See [Add or edit a skill](../contributing/add-or-edit-a-skill.md).

## Plugin manifests

Each tool finds the skills through its own manifest. They all point at the same `skills/` folder:

| Manifest | Used by |
| --- | --- |
| `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` | Claude Code, claude.ai / Cowork (synced), Copilot CLI |
| `plugin.json` (Agent Plugins 1.0) | Codex, VS Code |
| `.agents/plugins/marketplace.json` | Codex marketplace |
| `.cursor-plugin/plugin.json` + `.cursor-plugin/marketplace.json` | Cursor |
| `gemini-extension.json` | Gemini CLI (bundles `skills/` automatically) |

The **`skills` CLI** needs no manifest: it reads `skills/<slug>/` directly and copies the folder into the agent you choose.

## Why one copy

Maintaining a separate copy of every skill per tool would guarantee drift. Because every tool now reads `SKILL.md` natively:

1. Authors edit only `skills/`.
2. Every tool installs those same files, frontmatter, `references/` and `scripts/` included.
3. A change ships to every tool at once when the version is bumped.

## Validation (CI)

`scripts/validate.mjs` checks the repository:

- Every skill's `name` matches its folder name and follows the naming rules (lowercase letters, digits, single hyphens, max 64 characters).
- Every `description` exists, includes "Use when…", and stays within 1024 characters.
- Every `SKILL.md` has a `## Security` section with `### Defaults`, `### Destructive Actions`, `### Secrets` and `### Environment Variables`.
- Relative links in every markdown file under `skills/` resolve and stay inside the skill's folder (links in code blocks are ignored).
- Frontmatter values in `skills/` and `docs/` that contain `: ` are quoted.
- Every manifest parses. The versioned manifests (`.claude-plugin/plugin.json`, the plugin entry in `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json`, `plugin.json` and `gemini-extension.json`) must each declare a `version`, and all versions must match. The Cursor and Codex marketplace files have no version field; they point at the plugin, which carries it.

Run it locally with `node scripts/validate.mjs`. The GitHub Action in `.github/workflows/validate.yml` runs it on pull requests to any branch, on pushes to `main` and `next`, and manually (workflow dispatch).

## Repository layout

```
skills/<slug>/SKILL.md            Source of truth: one folder per skill
.claude-plugin/                   Claude Code / claude.ai / Copilot CLI plugin and marketplace
.cursor-plugin/                   Cursor plugin and marketplace
.agents/plugins/marketplace.json  Codex marketplace
plugin.json                       Agent Plugins manifest (Codex, VS Code)
gemini-extension.json             Gemini CLI extension
.github/workflows/validate.yml    CI that runs the validator
scripts/validate.mjs              Validates skills and manifests
docs/                             This documentation
CLAUDE.md                         Contributor guide (AGENTS.md is a symlink to it)
```

## Implications for docs

Skill pages mirror their `SKILL.md`, so keep the [skills reference](../skills/index.md) in step with `skills/` when you add or change a skill. See [Add or edit a skill](../contributing/add-or-edit-a-skill.md).
