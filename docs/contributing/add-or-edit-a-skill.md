---
title: Add or edit a skill
description: How to add a new Contentstack skill or change an existing one, then validate it before opening a pull request.
---

# Add or edit a skill

`skills/<slug>/SKILL.md` is the source of truth, and the only copy. Every tool installs it as-is, so there's nothing to regenerate. See [Architecture](../how-it-works/architecture.md).

## Edit an existing skill

1. Open `skills/<slug>/SKILL.md` and make your change.
2. If you added bundled assets, put them in `skills/<slug>/references/` or `skills/<slug>/scripts/` (or, like `studio`, as sibling guides next to `SKILL.md`) and link them with a relative path.
3. If the change affects when the skill should trigger, update the `description`.
4. Validate:

```bash
node scripts/validate.mjs
```

## Add a new skill

1. Create a directory: `skills/<new-slug>/`.
2. Copy the [skill template](skill-template.md) into `SKILL.md` and follow the rules in [Authoring conventions](authoring-conventions.md). List the Contentstack MCP tools that carry out the skill's steps under `## MCP tools`. The `name` must equal `<new-slug>`, and the `description` must include "Use when…" (1024 characters max).
3. Add any `references/` or `scripts/` the skill needs.
4. Add a row for the skill to the **Skills included** table in the root `README.md`.
5. Add a documentation page under `docs/skills/<new-slug>.md` and link it from `docs/skills/index.md`.
6. Add at least two [routing eval](routing-evals.md) cases, `evals/routing-<new-slug>-1` and `-2`, and run them.
7. Run `node scripts/validate.mjs` and commit.

The plugin manifests point at the whole `skills/` folder, so a new skill needs no manifest change.

## Choosing a slug

Slugs are stable identifiers used by the `skills` CLI, slash-command invocation, and the docs. Follow the existing convention:

- `cms-*` for CMS skills
- `dx-*` for Developer Experience / SDK skills
- `launch-*` for Launch skills
- product-name prefix otherwise (e.g. `brand-kit-assistant`, `developer-hub-app-architect`)

A few older slugs (`cms-live-preview-visual-editor-support-assistant`, `migration-companion`) predate this convention.

Use lowercase letters, digits, and single hyphens, max 64 characters.

## What the validator checks

`node scripts/validate.mjs` fails if:

- `name` is missing, doesn't match the folder, or breaks the naming rules.
- `description` is missing, lacks "Use when…", or is over 1024 characters.
- `SKILL.md` has a `##` section outside the [template](skill-template.md), misses one of the required sections (When to use, Instructions, MCP tools, Security), or has them out of order.
- `SKILL.md` has no `## Security` section, or it lacks `### Defaults`, `### Destructive Actions`, `### Secrets` or `### Environment Variables`.
- A relative link in any markdown file under `skills/` doesn't resolve or points outside the skill's folder (code blocks are ignored).
- A frontmatter value in `skills/` or `docs/` contains `: ` without quotes.
- A manifest doesn't parse, a versioned manifest (`.claude-plugin/plugin.json`, the plugin entry in `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json`, `plugin.json`, `gemini-extension.json`) has no `version`, or the versions don't match.

## CI will keep you honest

The GitHub Action in `.github/workflows/validate.yml` runs the validator on pull requests to any branch, on pushes to `main` and `next`, and manually (workflow dispatch). If it fails, run `node scripts/validate.mjs` locally, fix what it reports, and push again.

`.github/workflows/routing-evals.yml` runs the [routing evals](routing-evals.md) on pull requests that change `skills/` or `evals/`.

## Related

- [Skill template](skill-template.md)
- [Routing evals](routing-evals.md)
- [Authoring conventions](authoring-conventions.md)
- [Anatomy of a SKILL.md](../how-it-works/skill-anatomy.md)
- [Release & versioning](release-and-versioning.md)
