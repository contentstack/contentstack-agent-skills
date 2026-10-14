# Contentstack Skills

This repository bundles [Contentstack](https://www.contentstack.com) agent skills. Every skill lives once in `skills/<slug>/SKILL.md` (the [Agent Skills](https://agentskills.io) format) and is distributed to Claude Code, claude.ai, Cursor, Codex, GitHub Copilot, Gemini CLI and the `skills` CLI through the manifests at the repo root. There are no generated copies.

## Editing skills

- `name` must equal the folder name (lowercase, hyphens, max 64 chars).
- `description` says what the skill does and includes "Use when …" triggers, max 1024 chars. This is the only text agents see before loading a skill, so put routing cues here.
- Keep `SKILL.md` focused; move long material into `references/` and link it with a relative path.
- When adding a skill, add its row to the table in `README.md`, and add a `docs/skills/<slug>.md` page linked from `docs/skills/index.md`.
- Run `node scripts/validate.mjs` before committing. CI runs it on every PR.

## Releasing

Bump `version` to the same value in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json`, `plugin.json` and `gemini-extension.json`. Installed Claude Code plugins only update when the version changes. Add a section to `CHANGELOG.md` for the release.

## Contentstack references

When a skill needs up-to-date product or API details, consult:

- [developers.contentstack.com](https://developers.contentstack.com) — SDKs, CLIs, API references
- [contentstack.com/docs](https://www.contentstack.com/docs) — product documentation
- [contentstack.com/academy](https://www.contentstack.com/academy) — training and learning paths
- [contentstack.com/explorer](https://www.contentstack.com/explorer) — free sandbox accounts for testing
