---
title: Release & versioning
description: How the Contentstack Agent Skills bundle is versioned and released across its five formats.
---

# Release & versioning

The bundle ships as a single versioned package across all five formats. Versioning and release stay simple because everything derives from one source.

## Version source

The package version lives in the plugin manifests:

- `.claude-plugin/plugin.json`
- `.cursor-plugin/plugin.json`
- `gemini-extension.json`

Keep these in sync when bumping a version. The `manifest.json` `skill_count` and `skills` list should match what's actually in `skills/`.

## What a release contains

A release is the current state of `skills/` plus its regenerated artifacts:

- `skills/`: source of truth (skills, router, references, scripts)
- `cursor/rules/`: generated Cursor rules
- `codex/`: generated Codex tree
- The plugin/extension manifests and `manifest.json`

Because the generated trees are committed and verified by CI, any tagged commit on `main` is a coherent, installable release for every tool.

## Release checklist

1. Make changes under `skills/` (see [Add or edit a skill](add-or-edit-a-skill.md)).
2. Regenerate derived trees:
   ```bash
   bash scripts/build-cursor-rules.sh
   bash scripts/build-codex-skills.sh
   ```
3. Update `manifest.json` if skills were added or removed.
4. Bump the version in the plugin/extension manifests.
5. Confirm CI passes (the drift check must be green).
6. Tag the release.

## How updates reach users

| Tool | How users update |
| --- | --- |
| Claude Code | Re-run `/plugin install` / update the marketplace |
| Cursor | Update via the marketplace, or re-copy `cursor/rules/*.mdc` |
| Codex | Re-copy the `codex/` tree or re-sync the repo |
| Gemini CLI | Re-run `gemini extensions install contentstack/contentstack-agent-skills` |
| `skills` CLI | Re-run `npx skills add contentstack/contentstack-agent-skills@<slug>` |

Because all formats are generated from one source, every tool receives the same change set in a release.

## Compatibility

- Adding a skill is backward compatible: existing skills and routes are unaffected.
- Changing a slug is a breaking change for `skills` CLI users who reference it; avoid renaming slugs once published.
- Changing routing triggers can change which skill activates for a given request; review the router (`skills/CLAUDE.md`) when editing triggers.

## Related

- [Architecture](../how-it-works/architecture.md)
- [Add or edit a skill](add-or-edit-a-skill.md)
