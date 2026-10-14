---
title: Architecture
description: How Contentstack Agent Skills are authored once and generated into tool-specific formats that never drift.
---

# Architecture

Contentstack Agent Skills follow a **single-source, generated-artifacts** model. You author each skill once; the tool-specific formats are produced by build scripts and kept in sync automatically.

## Source of truth

Everything starts in `skills/`:

```
skills/
  CLAUDE.md                  # the router (intent → skill table)
  <slug>/
    SKILL.md                 # the canonical skill definition
    references/              # optional, read-on-demand docs
    scripts/                # optional, executable helpers
```

`skills/` is the **only** place you edit. See [Add or edit a skill](../contributing/add-or-edit-a-skill.md).

## Generated trees

Build scripts transform the source into each tool's format:

```
skills/<slug>/SKILL.md     ──►  cursor/rules/NN-<slug>.mdc
                           ──►  codex/<slug>/SKILL.md
skills/CLAUDE.md (router)  ──►  cursor/rules/00-router.mdc
                           ──►  codex/AGENTS.md
```

- **Cursor**: `scripts/build-cursor-rules.sh` writes `cursor/rules/`. The router becomes `00-router.mdc` with `alwaysApply: true`; each skill becomes `NN-<slug>.mdc`.
- **Codex**: `scripts/build-codex-skills.sh` writes `codex/`. The router becomes `AGENTS.md`; each skill becomes `<slug>/SKILL.md` with YAML frontmatter stripped and its `references/` and `scripts/` copied alongside.
- **Claude Code**: consumes `skills/` directly via the plugin manifests in `.claude-plugin/`.
- **Gemini CLI**: consumes the bundle via `gemini-extension.json`.
- **`skills` CLI**: pulls individual `skills/<slug>/` directories on demand.

## Why generated, not hand-maintained

Maintaining five copies of 22 skills by hand would guarantee drift. Instead:

1. Authors edit only `skills/`.
2. Build scripts regenerate `cursor/rules/` and `codex/`.
3. CI enforces that the generated trees match the source.

This keeps every tool's behavior identical and every update consistent.

## Drift protection (CI)

The GitHub Action in `.github/workflows/build.yml`:

- **On pull requests**: regenerates the trees and **fails the build** if anything differs from what's committed. This forces contributors to run the build scripts and commit the result.
- **On push to `main`**: regenerates the trees and commits any drift automatically (as `github-actions[bot]`).

The practical rule: never edit `cursor/rules/` or `codex/` directly. Your change will be reverted by the next regeneration.

## Repository layout

```
.claude-plugin/        Claude Code plugin + marketplace manifests
.cursor-plugin/        Cursor plugin manifest
.github/workflows/     CI that regenerates cursor/rules and codex
codex/                 Generated Codex tree: do not edit
cursor/rules/          Generated Cursor rules: do not edit
scripts/               Build scripts
skills/                Source of truth: edit here
docs/                  This documentation
manifest.json          Machine-readable index of all skills
gemini-extension.json  Gemini CLI extension manifest
```

## Implications for docs

Because skill pages mirror their `SKILL.md`, the [skills reference](../skills/index.md) is best kept in sync the same way, generated from `skills/*/SKILL.md` plus `manifest.json`. So it can't drift from the skills themselves. See [Authoring conventions](../contributing/authoring-conventions.md).
