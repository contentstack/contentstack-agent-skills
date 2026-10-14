---
name: analyze-project-fit
---

## When to use

Read-only diagnostic that inspects the user's project (package.json, framework, React version, Contentstack deps) and emits a tailored install path before any state-changing skill runs.

Use as the FIRST step when the user wants to add Studio to an existing project, or is unsure if their setup is compatible. Phrases: "add Studio to my app", "is my project compatible", "before I install". Always run before `install-studio`, `install-live-preview`, or `setup-section-preview`. Skip if already run this session.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Analyze project fit: pre-flight diagnostic for Studio install

## Why this skill exists

`install-studio` assumes a known project shape. In reality projects vary across:

- **React version**: the SDK supports React 18 and React 19. `@contentstack/studio-react` 1.5.1 and later peer-dep `react ^18.0.0 || ^19.0.0`. The one real blocker is a **stale SDK pin**: a lockfile already holding `@contentstack/studio-react` at 1.5.0 on a React 19 app fails with ERESOLVE. Fix the pin, never downgrade React.
- **Framework**: Next.js needs `NEXT_PUBLIC_*` env prefixes and SSR-safe init, Vite needs `dedupe` and a prod-build canvas, CRA needs `REACT_APP_*`.
- **Bundler quirks**: Next 16 + Turbopack has tree-shake edge cases. Custom webpack configs may not externalize React.
- **Existing Contentstack SDKs**: adding Studio to an app that already has `@contentstack/delivery-sdk` is a minimal-add, not a greenfield install.
- **Local serving**: Studio iframes the canvas. `http://localhost` works, mkcert is optional. Chrome asks for local network access: allow it.

Running blind through `install-studio` against these variants is what produces long debug sessions (dev-optimizer dual React, stale SDK pin, missing trusted HTTPS, etc.; see [`troubleshoot`](troubleshoot.md)). This skill front-loads the inspection so the next skill receives a clean, known shape.

This skill is **read-only**. It never writes files, never installs packages, never modifies the project. It produces a plan, the user confirms, then the appropriate downstream skill runs.

## Task

### 1. Inspect the project (no writes)

Run these checks in order:

```bash
# 1a. package.json — root + workspace packages if monorepo
cat {{projectRoot}}/package.json

# 1b. Lockfile → package manager
ls {{projectRoot}}/pnpm-lock.yaml {{projectRoot}}/yarn.lock {{projectRoot}}/package-lock.json {{projectRoot}}/bun.lockb 2>/dev/null

# 1c. Workspace / monorepo signals
ls {{projectRoot}}/turbo.json {{projectRoot}}/pnpm-workspace.yaml {{projectRoot}}/nx.json {{projectRoot}}/lerna.json 2>/dev/null

# 1d. TypeScript presence
ls {{projectRoot}}/tsconfig.json 2>/dev/null

# 1e. Single React check (the dual-React problem)
cd {{projectRoot}} && npm ls react 2>&1 | head -20

# 1f. Bundler configs
ls {{projectRoot}}/vite.config.* {{projectRoot}}/next.config.* {{projectRoot}}/webpack.config.* {{projectRoot}}/tsup.config.* 2>/dev/null

# 1g. Local HTTPS readiness
which mkcert ; ls {{projectRoot}}/certs/*.pem 2>/dev/null

# 1h. Deploy target
ls {{projectRoot}}/launch.json {{projectRoot}}/.cs-launch.json 2>/dev/null

# 1i. App-side i18n (every locale needs its own env Base URL later)
grep -E '"(next-intl|next-i18next|i18next|react-i18next|react-intl|@lingui/[a-z]+|next-international)"' {{projectRoot}}/package.json
find {{projectRoot}}/app {{projectRoot}}/src/app -maxdepth 2 -type d \( -name '[[]locale[]]' -o -name '[[]lang[]]' \) 2>/dev/null
grep -n "i18n" {{projectRoot}}/next.config.* 2>/dev/null ; ls {{projectRoot}}/middleware.* {{projectRoot}}/src/middleware.* 2>/dev/null
```

### 2. Classify the project

From the output above, extract:

| Signal | Detection rule |
|---|---|
| **Framework** | `package.json` deps: `next` means Next.js, `vite` means Vite, `react-scripts` means CRA, `@remix-run/*` means Remix, `astro` means Astro, and anything else is Custom |
| **React version** | the `react` field in `package.json` deps gives the version range. Resolve to the actual installed major via `npm ls react`. Classify as **18**, **19**, **17 or older** |
| **Single React** | `npm ls react` must show exactly one tree entry, on **18.x or 19.x** (the SDK peer-deps `react ^18.0.0 \|\| ^19.0.0` from 1.5.1): if it shows two entries or a deduped warning, that's a duplicate risk. A single 19.x entry is a pass, not a blocker |
| **Package manager** | `pnpm-lock.yaml` means pnpm, `yarn.lock` means yarn, `bun.lockb` means bun, and `package-lock.json` means npm |
| **TypeScript** | `tsconfig.json` exists |
| **Monorepo** | Any of `turbo.json` / `pnpm-workspace.yaml` / `nx.json` / `lerna.json` |
| **Existing Studio integration** | Any `@contentstack/studio-*` already in deps |
| **Existing CS app** | Any `@contentstack/*` already in deps (not Studio), implies minimal-add |
| **Next + Turbopack** | Next deps + `next dev --turbo` or `next dev --turbopack` in scripts |
| **mkcert ready** | `which mkcert` returns a path |
| **Data center / region** | See § 2b: Determine the data center below. **Never skip this.** |

### 2b. Determine the data center: standard region vs custom / private data center

**Nothing else in the skill pack figures this out, and several skills assume you already have.** Establish it here, once, and carry it forward.

**Why it matters more than it looks.** The Delivery SDK defaults to the **US prod CDA**, and the Studio React SDK derives its Studio API host from whatever stack you hand it. So a project targeting another data center that never sets `host:` will silently read and write **US prod**, no error, no warning, wrong data center. A custom / private data center (hosts supplied by Contentstack) has no `region` shortcut: set every host explicitly (`install-studio` § Custom / private data center).

Resolve in this order, stopping at the first hit:

```bash
# 1. Explicit host already in the app?
grep -rnE "https?://|host:|CONTENTSTACK_[A-Z_]+|CMA_HOST|STUDIO_API_HOST|CDA_HOST|PREVIEW_HOST|region" .env* src/ app/ lib/ 2>/dev/null | head

# 2. Region shortcut in use? (standard regions only — NA/EU/AU/AZURE_NA/AZURE_EU/GCP_NA/GCP_EU)
grep -rn "region:\s*['\"]" src/ app/ lib/ 2>/dev/null | head
```

3. **Ask, if neither is conclusive**: and ask for the URL, not the name, because the URL is unambiguous:

   > Which Contentstack environment is this stack on? Paste the URL you use to open Contentstack: `app.contentstack.com` (US), a regional host, or a custom host Contentstack supplied for a private data center.

The editor URL determines every other host. For a custom / private data center, get the full set (CDN, REST preview, CMA, Studio API, images) from Contentstack and set every host explicitly; see [`install-studio`](install-studio.md) § Custom / private data center.

**Record it in the report (step 4) as an explicit line.** Downstream skills consume it:

| Consumer | What changes on a custom / private data center |
|---|---|
| [`install-contentstack-mcp`](install-contentstack-mcp.md) | API calls need `CONTENTSTACK_CMA_BASE_URL` / `CDA_BASE_URL` plus a valid region code (a data-center name is not a region, and the CLI exits on it), and its **OAuth login can't reach a custom DC at all** (authorize host is region-derived, no override). Use `csdx` with OAuth there (or a management token, if the user prefers one). Defaults to **NA prod** if this answer is missing |
| **OAuth on a custom DC** | Needs that DC's **own** OAuth app id + client id: apps are registered per data center, so one data center's ids do not exist on another. **Ask the user, never reuse ids across DCs.** A wrong id makes the authorize page return "App with id … not found". See [`understand-contentstack-mcp` § OAuth on a custom region](understand-contentstack-mcp.md#oauth-on-a-custom-region) |
| [`install-studio`](install-studio.md) | Every host set explicitly. `host:` on `Contentstack.stack({...})` is mandatory, not optional |
| [`verify-setup`](verify-setup.md) | `previewHost` comes from this determination rather than the standard region map |
| [`author-composition-via-api`](author-composition-via-api.md) | `curl` not Python for CMA (the DC's chain may not be in Python's CA store) |

### 3. Choose a path

Pick exactly one based on the classification:

| Path | Detected shape | What to do next |
|---|---|---|
| **A. Greenfield-friendly** | **Vite / CRA / Next (App or Pages Router)** + React 18 or 19 + single React + no existing CS deps | Run `install-studio` directly. No pre-work needed. A fresh Next 15 + React 19 app lands here — framework is not what gates Path A; a stale SDK pin (B), React 17 (C), existing CS deps (D) or duplicate React (G) are. On Next + Turbopack, also read Path E's flag before installing. |
| **B. Stale SDK pin on React 19** | React 19.x detected AND `npm ls @contentstack/studio-react` (or the lockfile) shows 1.5.0 | **Block** `install-studio` until the pin moves. **Evidence:** `@contentstack/studio-react` 1.5.1+ peer-deps `react ^18.0.0 \|\| ^19.0.0`. 1.5.0 alone peer-deps `^18.0.0`, so the install fails with ERESOLVE on React 19. **Fix:** `<pm> add @contentstack/studio-react@latest` (run [`upgrade-studio-sdk`](upgrade-studio-sdk.md) so the sibling packages move together), then re-run `analyze-project-fit`. **Never downgrade React or Next to satisfy an old SDK pin.** A React 19 app with no prior Studio pin is Path A or D. |
| **C. React 17 or older** | React < 18 detected | **Block** `install-studio`. The user must upgrade to React 18 first. Refer them to the React 18 upgrade guide. The SDK won't work on 17: this is a hard requirement, not a soft one. |
| **D. Existing CS app (minimal-add)** | `@contentstack/delivery-sdk` or `@contentstack/live-preview-utils` already present | Do NOT re-init Delivery SDK. Take the minimal-add branch in `install-studio` (Studio-only install, reuses existing Delivery SDK init). |
| **E. Next + Turbopack** | Detected | Proceed to `install-studio` with Next-specific paths. Flag: SDK ships a canvas-route built-ins auto-bootstrap, but if the user is pinned to an older SDK there's a known Turbopack tree-shake regression. `troubleshoot-canvas` has the safety-net snippet. |
| **H. Custom / private data center** | Editor URL or config shows a custom host supplied by Contentstack | Not a blocker, but pin it before any state-changing skill. Set every host explicitly (no `region` shortcut); the MCP's OAuth login cannot reach a custom DC (its API calls can, with host overrides), and CMA calls use `curl`. Carry the hosts into `install-studio`, `verify-setup` and any provisioning skill. |
| **F. Custom bundler** | Webpack/tsup/rollup with no `external: ['react']` detected | Walk the user through `dedupe` config OR (recommended) switch to serving a prod build for the Studio canvas. The dev bundler is the most common source of dual-React issues. |
| **G. Multiple React instances** | `npm ls react` shows >1 entry | **Block** `install-studio`. Resolve duplicates first: identify which dep pulls the second React (`npm ls react`), add `overrides`/`resolutions` in `package.json` to pin a single version, reinstall, re-run `analyze-project-fit`. |

### 4. Report: what to tell the user

Print a single readable summary block:

```
✓ Project shape detected:
    Framework:        <Next | Vite | CRA | Remix | Astro | Custom>
    React:            <18.x | 19.x> — <single | duplicate>
    Package manager:  <pnpm | yarn | npm | bun>
    TypeScript:       <yes | no>
    Monorepo:         <yes (turbo/pnpm-workspace/etc.) | no>
    Existing CS SDKs: <none | delivery-sdk | live-preview-utils | studio-react>
    Local HTTPS:      <mkcert ready | not installed>
    Deploy target:    <launch | other host | none>
    i18n:             <none | next-intl (always) en,fr | [locale] segment en,de | …>

Chosen path: <A | B | C | D | E | F | G> [+ H] — <short label>

Next steps (in order):
  1. <exact command if any prep needed, e.g. pnpm add @contentstack/studio-react@latest ...>
  2. Invoke skill: <install-studio | install-studio (minimal-add branch) | …>
  3. Then: <setup-section-preview | …>

Blockers to resolve before install:
  • <list, or "none">
```

Wait for explicit user confirmation before invoking the next skill.

### 5. Hand-off

Once the user confirms, invoke the next skill in the chosen path. Pass forward what you discovered (framework, package manager, React version, TS) so the downstream skill doesn't re-prompt for things you already know.

## Inputs needed from the user

1. `projectRoot`: path to the project. Usually `.` (current dir).

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] Inspection commands ran and outputs were classified (no guessing: every signal in the classification table either matched a detection rule or was reported as "not detected").
- [ ] **The data center is established and stated explicitly**: a standard region (NA/EU/AU/AZURE_NA/AZURE_EU/GCP_NA/GCP_EU) or a custom / private data center with its hosts. Never left as "assumed": the SDK silently defaults to US, so a wrong assumption writes real data to the wrong data center with no error.
- [ ] Exactly one path (A to G, plus H if on a custom / private data center) was chosen with justification.
- [ ] The summary block was printed including the chosen path + next steps.
- [ ] If the path is a blocker (B/C/G), `install-studio` was NOT invoked: the user is given the prep step and asked to re-run `analyze-project-fit` after.
- [ ] If the path is an enabler (A/D/E/F), the downstream skill was invoked with the discovered context.
- [ ] No files were modified by this skill itself.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Trusting `package.json` `react` field over `npm ls react` | The dep range may say `^18.0.0` but the actual installed version could be 18.x or higher depending on resolution + lockfile | Always run `npm ls react` to confirm the installed major |
| Assuming React 19 is blocked | The SDK supports React 19 since 1.5.1. Telling a React 19 user to downgrade to 18.3.1 rewrites their app for nothing and can break Next 15 features they rely on | React 19 is Path A or D. Only a stale `@contentstack/studio-react` pin at 1.5.0 blocks it, and the fix is upgrading the SDK (Path B) |
| Skipping the monorepo check | Studio installed in the wrong workspace package doesn't get picked up by the canvas-app | Detect `pnpm-workspace.yaml` / `turbo.json`, ask which workspace package is the canvas-app |
| Routing every project through Path A by default | The smooth path only applies to a specific shape | Use the classification table: if any signal points to B to G, go there |
| Re-running `analyze-project-fit` after the user makes a change without re-running the inspection commands | Stale classification = wrong path | After any user-side prep (downgrade, dedupe), re-run inspection commands fresh |

## See also

- `install-studio`: the downstream skill for paths A/D/E/F
- `setup-section-preview`: for the canvas-iframe wiring
- `setup-local-https-canvas`: optional mkcert recipe, only if the app needs local HTTPS
- `troubleshoot-canvas`: reactive diagnosis if install proceeded and something failed downstream
- `verify-setup`: layered smoke test after install
