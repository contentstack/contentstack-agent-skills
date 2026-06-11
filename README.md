# Contentstack Skills

A bundle of 21 ready-to-use [Contentstack](https://www.contentstack.com) agent skills for AI coding tools, covering CMS implementation, Brand Kit guidance, delivery SDK development, migration workflows, Developer Hub app architecture, and Launch automation.

## What's in here?

Each skill is a self-contained instruction set that teaches an AI coding agent how to accomplish a specific Contentstack task: modeling content, querying entries, handling assets, configuring governance, integrating preview tooling, applying Brand Kit guidance, writing Delivery SDK code, building Developer Hub apps, automating Launch deployments, and more. Drop this repo into your AI tool of choice and the agent will know when and how to apply each skill based on what you ask.

The same skills are packaged in five formats so you can use whichever tool fits your workflow:

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

| Slug | Title | Product | What it helps with |
| --- | --- | --- | --- |
| `brand-kit-assistant` | Brand Kit Assistant | Brand Kit | Brand Kit concepts, setup, governance, Voice Profiles, Knowledge Vault, on-brand AI generation, and API-task routing. |
| `cms-assets` | Contentstack Assets | CMS | Asset organization, image transformations, publishing lifecycle, CDN behavior, and asset limits. |
| `cms-branches-aliases` | Branches & Aliases | CMS | Isolated content development, alias-based deployments, CI/CD integration, merge behavior, and rollback patterns. |
| `cms-data-modeling-best-practices` | Contentstack Data Modeling Best Practices | CMS | Content type design, references, global fields, groups, modular blocks, JSON RTE, taxonomy, tags, and model simplification. |
| `cms-entries` | Entries | CMS | Entry querying, localization, versioning, publishing, CDA usage, reference expansion, pagination, bulk operations, and Sync API patterns. |
| `cms-environments-publishing` | Contentstack Environments & Publishing | CMS | Environment setup, publishing behavior, delivery and preview tokens, Sync API usage, CDN behavior, and publish queues. |
| `cms-live-preview-visual-builder-support-assistant` | Live Preview and Visual Builder Support Assistant | Developer Experience | Live Preview and Visual Builder setup or debugging across CSR, SSR, SSG, middleware/BFF, and edit-tag flows. |
| `cms-localization` | Contentstack Localization | CMS | Language setup, fallback chains, localized and unlocalized entries, non-localizable fields, and multi-locale publishing. |
| `cms-releases` | Releases | CMS | Coordinated content deployment, release scheduling, staged deployment, webhook storm prevention, and CI/CD integration. |
| `cms-roles-permissions` | Roles & Permissions | CMS | Built-in roles, custom roles, teams, permission merging, token capabilities, and least-privilege access design. |
| `cms-taxonomy` | Contentstack Taxonomy | CMS | Hierarchical content classification, taxonomy vs tags or references, CDA taxonomy queries, localization, and import/export. |
| `cms-tokens-authentication` | Tokens & Authentication | CMS | Authentication methods, token types, API keys, credential security, rate limits, and SSO considerations. |
| `cms-variants-personalization` | Variants & Personalization | CMS | Audience-targeted content, variants vs separate entries, variant groups, A/B testing, and Personalize integration. |
| `cms-webhooks` | Contentstack Webhooks | CMS | Webhook configuration, event channels, payload handling, signature verification, retries, and reliable receiver design. |
| `cms-workflows` | Workflows & Publish Rules | CMS | Workflow stages, approval flows, transition restrictions, publish governance, automation hooks, and common pitfalls. |
| `developer-hub-app-architect` | Developer Hub App Architect | Developer Hub | Developer Hub and Marketplace app planning, UI location choices, React/TypeScript scaffolding, setup, SDK, manifest, proxy, and publishing issues. |
| `dx-delivery-sdk` | Delivery SDK | Developer Experience | Production-ready TypeScript with `@contentstack/delivery-sdk` for entries, assets, references, filters, sorting, pagination, locales, Live Preview, and Visual Builder. |
| `dx-migrate-js-to-ts-sdk` | Migrate JS to TS SDK | Developer Experience | Migration from the JavaScript Contentstack SDK to the TypeScript Delivery SDK, including API mapping, rewrites, and unsupported pattern callouts. |
| `launch-sync-environment-variables-from-env-example` | Sync Launch environment variables from .env.example | Launch | Comparing a local `.env.example` with Launch environment variables and patching missing keys without printing secrets. |
| `launch-trigger-and-monitor-launch-deployments` | Trigger and Monitor Launch Deployments | Launch | Triggering Launch deployments, polling deployment status, retrieving failure logs, and summarizing likely causes and next steps. |
| `migration-companion` | Contentstack Migration Companion | Developer Experience | Guided Contentful-to-Contentstack migration workflow covering prerequisites, content migration, code migration, bundled validation scripts, and completion reporting. |

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
- **[developers.contentstack.com](https://developers.contentstack.com)** — developer hub: SDKs, CLIs, API references, and guides
- **[contentstack.com/explorer](https://www.contentstack.com/explorer)** — start free, no credit card — try Contentstack in your browser
- **[contentstack.com/docs](https://www.contentstack.com/docs)** — full product documentation
- **[contentstack.com/academy](https://www.contentstack.com/academy)** — training, certifications, and learning paths

## License

See individual skill files for attribution. Contentstack branding and documentation belong to Contentstack.
