---
name: upgrade-studio-sdk
---

## When to use

Bump the Studio SDK packages the host app declares (usually just `@contentstack/studio-react`): pin versions, find what changed (type check, the 1.x → 2.0 table), smoke-check, roll back if needed.

Use when the user wants to upgrade the Studio SDK packages in their host app: "upgrade Studio SDK to latest", "what's new in `@contentstack/studio-react`", "is `studio-client@1.5` safe", "I want the new repeater fix", "upgrade to studio-react 2", "what broke in 2.0", "registration stopped type-checking after the upgrade". Do NOT use to install for the first time (`install-studio`). Do NOT use to develop the SDK itself.

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

2. **Find out what changed: from the compiler, not from memory.**
   - **No changelog ships in the npm packages.** As of 2.0.1, each `@contentstack/studio-*` tarball holds only `README.md`, `dist/` and `package.json`. The changelogs live in the SDK's source repo, which is private, and its `studio-react` changelog stops at 1.8.0. Don't tell the user to read a `node_modules/.../CHANGELOG.md`, and don't summarize release notes you haven't seen.
   - **Crossing a major (1.x → 2.x)?** Apply § [Upgrading from 1.x to 2.0](#upgrade-1-to-2) first.
   - **Let TypeScript list the breaks.** After installing the target (step 3), run the project's type check (`npx tsc --noEmit`, or the framework's `build`). Every registration, prop schema and fetch call the new types reject shows up there. A JavaScript project gets no such list: use the grep commands in § Upgrading from 1.x to 2.0 instead.
   - Pay extra attention to anything touching: registry singleton, SSR / `"use client"` boundary, `fetchCompositionData` signatures, URL pattern compilation, design-token / font loading, data-binder type-mismatch. Those surface integration friction even when nothing fails to compile.

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

<a id="upgrade-1-to-2"></a>

## Upgrading from 1.x to 2.0

`studio-react` 2.0.0 shipped on 2026-10-12 and 2.0.1 on 2026-10-16. Both lists below were checked by installing 1.9.0 (the last 1.x) and 2.0.1 side by side and comparing their types and runtime code.

### What 2.0 actually changed

The public `studio-react` exports gained three names and lost none. Most 1.9.0 code compiles unchanged.

| Change | 1.9.0 | 2.0.1 | Action | Details |
|---|---|---|---|---|
| Not-found errors | A miss throws `ComposableStudioError` (code `COMPOSITION_NOT_FOUND` / `COMPOSITION_NOT_FOUND_BY_URL`); there is no predicate to call | New exports `isCompositionNotFound`, `ComposableStudioError` and `CompositionNotFoundError` | Decide every 404 with `isCompositionNotFound(error)` instead of matching codes or messages | [`handle-404-pages`](handle-404-pages.md) |
| Composition kind | `hasSpec` and `hasTemplate` on the spec options | Both still present but `@deprecated`; new `connectedContentTypeUid` (`null` for freeform) | Read `connectedContentTypeUid` for the kind; never use either flag for a 404. `grep -rnE 'hasSpec\|hasTemplate' src app` | [`handle-404-pages`](handle-404-pages.md) |
| Canvas tokens | `StudioCanvas` writes no design-token variables | `StudioCanvas` writes the token `:root` variables itself once mounted | Delete any `<style>{getSSRStyles(null)}</style>` on the canvas page: it now only causes a hydration error. `grep -rn 'getSSRStyles(null)' src app` | [`setup-section-preview`](setup-section-preview.md) |
| Internal packages | `studio-client` 3.2, `studio-registry` 1.10 | `studio-client` 4.1, `studio-registry` 2.0 | Nothing, unless `package.json` pins one of them directly: then bump it in the same change (step 3) or you get two registries | Step 3 |

### Also check: rules older guides and code got wrong

These behave the same on 1.9.0 and 2.0.1, so they are not 2.0 changes. Code copied from older versions of these guides often breaks them, and an upgrade is a good time to fix it. TypeScript reports the first four.

| Rule | Wrong | Right | Find it | Details |
|---|---|---|---|---|
| `object` props need `properties` | `{ type: "object" }` | `{ type: "object", properties: { … } }` | `grep -rn 'type: "object"' src` | [`register-component`](register-component.md) step 3 |
| `array` props need `items` | `{ type: "array" }` | `{ type: "array", items: { type: "any" } }` (or the per-item prop) | `grep -rn 'type: "array"' src` | [`register-component`](register-component.md) step 3 |
| Lazy components register through `registerLazyComponent` | `registerComponent({ …, component: () => import("./X") })` (runs, but doesn't type-check) | `registerLazyComponent(config, () => import("./X").then((m) => m.X))`; the loader resolves to the component, not the module | `grep -rn 'component: () => import' src` | [`register-component`](register-component.md) § 5b |
| The hook takes no `searchQuery` | `useCompositionData({ url, searchQuery })` | `useCompositionData({ url })`; it reads `window.location` itself | `grep -rn 'useCompositionData(' src app` | [`setup-template-preview-routes`](setup-template-preview-routes.md) |
| `styles` is an object of style groups | `styles: [ … ]` | `styles: { default: …, <group>: … }`; `default` arrives as `className` | `grep -rn 'styles: \[' src` | [`register-component`](register-component.md) § 5c |
| `extendQuery` is deprecated | relied on silently | Still honoured, warns in development; no documented replacement for its `only` half | `grep -rn 'extendQuery' src app` | [`register-component-prop-contracts`](register-component-prop-contracts.md) |
| `refetchData` needs a connected composition | `refetchData` on every page | Fall back to `refetchSpec` on freeform compositions and before the first load | `grep -rn 'refetchData' src app` | [`csr-and-ssr-requirements`](csr-and-ssr-requirements.md) |

**After the bump:** restart the dev server (a running server keeps the old registrations), run the type check, then the smoke tests in step 4. Check the Components panel on the canvas: a registration that fails at runtime drops out of the palette without an error on the page.

## Knowing what actually changed

There is no public changelog for these packages (step 2). Read the compiler output and § Upgrading from 1.x to 2.0. Within a major, compare the installed `.d.ts` files before and after (`diff -r` two installs of `node_modules/@contentstack/studio-react/dist`) when you need more than the type check gives you.

A non-exhaustive list of older changes that required consumer-side action (confirm each applies to your delta before claiming it does):

- **Registry singleton moved to `globalThis`** (`studio-registry` / `studio-react` coordinated bump): required for RSC server-side fetch to see registered components. If you're upgrading FROM a pre-singleton version TO a post-singleton version, server-side `fetchSpec` calls that used to return "component not registered" will now resolve. No consumer code change beyond the upgrade.
- **Basics moved behind a `"use client"` isolation boundary** (`studio-react`): fixes "Attempted to call Page() from the server" in Next App Router. No consumer code change required. The renderer pulls in the client-only basics automatically.
- **Tolerant `useData` fallback** (`studio-react-components`): replaces a throw with an empty-data fallback plus a dev-only warning. SSR pass of basics no longer crashes outside a `DataCtxProvider`. Consumer-side: dev console may show one new warning, production unchanged.
- **`fetchCompositionData` requires `searchQuery` on the server**: see [`configure-csr-vs-ssr.md`](configure-csr-vs-ssr.md). Required for locale/variant/preview to flow from Studio's iframe params. Pre-existing as an integration step.

Do NOT extrapolate from this list. Confirm each against the installed types or a smoke test before claiming it applies.

## What this skill is NOT

- Not a guide to first-time installation (use [`install-studio`](install-studio.md)).
- Not a guide to SDK-internal development.
- Not a substitute for the type check and smoke test. Run both for every version delta.
- Not a guide to upgrading the Contentstack Delivery SDK (`@contentstack/delivery-sdk`) or Live Preview Utils (`@contentstack/live-preview-utils`): those are separate packages with their own CHANGELOGs, only loosely coupled to the Studio SDK.
