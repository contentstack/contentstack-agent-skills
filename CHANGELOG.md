# Changelog

All notable changes to the Contentstack agent skills bundle. Versions match the `version` field in every plugin manifest that declares one.

## 0.3.1

### Contentstack MCP server bundled with the plugin

- Every plugin now connects the hosted Contentstack MCP Profile Hub (`https://mcp-profile-hub.contentstack.com/api/mcp`), so the skills and the Contentstack tools install together. Sign-in is OAuth in the browser on first use, with no API key.
  - Claude Code and claude.ai: `.mcp.json` (`type: http`).
  - Codex, ChatGPT and other Agent Plugins clients: `mcp.json` (`type: streamable-http`).
  - Cursor: `mcpServers` in `.cursor-plugin/plugin.json`, which Cursor reads in place of `mcp.json`.
  - Gemini CLI: `mcpServers` in `gemini-extension.json` (`httpUrl`).
- Existing installs get the server on their next update and are asked to sign in the first time a Contentstack tool runs.

### New studio guides

- **`csr-and-ssr-requirements`:** what a Studio page needs as CSR or SSR on the visitor site, the Live Preview pane, Visual Editor and the canvas.
  - The five settings that must agree, plus preview mode vs builder mode. Builder mode needs `stackDetails.apiKey` and `.environment`, and a frame-and-listen check confirms Visual Editor's handshake without signing in.
  - Where the Edit button shows, and which refetch to call on studio-react 2.0.1: `refetchData` ignores freeform compositions.
  - Converting a page from one mode to the other.
- **`handle-404-pages`:** unknown URLs and bad slugs render the site's own 404 page on Next.js (App and Pages Router), Remix and React Router.
  - SSR sends a real 404 from a `try`/`catch`, clears the shared stack's preview hash before each fetch, and shares one fetch per request between the page and `generateMetadata`. CSR uses `noindex`.
  - The 404 is decided by `isCompositionNotFound` only, so a bad token or an outage stays an error.

### Changed skills

- **`studio` matches Studio SDK 2.0.** Brought in the Studio team's latest guide fixes and checked them against the released SDK.
  - Missing built-ins now surface as `COMPONENT_NOT_REGISTERED` ("Studio's own components are not registered"). The fix is to import `@contentstack/studio-react` above the fetch, not to upgrade. Updated in `troubleshoot-canvas`, `troubleshoot-ssr-rendering` and `byoc-end-to-end`.
  - `upgrade-studio-sdk` has a 1.x → 2.0 section, checked by installing 1.9.0 and 2.0.1 side by side.
    - It lists what 2.0 actually changed (`isCompositionNotFound`, deprecated `hasSpec`/`hasTemplate`, canvas tokens) separately from older rules that behave the same in both versions.
    - It no longer points to `CHANGELOG.md` files, which the npm packages don't ship.
  - `wire-studio-state` needs studio-react 1.8.0 or later, the first release that exports the state APIs.
  - Key and token failures are named `STACK_NOT_FOUND_ON_HOST`. Entry lookups that miss are `URL_MATCHED_NO_ENTRY`. Log lines start with `[Contentstack Studio]`.
  - `configure-csr-vs-ssr`: server styles come from `getSSRStyles`, computed on the server only. `isCompositionNotFound` is imported from `@contentstack/studio-react`. The Pages Router recipe reads `resolvedUrl`, not `req.url`. The RSC entry renders `<StudioServerComponent />`, and its components register through `@contentstack/studio-react/rsc` from a server module.
  - The four-question framework is defined once, in `design-component-library`. Other guides link to it.
  - Router triggers added for pinned Site Settings entries, Repeater recipes by API and App Router SSR crashes. `troubleshoot` stops after its clarifying question. `provision-studio-stack` waits for an explicit go on plan-only requests. `gate-third-party-scripts` covers analytics loader tags.
  - `use-compositions-api` says Studio API service and drops two endpoints the service doesn't have.
- **`studio` end-to-end audit fixes.** The skill was followed as a customer would on a Next.js 16 app with `@contentstack/studio-react` 2.0.1. Every changed snippet is typechecked against that release.
  - **Builds that look done but are wrong:**
    - Every plan now includes a primitive library step.
    - One Section-per-region rule replaces the conflicting reuse advice.
    - `resolveComposition` resets the preview hash, so drafts no longer leak to visitors.
    - The skill documents that the live site fetches only bound fields, and image props bind `.url`.
    - Section Slot nodes omit the slot key, which the API rejects with a 422.
    - New guides cover restarting the dev server after a registration change and a Studio-only route that sets no SEO metadata and turns 404s into 500s.
  - **SDK 2.0.1:**
    - `registerLazyComponent` is used for lazy registrations.
    - `object` and `array` props declare their required `properties` and `items`.
    - `styles` is an object of style groups.
    - `isStudioEditorMode` and `isCompositionNotFound` are imported from `@contentstack/studio-react`.
    - Built-in components use their SDK type names (`header`, `text`, `rich-text`, `hstack`).
    - The deprecated `extendQuery` is explained, and `StudioCanvas` needs no `dynamic()` wrapper or token style tag.
  - **New paths:**
    - An app that already has a catch-all route.
    - Live Preview without the Delivery SDK.
    - Next.js 16 `proxy.ts` and Turbopack.
    - Tailwind v4 `@theme` tokens and design props written in source.
    - Interactive embeds in rich text.
    - Static generation and caching for Studio routes.
    - The canvas route layout, without a route group, and its `frame-ancestors`-only headers.
  - **Compositions and MCP:**
    - One canonical list recipe (Repeater, item Box, Condition Block).
    - One wire-shape table for the CMA and the Compositions API.
    - The compositions content type ships as JSON.
    - Expected validator warnings are listed.
    - The MCP content-type snapshot and the HTTP fallback are explained, with `--scope` and the hosted connector.
    - Covers how to export the `csdx` OAuth token for scripts.
    - The delivery-token probe path is fixed.
  - **Consistency:**
    - The definition of done is ten checks everywhere.
    - `analyze-project-fit` runs first in the ordering hints.
    - Shell snippets work in zsh.
    - `verify-setup` is project-agnostic.
    - The Custom Preview URL is only required when preview is opened from an entry.
    - Example nodes carry all seven keys.

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
