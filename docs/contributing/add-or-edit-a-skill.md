---
title: Add or edit a skill
description: How to add a new Contentstack skill or change an existing one, then validate it before opening a pull request.
---

# Add or edit a skill

`skills/<slug>/SKILL.md` is the source of truth, and the only copy. Every tool installs it as-is, so there's nothing to regenerate. See [Architecture](../how-it-works/architecture.md).

## Edit an existing skill

1. Open `skills/<slug>/SKILL.md` and make your change.
2. If you added bundled assets, put them in `skills/<slug>/references/` or `skills/<slug>/scripts/` and link them with a relative path.
3. If the change affects when the skill should trigger, update the `description`.
4. Validate:

```bash
node scripts/validate.mjs
```

## Add a new skill

1. Create a directory: `skills/<new-slug>/`.
2. Add `SKILL.md` following the structure in [Anatomy of a SKILL.md](../how-it-works/skill-anatomy.md) and the rules in [Authoring conventions](authoring-conventions.md). The `name` must equal `<new-slug>`, and the `description` must include "Use when…" (1024 characters max).
3. Add any `references/` or `scripts/` the skill needs.
4. Add a row for the skill to the **Skills included** table in the root `README.md`.
5. Add a documentation page under `docs/skills/<new-slug>.md` and link it from `docs/skills/index.md`.
6. Run `node scripts/validate.mjs` and commit.

The plugin manifests point at the whole `skills/` folder, so a new skill needs no manifest change.

## Choosing a slug

Slugs are stable identifiers used by the `skills` CLI, slash-command invocation, and the docs. Follow the existing convention:

- `cms-*` for CMS skills
- `dx-*` for Developer Experience / SDK skills
- `launch-*` for Launch skills
- product-name prefix otherwise (e.g. `brand-kit-assistant`, `developer-hub-app-architect`)

Use lowercase letters, digits, and single hyphens, max 64 characters.

## What the validator checks

`node scripts/validate.mjs` fails if:

- `name` is missing, doesn't match the folder, or breaks the naming rules.
- `description` is missing, lacks "Use when…", or is over 1024 characters.
- A relative link in any markdown file under `skills/` doesn't resolve.
- A frontmatter value in `skills/` or `docs/` contains `: ` or ` #` without quotes.
- A manifest doesn't parse, or the `version` fields they declare don't match.

## CI will keep you honest

The GitHub Action in `.github/workflows/validate.yml` runs the validator on every pull request to `main` and on push to `main`. If it fails, run `node scripts/validate.mjs` locally, fix what it reports, and push again.

## Related

- [Authoring conventions](authoring-conventions.md)
- [Anatomy of a SKILL.md](../how-it-works/skill-anatomy.md)
- [Release & versioning](release-and-versioning.md)
