---
title: Add or edit a skill
description: How to add a new Contentstack skill or change an existing one, then regenerate the tool-specific trees.
---

# Add or edit a skill

`skills/` is the source of truth. You edit there, then regenerate the derived trees. Never edit `cursor/rules/` or `codex/` directly. They're build artifacts and CI will revert hand edits. See [Architecture](../how-it-works/architecture.md).

## Edit an existing skill

1. Open `skills/<slug>/SKILL.md` and make your change.
2. If you added bundled assets, put them in `skills/<slug>/references/` or `skills/<slug>/scripts/`.
3. Regenerate the derived trees:

```bash
bash scripts/build-cursor-rules.sh
bash scripts/build-codex-skills.sh
```

4. Commit both your `skills/` change **and** the regenerated `cursor/rules/` and `codex/` output.

## Add a new skill

1. Create a directory: `skills/<new-slug>/`.
2. Add `SKILL.md` following the structure in [Anatomy of a SKILL.md](../how-it-works/skill-anatomy.md) and the rules in [Authoring conventions](authoring-conventions.md).
3. Add any `references/` or `scripts/` the skill needs.
4. Add a routing row to `skills/CLAUDE.md` so the agent knows when to use it.
5. Add an entry to `manifest.json` with the `slug`, `title`, and `product`.
6. Regenerate the derived trees (commands above) and commit everything.
7. Add a documentation page under `docs/skills/<new-slug>.md` and link it from `docs/skills/index.md`.

## Choosing a slug

Slugs are stable identifiers used by the `skills` CLI and the manifest. Follow the existing convention:

- `cms-*` for CMS skills
- `dx-*` for Developer Experience / SDK skills
- `launch-*` for Launch skills
- product-name prefix otherwise (e.g. `brand-kit-assistant`, `developer-hub-app-architect`)

## What the build scripts do

| Script | Output |
| --- | --- |
| `scripts/build-cursor-rules.sh` | `cursor/rules/00-router.mdc` + `cursor/rules/NN-<slug>.mdc` |
| `scripts/build-codex-skills.sh` | `codex/AGENTS.md` + `codex/<slug>/SKILL.md` (frontmatter stripped) + copied assets |

Both derive entirely from `skills/`. Running them is idempotent.

## CI will keep you honest

The GitHub Action in `.github/workflows/build.yml`:

- **Fails pull requests** whose generated trees don't match a fresh build. So you can't forget to regenerate.
- **Auto-commits drift** on push to `main`.

If your PR fails on "Generated trees are out of date," run the two build scripts locally and commit the result.

## Related

- [Authoring conventions](authoring-conventions.md)
- [Anatomy of a SKILL.md](../how-it-works/skill-anatomy.md)
- [Architecture](../how-it-works/architecture.md)
