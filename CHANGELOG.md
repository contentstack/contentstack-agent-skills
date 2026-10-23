# Changelog

All notable changes to the Contentstack agent skills bundle. Versions match the `version` field in every plugin manifest that declares one.

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
