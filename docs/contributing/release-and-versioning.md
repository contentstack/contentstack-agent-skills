---
title: Release & versioning
description: How the Contentstack Agent Skills bundle is versioned and released to every supported tool.
---

# Release & versioning

The bundle ships as a single versioned package to every tool. Releases stay simple because every tool installs the same `skills/` folder.

## Version source

The version lives in the plugin manifests, and they must all match:

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` (the plugin entry's `version`)
- `.cursor-plugin/plugin.json`
- `plugin.json`
- `gemini-extension.json`

`node scripts/validate.mjs` reads every manifest, including `.cursor-plugin/marketplace.json` and `.agents/plugins/marketplace.json`, and fails if any declared versions disagree.

## Why the version matters

Plugin-based tools decide whether to update by comparing version numbers. Claude Code in particular only updates an installed plugin when the version changes, so changes merged to `main` without a version bump don't reach existing users.

## What a release contains

A release is the current state of the repository on `main`:

- `skills/`: the skills, with their references and scripts
- The plugin, marketplace, and extension manifests

There are no generated artifacts, so any validated commit on `main` is a coherent, installable release for every tool.

## Release checklist

1. Make changes under `skills/` (see [Add or edit a skill](add-or-edit-a-skill.md)).
2. Bump `version` to the same new value in every file listed above.
3. Add a section for the new version to [`CHANGELOG.md`](../../CHANGELOG.md), calling out renamed or removed skills.
4. Run `node scripts/validate.mjs`.
5. Confirm CI passes on the pull request.
6. Merge to `main`, tag `vX.Y.Z` on the merge commit, and publish a GitHub release whose notes are the version's `CHANGELOG.md` section.

## How updates reach users

| Tool | How users update |
| --- | --- |
| Claude Code | `/plugin marketplace update contentstack-skills`, or marketplace auto-update |
| claude.ai / Cowork | Automatic: the marketplace stays linked to the repository |
| Cursor | Update the plugin from **Settings → Plugins** |
| Codex | `codex plugin marketplace upgrade contentstack-skills`, then `codex plugin add contentstack-skills@contentstack-skills` |
| GitHub Copilot | Re-run `copilot plugin install contentstack-skills@contentstack-skills`, or update in VS Code |
| Gemini CLI | `gemini extensions update contentstack-skills` |
| `skills` CLI | Re-run `npx skills add contentstack/contentstack-agent-skills --skill <slug>` |

Because every tool installs the same files, every tool receives the same change set in a release.

## Compatibility

- Adding a skill is backward compatible: existing skills are unaffected.
- Changing a slug is a breaking change for `skills` CLI users and anyone invoking the skill by name; avoid renaming slugs once published.
- Changing a `description` can change which skill activates for a given request. Review the descriptions of neighboring skills when editing triggers so they don't overlap.

## Related

- [Architecture](../how-it-works/architecture.md)
- [Add or edit a skill](add-or-edit-a-skill.md)
