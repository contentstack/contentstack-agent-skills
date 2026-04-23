# Contentstack Skills

A bundle of 17 ready-to-use [Contentstack](https://www.contentstack.com) agent skills for AI coding tools. Exported 2026-04-23.

## What's in here?

Each skill is a self-contained instruction set that teaches an AI coding agent how to accomplish a specific Contentstack task — querying content, migrating schemas, building scaffolds, integrating SDKs, and more. Drop this repo into your AI tool of choice and the agent will know when and how to apply each skill based on what you ask.

The same skills are packaged in four formats so you can use whichever tool fits your workflow:

- **Claude Code** — installable plugin (`.claude-plugin/`)
- **Cursor** — rule files (`cursor/rules/`)
- **Codex / OpenAI agents** — markdown tree (`codex/`)
- **Gemini CLI** — extension manifest (`gemini-extension.json`)
- **[skills](https://github.com/anthropics/skills) CLI** — pulls any single skill on demand

You only need to install one. Pick the section below that matches your tool.

## Install

### Claude Code

```
/plugin marketplace add <this-repo>
/plugin install contentstack-skills
```

After install, the router at `skills/CLAUDE.md` is loaded into context and Claude will pick the matching skill automatically when you ask a relevant question.

### Cursor

Install via Cursor's plugin marketplace, **or** copy `cursor/rules/*.mdc` into your project's `.cursor/rules/` directory. The `00-router.mdc` rule is marked `alwaysApply: true`, so Cursor always knows which skill to reach for.

### Codex / OpenAI agents

Point your agent at this repo or copy the `codex/` directory into your project. The entry point is [`codex/AGENTS.md`](codex/AGENTS.md).

### Gemini CLI

```
gemini extensions install <this-repo>
```

### skills CLI (single skill on demand)

```
npx skills add <this-repo>@<skill-slug>
```

## Skills included

| Slug                                                         | Title                                               | Product              |
| ------------------------------------------------------------ | --------------------------------------------------- | -------------------- |
| `trigger-and-monitor-launch-deployments`                     | Trigger and Monitor Launch Deployments              | Launch               |
| `sync-launch-environment-variables-from-env-example`         | Sync Launch environment variables from .env.example | Launch               |
| `developer-hub-app-architect`                                | Developer Hub App Architect                         | Developer Hub        |
| `contentstack-variants-personalization`                      | Variants & Personalization                          | CMS                  |
| `contentstack-tokens-authentication`                         | Tokens & Authentication                             | CMS                  |
| `contentstack-releases`                                      | Releases                                            | CMS                  |
| `contentstack-roles-permissions`                             | Roles & Permissions                                 | CMS                  |
| `contentstack-webhooks`                                      | Contentstack Webhooks                               | CMS                  |
| `contentstack-branches-aliases`                              | Branches & Aliases                                  | CMS                  |
| `contentstack-localization`                                  | Contentstack Localization                           | CMS                  |
| `contentstack-environments-publishing`                       | Contentstack Environments & Publishing              | CMS                  |
| `contentstack-workflows`                                     | Workflows & Publish Rules                           | CMS                  |
| `contentstack-taxonomy`                                      | Contentstack Taxonomy                               | CMS                  |
| `contentstack-assets`                                        | Contentstack Assets                                 | CMS                  |
| `contentstack-entries`                                       | Entries                                             | CMS                  |
| `contentstack-live-preview-visual-builder-support-assistant` | Live Preview and Visual Builder Support Assistant   | Developer Experience |
| `contentstack-data-modeling-best-practices`                  | Contentstack Data Modeling Best Practices           | CMS                  |

## How it works

`skills/` is the source of truth. Every other tool-specific tree (`cursor/rules/`, `codex/`) is generated from it by the scripts in `scripts/`. A GitHub Action regenerates the derived trees on every push to `main` and fails PRs that forget to regenerate, so the copies never drift.

```
skills/<slug>/SKILL.md     ──► cursor/rules/NN-<slug>.mdc
                           ──► codex/<slug>/SKILL.md
skills/CLAUDE.md (router)  ──► cursor/rules/00-router.mdc
                           ──► codex/AGENTS.md
```

## Repository layout

```
.claude-plugin/        Claude Code plugin + marketplace manifests
.cursor-plugin/        Cursor plugin manifest
.github/workflows/     CI that regenerates cursor/rules and codex on push
codex/                 Generated Codex tree — do not edit
cursor/rules/          Generated Cursor rules — do not edit
scripts/               Contributor build scripts
skills/                Source of truth — edit here
gemini-extension.json  Gemini CLI extension manifest
```

## Editing skills

Edit only under `skills/`. Then regenerate the derived trees:

```
bash scripts/build-cursor-rules.sh
bash scripts/build-codex-skills.sh
```

The GitHub Action in `.github/workflows/build.yml` runs these on every push to `main` and commits any drift.

## Learn more about Contentstack

- **[contentstack.com](https://www.contentstack.com)** — product, pricing, and platform overview
- **[developers.contentstack.com](https://developers.contentstack.com)** — developer homepage: SDKs, CLIs, API references, and guides
- **[contentstack.com/explorer](https://www.contentstack.com/explorer)** — start free
- **[contentstack.com/docs](https://www.contentstack.com/docs)** — full product documentation
- **[contentstack.com/academy](https://www.contentstack.com/academy)** — training, certifications, and learning paths

## License

See individual skill files for attribution. Contentstack branding and documentation belong to Contentstack.
