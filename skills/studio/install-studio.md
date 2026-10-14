---
name: install-studio
---

## When to use

**Compatibility question?** "Can I install Studio", "is my project compatible", "check before I install": Read [`analyze-project-fit`](analyze-project-fit.md) instead, not this skill.

Install Contentstack Studio + Live Preview + Delivery SDK in this project, configure them with stack credentials, and wire studioSdk.init at the app shell.

Use when the user wants to add Contentstack Studio to an existing React app (Next.js, Vite, CRA, Remix, Astro): "install Studio in my app", "add Studio SDK". Installs the three SDKs (delivery-sdk, live-preview-utils, studio-react), validates credentials, wires side-effect init. Does NOT add the canvas route. Pair with `setup-section-preview`.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Install Studio in this project

## Context

Install three SDKs together, they're effectively one install:

- **`@contentstack/delivery-sdk`**: reads published content
- **`@contentstack/live-preview-utils`**: real-time updates (uses **Preview Token**, not Delivery Token)
- **`@contentstack/studio-react`**: Studio bridge (`studioSdk`, `<StudioCanvas />`, `<StudioComponent />`)

Each Delivery Token record on the stack carries three credentials: **Stack API Key**, **Delivery Token**, and an automatically-paired **Preview Token**. Don't ask the user to "create a preview token" separately.

Two Studio React components, NOT interchangeable:

- **`<StudioCanvas />`** mounts on the **Canvas route** (e.g. `/studio-canvas`). Previews Sections in Studio's iframe.
- **`<StudioComponent />`** mounts on **ONE catch-all route** (`app/[[...slug]]/page.tsx` for Next.js App Router, `<Route path="*">` for React Router). Studio resolves every URL via `sdk.fetchCompositionData({ url, searchQuery })`. No per-template routes needed.

This skill installs SDKs + wires global init. Adding the `<StudioCanvas />` route is a separate skill (`setup-section-preview`).

## Regional host map: fill in BOTH CDN host and Live Preview host

The Delivery SDK takes a CDN host. Live Preview takes a different, region-specific preview host. The `us` defaults you get if you omit them work **only** for North America stacks. Non-US stacks need both filled in.

| Region | CDN `host` (Contentstack.stack) | `live_preview.host` (preview channel) |
|---|---|---|
| `us` | (omit, default) | `rest-preview.contentstack.com` |
| `eu` | `eu-cdn.contentstack.com` | `eu-rest-preview.contentstack.com` |
| `azure-na` | `azure-na-cdn.contentstack.com` | `azure-na-rest-preview.contentstack.com` |
| `azure-eu` | `azure-eu-cdn.contentstack.com` | `azure-eu-rest-preview.contentstack.com` |
| `gcp-na` | `gcp-na-cdn.contentstack.com` | `gcp-na-rest-preview.contentstack.com` |
| `gcp-eu` | `gcp-eu-cdn.contentstack.com` | `gcp-eu-rest-preview.contentstack.com` |
| `au` | `au-cdn.contentstack.com` | `au-rest-preview.contentstack.com` |

For projects that already use a region-to-host helper, prefer that. It returns both hosts from a single `region` and stays current as Contentstack adds regions.

## Custom / private data center

A custom or private data center has no `region` shortcut: its hosts are supplied by Contentstack, so **set every host explicitly**. Never guess them. Ask the user for the exact hosts Contentstack gave them (or read them off the Contentstack URL they open):

> Which hosts did Contentstack give you for this stack? I need the Delivery, Live Preview, CMA, Studio API and app hosts exactly as supplied.

| Service | Host to set | Used by |
|---|---|---|
| CDA (Delivery) | `<cda-host>` | `Contentstack.stack({ host })` |
| Live Preview | `<preview-host>` | `live_preview.host` |
| CMA | `<cma-host>` | Management scripts, provisioning |
| Studio API | `<studio-api-host>` | Studio project creation, project listing |
| Editor (browser) | `<app-host>` | The Studio UI the user opens |
| Images CDN | `<images-host>` | Asset URLs in entry responses |

**Required `host:` override.** The Studio React SDK derives its Studio API host from whatever Delivery stack you pass it. **If you don't set `host:` on `Contentstack.stack({...})`, it defaults to the US prod CDA and the Studio SDK then points at the NA Studio API too.** Set the CDA host explicitly:

```ts
const stack = Contentstack.stack({
  apiKey, deliveryToken, environment,
  host: import.meta.env.VITE_CS_CDA_HOST,          // <-- required on a custom data center
  live_preview: {
    enable: true, preview_token,
    host: import.meta.env.VITE_CS_PREVIEW_HOST,
  },
});
```

Read the hosts from env vars (`VITE_CS_CDA_HOST` / `VITE_CS_PREVIEW_HOST`). The env Base URL (Settings, then Environments) must point at the running app, same as on a standard region.

## Existing Contentstack app? Take the minimal-add branch

Before doing anything destructive, check whether the user already has `@contentstack/delivery-sdk` AND `@contentstack/live-preview-utils` installed and a stack init somewhere in the codebase. If yes, **take the minimal-add branch** instead of emitting a new `lib/contentstack.ts`:

- Search for `Contentstack.stack({` or `contentstack.stack({`. The existing stack factory is what to reuse.
- Search for `ContentstackLivePreview.init(`. If present, do NOT call `init()` again. Doing so double-initializes the channel.
- Add `@contentstack/studio-react` only.
- Create a SEPARATE module (e.g. `lib/studio.ts`) that imports the existing `stack` and calls `studioSdk.init({ stackSdk: stack, contentTypeUid: "<studioContentTypeUid>" })`, using the uid resolved in § 0c. Export `sdk` from there. This branch needs § 0c exactly as much as the greenfield one does.
- Do not modify the existing `lib/contentstack.ts` (or equivalent module).

The full emit would clobber a custom stack factory. If NEITHER package is installed, proceed with the greenfield emit below.

> **Hazard: reusing the existing stack instance means Studio shares its Live Preview state with everything else that touches it.** `stack.livePreviewQuery(...)` doesn't scope to one call: it mutates a single shared object (`_client.stackConfig.live_preview` in `@contentstack/delivery-sdk`, the equivalent on the legacy `contentstack` v3 SDK) that lives on the stack instance itself, not on the request. If the app's OWN code calls `.livePreviewQuery(...)` on that SAME stack anywhere else — even with a legitimate, unrelated reason, e.g. a parent layout's own data fetch doing `stack.livePreviewQuery(live_preview ?? {})` with no override — it resets that shared state to empty. Next.js (and most SSR frameworks) run a page's layout(s) and the page itself concurrently on one request, so that reset can land in between two of Studio's OWN internal composition-resolution queries for the SAME lookup, flipping some of them back to the Delivery API mid-resolution with no code change and no error. Symptom: Live Preview intermittently doesn't apply — see [`troubleshoot-canvas`](troubleshoot-canvas.md) § Live Preview state resets mid-request for the full diagnosis. **If the app makes its own `.livePreviewQuery(` calls elsewhere on the same stack, give Studio's `stackSdk` its own independent stack instance instead of reusing the app's.** Reuse the app's Delivery Token/credentials to construct it, just not the same object.

## Task

### 0. FIRST: run `analyze-project-fit`

Before this skill changes anything, Read `analyze-project-fit` and print its summary block. A hand inspection doesn't count. It picks the path:

- **Path A (Greenfield-friendly)**: continue with this skill from §0a
- **Path D (Existing-app minimal-add)**: continue with this skill from §0b minimal-add branch
- **Path B / C / G (blockers: stale SDK pin on React 19, React 17, duplicate React)**: STOP. Resolve the blocker, re-run `analyze-project-fit`, then return here.

Skip only if it already ran this session.

### 0a. STACK-LEVEL PRE-FLIGHT: Visual Experience must be enabled (do NOT skip)

Confirm **Live Preview is enabled at the stack level**: read `stack_settings.live_preview.enabled` from `GET /v3/stacks/settings` rather than asking, and enable it by API if it is off ([`enable-visual-experience` § Do it by API](enable-visual-experience.md#api-path)). Otherwise every step succeeds locally and **silently fails at runtime** (blank canvas, no `data-cslp` tags).

If the user has never run `enable-visual-experience` for this stack, call it now and wait for its acceptance. If they insist it's already set up, ask them to confirm explicitly: "In Settings, under Visual Experience, on the General tab, `Enable Live Preview` is checked + Saved (yes/no? Delivery Token has a Preview Token) yes/no?" If unsure, run `enable-visual-experience`.

### 0b. PRE-FLIGHT GATE: non-greenfield detection (do NOT skip)

Scan for an existing Contentstack integration. If found, **switch to the minimal-add branch**. The full emit will clobber a custom stack factory.

Check ALL signals in parallel:

```bash
# Existing stack factory
grep -rEn "Contentstack\.stack\(|contentstack\.stack\(" --include='*.ts' --include='*.tsx' --include='*.js' --include='*.mjs' src/ app/ lib/ pages/ 2>/dev/null | head -5

# Existing Live Preview init (NEVER call init() twice)
grep -rEn "ContentstackLivePreview\.init\(" --include='*.ts' --include='*.tsx' --include='*.js' --include='*.mjs' . 2>/dev/null | head -5

# Existing Contentstack-config module (common names)
ls src/lib/contentstack.* lib/contentstack.* src/contentstack.* contentstack.config.* 2>/dev/null

# package.json — Delivery SDK + Live Preview already installed?
grep -E "@contentstack/delivery-sdk|@contentstack/live-preview-utils" package.json | head -3
```

**Branching rule:**

| Signal | Branch to take |
|---|---|
| Both `@contentstack/delivery-sdk` AND `@contentstack/live-preview-utils` already in `package.json` | **Minimal-add**: `npm install @contentstack/studio-react` only, create separate `lib/studio.ts` (see § Existing Contentstack app above) |
| Only one of the two installed | Ask user, likely partial install in progress. Do NOT auto-install the other |
| **Existing `lib/contentstack.ts`** (or similar) with a stack factory | **Minimal-add**: even if package.json looks "clean," the project may have a custom stack module. Don't overwrite. |
| **Existing `ContentstackLivePreview.init(...)` call** anywhere in the codebase | **Minimal-add**: adding a second `init()` double-initializes the channel and breaks Live Preview. |
| NEITHER package installed AND no existing stack module | **Greenfield**: proceed with the full emit below |

When in doubt, STOP and ask: "I found `<file>` with `<signal>`, looks like an existing Contentstack integration. Add Studio as a minimal addition (separate `lib/studio.ts` importing your existing stack)?" Default to YES.

### 0c. PRE-FLIGHT GATE: resolve the Studio project, then read its content type (do NOT skip)

`studioSdk.init({ contentTypeUid })` has to name the **same compositions content type the Studio project points at**. That uid belongs to the project, not to the stack: one stack can host several Studio projects, each with its own `contentTypeUid` (`compositions_first`, `compositions_second`, `<user>_compositions`, …). Defaulting to `"compositions"` is therefore a guess, and it fails late and confusingly. Studio raises **"Content Types Don't Match"** over the canvas — *Expected* is the project's uid, *Actual* is whatever the SDK asked for — and loads nothing at all.

**If the user named a Studio project, use it. If they didn't, ASK — never default.** List the projects rather than making them find and paste a uid:

```bash
curl -s "https://<studio-api-host>/v1/projects" \
  -H "Authorization: Bearer <oauth-access-token>" \
  -H "organization_uid: <org-uid>" | jq -r \
  '.projects[] | "\(.uid)  \(.name)  stack=\(.connectedStackApiKey)  ct=\(.contentTypeUid)"'
```

`<studio-api-host>` is `composable-studio-api.contentstack.com` on prod NA (`eu-`, `azure-na-`, `azure-eu-`, `gcp-na-`, `gcp-eu-` prefixes for the other regions), and the host Contentstack supplied on a custom / private data center (§ Custom / private data center). The auth ladder, plus two token-free ways to enumerate projects (`csdx studio:project:set` with a deliberately invalid id, and Studio's own project switcher), are in [`configure-studio`](configure-studio.md#select-the-studio-project). Don't re-derive them here.

**Branch on the count:**

| Projects found | What to do |
|---|---|
| **0** | There is nothing to point the SDK at. Run [`provision-studio-project`](provision-studio-project.md) first, then come back |
| **1** | Use it, and **state which** ("Using project `<name>` (`<uid>`), content type `<contentTypeUid>`"). Never adopt it silently |
| **2 or more** | **STOP and ask.** Print a numbered list with name, uid, connected stack and `contentTypeUid`, and let the user pick **by number**. You already hold every uid, so never make them paste one. Never guess from a name that resembles the repo |

**Record two values for the rest of the run**, and don't re-ask for either:

- `studioProjectId` — the chosen project's `uid`. Hand it to [`configure-studio`](configure-studio.md), [`setup-section-preview`](setup-section-preview.md) and every later skill.
- `studioContentTypeUid` — the chosen project's **`contentTypeUid`, verbatim**. Only when the listing shows that field empty or absent does the project genuinely fall back to `compositions`, and only then is `compositions` the right value to write.

**Cross-check the project against the stack before writing any file.** Its `connectedStackApiKey` must equal the `<stackApiKey>` you were given. If they differ, stop and say so: installing against a project bound to a different stack yields an empty compositions list and **HTTP 412 "We can't find that Stack"** at runtime ([`troubleshoot-canvas`](troubleshoot-canvas.md)), and no SDK-side config fixes it.

### 1. Greenfield path: only after § 0 confirms no existing integration

1. **Detect the framework.** Look in `package.json` `dependencies` for one of:
   - `next` means Next.js (App Router or Pages Router. Detect via `app/` vs `pages/`)
   - `vite` means Vite (probably with React)
   - `react-scripts` means CRA
   - `@remix-run/*` means Remix
   - `astro` means Astro
   - anything else: ask the user which framework / report unsupported and stop.

   **Next.js advisory check.** If `next@14.2.x` is present, ensure the patch version is `>= 14.2.25`. Earlier `14.2.x` patches (including the `create-next-app` default `14.2.18`) are affected by CVE-2025-29927 (middleware authorization bypass). Bump to the latest patched `14.2.x` (stays React-18 + App-Router compatible, no migration needed). Print the recommendation. Let the user run the bump.

2. **Detect the package manager.** `pnpm-lock.yaml` means pnpm, `yarn.lock` means yarn, and neither means npm.

3. **Pre-flight: validate credentials before writing any code.** Make a CMA call to confirm `stackApiKey` + `deliveryToken` work:
   ```
   GET https://cdn.contentstack.io/v3/content_types?include_count=true
   Headers:
     api_key: <stackApiKey>
     access_token: <deliveryToken>
   ```
   (Use the regional CDN host if `region != us`: `eu-cdn.contentstack.com`, `azure-na-cdn.contentstack.com`, `azure-eu-cdn.contentstack.com`, `gcp-na-cdn.contentstack.com`, `au-cdn.contentstack.com`.)

   If non-200, fail fast with a clear message: "Your Stack API Key or Delivery Token didn't validate. In your Stack's Settings, under Tokens, open Delivery and verify the values."

   Validate the Preview Token separately with [`verify-setup`](verify-setup.md) Layer 6: the regional preview host and a content-type entries endpoint. Do not substitute a preview token into this delivery-host schema request. A failure there does not establish that the preview token is invalid and must not trigger token replacement.

   **Then assert the target environment has a Base URL for the locale**, same call, `environments` endpoint, no extra credentials needed:
   ```
   GET https://cdn.contentstack.io/v3/environments
   Headers:
     api_key: <stackApiKey>
     access_token: <deliveryToken>
   ```
   (Same regional host rule as above.) In the response, find the environment named `<environment>` and check its per-locale URL for `<defaultLocale>`:
   ```jsonc
   { "environments": [
     { "name": "preview", "urls": [ { "locale": "en-us", "url": "" } ] }  // ← empty url is the failure
   ] }
   ```
   On a localized app (the `i18n` row from `analyze-project-fit` is not `none`), check `urls[]` for **every** locale the app serves, not only `<defaultLocale>`. A locale-prefixed app needs the prefix in each URL (`http://localhost:3000/en`, `http://localhost:3000/fr`). [`convert-project-to-studio`](convert-project-to-studio.md) § Step 3 has the map and the write. **Fail on any locale the app serves, not only the default.** If `urls[locale == L].url` is **empty or missing for ANY app locale `L`** (that is just `<defaultLocale>` on an un-localized app, and every mapped locale on a localized one), fail fast, do NOT proceed to install, and name the failing locale(s) rather than reporting the default:
   > Environment `<environment>` has no Base URL for locale(s) `<failing locales>`. Studio composes the canvas iframe address as **Base URL (this value) + Canvas URL (path)**, so an empty Base URL silently blocks the canvas later — for that locale only, which is why a passing default locale proves nothing about the rest. Studio's Settings, under Configuration, will refuse to save the Canvas URL with a "no base URL found" error that points at the wrong layer. Set it now in the Stack's **Settings**, under **Environments**: select **`<environment>`** and fill in the **URL for each failing locale** (e.g. `http://localhost:5173` for local dev, `http://localhost:5173/fr` on a locale-prefixed app), then re-run.

   This is the single most common cause of a blank canvas after a "successful" install. The data is right here in the pre-flight, so catch it now rather than three skills later. See `setup-section-preview` and `configure-studio`, which also guard this.

4. **Confirm a single React major.** The SDK peer-deps `react ^18.0.0 || ^19.0.0`, so React 18 and React 19 both work. Do not downgrade a React 19 app. What matters is one copy.

   ```bash
   <pm> ls react   # must show exactly one entry, on 18.x or 19.x
   ```

   More than one entry: find the dep pulling the second copy, add `overrides` / `resolutions` pinning the app's version, reinstall, re-check. Pin exactly (`-E`) only when duplicates keep coming back. `@types/react` and `@types/react-dom` must match the installed major.

5. **Install Studio dependencies from public npm.**
   ```bash
   <pm> add @contentstack/delivery-sdk @contentstack/live-preview-utils @contentstack/studio-react
   ```
   Use `npm install` / `yarn add` / `pnpm add` as detected. Studio ships on public npm, no custom registry, `.npmrc`, or auth token needed. If you see instructions pointing at `npm.pkg.github.com` or a GitHub Personal Access Token, that's an internal-only registry mirror. Install from public npm instead.

6. **Create `src/lib/contentstack.ts`** (or `lib/contentstack.ts` for Next.js App Router, pick the right place based on the project's source layout).

   **IMPORTANT: pick ONE env-access syntax based on the framework detected in step 1. Do NOT mix `import.meta.env` and `process.env` in the same file: `import.meta.env` does not type-check or compile under Next.js (and `process.env` is undefined in Vite browser bundles).**

   Use this decision table:

   | Framework detected | Env prefix | Env access syntax |
   | --- | --- | --- |
   | `next` in deps | `NEXT_PUBLIC_` | `process.env.NEXT_PUBLIC_*` |
   | `vite` in deps | `VITE_` | `import.meta.env.VITE_*` |
   | `react-scripts` (CRA) | `REACT_APP_` | `process.env.REACT_APP_*` |
   | `@remix-run/*` | (none, server env) | `process.env.*` |
   | `astro` | `PUBLIC_` | `import.meta.env.PUBLIC_*` |

   **Next.js variant** (emit this exact file body when `next` is in `package.json` dependencies):
   ```ts
   import Contentstack from "@contentstack/delivery-sdk";
   import { studioSdk } from "@contentstack/studio-react";

   const previewToken = process.env.NEXT_PUBLIC_CONTENTSTACK_PREVIEW_TOKEN;

   // Region → host derivation. NEVER hardcode `rest-preview.contentstack.com` —
   // that's US only; every other region 401s against it. Source: Regional host map above.
   const CDN_HOSTS = {
     us: undefined,
     eu: "eu-cdn.contentstack.com",
     "azure-na": "azure-na-cdn.contentstack.com",
     "azure-eu": "azure-eu-cdn.contentstack.com",
     "gcp-na": "gcp-na-cdn.contentstack.com",
     "gcp-eu": "gcp-eu-cdn.contentstack.com",
     au: "au-cdn.contentstack.com",
   } as const;
   const PREVIEW_HOSTS = {
     us: "rest-preview.contentstack.com",
     eu: "eu-rest-preview.contentstack.com",
     "azure-na": "azure-na-rest-preview.contentstack.com",
     "azure-eu": "azure-eu-rest-preview.contentstack.com",
     "gcp-na": "gcp-na-rest-preview.contentstack.com",
     "gcp-eu": "gcp-eu-rest-preview.contentstack.com",
     au: "au-rest-preview.contentstack.com",
   } as const;
   const region = (process.env.NEXT_PUBLIC_CONTENTSTACK_REGION ?? "us") as keyof typeof PREVIEW_HOSTS;
   const cdnHost = CDN_HOSTS[region];
   const previewHost = PREVIEW_HOSTS[region];

   export const stack = Contentstack.stack({
     apiKey: process.env.NEXT_PUBLIC_CONTENTSTACK_API_KEY!,
     deliveryToken: process.env.NEXT_PUBLIC_CONTENTSTACK_DELIVERY_TOKEN!,
     environment: process.env.NEXT_PUBLIC_CONTENTSTACK_ENVIRONMENT!,
     region,
     ...(cdnHost ? { host: cdnHost } : {}),
     // Live Preview block ONLY when a preview token is present. With an empty token the
     // Delivery SDK init fails — and we don't want LP failure to break the SDK either.
     ...(previewToken ? {
       live_preview: {
         enable: true,
         preview_token: previewToken,
         host: previewHost,
       },
     } : {}),
   });

   // Live Preview init is async and caught, so an LP failure (bad token, LP not enabled
   // on the stack, network) NEVER blocks studioSdk.init below. A common failure mode:
   // ContentstackLivePreview.init() throws → studioSdk.init() is unreachable → Studio
   // canvas shows "SDK Not Initialized" even though the SDK itself was fine.
   // Import it ONLY with a preview token: live-preview-utils (4.5.3) draws its Edit
   // button on import, even without init(), so visitors would see it in production.
   if (previewToken && typeof window !== "undefined") {
     import("@contentstack/live-preview-utils")
       .then(({ default: ContentstackLivePreview }) =>
         ContentstackLivePreview.init({
           enable: true,
           mode: "builder",   // default "preview" never starts Visual Editor's editing layer
           ssr: true,         // false for CSR / static apps
           stackDetails: {
             apiKey: process.env.NEXT_PUBLIC_CONTENTSTACK_API_KEY!,
             environment: process.env.NEXT_PUBLIC_CONTENTSTACK_ENVIRONMENT!,
           },
           clientUrlParams: { host: "<region-app-host>" }, // e.g. app.contentstack.com (NA), eu-app.contentstack.com (EU)
           editButton: { enable: true, exclude: ["outsideLivePreviewPortal"] },
           editInVisualBuilderButton: { enable: false }, // else a "Start Editing" link on every page
         }),
       )
       .catch((err) => console.warn("[studio] Live Preview init failed; continuing without LP.", err));
   }

   export const sdk = studioSdk.init({
     stackSdk: stack,
     // The literal is `studioContentTypeUid` from § 0c — the chosen project's own
     // contentTypeUid. Write `"compositions"` here ONLY if that is what the project
     // actually reported; a guess surfaces as "Content Types Don't Match" in Studio.
     contentTypeUid: process.env.NEXT_PUBLIC_CONTENTSTACK_STUDIO_CONTENT_TYPE ?? "<studioContentTypeUid>",
     // Emits the data-cslp attributes Visual Editor needs to map a DOM node back
     // to its field. Off by default: the renderer checks `config.cslp.appendTags`
     // before attaching either attribute bag, so with this absent NO component
     // gets a tag no matter how correctly it spreads them, and the page opens in
     // VB with nothing editable. Set it at install time, once, for every project.
     cslp: { appendTags: true },
     // Add `fetchTemplateEntry` here so a new entry is editable on the page before anyone
     // types into it: see `make-visual-editor-editable` § 4.
   });

   export { studioSdk };
   ```

   **Vite variant** (emit this exact file body when `vite` is in `package.json` dependencies / devDependencies):
   ```ts
   import Contentstack from "@contentstack/delivery-sdk";
   import { studioSdk } from "@contentstack/studio-react";

   const previewToken = import.meta.env.VITE_CONTENTSTACK_PREVIEW_TOKEN;

   // Region → host derivation. NEVER hardcode `rest-preview.contentstack.com` —
   // that's US only; every other region 401s against it. Source: Regional host map above.
   const CDN_HOSTS = {
     us: undefined,
     eu: "eu-cdn.contentstack.com",
     "azure-na": "azure-na-cdn.contentstack.com",
     "azure-eu": "azure-eu-cdn.contentstack.com",
     "gcp-na": "gcp-na-cdn.contentstack.com",
     "gcp-eu": "gcp-eu-cdn.contentstack.com",
     au: "au-cdn.contentstack.com",
   } as const;
   const PREVIEW_HOSTS = {
     us: "rest-preview.contentstack.com",
     eu: "eu-rest-preview.contentstack.com",
     "azure-na": "azure-na-rest-preview.contentstack.com",
     "azure-eu": "azure-eu-rest-preview.contentstack.com",
     "gcp-na": "gcp-na-rest-preview.contentstack.com",
     "gcp-eu": "gcp-eu-rest-preview.contentstack.com",
     au: "au-rest-preview.contentstack.com",
   } as const;
   const region = (import.meta.env.VITE_CONTENTSTACK_REGION ?? "us") as keyof typeof PREVIEW_HOSTS;
   const cdnHost = CDN_HOSTS[region];
   const previewHost = PREVIEW_HOSTS[region];

   export const stack = Contentstack.stack({
     apiKey: import.meta.env.VITE_CONTENTSTACK_API_KEY!,
     deliveryToken: import.meta.env.VITE_CONTENTSTACK_DELIVERY_TOKEN!,
     environment: import.meta.env.VITE_CONTENTSTACK_ENVIRONMENT!,
     region,
     ...(cdnHost ? { host: cdnHost } : {}),
     // Conditional LP block — see Next variant above for rationale
     ...(previewToken ? {
       live_preview: {
         enable: true,
         preview_token: previewToken,
         host: previewHost,
       },
     } : {}),
   });

   // LP init failure must never block studioSdk.init below
   // Only with a preview token (see the Next variant above).
   if (previewToken) {
     import("@contentstack/live-preview-utils")
       .then(({ default: ContentstackLivePreview }) =>
         ContentstackLivePreview.init({
           enable: true,
           mode: "builder",   // see the Next variant above
           ssr: false,
           stackDetails: {
             apiKey: import.meta.env.VITE_CONTENTSTACK_API_KEY!,
             environment: import.meta.env.VITE_CONTENTSTACK_ENVIRONMENT!,
           },
           clientUrlParams: { host: "<region-app-host>" }, // e.g. app.contentstack.com (NA), eu-app.contentstack.com (EU)
           editButton: { enable: true, exclude: ["outsideLivePreviewPortal"] },
           editInVisualBuilderButton: { enable: false },
         }),
       )
       .catch((err) => console.warn("[studio] Live Preview init failed; continuing without LP.", err));
   }

   export const sdk = studioSdk.init({
     stackSdk: stack,
     // `studioContentTypeUid` from § 0c — see the Next variant above. Not a guess.
     contentTypeUid: import.meta.env.VITE_CONTENTSTACK_STUDIO_CONTENT_TYPE ?? "<studioContentTypeUid>",
     // ⛔ Do NOT omit — see the Next variant above. Without `appendTags` no
     // bound value carries `data-cslp` and nothing is editable in Visual Editor.
     cslp: { appendTags: true },
   });

   export { studioSdk };
   ```

   For CRA / Remix / Astro, follow the same pattern using the table above, emit a single env-access syntax matching the detected framework. Never emit both `import.meta.env` and `process.env` references for the same variable.

   `export const sdk = studioSdk.init(...)`: the return value is the live SDK that downstream skills call (`sdk.fetchCompositionData(...)`). The `studioSdk` namespace export is un-initialized.

7. **Create `.env.local`** (gitignored) with the collected values:
   ```
   <PREFIX>_CONTENTSTACK_API_KEY=<stackApiKey>
   <PREFIX>_CONTENTSTACK_DELIVERY_TOKEN=<deliveryToken>
   <PREFIX>_CONTENTSTACK_PREVIEW_TOKEN=<previewToken>
   <PREFIX>_CONTENTSTACK_ENVIRONMENT=<environment>
   <PREFIX>_CONTENTSTACK_DEFAULT_LOCALE=<defaultLocale>
   <PREFIX>_CONTENTSTACK_STUDIO_CONTENT_TYPE=<studioContentTypeUid>
   ```

   The last one is the `contentTypeUid` from § 0c. The init file reads it, so omitting it silently falls through to the literal in `studioSdk.init` — which is exactly how a project on `<user>_compositions` ends up asking for `compositions`.
   Add `.env.local` to `.gitignore` if not already there.

   **`.env.local` shadowing trap.** Vite (and CRA, Next) load env files in this order: `.env`, then `.env.local`, then `.env.[mode]`, then `.env.[mode].local`, with later files **overriding earlier ones for the same key**. `.env.local` is loaded in every mode (dev AND build) and silently wins over `.env`. The trap pattern: a project re-provisions and writes fresh values to `.env`, but a stale `.env.local` (left from a previous run, perhaps with `<PREFIX>_CONTENTSTACK_PREVIEW_TOKEN=undefined` literally as a string) still exists and overrides them. Two distinct failure signatures for the same root cause:

   - **Stale bad preview token**: canvas iframe throws **HTTP 401** from `rest-preview.contentstack.*` with no CORS headers, which produces "Component Loading Error" on a project that worked yesterday.
   - **Stale stack api_key from a copied project**: the app initializes the OLD stack while Studio's project points at the NEW one, which produces **HTTP 412 "We can't find that Stack. Please try again."** on the CMA and **"No composition for /…"** at runtime. Especially common when scaffolding a new project by copying a working app's directory. <!-- style-lint: allow -->

   Mitigation:
   - When provisioning writes `.env`, **also delete** any stale `.env.local` (or rewrite it from `.env.example`).
   - Never let `.env.local` carry `<key>=undefined` or `<key>=` (empty). The SDK init can't distinguish a literal `"undefined"` string from a real token and the CDA rejects it.
   - After writing env files, log its presence once via `console.log(Boolean(import.meta.env.<PREFIX>_CONTENTSTACK_PREVIEW_TOKEN))` (never the token itself) to confirm it resolved, then remove the log before claiming setup succeeded.

8. **Wire the import** at the app shell so init runs once. The right file depends on framework:
   - **Next.js App Router**: **DO NOT import `@/lib/contentstack` directly in `app/layout.tsx`.** `layout.tsx` is a Server Component. A side-effect import there runs `studioSdk.init` / `ContentstackLivePreview.init` on the server, where the canvas iframe never sees them. Studio loads with no SDK in the client realm and `<StudioCanvas />` errors. Instead, create a tiny client boundary:
     ```tsx
     // app/studio-init.tsx
     "use client";
     import "@/lib/contentstack";   // side-effect import — runs init in the client bundle
     export function StudioInit() { return null; }
     ```
     ```tsx
     // app/layout.tsx (Server Component — no "use client")
     import { StudioInit } from "./studio-init";
     export default function RootLayout({ children }: { children: React.ReactNode }) {
       return (
         <html><body>
           <StudioInit />
           {children}
         </body></html>
       );
     }
     ```
     `StudioInit` renders `null`. Its only job is to carry the side-effect import into the client module graph so the SDK initializes where the canvas runs.
   - **Next.js Pages Router**: the rule is **`studioSdk.init()` must complete before `<StudioCanvas>` mounts**. Any top-level side-effect import in a module that evaluates first satisfies it. `pages/_app.tsx` is the natural home because it's the client entry. What breaks the rule:
     - Init inside a `useEffect` fires **after** render commits. Canvas has already mounted and posted `ready`, which leaves **"Canvas Component Did Not Load"** with no other symptom.
     - Init inside a dynamic `import()` awaited before render, WHEN the canvas is also `dynamic({ ssr:false })`. Both are async, they race, canvas usually wins.

     ```tsx
     // pages/_app.tsx
     import "@/lib/contentstack";   // top-level, synchronous — NOT in useEffect, NOT dynamic import
     import type { AppProps } from "next/app";
     export default function App({ Component, pageProps }: AppProps) {
       return <Component {...pageProps} />;
     }
     ```

     If you can't reason about module-graph ordering (or the canvas is very deeply lazy-loaded), a defensive move is to duplicate the top-level static import in the file that renders `<StudioCanvas>`. Same-module init is the strongest guarantee, though usually not required.
   - Vite / CRA: import in `src/main.tsx` or `src/index.tsx`.
   - Remix: import in `app/root.tsx`.

   Add `import "@/lib/contentstack";` near the top of that file (no destructuring. The side-effects matter).

9. **For Vite projects: serve a PROD BUILD to the canvas (not the dev server).**

   Vite's dev optimizer can pre-bundle the SDK with a separately-loaded React (different `?v=hash`) and break hook calls. Studio's canvas throws "Invalid hook call". `resolve.dedupe` / `optimizeDeps.include` only partially help. The reliable fix is `vite preview`.

   - Add to `vite.config.*` as defense-in-depth (does NOT replace the prod-build rule):
     ```ts
     resolve: { dedupe: ['react', 'react-dom'] },
     optimizeDeps: {
       include: [
         'react', 'react-dom',
         '@contentstack/delivery-sdk',
         '@contentstack/live-preview-utils',
         '@contentstack/studio-react',
       ],
     },
     ```
   - **Serve via `vite preview`:** `<pm> build && <pm> exec vite preview --port <port>`. Verify in DevTools, on the Network tab: files look like `assets/<chunk>-<hash>.js` with NO `?v=<hash>` query strings.

10. **Continue the setup workflow.** When called for whole-project setup, return to `convert-project-to-studio` and execute canvas routing, template routing, configuration, and verification with the choices already resolved there. Do not stop after installing packages. For an explicit SDK-only request, report the SDK installation and list these remaining capabilities:
   ```
   Studio + Live Preview + Delivery SDK installed.

   Next:
     1. Open Studio at <studio URL — usually https://app.contentstack.com/#!/studio>
     2. Select project <studioProject name> (<studioProjectId>) — the one this install points at
     3. REQUIRED — run `setup-section-preview` to add the /canvas route (mounts <StudioCanvas />).
        Not optional: Section authoring needs it, and a later catch-all route will claim /canvas
        if nothing owns it.
     4. (Optional) Run `setup-local-https-canvas` ONLY if your app needs HTTPS-on-localhost for service workers, secure cookies, or strict policy. Plain `http://localhost:<port>` works for Studio's iframe — browsers treat localhost as a trusted origin.
     5. Wire Studio into routing — run `setup-template-preview-routes`. It asks wildcard (one
        catch-all owns every URL) vs dedicated per-pattern routes, and in wildcard mode also
        wires header/footer preservation and 404 handling.
   ```

## Inputs needed from the user

In this order. Stop and ask the user if any is missing. DO NOT proceed without them.

1. `stackApiKey`: Stack API Key
2. `deliveryToken`: Delivery Token (sensitive)
3. `previewToken` (Preview Token (sensitive)) paired with the same Delivery Token record
4. `environment`: Environment name
5. `defaultLocale`: default to `en-us` if unsure
6. `region`: default to `us`
7. `studioProject`: which Studio project this app renders. **Ask if it wasn't supplied** — § 0c lists them and branches on the count. There is no safe default

Tokens (2 and 3): reuse the delivery token `enable-visual-experience` created, or let it create one by API (§ 0a). Ask the user only if both fail.

`studioContentTypeUid` is NOT an input: it is **derived** from the chosen project's `contentTypeUid` in § 0c. Never ask the user for it, and never assume `compositions`.

If the user doesn't know where to find them, point them at:
- Stack credentials: on `app.contentstack.com`, go to the org dashboard, open Headless CMS and pick the stack. Then use **More**, **Settings**, **Tokens** and click an existing Delivery Token to see all three values in one form
- Environment list: the same Settings sidebar, under **Environments**
- Studio projects: the project switcher in Studio's top bar, or the `GET /v1/projects` listing in § 0c

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, do not claim success. Surface the failure and stop.

- [ ] `analyze-project-fit` was run and chose Path A or D (otherwise install would have been blocked)
- [ ] `<pm> ls react` shows exactly one React entry (18.x or 19.x), and `@types/react` + `@types/react-dom` match that major
- [ ] `<pm> ls react` shows a single tree entry (18.x or 19.x, no duplicates)
- [ ] `package.json` lists all three Contentstack packages in `dependencies`
- [ ] Delivery credentials passed the delivery read; preview credentials passed `verify-setup` Layer 6 on the preview host. These are separate checks.
- [ ] The target environment has a non-empty Base URL for **every locale the app serves** (asserted from the `environments` pre-flight — the default locale alone is not enough on a localized app), or the user was told which locales are missing and stopped
- [ ] `src/lib/contentstack.ts` (or framework equivalent) exists with the three SDK inits
- [ ] **`cslp: { appendTags: true }` is set in `studioSdk.init`**. Every Studio project is a Visual Editor project. With this off or absent, `studioAttributes` and every `$`-twin arrive empty across the whole app and no component-level fix helps. See [`complete-the-build`](complete-the-build.md) item 1.
- [ ] Live Preview init is wrapped in **try/catch** and the `live_preview` block on the stack is **conditional on a non-empty preview token**
- [ ] **A Studio project was resolved from an actual `GET /v1/projects` listing, not assumed.** With 2+ projects the user picked; with exactly 1 it was named back to them. Its `connectedStackApiKey` equals `<stackApiKey>`
- [ ] **`contentTypeUid` in the init file equals the chosen project's `contentTypeUid`** (compare the emitted file against the listing — `grep contentTypeUid src/lib/contentstack.ts`). If it reads `compositions`, that is correct ONLY when the project reported `compositions`
- [ ] `.env.local` exists with the six `<PREFIX>_CONTENTSTACK_*` vars, including `_STUDIO_CONTENT_TYPE`
- [ ] `.gitignore` includes `.env.local`
- [ ] The app shell imports `@/lib/contentstack` for side-effect init. For Next.js App Router specifically, the import lives in a `"use client" StudioInit` component rendered from `app/layout.tsx`, NOT a direct side-effect import in the layout itself.
- [ ] For Vite: `resolve.dedupe` + `optimizeDeps.include` are set. The user has been told to serve a prod build (`vite preview`) to the Studio canvas
- [ ] `<pm> run dev` (or `vite preview` for the canvas) starts without runtime errors
- [ ] **Asserted from the rendered page, not from the source:** once a composition renders at a URL, `curl -s <url> | grep -c 'data-cslp'` returns a number greater than zero. Zero means bound values are reaching the DOM with no edit anchor. Visual Editor shows the page and refuses to edit it. Check `appendTags` above first, then the component's `$`-prefixed props ([`register-component`](register-component.md) § CSLP tags). If no composition exists yet, defer this check to [`verify-setup`](verify-setup.md) and say so.

If acceptance fails, do not silently move on. Report exactly which step broke and stop so the user can intervene.

## After install: if Studio says "Content Types Don't Match"

A dialog over the canvas: *"Studio is set up for the content type `<expected>`, but the code on your site is asking for `<actual>`."* **Expected** is the Studio project's `contentTypeUid`; **Actual** is what `studioSdk.init` passed. Nothing renders until they agree.

Fix it on the SDK side, not by renaming the content type: set `contentTypeUid` (and `<PREFIX>_CONTENTSTACK_STUDIO_CONTENT_TYPE` in `.env.local`, which overrides it) to the **Expected** value the dialog names, then restart the dev server — env files bake in at start time. If both look right in the source, check for a stale `.env.local` shadowing `.env` (§ step 7).

Two causes worth telling apart, because the fix differs:

- **The install guessed.** § 0c was skipped, so the init fell through to a literal `"compositions"` while the project was provisioned as `<user>_compositions`. Re-run § 0c and rewrite the value.
- **The app points at the wrong project.** The uid it asks for is real, just owned by a different Studio project on the same stack. Re-select the project ([`configure-studio`](configure-studio.md#select-the-studio-project)) before touching the SDK config, or you will bind the app to the wrong compositions.

## After install: if you see "SDK Not Initialized" in Studio

**Do NOT re-run this skill.** The popup is misleading. It usually means a Template URL match failed, not a broken SDK install. See `troubleshoot-canvas` § Run this FIRST: the section-test pre-flight. If Sections render, jump to `troubleshoot-composition-resolution`. Only if Sections also fail should you re-check this skill's acceptance steps.

## After install (minimal-add branch): if Live Preview intermittently doesn't apply

Same fetch, same hash, sometimes hits `rest-preview.contentstack.com` and sometimes falls back to `cdn.contentstack.io`, with no code change in between. This is the shared-stack hazard flagged in § Existing Contentstack app? Take the minimal-add branch above: something else in the app calls `.livePreviewQuery(...)` on the same stack instance Studio's SDK uses, resetting the shared preview state mid-request. Do NOT chase this as a token or Studio-config problem. See `troubleshoot-canvas` § Live Preview state resets mid-request for the diagnostic and the fix (give Studio's `stackSdk` its own stack instance).

## After install: if the Design tab is missing / disabled

Not a broken install, three separate gates control the Design tab:

1. **Design tab missing entirely** (right panel is Settings only) means **Enable Freeform Feature** is off on the Studio project. Toggle it in Studio's Settings, under Configuration, or PUT `settings.configuration.isFreeformEnabled: true` via the Studio API.
2. **Design tab present but every control looks disabled / read-only** means `registerDesignTokens(tokens)` was called **without** the options arg. `allowedValuesLevel` defaults to `"dynamic"` which permits data-binding only, not token selection. **Fix:** always pass `{ allowedValuesLevel: "tokens" }` as the second arg. See [`import-design-tokens`](import-design-tokens.md) for the full token payload shape.
3. **Design tab appears but is empty for one specific component** means that component's `registerComponent` schema didn't declare a `styles` block. See [`register-component`](register-component.md) § Design panel: component must declare `styles`.

## See also

- Pair with `setup-section-preview` to add the Canvas route next.
- Use `verify-setup` to run a layered end-to-end smoke test after install.
- Use `troubleshoot-canvas` if the canvas iframe doesn't render after both skills are run.
