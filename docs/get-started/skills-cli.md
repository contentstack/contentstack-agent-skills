---
title: Use a single skill via the skills CLI
description: Pull one Contentstack skill on demand with the skills CLI instead of installing the whole bundle.
---

# Use a single skill via the skills CLI

When you only need one capability, the [`skills` CLI](https://github.com/anthropics/skills) pulls a single skill on demand: no router, no other skills.

## Install one skill

```
npx skills add contentstack/contentstack-agent-skills@<skill-slug>
```

For example, to add just the Delivery SDK skill:

```
npx skills add contentstack/contentstack-agent-skills@dx-delivery-sdk
```

Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills)

## Finding the slug

The slug is the skill's directory name. Find it in the [skills reference](../skills/index.md) or in `manifest.json`. Common ones:

| Slug | Skill |
| --- | --- |
| `dx-delivery-sdk` | Delivery SDK |
| `cms-entries` | Entries |
| `cms-data-modeling-best-practices` | Data Modeling Best Practices |
| `cms-live-preview-visual-builder-support-assistant` | Live Preview & Visual Builder Support |
| `migration-companion` | Migration Companion |

## When to use this vs the full bundle

- **Single skill** → you want one focused capability and don't need automatic routing across many topics.
- **Full bundle** (Claude Code, Cursor, Codex, Gemini) → you want the agent to choose the right skill automatically across all 22. See [Supported tools](../overview/supported-tools.md).

## Note on routing

The `skills` CLI installs exactly the skill you name. There is no router and no auto-selection. The agent uses the one skill you added. If you want intent-based routing across the whole catalog, install a full-bundle format instead.

## Update

Re-run `npx skills add contentstack/contentstack-agent-skills@<skill-slug>` to fetch the latest version of that skill.
