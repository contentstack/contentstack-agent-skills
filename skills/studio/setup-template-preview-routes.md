---
name: setup-template-preview-routes
---

## When to use

Wire Studio into the app's routing: a CATCH-ALL (wildcard) route so every visitor URL resolves through `<StudioComponent />`, or dedicated per-pattern routes. Asks which. Wildcard mode also wires site chrome (header/footer) preservation and 404 handling.

Use when adding Studio-rendered template routes (Vite/React Router or Next.js App Router), seeing "Template did not load" / "NO_COMPOSITION_FOR_URL" on a template URL, or finishing the Studio setup chapter (after `install-studio` + `setup-section-preview`). Phrases: "make every URL go through Studio", "wire catch-all template route", "wildcard or single page", "template URL 404s", "header/footer disappeared after adding Studio", "my 404 page stopped working", "duplicate header on Studio pages". Skip if only the section-authoring `/canvas` route is needed (that's `setup-section-preview`).

> **STOP before writing any file.** Ask: (1) one catch-all route for every URL, or dedicated routes such as `/blog/*`; (2) which paths to keep out; (3) whether the header and footer stay in code or become Studio Sections. Wait for the answers. Skip what `convert-project-to-studio` already settled.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Wire template preview routes

**Caller context:** when `convert-project-to-studio` has resolved minimal setup, inherit its wildcard, code-owned chrome, and locale choices. Do not repeat the route-mode question. Ask only for choices not already settled by the user or caller.

**Editor rendering note:** the simplified no-spec examples below are not sufficient evidence of working preview. A plain `<div />` does not mount `StudioComponent` or start its editor bridge. Preserve valid `specOptions` (including `fetchOptions`) and let the renderer handle its supported editor mode. If resolution throws before producing those options, use only a fallback verified against the installed SDK; do not fabricate options or mark an empty 200 response successful. The unsaved-template browser check in `verify-setup` must pass before claiming preview is complete.

## Context

The user has Studio installed (`install-studio`). The `/canvas` section-authoring route (`setup-section-preview`) is a hard requirement of this skill. Step 2 creates it if it's missing rather than bailing, because a catch-all silently claims `/canvas` when no route owns it. They now need to wire Studio as the **default renderer for every URL on the site**, so any published composition resolves to its template automatically, and any opened template in Studio's iframe renders live.

**Catch-all is the recommended default, not mandatory, and on an existing app it's a question, not an assumption (step 3).** A catch-all doesn't just add Studio. It takes over every URL the app didn't explicitly claim, which is why wildcard mode carries the extra chrome + 404 work in step 5a. This skill registers ONE route matching every URL. Studio resolves the composition by URL at render time via `sdk.fetchCompositionData({ url, searchQuery })`. With no match, **the call rejects** (it does not resolve null), which the catch-all must translate into a 404, see step 5a (iii). Per-template route registration is **not needed** (Studio's URL patterns handle matching internally), but it's valid if you have a reason (see below).

**When dedicated routes are a fit instead of the catch-all:**
- You're adding Studio to an existing app where you want explicit control over which URL patterns route through Studio (e.g. `app/blog/[slug]/page.tsx` mounting `<StudioComponent />` for blog posts only, while `/products/*` stays on hand-coded pages).
- Your routing layer has constraints catch-all can't satisfy (route-level middleware, per-route auth, framework-specific data fetching that varies by URL shape).
- You're gradually migrating from hand-coded pages, each new dedicated `<StudioComponent />` route replaces one set of hand-coded pages.

For dedicated routes: mount `<StudioComponent />` (with the request URL passed to `sdk.fetchCompositionData({ url, searchQuery })` or `useCompositionData`). The renderer handles iframe preview and visitor render the same way. A dedicated per-pattern route is functionally identical to Studio.

**Opt-outs are explicit (catch-all mode only).** If the user has paths that must NOT go through Studio (`/api/*`, `/admin/*`, custom static pages), this skill registers those routes ahead of the catch-all so they take precedence. Dedicated-route mode doesn't need opt-outs, only the URLs you explicitly route through `<StudioComponent />` go through Studio.

The skill emits route code that mounts `<StudioComponent />` for the URL. The same component handles both direct visitors (rendering the deployed composition from CDA) and in-Studio iframe preview (rendering the unsaved working spec). Mode-switching happens inside the renderer. You do not branch on iframe context in your route code. The separate `/canvas` route (from `setup-section-preview`) is the only place `<StudioCanvas />` appears.

There are TWO Studio React components in play:

- **`<StudioComponent />`**: the renderer for visitor routes (`/blog/:slug`, the catch-all, etc.). Reads a published composition spec from CDA via `sdk.fetchCompositionData({ url, searchQuery })` (or `useCompositionData`) and renders it. When Studio loads the same URL in its iframe, it switches modes internally to show the unsaved spec. Your code does nothing different.
- **`<StudioCanvas />`**: the dedicated section-preview iframe target. Mount it once at `/canvas` (per `setup-section-preview`). Studio's Canvas URL config points here. You do NOT mount `<StudioCanvas />` on visitor routes.

## Failure signatures: all mean "no `<StudioComponent>` at the template's URL"

Before running the Task steps, know the failure modes. These three symptoms have ONE root cause: a Connected template's URL isn't served by a route mounting `<StudioComponent>`.

| Symptom in Studio's canvas / on the deployed site | Root cause |
|---|---|
| Studio previews **the existing hand-coded page** (looks correct but authoring changes don't reflect) | The template's URL is served by a legacy hand-coded route the catch-all/dedicated Studio route hasn't replaced. Studio's iframe renders the legacy route as-is. |
| Studio shows **"Template Did Not Load"** or a **404** in the iframe on a template URL you just created | No route in the app matches that URL, or the matching route returns empty because `<StudioComponent>` never mounts. |
| Studio shows **"SDK is not initialized"** on the template URL | A route matches the URL but doesn't import the module where `studioSdk.init()` runs (`lib/studio.ts` in the standard install). `<StudioComponent>` requires init to have happened by mount time. Init only runs when the module is imported. |

Fix, in order: (1) a route in the app matches the template's URL, (2) that route mounts `<StudioComponent>` (directly or via a wrapper that does), (3) that route's module tree imports the module that runs `studioSdk.init()`. All three must hold before authoring a Connected template.

## Task

1. **Confirm prerequisites.** Bail with a clear message if any of these are missing:
   - `@contentstack/studio-react` is in `package.json` dependencies.
   - `studioSdk.init(...)` runs at the app shell (created by `install-studio`).
   - Components are registered before Studio mounts (project-specific `registerComponents()` call).
   - Env vars are set: stack API key, delivery token, preview token, environment, region, branch (using the framework's prefix: `VITE_`, `NEXT_PUBLIC_`, etc.).
   - **The environment base URL matches the served canvas-app's scheme.** Studio iframes connected-template previews at the env base URL (the `urls[].url` value from `GET /v3/environments/<env>`), NOT at `canvasUrl`. If the env is `http://localhost:5173` but your dev server is HTTPS-only (mkcert), the iframe gets nothing back and Studio shows "SDK Not Initialized" on connected templates while sections still render fine. **Fix:** `PUT /v3/environments/<env>` so `urls[].url` matches the canvas-app's scheme (HTTPS for local mkcert dev).
   - **One env Base URL serves all Studio projects on the stack.** The env URL is a **stack-level** resource. Multiple Studio projects on one stack share the single `urls[].url` per locale. If you're running two or more Studio projects against different local apps (e.g. project A on `:5192`, project B on `:3000`), they CANNOT both preview at once on the same environment. Pick separate environments per project (recommended: create `<project>_preview` for each) or separate stacks. See [`configure-studio`](configure-studio.md) § Common pitfalls for the full rationale + three options.

2. **COMPULSORY: the `/canvas` route must exist. Create it if it doesn't. Never skip, never bail, never leave it for later.**

   This runs in **both** route modes and applies to **every** project, migration or greenfield. A Studio project without a canvas route cannot author Sections at all, and in wildcard mode its absence actively breaks things (below). Detect:

   ```bash
   # Search by CONTENT, not by guessed path — the mount is what matters.
   grep -rln "StudioCanvas" app src pages 2>/dev/null
   # Then locate the route file, wherever it lives:
   find app src pages -path "*canvas*" \( -name "page.*" -o -name "*Canvas*" -o -name "canvas.*" \) 2>/dev/null | head
   ```

   **Do not conclude "no canvas route" from a fixed path list.** Real projects put it at `src/app/canvas/`, `app/(studio)/canvas/`, `app/[locale]/canvas/` (locale-prefixed), `pages/canvas.tsx`, or a custom `canvasPath` entirely. **Runtime-verified false negative:** checking only `app/canvas/page.tsx` reported "no canvas route" on a project whose route was at `src/app/[locale]/canvas/page.js`, and acting on that would have created a duplicate. The `grep` for `StudioCanvas` is authoritative. The `find` only tells you where it is.

   | Result | Action |
   |---|---|
   | Route found + Studio's Canvas URL set to its path | Continue to step 3. |
   | Route found, Canvas URL not set in Studio | Run [`setup-section-preview`](setup-section-preview.md) step 4. The file alone is half the wiring. |
   | **Nothing found** | **Run [`setup-section-preview`](setup-section-preview.md) now, in full, then come back.** Do not emit any template route first. |

   `setup-section-preview` owns this route and everything around it: framework-correct file path, the client-only `dynamic({ ssr: false })` wrapper, chrome isolation, iframe-allowed headers, and the Canvas URL setting in Studio. Don't hand-roll a `/canvas` file here. Delegate.

   **Why this is compulsory in wildcard mode specifically.** A catch-all matches `/canvas` like any other URL. With no canvas route registered, `<Route path="*">` / `app/[[...slug]]/page.tsx` claims it, Studio's section iframe loads the catch-all, `fetchCompositionData({ url: "/canvas" })` finds no composition, and the author gets a blank frame, or (once step 5a's 404 handling lands) **your 404 page rendered inside Studio's section-authoring canvas**. Every Section in the project looks broken, and no error message points at routing. In dedicated mode nothing claims `/canvas`, so the shadowing failure doesn't occur. The route is still mandatory, just for the ordinary reason that Section authoring needs it.

3. **Ask which route mode: wildcard or single-page. Do not assume.**

   **This is a required gate on any app that already has pages.** Detect first, then ask, never wire a catch-all into an existing app without the user picking it, because the catch-all takes over every unmatched URL including the app's own 404.

   ```bash
   # How many pages does the app already own? Cover src/app and every extension —
   # Next projects use .js/.jsx as often as .tsx, and route groups / [locale]
   # segments mean the depth is unpredictable.
   find app src/app pages src/pages src/routes \
        \( -name 'page.*' -o -name 'index.*' -o -name '*Route.*' \) 2>/dev/null | head -30
   grep -rn "<Route" src app 2>/dev/null | head -20
   ```

   **A zero result here does NOT mean greenfield.** Verify before believing it: `ls src/app app pages 2>/dev/null`. Treating a false negative as greenfield skips the ask entirely and wires a catch-all into an app full of pages, which is the exact outcome this gate exists to prevent.

   Ask verbatim:

   > How should Studio be wired into your routing?
   >
   > **A. Wildcard (catch-all): RECOMMENDED.** One route matches every URL your code does not already claim. Your existing routes are untouched, because a more specific route wins over the catch-all. Studio resolves the matching template at render time via `sdk.fetchCompositionData({ url, searchQuery })`. You never register a template URL again, and new templates go live without a code change. Because it owns every unmatched URL, I'll also wire your site chrome (header/footer) and keep your existing 404 page (step 5a).
   >
   > **B. Single-page / dedicated routes: when you want pattern-level control.** Only the URL patterns you name mount `<StudioComponent />` (e.g. `/blog/*` through Studio, `/products/*` stays hand-coded). Nothing else can reach Studio, not even a new URL an author creates. You add a route per pattern as you migrate.
   >
   > Which one?

   **Default when the user has no preference:** **A**, on greenfield and on existing apps alike. On an existing app, A with `chromeOwner = code` and the existing 404 is the minimal conversion ([`convert-project-to-studio`](convert-project-to-studio.md)): code routes keep winning, Studio serves only the URLs nobody claimed. Take **B** when the user wants explicit control over which URL patterns may ever reach Studio, or a routing constraint (per-route middleware, auth) rules out a catch-all. B still consolidates to A later (see [`migrate-page-to-studio`](migrate-page-to-studio.md)).

   **If A (wildcard):** collect opt-outs, then run steps 4, 5, **5a (chrome + 404: mandatory)**, 6, 7.

   > Are there any paths that should NOT go through Studio? Examples: `/api/*` (API routes), `/admin/*` (admin pages), or any custom non-Studio pages.
   >
   > Leave empty (default) to keep the catch-all unrestricted. RECOMMENDED.

   Register any opt-outs ahead of the catch-all (step 5).

   **If B (single-page / dedicated):** collect the URL patterns to route through Studio. Run step 4, then register ONE route per pattern mounting the same shared component, skip the catch-all in step 5 and skip step 5a entirely (existing chrome and 404 keep working untouched. Nothing is being taken over). Opt-outs are meaningless in this mode, only the patterns you register go through Studio. Everything in steps 6 and 7 still applies.

4. **Create one shared route component.** Do NOT generate a separate page per template. Every template route uses identical wiring. One generic component handles all of them.

   **React Router (Vite/CRA) variant**: emit at the path the user chose (default `src/routes/LinkedRoute.tsx`):

   ```tsx
   import { useLocation } from "react-router-dom";
   import { StudioComponent, useCompositionData } from "@contentstack/studio-react";

   export function LinkedRoute() {
     const { pathname } = useLocation();
     const { specOptions, isLoading, error } = useCompositionData({ url: pathname });
     if (isLoading) return <div>Loading…</div>;
     if (error) return <div>No composition for {pathname}</div>;   // wildcard mode: replace with the classified 404 branch in step 5a (iii)
     if (!specOptions?.spec) return <div>Composition found but empty.</div>;
     return <StudioComponent specOptions={specOptions} />;
   }
   ```

   **Next.js App Router variant (SSR (recommended for SEO sites)**) fetch in a Server Component, branch in a `"use client"` wrapper. The CSR `useCompositionData` snippet further below is for **SPAs without SEO needs only**. App Router apps that care about SEO must use this server-side path.

   ```tsx
   // app/[[...slug]]/page.tsx — Server Component
   import { sdk } from "@/lib/contentstack";
   import { StudioRender } from "./StudioRender";
   export default async function Page({ params, searchParams }) {
     // Same fetch for visitor + in-Studio iframe — StudioComponent picks the
     // right render path internally. Forward the full request searchQuery so
     // Studio's iframe overrides (locale / variant / preview entry) reach the SDK.
     const { slug } = await params;   // a Promise on Next 15+
     const url = "/" + (slug ?? []).join("/");
     const searchQuery = new URLSearchParams((await searchParams) as Record<string, string>).toString();
     // Unwrapped for clarity — this call THROWS when no composition matches, so
     // shipping it as-is returns 500 on every unclaimed URL. Step 5a (iii) has
     // the production form using resolveComposition.
     const specOptions = await sdk.fetchCompositionData({ url, searchQuery });
     return <StudioRender specOptions={specOptions} />;
   }
   ```

   ```tsx
   // app/[[...slug]]/StudioRender.tsx — Client Component
   "use client";
   import { StudioComponent } from "@contentstack/studio-react";

   export function StudioRender({ specOptions, editorMode = false }: { specOptions?: any; editorMode?: boolean }) {
     // Missing options on a VISITOR render is a real bug — fail loudly rather than
     // serving an empty 200. Inside Studio's iframe the same state is legitimate:
     // an unsaved template has no published spec yet, so the editor path passes
     // `editorMode` and the guard stands down. Throwing there would turn the
     // editor exemption below (§ 5a) into a render-time error on every unsaved
     // template — the opposite of what that path exists to do.
     if (!editorMode && !specOptions?.fetchOptions) throw new Error("Studio render options are missing; verify editor bootstrap for the installed SDK.");
     // StudioComponent handles iframe context internally — same component on
     // visitor routes and inside Studio's preview iframe. Mount it even with no
     // spec: a bare `<div />` returns 200 without starting the editor bridge.
     // Confirm the no-spec form against the installed SDK (§ Editor-mode
     // detection) instead of fabricating options.
     return <StudioComponent specOptions={specOptions} />;
   }
   ```

   **App Router CSR variant (SPAs only (no SEO requirement)**) emit at `app/_components/LinkedRoute.tsx`, marked `"use client"`. Skip this for any visitor-facing site. The SSR pattern above is the default:

   ```tsx
   "use client";
   import { usePathname, useSearchParams } from "next/navigation";
   import { StudioComponent, useCompositionData } from "@contentstack/studio-react";

   export function LinkedRoute() {
     const pathname = usePathname();
     const searchParams = useSearchParams();
     return <VisitorComposition url={pathname} searchParams={searchParams} />;
   }

   function VisitorComposition({ url, searchParams }: {
     url: string;
     searchParams: URLSearchParams;
   }) {
     // Pass `searchQuery` as the raw URLSearchParams OBJECT — NOT a stringified
     // form and NOT omitted. Studio's editor-mode detection reads editor params
     // (see § Editor-mode detection below) directly off this object. The 1.5.x
     // .d.ts type says `URLSearchParamsString` but the object is what actually
     // works; passing the string form or omitting the arg breaks editing of
     // unsaved compositions.
     //
     // `extendQuery` merges into the CDA fetch. Keeping locale-only avoids
     // hydration mismatches from server-included fields.
     const { specOptions, isLoading, error } = useCompositionData({
       url,
       searchQuery: searchParams,
       extendQuery: { blog_post: { only: ["locale"] } },   // one entry per connected CT
     });
     if (isLoading) return <div>Loading…</div>;
     if (error) return <div />;                            // empty div, NOT null
     if (!specOptions?.spec) return <div />;               // canvas host needs a mount target
     return <StudioComponent specOptions={specOptions} />;
   }
   ```

   ### Why the `searchQuery` object + empty `<div>` matter

   - **`searchQuery` = raw URLSearchParams object.** When Studio's iframe loads the template URL, it appends editor-mode params. The SDK reads them off `searchQuery` to switch from "render deployed composition" to "render unsaved working spec." Omit `searchQuery` and the SDK falls through to the deployed path, which returns `null` on a not-yet-saved composition, so you get **"Template Did Not Load."**
   - **Return an empty `<div />` (not `null`) when there's no spec.** Studio's canvas host queries the mount target after route render. If there's nothing in the DOM it can't drive it, and Studio shows "SDK Not Initialized" or a blank error. An empty div gives it something to attach to. **In wildcard mode this applies to the editor iframe only**, for real visitors the no-spec branch must render the 404 page instead, or the site never 404s. Step 4a (iii) has the gated version. Use that one.
   - **`extendQuery` per connected CT.** Recommended; older docs snippets omit it. Restrict to `only: ["locale"]` to avoid over-fetching.

5. **Register the catch-all route: pick `[...slug]` vs `[[...slug]]` based on existing app pages.**

   #### Pre-step: detect existing root + specific routes (Next.js only)

   Before emitting the catch-all file, grep for existing routes so Next.js's root-collision rule (cited from [nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes](https://nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes): "with optional, the route without the parameter is also matched") is handled correctly:

   ```bash
   # Does a ROOT page already exist? Any extension, app/ or src/app/, and note that
   # a locale-prefixed app's root lives at app/[locale]/page.* — which still owns "/".
   find app src/app -maxdepth 2 -name 'page.*' 2>/dev/null
   ls pages/index.* 2>/dev/null

   # What other specific routes exist? (informational — they win by Next precedence)
   find app src/app pages -name 'page.*' 2>/dev/null | head -20
   ```

   **Getting this wrong causes the exact collision the rule below prevents.** `ls app/page.tsx` returns nothing on a project whose root is `src/app/[locale]/page.js`, you conclude greenfield, emit the optional `[[...slug]]`, and it collides with the root page that was there all along. **Runtime-verified false negative.** If the `find` shows any root-level `page.*`, treat the app as having a root page.

   **Branching rule:**

   | Signal | Catch-all file to emit |
   |---|---|
   | `app/page.tsx` (or `pages/index.tsx`) **exists** | `app/[...slug]/page.tsx`: **non-optional** catch-all. Does NOT match `/`. The existing root page keeps owning `/`. Coexists cleanly. |
   | No root page found, so greenfield-style | `app/[[...slug]]/page.tsx`: **optional** catch-all. Matches `/` AND all nested URLs. |
   | **Locale-prefixed app** (`app/[locale]/page.*` owns `/en`, `/fr`) | `app/[locale]/[...slug]/page.tsx`, **inside** the segment. Strip the prefix before building `url`, pass the mapped stack locale as `{ locale }`, forward `searchQuery` untouched. See [`convert-project-to-studio`](convert-project-to-studio.md) § Step 3 for the map and the Base URL rule. |

   Tell the user verbatim what you found:

   > Detected `app/page.tsx` (or whichever). Using **non-optional** `[...slug]` so it doesn't collide with your root page. Existing specific routes win by Next.js's standard precedence (more-specific route beats catch-all).

   #### Emit the route files

   **The canvas route must exist — its position does not matter.** React Router v6+ ranks routes by specificity, so `/canvas` beats `path="*"` wherever it sits in the table; Next.js does the same by its own precedence rules. (This repo's fixture runs `react-router-dom@7`.) What actually breaks is a **missing** route: with no `/canvas`, the catch-all owns it and Studio's section iframe renders a composition lookup (blank frame, or your 404) instead of `<StudioCanvas />`. Confirm it's there (step 1).

   **React Router**: in `src/main.tsx` (or wherever the route table lives), register the canvas route, any opt-outs, and the catch-all — order is not significant:

   ```tsx
   <Routes>
     {/* Section authoring. Must EXIST (position is irrelevant — routes are
         ranked); without it `path="*"` claims /canvas and Studio's section
         iframe renders a composition lookup instead of <StudioCanvas />. */}
     <Route path="/canvas" element={<CanvasRoute />} />

     {/* Opt-outs (only if user provided them; otherwise omit this block) */}
     <Route path="/api/*"   element={<NotFoundOrApiHandler />} />
     <Route path="/admin/*" element={<AdminApp />} />

     {/* DEFAULT — catch-all: every other URL flows through Studio */}
     <Route path="*" element={<LinkedRoute />} />
   </Routes>
   ```

   **Next.js App Router**: based on the detection above, create ONE catch-all file: `app/[...slug]/page.tsx` when an existing root page owns `/`, `app/[[...slug]]/page.tsx` on a greenfield app. Its body is the gated renderer in step 5a (iii).

   The catch-all itself must 404 unclaimed paths, but **only for real visitors**. See step 5a for the editor-mode gate. A bare `if (!specOptions?.spec) notFound();` 404s unsaved templates inside Studio's own iframe.

   Do NOT create `app/blog/[slug]/page.tsx`, `app/products/[sku]/page.tsx`, etc. The catch-all handles all of them. Studio's URL-pattern matching runs inside `sdk.fetchCompositionData({ url, searchQuery })`. The router doesn't need to know about each template.

5a. **Wildcard mode ONLY: preserve site chrome and 404. Mandatory. Do not skip.**

   A catch-all takes over every URL that isn't explicitly claimed. Two things silently disappear when it lands in an existing app: **the header/footer that used to be rendered by the pages it replaced**, and **the app's own 404 page** (the catch-all now matches the URLs that used to fall through to it). Neither throws an error. The site just renders bare compositions on every route and never 404s.

   #### (i) Decide who owns the chrome: code or Studio

   Ask verbatim:

   > Your header and footer: should they stay in code, or become Studio Sections that authors can edit?
   >
   > **Code-owned: RECOMMENDED when migrating an existing app.** Header/footer stay in your layout and wrap every Studio-rendered page. Zero authoring risk, nothing to rebuild. Authors edit page bodies only.
   >
   > **Studio-owned.** Header/footer become Sections placed on each template. Authors edit everything, including nav. Requires building those Sections first, and the code layout must stop rendering them or you'll get two of each.

   | Owner | Layout renders chrome? | Templates contain Header/Footer sections? | Cost |
   |---|---|---|---|
   | **Code** (default) | Yes | No | None, chrome keeps working as-is |
   | **Studio** | No, strip it | Yes, on every template | Build Header + Footer Sections first ([`build-section`](build-section.md)). Place them on each template |

   **Both owners at once produce a duplicated header and footer on every page.** Pick exactly one owner. If the user wants Studio-owned, do NOT strip the layout chrome until the Sections exist and are placed, otherwise the site ships headerless.

   #### (ii) Wire code-owned chrome so the catch-all inherits it

   First, find out whether the chrome is in a layout or repeated per page:

   ```bash
   # Next.js — is chrome in the root layout, or in individual pages?
   grep -n "Header\|Footer\|Nav" app/layout.tsx 2>/dev/null
   grep -rln "Header\|Footer" app/**/page.tsx src/pages/ 2>/dev/null | head
   # React Router — is chrome around <Routes>, or inside each page component?
   grep -n "Header\|Footer\|Outlet" src/App.tsx src/main.tsx 2>/dev/null
   ```

   | What you find | What to do |
   |---|---|
   | **Next.js, chrome in `app/layout.tsx`** | Nothing. The catch-all is nested under the root layout and inherits it automatically. Verify visually in step 7. |
   | **Next.js, chrome imported per `page.tsx`** | Lift it into `app/layout.tsx` (or a route-group layout), remove it from the individual pages. The catch-all replaces those pages. Per-page chrome dies with them. |
   | **React Router, chrome wraps `<Routes>` in `App.tsx`** | Nothing. Every route including the catch-all renders inside it. |
   | **React Router, chrome inside each page component** | Add a layout route (below) and nest the catch-all inside it. |

   React Router layout route, note `/canvas` stays **outside** it:

   ```tsx
   function SiteChrome() {
     return (
       <>
         <Header />
         <Outlet />   {/* Studio-rendered page goes here */}
         <Footer />
       </>
     );
   }

   <Routes>
     {/* /canvas must NOT be wrapped in site chrome — Studio's section-authoring
         iframe would render your header + footer around every section. */}
     <Route path="/canvas" element={<CanvasRoute />} />

     <Route element={<SiteChrome />}>
       <Route path="*" element={<LinkedRoute />} />
     </Route>
   </Routes>
   ```

   **`/canvas` outside the chrome is not cosmetic.** `<StudioCanvas />` renders one Section at a time inside Studio's authoring iframe. Wrapped in site chrome, every section is authored inside a full page header and footer. The section's own spacing, sticky behavior, and viewport measurements all read wrong. Same rule for Next.js: if `/canvas` sits under a layout that renders chrome, move it into a route group with a bare layout.

   #### (iii) Wire the 404, and exempt Studio's editor iframe

   The catch-all now owns unmatched URLs, so "no composition for this URL" is the site's 404 path. **Reuse the project's existing not-found page** (`app/not-found.tsx`, `pages/404.tsx`, the app's `NotFound` component, or the per-locale one under `app/[locale]/`). Create a new file only when none exists. **But the same no-spec condition happens legitimately inside Studio's iframe** for a template that hasn't been saved yet. 404 unconditionally and every unsaved template shows your 404 page in the canvas ("Template Did Not Load"). Gate on editor mode: reuse `isStudioEditorMode` from § Editor-mode detection below.

   **`fetchCompositionData` throws on a miss. It does not resolve with an empty spec.** A guard like `if (!specOptions?.spec) notFound()` never runs on the path it was written for. The `await` rejects first and the visitor gets a **500 instead of your 404 page**. Use the canonical [`resolveComposition`](configure-csr-vs-ssr.md#resolve-composition-helper) wrapper (it classifies known not-found ids as 404 and rethrows real failures), don't hand-roll a second one, and never blanket-catch.

   **Next.js App Router**: 404 for visitors, empty mount target for the editor:

   ```tsx
   // app/[...slug]/page.tsx (or [[...slug]])
   import { notFound } from "next/navigation";
   import { sdk } from "@/lib/contentstack";
   import { resolveComposition } from "@/lib/resolve-composition";
   import { StudioRender } from "./StudioRender";
   import { isStudioEditorMode } from "@/lib/studio-editor-mode"; // § Editor-mode detection below

   export default async function Page({ params, searchParams }) {
     const { slug } = await params;
     const url = "/" + (slug ?? []).join("/");
     const query = new URLSearchParams((await searchParams) as Record<string, string>);

     // Throws on CDA/token/network failure (correctly → 500); returns notFound
     // only for the known "no composition here" error ids.
     const { specOptions, notFound: miss } = await resolveComposition(sdk, {
       url,
       searchQuery: query.toString(),
     });

     if (miss) {
       // In Studio's iframe an unsaved template legitimately has no published spec —
       // 404ing here is what produces "Template Did Not Load" in the canvas.
       // A null spec (not undefined: that crashes) asks Studio for the draft.
       if (isStudioEditorMode(query)) return <StudioRender editorMode specOptions={{
         spec: null, hasSpec: false, hasTemplate: false, seo: null,
         fetchOptions: { config: sdk.getConfig(), compositionQuery: { url },
           searchQuery: query.toString(), options: {}, mode: "edit" } }} />;
       notFound();   // real visitor → app/not-found.tsx
     }
     return <StudioRender specOptions={specOptions} />;
   }
   ```

   **Test the 404 with two URLs, not one.** `/definitely-not-a-page` fails at pattern match (`NO_COMPOSITION_FOR_URL`). A bad slug under a connected template (`/blog/zzz-not-an-entry`) matches the pattern and fails later at entry lookup (`URL_MATCHED_NO_ENTRY`). `isCompositionNotFound` covers both; a hand-rolled list that knows only the first still 500s on every mistyped slug. Full taxonomy: [`troubleshoot-composition-resolution` § Runtime error taxonomy](troubleshoot-composition-resolution.md).

   If `app/not-found.tsx` doesn't exist, create one: `notFound()` falls back to Next's unstyled default otherwise, which won't have the site chrome:

   ```tsx
   // app/not-found.tsx
   export default function NotFound() {
     return (
       <main>
         <h1>Page not found</h1>
         <p>The page you’re looking for doesn’t exist.</p>
         <a href="/">Back to home</a>
       </main>
     );
   }
   ```

   **React Router**: the catch-all and the old 404 route are BOTH `path="*"`. The first match wins, so registering the Studio catch-all silently retires the app's `<NotFound />`. Fold it into the no-spec branch instead of leaving it as a dead route:

   ```tsx
   import { useLocation } from "react-router-dom";
   import { StudioComponent, useCompositionData } from "@contentstack/studio-react";
   import { isCompositionNotFound } from "@contentstack/studio-client";
   import NotFound from "./pages/NotFound";   // the app's EXISTING 404 page — reuse it
   import { isStudioEditorMode } from "./lib/studio-editor-mode"; // § Editor-mode detection below

   export function LinkedRoute() {
     const { pathname, search } = useLocation();
     const searchParams = new URLSearchParams(search);
     const { specOptions, isLoading, error } = useCompositionData({
       url: pathname,
       searchQuery: searchParams,
     });

     if (isLoading) return <div>Loading…</div>;

     // The hook stores the SDK's rejection verbatim in `error`, so a not-found
     // and a CDA outage arrive on the same branch. Ask the SDK which it is.
     const isMiss = !error || isCompositionNotFound(error);
     if (error && !isMiss) throw error;   // real failure — don't turn it into a 404

     if (error || !specOptions?.spec) {
       // Editor iframe, unsaved template: null-spec options as in App Router (not 404, not <div />).
       if (isStudioEditorMode(searchParams)) return <StudioComponent specOptions={{ spec: null,
         fetchOptions: { compositionQuery: { url: pathname }, searchQuery: searchParams.toString(), options: {}, mode: "edit" } } as any} />;
       return <NotFound />;
     }
     return <StudioComponent specOptions={specOptions} />;
   }
   ```

   Delete the now-unreachable `<Route path="*" element={<NotFound />} />`. It can never match once the Studio catch-all is registered.

   **Optional: a Studio-authored 404.** If authors should own the 404 page too, build a Freeform template at `/404` ([`build-freeform-template`](build-freeform-template.md)) and, in the no-spec visitor branch, fetch that composition instead of rendering the hard-coded page. Keep the hard-coded fallback for when the `/404` composition itself fails to resolve, never leave the branch with nothing to render.

   #### (iv) Tell the user what changed

   > Wildcard route wired. Also changed:
   > - Header/footer: **\<code-owned via `app/layout.tsx` / `SiteChrome` layout route\>**, every Studio page renders inside them.
   > - `/canvas` deliberately excluded from site chrome so section authoring isn't wrapped in your header and footer.
   > - 404: unmatched URLs now render **\<`app/not-found.tsx` / your existing `NotFound` page\>**. Studio's editor iframe is exempt, so unsaved templates still preview.

6. **Verify Canvas URL in Studio.** In Studio, open Project Settings. Canvas URL should be the **path** of the canvas route (`/canvas` in dev), NOT a template route and NOT a full origin. Studio prepends the origin itself (the targeted environment's per-locale Base URL), so the composed iframe address resolves to e.g. `http://localhost:5173/canvas`. Studio reaches template routes by rewriting the iframe URL to the template's pattern. The SDK handles iframe context internally. Your code only mounts `<StudioComponent />` and the rest happens behind the scenes. (See `understand-canvas-url` for the full concept.)

7. **Smoke-test both code paths.**
   1. `npm run dev` (or equivalent): app boots, no console errors.
   1b. **`/canvas` first.** Open `http://localhost:<port>/canvas`. `<StudioCanvas />` renders. "No composition for /canvas", a blank frame, or the 404 page means the catch-all is claiming it (see step 2). Check this before anything else. Every Section in the project depends on it.
   2. Visit `http://localhost:5173/blog/<published-entry-slug>` directly. The published composition should render. If it doesn't: either the template isn't deployed, no entry with that slug exists, or the URL pattern in Studio doesn't match `/blog/:slug`.
   3. In Studio, open a template, click Preview Entry, and pick a real entry. Studio loads the visitor URL inside its iframe. The canvas should render the template bound to that entry's data. `<StudioComponent />` detects iframe context internally and shows the live in-canvas runtime.
   4. Edit the template in Studio (drop a component) WITHOUT saving. The canvas should update live, proving the renderer routed through the in-iframe live path (CDA has nothing yet).

   **Wildcard mode: three more checks. A pass on 1-4 says nothing about these. On a localized app repeat 5 to 7 once per locale, at each locale's Base URL:**
   5. **Chrome.** The rendered template URL shows the site header and footer, exactly once each.
   6. **404: two URLs, both must return 404 and neither may 500.** (a) `http://localhost:5173/definitely-not-a-page`, fails at pattern match. (b) A valid prefix with a bad slug under a connected template, e.g. `/blog/zzz-not-an-entry`, matches the pattern and fails later at entry lookup, with a different error id. A 500 on either means the fetch isn't wrapped ([`resolveComposition`](configure-csr-vs-ssr.md#resolve-composition-helper)). A blank page or empty div means the no-spec branch never got the 404 wiring from step 5a (iii).
   7. **Editor exemption.** Create a template and open it in Studio WITHOUT saving. The canvas renders it. If the 404 page appears there instead, the `isStudioEditorMode` gate is missing or reading the wrong params.

8. **Print next steps verbatim:**
   ```
   Template preview routes wired.

   You should now be able to:
     - Visit any template URL directly in a browser and see the published composition.
     - Open a template in Studio with Preview Entry and see live, unsaved edits.

   Common gotchas if something looks off:
     - Studio's project-level Canvas URL must point at /canvas, NOT a template route.
     - Templates with URL pattern /blog/{{entry.url}} only resolve for entries with a non-empty `url` field.
     - For iteration bindings inside a template, bind to repeater.<field> — the visitor render uses the same spec.
   ```

## Inputs needed from the user

1. `routeMode`: **`wildcard`** (one catch-all owns every URL) or **`dedicated`** (only named patterns go through Studio). **Always ask on an existing app** (step 3). Default `wildcard` for greenfield, `dedicated` for an app with existing hand-coded pages.
2. `studioPatterns`: dedicated mode only. The URL patterns to route through Studio (e.g. `/blog/*`, `/landing/*`). One route each. Everything else untouched.
3. `chromeOwner` (wildcard mode only. **`code`** (default) header/footer stay in the layout) or **`studio`** (header/footer become Sections on each template). Never both. See step 5a (i).
4. `optOutPaths`: wildcard mode only. Comma-separated route patterns that should NOT go through Studio. **Leave empty (default) to keep the catch-all unrestricted. RECOMMENDED.** Provide only for explicit non-Studio routes (`/api/*`, `/admin/*`).
5. `sharedRoutePath`: where the shared `LinkedRoute` component should live. Default `src/routes/LinkedRoute.tsx` for Vite, `app/_components/LinkedRoute.tsx` for Next.js App Router.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, do not claim success. Surface the failure and stop.

- [ ] **The user was asked wildcard vs dedicated and picked one** (step 3). On an app with existing pages, a catch-all was NOT wired without that choice.
- [ ] **A `/canvas` route mounting `<StudioCanvas />` exists**, created by `setup-section-preview` if it was missing, not skipped and not bailed on. Studio's project-level Canvas URL matches its path.
- [ ] **`/canvas` is NOT shadowed by the catch-all.** Load `http://localhost:<port>/canvas` directly: `<StudioCanvas />` renders. If it shows "No composition for /canvas", a blank frame, or the 404 page, the catch-all is claiming it. React Router: move the canvas `<Route>` above `path="*"`. Next.js: the static canvas page file is missing.
- [ ] `LinkedRoute` exists at the chosen path and mounts `<StudioComponent />` for visitor URLs (no iframe-detection branching).

**Wildcard mode adds these, all mandatory:**

- [ ] **Site chrome survives.** Load any Studio-rendered URL: the header and footer that the app rendered before are still there. Chrome lives in exactly ONE place: the code layout OR Studio Sections on the template, never both (no duplicated header/footer anywhere).
- [ ] **`/canvas` renders WITHOUT site chrome.** Open a Section in Studio: no site header or footer around it.
- [ ] **Unmatched URLs 404: verified on BOTH shapes.** `/definitely-not-a-page` (pattern-match miss) **and** a bad slug under a connected template like `/blog/zzz-not-an-entry` (entry-lookup miss) each render the app's 404 page. **Neither returns 500**. A 500 means `fetchCompositionData` is unwrapped and its rejection is escaping. Not a blank page, not an empty div, not a Studio error.
- [ ] **The editor iframe is exempt from the 404.** Create a template, do NOT save it, open it in Studio: the canvas renders live edits. If it shows the 404 page or "Template Did Not Load", the editor-mode gate in step 5a (iii) is missing or checking the wrong params.
- [ ] React Router only: the old `<Route path="*" element={<NotFound />} />` was removed (unreachable once the Studio catch-all registers) and `NotFound` is reachable via `LinkedRoute`'s no-spec branch.

**Dedicated mode:** every pattern in `studioPatterns` mounts `<StudioComponent />`. Every other route, the existing chrome, and the existing 404 page are unchanged (verify by loading one non-Studio page and one bad URL).

- [ ] **ONE catch-all route** is registered (wildcard mode). For Next.js: `app/[...slug]/page.tsx` (non-optional) WHEN the app has an existing `app/page.tsx`, OR `app/[[...slug]]/page.tsx` (optional) WHEN greenfield with no root page. For React Router: `<Route path="*">` registered LAST. The catch-all points at `LinkedRoute`.
- [ ] If the app has an existing `app/page.tsx`: confirm the chosen catch-all does NOT collide (greenfield-style `[[...slug]]` is wrong here, must be `[...slug]`).
- [ ] If the user provided opt-outs, those routes are registered ahead of the catch-all and bypass Studio correctly.
- [ ] Studio's project-level Canvas URL still points at `/canvas` (not a template route).
- [ ] Direct visit to ANY published template URL renders the matching composition (URL pattern resolved by Studio's CDA query, not by per-route registration).
- [ ] Opening any template in Studio's Preview Entry renders the live canvas (including unsaved edits).
- [ ] Opt-out routes (if any) are NOT served by Studio.
- [ ] `npm run dev` (or equivalent) starts without runtime errors.

## Editor-mode detection: for custom renderers

If you're shipping a custom `StudioRenderer` (rather than importing `<StudioComponent />` directly, e.g. because you're doing per-route swaps in a partial-adoption app and want to gate on editor mode explicitly), detect editor mode by checking Studio's iframe search params:

```ts
// lib/studio-editor-mode.ts
export function isStudioEditorMode(searchParams: URLSearchParams): boolean {
  return (
    searchParams.get("cs-composable-studio") === "true" ||
    searchParams.has("cs-composable-uid") ||
    searchParams.has("hash")
  );
}
```

**If you copied a `StudioRenderer` from another project** and editor mode never activates (Studio always shows "Template Did Not Load" for unsaved templates), the reference is likely gated on a different param set (`content_type_uid` / `entry_uid` / `live_preview`) than the public SDK's iframe sends. Replace the check with the one above. Always verify against `document.location.search` inside the live Studio iframe (`window.parent === window ? "standalone" : "iframe"`, then log the search params) if you're unsure which scheme applies to the SDK version you installed.

## Environment Base URL: must be reachable + include locale segment

Studio previews Connected templates by having its canvas iframe fetch `<env base URL> + <template URL>`. Two things trip this up on real projects:

1. **Base URL must point at the LOCAL dev server for local authoring.** If you set the preview environment's base URL to a deployed hostname (`https://<slug>.contentstackapps.com`), Studio previews templates against the deployed build, which won't have any newly-added `<StudioComponent>` routes yet. Symptom: "Template Did Not Load" / 404 in the iframe. **Fix:** `PUT /v3/environments/<env>` so `urls[].url` points at `http://localhost:3000` (or the dev port). Re-flip to the deployed URL when you're done authoring locally.

2. **Locale-prefixed apps: the per-locale base URL carries the app's prefix, and nothing else does.** If your app uses `next-intl` or similar and routes are `/en/*` / `/fr/*`, the env base URL for `en-us` is `http://localhost:3000/en` and for `fr-fr` is `http://localhost:3000/fr`, NOT the bare origin. Otherwise Studio composes `<base URL> + <template URL>` = `/` + `/` = `//` (unresolvable). One env has one base URL per locale. Set every one the app serves, not only the default. The other half of the rule: composition URLs never carry the prefix, and the catch-all strips it from the request path before calling Studio. A doubled `/en/en` means one of those two carried it (see [`troubleshoot-canvas`](troubleshoot-canvas.md)).

## Locale-prefixed apps: the middleware 307 breaks the iframe

Distinct from the trailing-slash 308 below, same outcome: **any redirect breaks the preview iframe**. It never lands on the destination, and Studio reports the generic "Template Did Not Load" / blank frame.

**The shape.** Composition URLs are authored without a locale prefix (`/rewards`), because locale is a Studio context variable (`{{locale}}`), not part of the stored path. Studio then iframes `<env base URL> + <composition url>`. With `next-intl` on `localePrefix: "always"` (the default), a request to `/rewards` has no locale segment, so the middleware **307-redirects** it to `/en/rewards`, and the iframe dies on the redirect.

**Three fixes: pick one, don't stack them:**

| Fix | How | Trade-off |
|---|---|---|
| **Locale in the env base URL** (simplest) | Set the environment's per-locale URL to `http://localhost:3000/en` so the composed address is already `/en/rewards` | One base URL per locale per environment, which is exactly the model, but it means one environment previews one locale |
| **Exempt Studio paths from the locale middleware** | Narrow the middleware `matcher` so `/canvas` (and any preview path) bypasses locale rewriting | Keeps one base URL. Needs care that the exemption doesn't leak to visitor routes |
| **`localePrefix: "as-needed"`** | Default locale serves unprefixed, so `/rewards` resolves 200 with no redirect | Changes public URL shape for the whole site, only if that's acceptable independently |

**Verify with `curl`, not the browser**: a browser follows the redirect and looks fine while the iframe does not:

```bash
curl -sS -o /dev/null -w "%{http_code} -> %{redirect_url}\n" "http://localhost:3000/rewards"
# 200 (empty redirect_url) = good.  307/308 + a redirect_url = the iframe will fail.
```

Run this against the **exact composed address** Studio uses (env base URL + composition url). Any 3xx is a failure, whatever its cause: locale prefix, trailing slash, auth wall, or a rewrite.

<a id="bare-entry-url-hazard"></a>

## Bare `{{entry.url}}` catch-all: hazard once a second template exists

A composition `url` of just `{{entry.url}}` (no literal prefix) matches **every** path. With one template that's convenient. Add a second and the bare pattern usually wins or ties on specificity, so URLs you meant for the new template resolve to the old one, and ties break deterministically-but-arbitrarily by `composable_uid`, so it can look random across machines.

Give every template at least one literal segment (`/blog/{{entry.url}}`, `/rewards`). If a genuine site-wide fallback is wanted, keep exactly one bare pattern and make every other template more specific. Diagnosis + ranking mechanics: [`troubleshoot-composition-resolution`](troubleshoot-composition-resolution.md) § Symptom-to-stage matrix (rows on specificity ties and bare placeholders).

## Trailing-slash 308 breaks the Studio iframe on locale-prefixed apps

Studio composes the preview URL as `<base URL> + <template URL>`. On locale-prefixed Next apps, `<base URL>` ends `/en` and a template `url = "/"` produces `/en/`, which Next 308-redirects to `/en`. The redirect breaks the iframe: it never lands on the destination.

**Fix in `next.config.js`:**

```js
module.exports = {
  skipTrailingSlashRedirect: true,   // Studio-authored URLs must resolve 200 directly
  // ...
};
```

Or normalize the template URL patterns to never end in `/`. This is Next-specific but every locale-prefixed framework has an equivalent behavior. Check the framework's docs if you see the iframe stuck on a redirect.

## Third-party global scripts on Studio routes surface as runtime overlays

Analytics / commerce embeds that `throw` on failure show up as scary-but-harmless runtime overlays inside the Studio iframe. Common offenders: Lytics (`throw new Error("Load error!")` in its script.onload), FontAwesome kit (403 when missing), commerce widget script loaders. Studio didn't cause them, but they render on the routes Studio previews and confuse the "is my setup working?" check.

**Recommended:** audit the app's global `<Script>`s / analytics tags on the routes Studio renders. Third-party loaders that `throw` on failure should be either (a) removed from Studio's routes via a route-group / layout guard, or (b) patched to `console.warn` + `return` instead of `throw`. See [`troubleshoot-canvas`](troubleshoot-canvas.md) § Third-party global-script overlays for the full playbook.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Wiring the catch-all without a `/canvas` route in place | `path="*"` / `[[...slug]]` matches `/canvas` too. Studio's section iframe hits the catch-all, `fetchCompositionData({ url: "/canvas" })` returns nothing, and every Section in the project renders as a blank frame, or as your 404 page once step 5a lands. Nothing in the error mentions routing | Create it via `setup-section-preview` **before** emitting the catch-all (step 2, compulsory in both modes). React Router: `/canvas` above `path="*"`. Next.js: the static `app/canvas/page.tsx` (or `app/(studio)/canvas/page.tsx`) file must exist, precedence only helps if there's a file to prefer |
| Wiring a catch-all into an existing app without asking | It silently claims every URL the app didn't explicitly route, including the ones that used to reach the 404 page. The user expected Studio added, not Studio in front of everything | Ask (step 3). Wildcard with code precedence, `chromeOwner = code` and the existing 404 is the minimal-conversion default. Dedicated when the user wants pattern-level control |
| Header/footer vanish on Studio-rendered pages | They were imported per `page.tsx` / per page component, and the catch-all replaced those files | Lift chrome into the layout (Next `app/layout.tsx`) or a React Router layout route wrapping the catch-all, step 5a (ii) |
| Header and footer render twice | Code layout renders them AND the template has Header/Footer Sections on it | One owner only. Strip whichever side isn't the chosen `chromeOwner` |
| Site chrome wraps the `/canvas` section-authoring iframe | `/canvas` was nested inside the chrome layout, so every Section is authored inside a full page header + footer: spacing, sticky positioning, and viewport measurements all read wrong | Register `/canvas` outside the chrome layout (React Router) or in a bare-layout route group (Next.js) |
| Unmatched URLs render blank instead of 404ing | The no-spec branch returns an empty `<div />`, correct for the editor iframe, wrong for visitors, and the catch-all now owns every unmatched URL | Gate on `isStudioEditorMode`: empty div in the editor, 404 page for visitors, step 5a (iii) |
| Unsaved templates show the 404 page inside Studio's canvas ("Template Did Not Load") | The 404 fires unconditionally on no-spec. An unsaved template legitimately has no published spec | Same gate, other direction. Verify `isStudioEditorMode` checks the params the installed SDK actually sends (§ Editor-mode detection) |
| React Router: the app's `<Route path="*" element={<NotFound />} />` left in place | Both it and the Studio catch-all are `path="*"`. First match wins, so one of them is dead code, usually the 404 | Remove the old route. Render `NotFound` from `LinkedRoute`'s visitor no-spec branch |

## See also

- `install-studio`: installs the SDKs this skill depends on.
- `setup-section-preview`: adds the `/canvas` section-authoring route.
