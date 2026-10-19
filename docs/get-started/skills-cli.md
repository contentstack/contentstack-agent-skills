---
title: Use a single skill via the skills CLI
description: Pull one Contentstack skill on demand with the skills CLI instead of installing the whole bundle.
---

# Use a single skill via the skills CLI

When you only need one capability, or your agent has no plugin system, the [`skills` CLI](https://github.com/vercel-labs/skills) installs individual skills on demand. It writes them into the right folder for Claude Code, Cursor, Codex, Copilot, Gemini, Windsurf, Cline, and other agents.

## Install one skill

```
npx skills add contentstack/contentstack-agent-skills --skill <skill-slug>
```

For example, to add just the Delivery SDK skill:

```
npx skills add contentstack/contentstack-agent-skills --skill dx-delivery-sdk
```

To see every skill in the bundle:

```
npx skills add contentstack/contentstack-agent-skills --list
```

Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills)

## Finding the slug

The slug is the skill's directory name (and its `name` field). Find it with `--list` or in the [skills reference](../skills/index.md). Common ones:

| Slug | Skill |
| --- | --- |
| `dx-delivery-sdk` | Delivery SDK |
| `cms-entries` | Entries |
| `cms-data-modeling-best-practices` | Data Modeling Best Practices |
| `cms-live-preview-visual-editor-support-assistant` | Live Preview & Visual Editor Support |
| `migration-companion` | Migration Companion |
| `studio` | Contentstack Studio |

## When to use this vs the full bundle

- **Single skill** → you want one focused capability, or your agent isn't covered by a plugin install.
- **Full bundle** (Claude Code, claude.ai, Cursor, Codex, Copilot, Gemini) → you want every skill available and kept up to date through your tool's plugin system. See [Supported tools](../overview/supported-tools.md).

## Note on selection

Skills installed this way work exactly like the bundled ones: the agent loads a skill when your request matches its description. With fewer skills installed, there's simply less to choose from. See [How skill selection works](../how-it-works/router.md).

## Update

Re-run `npx skills add contentstack/contentstack-agent-skills --skill <skill-slug>` to fetch the latest version of that skill.
