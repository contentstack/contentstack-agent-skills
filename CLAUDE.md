# Contentstack Skills

This repository bundles a collection of [Contentstack](https://www.contentstack.com) agent skills for use with Claude Code, Cursor, Codex, Gemini, and the `skills` CLI.

## Routing

The router lives at [skills/CLAUDE.md](skills/CLAUDE.md). Follow it to pick the right skill for a given user request.

Each skill's canonical definition is at `skills/<slug>/SKILL.md`. The `cursor/rules/` and `codex/` trees are generated artifacts — do not edit them by hand.

## Contentstack references

When a skill needs up-to-date product or API details beyond what's in `skills/<slug>/SKILL.md`, consult:

- [developers.contentstack.com](https://developers.contentstack.com) — SDKs, CLIs, API references
- [contentstack.com/docs](https://www.contentstack.com/docs) — product documentation
- [contentstack.com/academy](https://www.contentstack.com/academy) — training and learning paths
- [contentstack.com/explorer](https://www.contentstack.com/explorer) — free sandbox accounts for testing
