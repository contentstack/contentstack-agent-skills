# Changelog

All notable changes to the Contentstack agent skills bundle. Versions match the `version` field in every plugin manifest that declares one.

## 0.4.1

This release adds nine skills, connects every plugin to the hosted Contentstack MCP server, and corrects claims in the existing skills that didn't match the product. The `studio` skill now matches Studio SDK 2.0.

### Highlights

- **The Contentstack MCP server comes with the plugin.** Installing the skills also connects the hosted MCP Profile Hub, so an agent can work on your stacks instead of only advising. You sign in through the browser the first time a Contentstack tool runs. No API key is needed.
- **Nine new skills:** Personalize, Lytics, Launch hosting, Automate, the `csdx` CLI, the MCP server, GraphQL, JSON RTE and Marketplace apps.
- **Accuracy pass.** Every skill was checked against the product wiki, with the public docs and OpenAPI specs as tiebreaker. Webhook signature verification, taxonomy query operators and Launch environment updates were wrong before and are fixed now.
- **Studio SDK 2.0.** The `studio` skill was followed end to end on a Next.js 16 app with `@contentstack/studio-react` 2.0.1, and every changed snippet is typechecked against that release. New guides cover CSR vs SSR and 404 pages.
- **One template for every skill**, listing the MCP tools that carry out each step.

### Upgrading

- Update the plugin the usual way for your tool (see [Release & versioning](https://github.com/contentstack/contentstack-agent-skills/blob/main/docs/contributing/release-and-versioning.md#how-updates-reach-users)). The MCP server arrives with the update.
- No skills were renamed or removed.

### New skills

- `personalize`: experiences, audiences, attributes and events, the Personalize Edge SDK and Edge API, the Management API, and edge middleware that resolves variants before rendering.
- `lytics`: the Lytics JavaScript tag, identity resolution, schema, audiences and the Segment API, consent and deletion, and sending audiences to Personalize.
- `launch-platform`: hosting on Launch, covering builds, Cloud and Edge Functions, `launch.json`, caching and revalidation, deploy hooks, domains, access control, log targets, monorepos and limits.
- `automations`: Contentstack Automate rules, triggers, connectors, control flow, custom code, executions and debugging.
- `dx-cli`: the `csdx` CLI for auth, export, import, seed, clone, bulk operations, migration scripts, branch merges and plugins.
- `dx-mcp-server`: connecting AI agents through the local `@contentstack/mcp` server or the hosted MCP Profile Hub, and when to use each.
- `cms-graphql`: the GraphQL Content Delivery API, covering endpoints, schema, references, modular blocks, JSON RTE, limits and Live Preview.
- `cms-json-rte`: rendering and serializing JSON Rich Text Editor content with `@contentstack/utils`, render options, embedded entries and assets, GraphQL, React, HTML↔JSON conversion and Live Preview tags.
- `marketplace-apps`: choosing, installing and configuring first-party Marketplace apps, app configuration vs field configuration, and reading app data on delivery.

### Contentstack MCP server

- **Bundled with every plugin.** Each plugin connects the hosted MCP Profile Hub (`https://mcp-profile-hub.contentstack.com/api/mcp`) with OAuth sign-in:
  - Claude Code and claude.ai: `.mcp.json` (`type: http`).
  - Codex, ChatGPT and other Agent Plugins clients: `mcp.json` (`type: streamable-http`).
  - Cursor: `mcpServers` in `.cursor-plugin/plugin.json`, which Cursor reads in place of `mcp.json`.
  - Gemini CLI: `mcpServers` in `gemini-extension.json` (`httpUrl`).
- **MCP tools in every skill.** Each skill names the Contentstack MCP tools that carry out its steps, taken from the server's published definitions, or says that none exist and what to use instead.
- **Advisory by default.** Skills use write, publish, deploy or delete tools only when you ask, after naming the target and getting your confirmation.
- **Launch action skills** use the `launch` MCP tools (`update_an_environment`, `create_deployment`, `get_deployment_logs`) when they're connected.

### Accuracy fixes

- **`cms-webhooks`:** signature verification now uses `X-Contentstack-Request-Signature` (RSA-PSS SHA-256) or the opt-in `X-Contentstack-HMAC-Signature` over `{timestamp}.{body}`. Payload fields, workflow events, retry timing and branch scoping are corrected, and unverified limits are removed.
- **`cms-taxonomy`:** the CDA operators are now the documented `$in`, `$exists`, `$eq_below`, `$below`, `$eq_above` and `$above` (with `levels`), replacing operators that don't exist. Depth and plan limits are added.
- **`launch-sync-environment-variables-from-env-example`:** updates go through `PUT` with the full environment object (there is no PATCH), with regional hosts and auth.
- **`launch-trigger-and-monitor-launch-deployments`:** logs come from the deployment-logs endpoint, the status list is complete with `LIVE` as success, and rollback is added.
- **`brand-kit-assistant`:** Voice Profile dials are 1–4, request headers are corrected, and v2 kits (Documents) and the other Brand Kit surfaces are added.
- **`cms-branches-aliases`:** the branch limit is plan-dependent, module scoping follows the public docs, and compare and merge strategies are added.
- **`cms-entries` and `cms-variants-personalization`:** both now have real instructions. Before, they were empty.
- **Other CMS skills:**
  - `cms-localization`: Unlocalize is documented.
  - `cms-releases`: 25 items per request, plus Releases v2.
  - `cms-roles-permissions`: permissions are a union of roles with no deny, and M2M apps are covered.
  - `cms-workflows`: self-advancement prevention is a per-stage option.
  - `cms-assets`: Assets DAM limits and routing are added.
  - `cms-environments-publishing`: all CDA hosts and the rate-limit split are listed.
  - `cms-tokens-authentication`: M2M apps and preview tokens are covered.
  - `cms-data-modeling-best-practices`: adds the limits to design around.
- **`developer-hub-app-architect`:** adds the Content Type Sidebar and Global Full Page locations, covers M2M apps, lifecycle webhooks and per-installation secrets, and links to its one coding reference instead of reference files that didn't exist.
- **`dx-delivery-sdk` and `dx-migrate-js-to-ts-sdk`:** the Security sections copied from Launch are replaced, and the package name is now `@contentstack/persistence-plugin`.
- **`asset-management`:** user-defined field types match the current docs.
- **Formatting:** instructions that were raw JSON are now prose, and the broken Product Context bullets are fixed.

### Studio

- **New guide, `csr-and-ssr-requirements`:** what a Studio page needs as CSR or SSR on the visitor site, the Live Preview pane, Visual Editor and the canvas. Covers the five settings that must agree, preview mode vs builder mode, where the Edit button shows, which refetch to call on studio-react 2.0.1, and converting a page from one mode to the other.
- **New guide, `handle-404-pages`:** unknown URLs and bad slugs render the site's own 404 page on Next.js (App and Pages Router), Remix and React Router. SSR sends a real 404, and the 404 is decided by `isCompositionNotFound` only, so a bad token or an outage stays an error.
- **Upgrading from 1.x:** `upgrade-studio-sdk` has a 1.x → 2.0 section, checked by installing 1.9.0 and 2.0.1 side by side. It separates what 2.0 actually changed from older rules that behave the same in both versions.
- **Builds that looked done but were wrong:**
  - Every plan includes a primitive library step, and one Section-per-region rule replaces the conflicting reuse advice.
  - `resolveComposition` resets the preview hash, so drafts no longer leak to visitors.
  - The live site fetches only bound fields, and image props bind `.url`.
  - Section Slot nodes omit the slot key, which the API rejects with a 422.
- **SDK 2.0.1 APIs:** `registerLazyComponent` for lazy registrations, `properties` and `items` on `object` and `array` props, `styles` as style groups, built-in component type names (`header`, `text`, `rich-text`, `hstack`), and `getSSRStyles` for server styles.
- **Errors match the SDK:** missing built-ins surface as `COMPONENT_NOT_REGISTERED` (fix: import `@contentstack/studio-react` above the fetch), key and token failures as `STACK_NOT_FOUND_ON_HOST`, and entry lookups that miss as `URL_MATCHED_NO_ENTRY`.
- **New paths:** apps that already have a catch-all route, Live Preview without the Delivery SDK, Next.js 16 `proxy.ts` and Turbopack, Tailwind v4 `@theme` tokens, interactive embeds in rich text, static generation and caching for Studio routes, and the canvas route layout and headers.
- **Compositions and MCP:** one canonical list recipe (Repeater, item Box, Condition Block), one wire-shape table for the CMA and the Compositions API, the compositions content type as JSON, and the MCP content-type snapshot with its HTTP fallback.
- **Consistency:** the definition of done is ten checks everywhere, `analyze-project-fit` runs first, shell snippets work in zsh, and `verify-setup` is project-agnostic.

### One skill template

- **Every skill uses the same sections:** When to use, Before you answer, Instructions, MCP tools, Output, Security, References, Examples. `scripts/validate.mjs` rejects missing, extra or out-of-order sections. The duplicated Description, User Problem, Success Criteria, Expected Inputs/Outputs, Workflow Summary, Tooling Notes and Product Context blocks are folded in, so the existing skills are about 770 lines shorter. See [the skill template](https://github.com/contentstack/contentstack-agent-skills/blob/main/docs/contributing/skill-template.md).
- **Routing cues:** each skill's When to use ends with the neighbouring skills to use instead, and many descriptions gained a "For X, use Y." cue.

### For contributors

- **Routing evals:** `evals/` holds 62 `claude plugin eval` cases, two or more per automatically invoked skill. Each checks that a prompt loads the right skill and, for close neighbours, doesn't load the wrong one. `.github/workflows/routing-evals.yml` runs them on PRs that touch `skills/` or `evals/` and needs an `ANTHROPIC_API_KEY` secret. See [Routing evals](https://github.com/contentstack/contentstack-agent-skills/blob/main/docs/contributing/routing-evals.md).

### Contributors

Thanks to @sumitjain-cstk for the Studio SDK 2.0 sync, the end-to-end audit fixes and the CSR/SSR and 404 guides (#29, #30).

**Full changelog:** https://github.com/contentstack/contentstack-agent-skills/compare/v0.3.0...v0.4.1

## 0.3.0

### New skills

- `asset-management`: advisory guidance for the standalone Assets (DAM) product: spaces and workspaces, folders, asset types and user-defined fields, localization, saved views, searching the Assets API, AI tags and alt text, duplicate management, versions, trash and restore, visual markups and CMS integration.

### Changed skills

- **`cms-assets` routing:** scoped to the stack asset library. Assets DAM questions, and any request to read or update user-defined fields, now route to `asset-management`, since the stack asset library doesn't support user-defined fields.
- **`cms-live-preview-visual-editor-support-assistant`:** ports the fixes that missed 0.2.0. Open in New Tab is scoped to Live Preview, since Visual Editor always renders in its iframe. Also: the missing navigation entry checks the stack's Live Preview setting first, the CORS entry drops an unverified allowlist claim, GraphQL preview keeps the delivery headers, `livePreviewQuery` key rules, the edit button `exclude` config needing `init()`, SDK caching separated from app and CDN caching, and `stackSdk` notes for the legacy SDK.

## 0.2.0

### Install anywhere, from one source

- Every skill now lives once in `skills/<slug>/SKILL.md` ([Agent Skills](https://agentskills.io) format), and every supported tool reads that folder directly.
- New and updated plugin manifests: Claude Code, claude.ai and Cowork (`.claude-plugin/`), Codex (`plugin.json`, `.agents/plugins/marketplace.json`), Cursor (`.cursor-plugin/`), GitHub Copilot (reads `.claude-plugin/` and `plugin.json`) and Gemini CLI (`gemini-extension.json`).
- The marketplace plugin source is now `"./"`, so the repo syncs on claude.ai and Cowork.
- The README has real install commands for every tool, and a new `docs/` site covers install, architecture, contributing and every skill.

### New skills

- `dx-kickstart-next`: building, reviewing and debugging Contentstack's Next.js kickstart.
- `studio`: Contentstack Studio end to end, routed to bundled specialist guides. `studio` ships as a preview; some guides are still being reconciled with the Studio team.

### Changed skills

- **Live Preview support is rebuilt** as a seven-step diagnostic protocol covering Live Preview, Visual Editor and Timeline, with twelve reference files.
- **`migration-companion` is leaner.** Its `SKILL.md` went from 959 to about 340 lines; per-step detail now lives in `references/step-*.md` and loads only when that step runs.
- **Security review:** token handling, TLS, frame headers and confirmation steps tightened across skills. `migration-companion` resolves its Contentful token without printing it, logs to the session directory by default, and discloses that its prerequisite check may install or upgrade global CLIs.
- **Better automatic triggering.** Every skill's `description` now says when to use it, so agents can pick the right skill without a separate router file.

### Breaking changes

- **Removed `cursor/rules/` and `codex/`.** If you copied those folders by hand, remove them and install with the Cursor or Codex instructions in the README.
- **Renamed** `cms-live-preview-visual-builder-support-assistant` → `cms-live-preview-visual-editor-support-assistant`.
- **Skill names now match their folders:** `contentstack-migration-companion` → `migration-companion`.
- **Removed `skills/CLAUDE.md`** (the router) and `manifest.json`.

### Contributors

- **Validation in CI:** `node scripts/validate.mjs` checks that each skill's `name` matches its folder and follows the naming rules; that its `description` exists, is at most 1024 characters and includes "Use when"; that `SKILL.md` has a `## Security` section with `### Defaults`, `### Destructive Actions`, `### Secrets` and `### Environment Variables`; that relative links in every Markdown file under `skills/` resolve and stay inside the skill folder; that frontmatter values containing `: ` in `skills/` and `docs/` are quoted; and that the manifests parse and every versioned manifest carries the same `version`. It replaces the build-and-commit workflow and runs on pull requests to any branch, pushes to `main` and `next`, and manual dispatch.
- **Releases:** bump `version` in every manifest and add an entry here.

## 0.1.0

Initial bundle of 21 skills.
