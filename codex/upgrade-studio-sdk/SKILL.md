# upgrade-studio-sdk


## When to use

Bump the Studio SDK packages (studio-react, studio-react-components, studio-client, studio-registry, studio-core, studio-internal, studio-react-editor) in the host app — pin versions, read CHANGELOGs, smoke-check, roll back if needed.

Use when the user wants to upgrade the Studio SDK packages in their host app — "upgrade Studio SDK to latest", "what's new in `@contentstack/studio-react`", "is `studio-client@1.5` safe", "I want the new repeater fix". Do NOT use to install for the first time (`install-studio`). Do NOT use to develop the SDK itself.

# Upgrade the Studio SDK packages

## Context

The Studio SDK is a multi-package monorepo published as independent versions per package (lerna `versioning: independent`). The packages a host app typically installs are:

| Package | Role | Recent versions |
|---|---|---|
| `@contentstack/studio-react` | Renderer + hooks (`StudioComponent`, `useCompositionData`, registration entry points) | `1.3.x` |
| `@contentstack/studio-react-components` | Built-in basics (Page, Section, Text, Repeater, ConditionBlock, …) — `"use client"` modules | `1.5.x` |
| `@contentstack/studio-client` | CDA/CMA orchestration: `fetchCompositionData`, `fetchSpec`, URL resolution | `1.5.x` |
| `@contentstack/studio-registry` | `ComponentRegistry`, `DesignRegistry`, data-binder, globalThis singleton | `1.4.x` |
| `@contentstack/studio-core` | Internal core: light SDK init, font loading, design-token cascade | `1.1.x` |
| `@contentstack/studio-internal` | Internal types + apply/transform helpers | `1.2.x` |
| `@contentstack/studio-react-editor` | The edit-mode renderer (`StudioCanvas`'s renderer) | `1.3.x` |

Versions follow [SemVer](https://semver.org). Changelogs are committed per package in the SDK repo and follow Conventional Commits — entries are grouped by `feat` / `fix` / `perf` / `refactor`. There is no separate "Breaking Changes" section; treat any minor-version bump that involves cross-package work (registry, renderer, basics together) as carrying coordination risk.

The `peerDependencies` are `react ^18.0.0` and `react-dom ^18.0.0` — React 19 is unsupported and blocked at install time by npm/pnpm. The SDK packages also depend on each other internally; mixing major versions across them is unsupported.

## Task

1. **Capture current state.**
   - `cat package.json | grep '"@contentstack/studio'` in the host app to see currently pinned ranges.
   - `npm ls @contentstack/studio-react @contentstack/studio-react-components @contentstack/studio-client @contentstack/studio-registry @contentstack/studio-core @contentstack/studio-internal @contentstack/studio-react-editor` to see the actually-resolved versions.
   - If the lockfile is missing or stale, also run `npm view @contentstack/studio-react versions --json | tail` to see what's published.

2. **Read the CHANGELOG delta — actually read it.**
   - For each package the host app installs, open its CHANGELOG and read every entry from the installed version up to the target. Do not summarize from imagination; copy or paraphrase actual entries.
   - The studio-client CHANGELOG lives at `node_modules/@contentstack/studio-client/CHANGELOG.md` on the consumer side. Same for the other packages.
   - Flag any entry that touches: registry singleton, SSR / `"use client"` boundary, `fetchSpec` / `fetchCompositionData` signatures, URL pattern compilation, design-token / font loading, data-binder type-mismatch. Those are the ones most likely to surface integration friction even when the bump is technically non-breaking.

3. **Upgrade together, not piecemeal.** Bump all Studio SDK packages installed by the host in the same change. Mixing, say, `studio-react@1.3` with `studio-registry@1.2` risks the registry-singleton API drift (the globalThis-backed singleton landed across packages in coordinated bumps).
   - Pick the exact versions (avoid `^` for the upgrade commit so the resolved versions are reproducible; you can relax to `^` after smoke passes).
   - Run `npm install @contentstack/studio-react@<v> @contentstack/studio-react-components@<v> @contentstack/studio-client@<v> @contentstack/studio-registry@<v> @contentstack/studio-core@<v> @contentstack/studio-internal@<v> @contentstack/studio-react-editor@<v>` (or the matching `pnpm` / `yarn` form). Use `--save-exact` if you want the upgrade-commit to pin exact versions.

4. **Smoke-test the host app.** Concrete steps depend on the framework — the matrix below is the minimum surface that catches the common breakages.

   | Framework | Smoke steps |
   |---|---|
   | `next-app` | `npm run build` (catches `"use client"` boundary errors at compile) → `npm start` → load a Connected Template URL → DevTools console: no errors, no `useData` warnings in production → DevTools Network: confirm composition + entry queries return 200. |
   | `next-pages` | `npm run build` → load a composition route → no console errors. |
   | `vite-spa` | `npm run build && npm run preview` → load a composition URL → console clean → check `<StudioCanvas>` mounts on the canvas route. |
   | `remix` | `npm run build` (loader-side fetch must compile) → load a composition URL → ensure server fetch passes `searchQuery`. |

   Across all frameworks: re-check the canvas route (`/canvas` or equivalent) separately — the canvas-route renderer has historically had built-in registration regressions that don't always surface on `<StudioComponent>` routes (see the corresponding `troubleshoot-canvas` row).

5. **If something breaks.** Match the symptom to the troubleshooting skill — `troubleshoot-ssr-rendering` for boundary errors, `troubleshoot-data-binding` for binding drift, `troubleshoot-composition-resolution` for live-site URL behavior, `troubleshoot-canvas` for editor iframe. Almost every recent SDK regression has a corresponding row in one of those skills.

6. **Rollback path** (concrete; do not skip in production).
   - Revert `package.json` and the lockfile to the pre-upgrade commit (`git checkout HEAD~1 -- package.json package-lock.json`).
   - `rm -rf node_modules && npm install` (don't try to selectively downgrade — lockfile reconciliation across the seven packages is unreliable).
   - Re-run the smoke check. If you can't get back to a working state with a hard revert, escalate.

## Knowing what actually changed

Each package publishes a CHANGELOG derived from Conventional Commits. Read the CHANGELOG for every package in your delta before upgrading.

A non-exhaustive list of changes that historically required consumer-side action (read each from its CHANGELOG before claiming it applies to your delta):

- **Registry singleton moved to `globalThis`** (`studio-registry` / `studio-react` coordinated bump) — required for RSC server-side fetch to see registered components. If you're upgrading FROM a pre-singleton version TO a post-singleton version, server-side `fetchSpec` calls that used to return "component not registered" will now resolve. No consumer code change beyond the upgrade.
- **Basics moved behind a `"use client"` isolation boundary** (`studio-react`) — fixes "Attempted to call Page() from the server" in Next App Router. No consumer code change required; the renderer pulls in the client-only basics automatically.
- **Tolerant `useData` fallback** (`studio-react-components`) — replaces a throw with an empty-data fallback plus a dev-only warning. SSR pass of basics no longer crashes outside a `DataCtxProvider`. Consumer-side: dev console may show one new warning; production unchanged.
- **`fetchCompositionData` requires `searchQuery` on the server** — see [`configure-csr-vs-ssr.md`](../configure-csr-vs-ssr/SKILL.md). Required for locale/variant/preview to flow from Studio's iframe params. Pre-existing as an integration step.

Do NOT extrapolate from this list; **only the actual CHANGELOG entries for your delta** tell you which of these apply.

## What this skill is NOT

- Not a guide to first-time installation (use [`install-studio`](../install-studio/SKILL.md)).
- Not a guide to SDK-internal development.
- Not a substitute for reading the CHANGELOG. Always read the actual CHANGELOG entries for your version delta.
- Not a guide to upgrading the Contentstack Delivery SDK (`@contentstack/delivery-sdk`) or Live Preview Utils (`@contentstack/live-preview-utils`) — those are separate packages with their own CHANGELOGs, only loosely coupled to the Studio SDK.
