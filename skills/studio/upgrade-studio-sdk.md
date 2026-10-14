---
name: upgrade-studio-sdk
---

## When to use

Bump the Studio SDK packages the host app declares (usually just `@contentstack/studio-react`): pin versions, read CHANGELOGs, smoke-check, roll back if needed.

Use when the user wants to upgrade the Studio SDK packages in their host app: "upgrade Studio SDK to latest", "what's new in `@contentstack/studio-react`", "is `studio-client@1.5` safe", "I want the new repeater fix". Do NOT use to install for the first time (`install-studio`). Do NOT use to develop the SDK itself.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Upgrade the Studio SDK packages

## Context

The Studio SDK is published as several `@contentstack/studio-*` packages, each versioned independently. A host app normally declares only `@contentstack/studio-react` (renderer, hooks, `StudioComponent`, `StudioCanvas`, registration entry points), which is what `install-studio` installs. `studio-react` pulls in the other Studio packages it needs (built-in components, client, registry) as its own dependencies. Only declare another `@contentstack/studio-*` package directly if the app imports from it, and then keep it in the same upgrade.

Versions follow [SemVer](https://semver.org). Changelogs are committed per package in the SDK repo and follow Conventional Commits: entries are grouped by `feat` / `fix` / `perf` / `refactor`. There is no separate "Breaking Changes" section. Treat any minor-version bump that involves cross-package work (registry, renderer, basics together) as carrying coordination risk.

The `peerDependencies` are `react ^18.0.0 || ^19.0.0` and `react-dom ^18.0.0 || ^19.0.0` from 1.5.1 onward. Only 1.5.0 peer-deps `^18.0.0` alone (1.4.x and earlier declare `>=16.0.0`), so a React 19 app pinned to 1.5.0 must upgrade the SDK first (never downgrade React). The SDK packages also depend on each other internally. Mixing major versions across them is unsupported.

## Task

1. **Capture current state.**
   - `grep '"@contentstack/studio' package.json` in the host app to see which Studio packages it declares and their ranges.
   - List the resolved versions of every `@contentstack/studio-*` package with the project's package manager: `npm ls --all | grep @contentstack/studio`, `pnpm why @contentstack/studio-react`, or `yarn why @contentstack/studio-react`.
   - To see what's published, run `npm view @contentstack/studio-react versions --json` (or `pnpm view` / `yarn info`).

2. **Read the CHANGELOG delta: actually read it.**
   - For each package the host app installs, open its CHANGELOG and read every entry from the installed version up to the target. Do not summarize from imagination. Copy or paraphrase actual entries.
   - The studio-client CHANGELOG lives at `node_modules/@contentstack/studio-client/CHANGELOG.md` on the consumer side. Same for the other packages.
   - Flag any entry that touches: registry singleton, SSR / `"use client"` boundary, `fetchSpec` / `fetchCompositionData` signatures, URL pattern compilation, design-token / font loading, data-binder type-mismatch. Those are the ones most likely to surface integration friction even when the bump is technically non-breaking.

3. **Upgrade the packages the host declares, together.** Bump every `@contentstack/studio-*` package listed in the host's `package.json` in the same change. Usually that is only `@contentstack/studio-react`, as `install-studio` installs it. `studio-react` declares the other Studio packages as its own dependencies, so upgrading it brings in matching versions. Do **not** add those internal packages to `package.json`: a direct pin that falls outside `studio-react`'s range installs a second copy, which splits the registry singleton (the globalThis-backed singleton landed across packages in coordinated bumps).
   - Pick the exact versions (avoid `^` for the upgrade commit so the resolved versions are reproducible. You can relax to `^` after smoke passes).
   - Install with the project's package manager: `npm install --save-exact @contentstack/studio-react@<v>`, `pnpm add --save-exact @contentstack/studio-react@<v>`, or `yarn add --exact @contentstack/studio-react@<v>` (plus any other `@contentstack/studio-*` package already in `package.json`).
   - Re-run the listing from step 1: each Studio package should resolve to a single version (no duplicate nested copies).

4. **Smoke-test the host app.** Concrete steps depend on the framework. The matrix below is the minimum surface that catches the common breakages. Commands are shown with `npm`; use the `pnpm` / `yarn` equivalents if that's the project's package manager.

   | Framework | Smoke steps |
   |---|---|
   | `next-app` | Run `npm run build` (it catches `"use client"` boundary errors at compile), then `npm start`, then load a Connected Template URL. In the DevTools console: no errors, no `useData` warnings in production. In the DevTools Network tab: confirm composition + entry queries return 200. |
   | `next-pages` | Run `npm run build`, then load a composition route, and confirm no console errors. |
   | `vite-spa` | Run `npm run build && npm run preview`, then load a composition URL, confirm the console is clean, and check `<StudioCanvas>` mounts on the canvas route. |
   | `remix` | Run `npm run build` (the loader-side fetch must compile), then load a composition URL, and ensure the server fetch passes `searchQuery`. |

   Across all frameworks: re-check the canvas route (`/canvas` or equivalent) separately. The canvas-route renderer has historically had built-in registration regressions that don't always surface on `<StudioComponent>` routes (see the corresponding `troubleshoot-canvas` row).

5. **If something breaks.** Match the symptom to the troubleshooting skill: `troubleshoot-ssr-rendering` for boundary errors, `troubleshoot-data-binding` for binding drift, `troubleshoot-composition-resolution` for live-site URL behavior, `troubleshoot-canvas` for editor iframe. Almost every recent SDK regression has a corresponding row in one of those skills.

6. **Rollback path** (concrete. Do not skip in production).
   - First run `git status` and show the user what the rollback would overwrite or discard (uncommitted edits to `package.json`, the lockfile, and the whole `node_modules`). Get their confirmation before running the steps below; if there are uncommitted changes they want to keep, stash or commit them first.
   - Restore `package.json` and the project's own lockfile (`package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`) from the last commit before the upgrade: `git checkout <pre-upgrade-commit> -- package.json <lockfile>`. Find that commit with `git log -- package.json`, not by assuming `HEAD~1`.
   - `rm -rf node_modules`, then a clean install from that lockfile with the project's package manager: `npm ci`, `pnpm install --frozen-lockfile`, or `yarn install --frozen-lockfile` (`yarn install --immutable` on Yarn 2+). Don't try to selectively downgrade: lockfile reconciliation across the Studio packages is unreliable.
   - Re-run the smoke check. If you can't get back to a working state with a hard revert, escalate.

## Knowing what actually changed

Each package publishes a CHANGELOG derived from Conventional Commits. Read the CHANGELOG for every package in your delta before upgrading.

A non-exhaustive list of changes that historically required consumer-side action (read each from its CHANGELOG before claiming it applies to your delta):

- **Registry singleton moved to `globalThis`** (`studio-registry` / `studio-react` coordinated bump): required for RSC server-side fetch to see registered components. If you're upgrading FROM a pre-singleton version TO a post-singleton version, server-side `fetchSpec` calls that used to return "component not registered" will now resolve. No consumer code change beyond the upgrade.
- **Basics moved behind a `"use client"` isolation boundary** (`studio-react`): fixes "Attempted to call Page() from the server" in Next App Router. No consumer code change required. The renderer pulls in the client-only basics automatically.
- **Tolerant `useData` fallback** (`studio-react-components`): replaces a throw with an empty-data fallback plus a dev-only warning. SSR pass of basics no longer crashes outside a `DataCtxProvider`. Consumer-side: dev console may show one new warning, production unchanged.
- **`fetchCompositionData` requires `searchQuery` on the server**: see [`configure-csr-vs-ssr.md`](configure-csr-vs-ssr.md). Required for locale/variant/preview to flow from Studio's iframe params. Pre-existing as an integration step.

Do NOT extrapolate from this list. **Only the actual CHANGELOG entries for your delta** tell you which of these apply.

## What this skill is NOT

- Not a guide to first-time installation (use [`install-studio`](install-studio.md)).
- Not a guide to SDK-internal development.
- Not a substitute for reading the CHANGELOG. Always read the actual CHANGELOG entries for your version delta.
- Not a guide to upgrading the Contentstack Delivery SDK (`@contentstack/delivery-sdk`) or Live Preview Utils (`@contentstack/live-preview-utils`): those are separate packages with their own CHANGELOGs, only loosely coupled to the Studio SDK.
