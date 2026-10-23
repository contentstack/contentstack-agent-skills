# Contentstack Skills

A bundle of ready-to-use [Contentstack](https://www.contentstack.com) agent skills for AI coding tools, covering CMS implementation, Brand Kit guidance, delivery SDK development, kickstart maintenance, migration workflows, Developer Hub app architecture, Launch automation, and Contentstack Studio.

## What's in here?

Each skill is a self-contained instruction set that teaches an AI coding agent how to accomplish a specific Contentstack task: modeling content, querying entries, handling assets, configuring governance, integrating preview tooling, applying Brand Kit guidance, writing Delivery SDK code, building Developer Hub apps, automating Launch deployments, and more. Drop this repo into your AI tool of choice and the agent will know when and how to apply each skill based on what you ask.

Every skill lives once, in `skills/<slug>/SKILL.md`, following the open [Agent Skills](https://agentskills.io) format. Claude Code, claude.ai, Cursor, Codex, GitHub Copilot, Gemini CLI and the [`skills` CLI](https://github.com/vercel-labs/skills) all read that format natively, so there are no per-tool copies. Each tool installs the bundle through its own plugin manifest.

## Install

Install with whichever tool you use. Each method gives you all the skills, and the agent loads the right one based on what you ask.

### Claude Code

```
/plugin marketplace add contentstack/contentstack-agent-skills
/plugin install contentstack-skills@contentstack-skills
```

### claude.ai and Claude Cowork

Go to **Customize → Plugins → Add marketplace** and enter `contentstack/contentstack-agent-skills`. The skills sync to claude.ai, Cowork and Claude Code, and update when a new version is released.

### Cursor

Open **Settings → Plugins**, choose **Add from GitHub repository**, and enter `https://github.com/contentstack/contentstack-agent-skills`.

### Codex

```
codex plugin marketplace add contentstack/contentstack-agent-skills
codex plugin add contentstack-skills@contentstack-skills
```

### GitHub Copilot

Copilot CLI:

```
copilot plugin marketplace add contentstack/contentstack-agent-skills
copilot plugin install contentstack-skills@contentstack-skills
```

VS Code: add `"contentstack/contentstack-agent-skills"` to the `chat.plugins.marketplaces` setting, then install **contentstack-skills** from the Extensions view.

### Gemini CLI

```
gemini extensions install https://github.com/contentstack/contentstack-agent-skills
```

### skills CLI (any agent)

```
npx skills add contentstack/contentstack-agent-skills --skill cms-entries
npx skills add contentstack/contentstack-agent-skills --skill cms-entries --skill cms-assets
```

Use `--list` to see every skill, or leave out `--skill` to install them all. The CLI installs into the right folder for Claude Code, Cursor, Codex, Copilot, Gemini, Windsurf, Cline and others.

## Skills included

| Slug | Title | Product | What it helps with |
| --- | --- | --- | --- |
| `asset-management` | Asset Management | Assets | Assets DAM spaces and workspaces, folders, asset types and metadata, localization, saved views, AI tagging and alt text, duplicate management, versions, trash and restore, visual markups, and CMS integration. |
| `brand-kit-assistant` | Brand Kit Assistant | Brand Kit | Brand Kit concepts, setup, governance, Voice Profiles, Knowledge Vault, on-brand AI generation, and API-task routing. |
| `cms-assets` | Contentstack Assets | CMS | Asset organization, image transformations, publishing lifecycle, CDN behavior, and asset limits. |
| `cms-branches-aliases` | Branches & Aliases | CMS | Isolated content development, alias-based deployments, CI/CD integration, merge behavior, and rollback patterns. |
| `cms-data-modeling-best-practices` | Contentstack Data Modeling Best Practices | CMS | Content type design, references, global fields, groups, modular blocks, JSON RTE, taxonomy, tags, and model simplification. |
| `cms-entries` | Entries | CMS | Entry querying, localization, versioning, publishing, CDA usage, reference expansion, pagination, bulk operations, and Sync API patterns. |
| `cms-environments-publishing` | Contentstack Environments & Publishing | CMS | Environment setup, publishing behavior, delivery and preview tokens, Sync API usage, CDN behavior, and publish queues. |
| `cms-live-preview-visual-editor-support-assistant` | Live Preview and Visual Editor Support Assistant | Developer Experience | Live Preview, Visual Editor (Visual Builder) and Timeline setup or debugging: Onboarding Check, rendering-mode contracts (CSR, SSR, SSG, GraphQL), edit tags, FAQ-backed fixes, and Support handover. |
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
| `dx-kickstart-next` | Contentstack Kickstart Next | Developer Experience | Maintaining Contentstack's Next.js kickstart: App Router structure, Delivery SDK setup, Live Preview, seeded stack alignment, env vars, validation, and PR reviews. |
| `dx-migrate-js-to-ts-sdk` | Migrate JS to TS SDK | Developer Experience | Migration from the JavaScript Contentstack SDK to the TypeScript Delivery SDK, including API mapping, rewrites, and unsupported pattern callouts. |
| `launch-sync-environment-variables-from-env-example` | Sync Launch environment variables from .env.example | Launch | Comparing a local `.env.example` with Launch environment variables and patching missing keys without printing secrets. |
| `launch-trigger-and-monitor-launch-deployments` | Trigger and Monitor Launch Deployments | Launch | Triggering Launch deployments, polling deployment status, retrieving failure logs, and summarizing likely causes and next steps. |
| `migration-companion` | Contentstack Migration Companion | Developer Experience | Guided Contentful-to-Contentstack migration workflow covering prerequisites, content migration, code migration, bundled validation scripts, and completion reporting. |
| `studio` | Studio (preview) | Studio | Contentstack Studio end to end: SDK install, project provisioning, component registration, sections and templates, data binding, canvas and preview routes, verification, and troubleshooting. A router skill that loads one of 109 bundled specialist files per task. |

## How it works

Each skill is a folder with a `SKILL.md` (YAML frontmatter plus instructions) and optional `references/` and `scripts/`. Agents see only each skill's `name` and `description` up front, and load the rest when a request matches the "Use when…" part of the description.

## Repository layout

```
skills/<slug>/SKILL.md            Source of truth: one folder per skill
.claude-plugin/                   Claude Code / claude.ai / Copilot CLI plugin and marketplace
.cursor-plugin/                   Cursor plugin and marketplace
.agents/plugins/marketplace.json  Codex marketplace
plugin.json                       Agent Plugins manifest (Codex, VS Code)
gemini-extension.json             Gemini CLI extension
docs/                             Documentation: install, architecture, contributing, skill reference
scripts/validate.mjs              Validates skills and manifests (runs in CI)
```

## Contributing

1. Add or edit `skills/<slug>/SKILL.md`. The `name` must match the folder, and the `description` must say what the skill does and include "Use when…" (1024 characters max).
2. Add a row to the table above, and add a `docs/skills/<slug>.md` page linked from `docs/skills/index.md`.
3. Run `node scripts/validate.mjs`.
4. For a release, bump `version` in every manifest. The validator fails if they disagree. Claude Code only updates installed plugins when the version changes. Add a `CHANGELOG.md` entry.

## Learn more about Contentstack

- **[contentstack.com](https://www.contentstack.com)** — product, pricing, and platform overview
- **[developers.contentstack.com](https://developers.contentstack.com)** — developer hub: SDKs, CLIs, API references, and guides
- **[contentstack.com/explorer](https://www.contentstack.com/explorer)** — start free, no credit card — try Contentstack in your browser
- **[contentstack.com/docs](https://www.contentstack.com/docs)** — full product documentation
- **[contentstack.com/academy](https://www.contentstack.com/academy)** — training, certifications, and learning paths

## License

[MIT](LICENSE). Contentstack branding and documentation belong to Contentstack.
