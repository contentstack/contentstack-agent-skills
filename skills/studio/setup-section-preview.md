---
name: setup-section-preview
---

## When to use

Add the canvas route that mounts `<StudioCanvas />`, then print the Canvas URL to set in Studio (browser-only, step 4). **Required on every Studio project, not an optional extra.** **STOP before writing any file:** read the project's environment and its per-locale URL by API (§ 0), show them, confirm the path (default `/canvas`), and wait for a yes.

Use right after `install-studio` to wire the section-authoring route. Also invoked by [`setup-template-preview-routes`](setup-template-preview-routes.md) step 2 when it finds no canvas route: a catch-all matches `/canvas` like any other URL, so with nothing owning that path Studio's section iframe renders a composition lookup (blank frame, or the site's 404) instead of `<StudioCanvas />`. Phrases: "set up canvas route", "MISSING_CANVAS_URL", "where does StudioCanvas mount", "canvas iframe is blank in Studio". Do NOT use to add template/preview routes (use `setup-template-preview-routes`) or to fix a misbehaving canvas after setup (use `troubleshoot-canvas`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them), and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Set up the section preview route

## Context

The "canvas route" is the page in the user's app that Studio loads inside its iframe to preview sections. Two things have to line up:

1. A route in the app at a known path (e.g. `/canvas`) that mounts `<StudioCanvas />`
2. The same path set as **Canvas URL** in the Studio project's Settings, under Configuration

Without both, opening a section in Studio shows the `MISSING_CANVAS_URL` error.

**Two unrelated "Base URLs": don't confuse them.** (1) The "Base URL" under Visual Experience, then Custom Preview URL (set by `enable-visual-experience`) drives **template** preview URLs, not relevant here. (2) The **canvas** Base URL is the per-locale URL on the environment your Studio project targets (in Contentstack, open the stack's Settings, go to Environments, open `<env>`, and read the URL for `<locale>`). Studio composes the canvas iframe address as **canvas Base URL (origin) + Canvas URL (path)**. This skill sets the path. The origin must already exist on the targeted environment, or the canvas stays blank.

Mounting `<StudioCanvas />` is simple: it takes no required props. Studio drives it via URL parameters. The harder part is making sure the framework's routing wires it correctly (App Router vs Pages Router vs React Router vs Remix).

Prerequisite: `install-studio` has run, so `@contentstack/studio-react` is in the project.

## Task

### 0. CONFIRM-AND-GO GATE: the canvas origin chain (do this BEFORE creating the route)

The canvas iframe address is **canvas Base URL (origin) + Canvas URL (path)**. This skill sets the path (step 4). The **origin comes from the per-locale URL on the environment your Studio project targets**. If that URL is empty, Studio can't build the iframe address and the canvas stays blank, with an error that points at the wrong layer. Most "canvas won't load" reports at this stage are this, not the route. Do NOT create the canvas route until all three are confirmed.:

1. **Identify the dev origin** the canvas runs at, e.g. `http://localhost:51723`. If a dev server is running, it's that server's origin (the same one step 3 hits for its 200 check). If not, ask the user which origin they'll serve the app at locally.
2. **Confirm an environment carries that origin** as its per-locale URL: in Contentstack, open the stack's Settings, go to Environments, open `<env>`, and the URL for `<locale>` must equal the dev origin, with no path: Studio appends the Canvas URL as plain text, so `http://localhost:3000/en` loads `/en/canvas`. (This is the **canvas** Base URL, NOT the Visual Experience Custom Preview URL.) If it's empty or wrong, guide the user to set it now before continuing.
3. **Confirm that same environment is the one the project targets**: in the Studio project, open Settings, then Configuration, and read the Environment field. If the project points at a different environment (e.g. an empty `preview`), that mismatch **is** the trap: either set that environment's per-locale URL to the dev origin, or repoint the project's Environment (via `configure-studio`) at the environment that already has it.

**Recommended topology (avoids clobbering deployed envs):** an environment record holds ONE URL per locale, so pointing `preview` at `localhost` breaks your deployed preview later. Prefer a dedicated **`development`** environment whose per-locale URL is `localhost`, with `preview`/`production` reserved for real origins, and point the Studio project's Environment at `development` for local authoring. Switch the project to `preview`/`production` when you deploy (see `deploy-studio-site`). This is a recommendation, not a requirement: if you deliberately use one shared environment, just make sure its per-locale URL matches wherever you're currently serving the canvas.

Only once 1 to 3 hold, continue.

1. **Detect the framework.** Look at `package.json` and the project's directory structure:
   - `next` in deps plus an `app/` folder means Next.js App Router
   - `next` in deps plus a `pages/` folder means Next.js Pages Router
   - `vite` in deps means Vite (look for `src/routes/` or check for react-router)
   - `@remix-run/*` in deps means Remix
   - `react-scripts` means CRA (probably with react-router)
   - otherwise, ask the user which framework

2. **Create the canvas route file** at the framework-appropriate path.

   **The canvas route MUST be isolated from your app's global chrome.** The route that mounts `<StudioCanvas />` should render ONLY that component: no site header/footer, no analytics tags (Lytics / Segment / GA), no third-party embeds, no global `<Script>`s (FontAwesome kits, commerce widgets, chat popups), no auth-gated wrappers. Every one of those runs inside Studio's canvas iframe when the user opens Studio, and any script that `throw`s on failure surfaces as a runtime overlay INSIDE Studio's canvas (looks like Studio is broken, isn't).

   **Framework-specific isolation patterns:**

   - **Next.js App Router:** put the canvas at a route group that has its own minimal `layout.tsx` returning `{children}` only, e.g. `app/(studio)/canvas/page.tsx` with `app/(studio)/layout.tsx` doing `export default function StudioLayout({children}) { return <>{children}</>; }`. Route groups let you opt out of the app's parent layouts (analytics, header, etc.) without changing URLs.
     - **Alternative, layout guard:** if you can't use a route group, guard the existing `RootLayout` with a pathname check that skips analytics / third-party scripts when the pathname matches `*/canvas`.
   - **Next.js Pages Router:** use `_app.tsx` with a pathname guard (`router.pathname === "/canvas" ? <Component/> : <ChromeWrapper><Component/></ChromeWrapper>`).
   - **Vite / React Router / Remix:** the CanvasRoute component sits at the router level, above your app chrome: the chrome only wraps the visitor routes.

   **Verify isolation before proceeding.** Open `http://localhost:<port><canvasPath>` in a browser, open DevTools, then the Network tab. You should see **only** the framework's assets + `@contentstack/*`, NO calls to `kit.fontawesome.com`, `c.lytics.io`, GA, chat providers, commerce embeds. If you see any of those, follow the isolation pattern above and re-verify. Skipping this step is fine short-term but every wrong-network-request shows up as a scary overlay to whoever opens Studio next.

   **Next.js App Router** (`app/<canvasPath>/page.tsx`), `<StudioCanvas/>` must load client-only:
   ```tsx
   "use client";
   import dynamic from "next/dynamic";
   import { getSSRStyles } from "@contentstack/studio-react";

   // StudioCanvas is client-only: it reads browser-only context (window.location,
   // post-message channel to Studio's parent frame). Server-rendering it produces
   // null on the server and a populated tree on the client — a guaranteed
   // hydration mismatch. Load it client-only.
   const StudioCanvas = dynamic(
     () => import("@contentstack/studio-react").then((m) => m.StudioCanvas),
     { ssr: false },
   );

   export default function CanvasRoute() {
     return (<><style>{getSSRStyles(null)}</style><StudioCanvas /></>);
   }
   ```

   **Next.js Pages Router** (`pages/<canvasPath>.tsx`), same SSR-mismatch reason, wrap in `dynamic({ ssr: false })`:
   ```tsx
   import dynamic from "next/dynamic";
   const StudioCanvas = dynamic(
     () => import("@contentstack/studio-react").then((m) => m.StudioCanvas),
     { ssr: false },
   );
   export default function CanvasRoute() {
     return <StudioCanvas />;
   }
   ```

   **Vite + React Router** (`src/routes/CanvasRoute.tsx` + router config update), Vite is SPA-only, so a plain import is safe:
   ```tsx
   import { StudioCanvas } from "@contentstack/studio-react";
   export default function CanvasRoute() {
     return <StudioCanvas />;
   }
   ```
   Plus add `{ path: "<canvasPath>", element: <CanvasRoute /> }` to the existing router config.

   **Remix** (`app/routes/<canvasPath>.tsx`), Remix server-renders by default. Use `ClientOnly` or a `useEffect`-mounted boundary:
   ```tsx
   import { ClientOnly } from "remix-utils/client-only";
   import { StudioCanvas } from "@contentstack/studio-react";
   export default function CanvasRoute() {
     return <ClientOnly fallback={null}>{() => <StudioCanvas />}</ClientOnly>;
   }
   ```

   **Every framework: render `<style>{getSSRStyles(null)}</style>` beside `<StudioCanvas />`.** In studio-react 1.9.0 `StudioCanvas` writes no design-token `:root` variables, so token styles (padding, max-width, colors) resolve to nothing on the canvas.

   Convert `<canvasPath>` to the framework's expected filename (e.g. `/canvas` becomes `canvas/page.tsx` for App Router, or `canvas.tsx` for Pages Router).

3. **Verify the route locally** if a dev server is running. Hit `http://localhost:<port><canvasPath>` and confirm it returns 200. If no dev server, print the URL the user should test once they start it.

4. **Set Canvas URL in Studio.** This is the second half: the route file is useless without the matching Studio setting. Print clear manual instructions for the user to apply in Studio:
     ```
     Open: <studioHost>/projects/<studioProjectId>/settings/configuration
     Set "Canvas URL" to: <canvasPath>
     Click Save.
     ```

5. **iframe-allowed config (REQUIRED on every dev server).** Studio iframes the canvas-app from `https://app.contentstack.com/#!/studio`. The browser will silently block the iframe unless the canvas-app's dev server allows being iframed from a different origin.

   For local dev, `http://localhost:<port>` works as the Canvas URL origin: browsers treat localhost as a trusted origin (W3C Secure Contexts spec), so no HTTPS / mkcert is needed for the basic case. Run `setup-local-https-canvas` only if your app needs HTTPS-on-localhost for unrelated reasons (service workers, secure cookies, strict browser policy).

   For Vite-based apps, add to `vite.config.*`. **Configure BOTH `server` and `preview`: the canvas should be served from `vite preview` (a prod build), not the dev server.** Vite's dev optimizer can pre-bundle the SDK with a separately-loaded React (different `?v=` hash) and break hook calls in the canvas, even with one React in `node_modules`. Use the dev server for non-Studio iteration. The moment Studio iframes the app, switch to `vite preview`. See `install-studio` step 9 for the full reasoning.

   ```ts
   server: {
     // ...existing config...
     // Only list explicit non-localhost hostnames (e.g. a tunnel); never `true`.
     // allowedHosts: ['my-tunnel.example.dev'],
     headers: {
       // Let only Studio (*.contentstack.com) frame the app. No wildcard origins.
       'Content-Security-Policy': "frame-ancestors 'self' https://*.contentstack.com;",
     },
   },
   preview: {
     // RECOMMENDED canvas target — `<pm> build && <pm> exec vite preview` serves a deduped prod bundle
     // (no runtime optimizer to split React across passes)
     // Local canvas target only: let Studio frame it, nothing else.
     headers: {
       'Content-Security-Policy': "frame-ancestors 'self' https://*.contentstack.com;",
     },
   },
   ```

   For Next.js, set the headers in `next.config.js`, **scoped to the canvas route only** (replace `/canvas` with your `<canvasPath>`). Visitor routes keep their normal framing policy, so the rest of the site cannot be framed by arbitrary origins:
   ```js
   module.exports = {
     async headers() {
       const canvasHeaders = [
         // Studio runs on *.contentstack.com (all regions). Add your own origin if you embed the canvas elsewhere.
         { key: 'Content-Security-Policy', value: "frame-ancestors 'self' https://*.contentstack.com;" },
         { key: 'Access-Control-Allow-Origin', value: '*' },
       ];
       return [
         { source: '/canvas', headers: canvasHeaders },
         { source: '/canvas/:path*', headers: canvasHeaders },
       ];
     },
   };
   ```

   The Vite blocks above are for local use only and allow framing by Studio's origin, nothing wider. Don't add `frame-ancestors *` or `Access-Control-Allow-Origin: *`, and don't ship a global framing policy to production: scope it to the canvas route.

   **Why it matters:** the `frame-ancestors` CSP header tells the browser Studio's origin may embed the page; without it, Studio's iframe stays blank with no console error, a particularly hard failure to diagnose. If you reach the server through a non-localhost hostname (e.g. a tunnel) and Vite returns "host not allowed" (403), list that hostname in `allowedHosts`; never set it to `true`.

6. **Sanity check.** Tell the user to:
   1. Open Studio at the project's Compositions list
   2. Click any section (Sections tab)
   3. Confirm the canvas iframe loads with `<StudioCanvas />` content, no MISSING_CANVAS_URL banner

## Inputs needed from the user

1. `canvasPath` (defaults to `/canvas`): the path to use. Confirm with user before creating the file in case they have a routing convention.
2. `studioProjectId` (required): to set Canvas URL via API or to print the right manual link. **Resolve it by listing the org's projects ([`configure-studio` § Select the Studio project](configure-studio.md#select-the-studio-project)), not by guessing from a name.** Setting Canvas URL on the wrong project leaves the real one unconfigured and the canvas blank.
3. `studioHost` (defaults to `https://app.contentstack.com/#!/studio`): to construct the right URL. Adjust for non-US regions. On a custom / private data center (hosts supplied by Contentstack), set it explicitly to that data center's app host (see [`analyze-project-fit`](analyze-project-fit.md) § 2b).

## Acceptance

- [ ] BEFORE creating the route: confirmed the targeted environment has a non-empty per-locale URL equal to the dev origin, AND the Studio project targets that environment
- [ ] Canvas route file exists in the right location for the detected framework
- [ ] The file mounts `<StudioCanvas />` and the token `<style>` (nothing else, no required props)
- [ ] If a dev server was running, the route returns 200
- [ ] Canvas URL is set in Studio Project Settings, under Configuration, to match the path
- [ ] For local dev: canvas-app serves over trusted HTTPS (via `setup-local-https-canvas`), AND the framework config sends `frame-ancestors 'self' https://*.contentstack.com` (no wildcard ACAO; `allowedHosts` only lists explicit non-localhost hostnames, never `true`)
- [ ] Opening a section in Studio loads the canvas iframe without errors (no blank frame, no "host not allowed", no mixed-content block)

If the Studio API call wasn't possible (no auth), the manual step is printed and the skill explicitly tells the user to complete it before claiming success.

## See also

- `understand-canvas-url`: concept explainer: what Canvas URL is, why a relative path, why `/canvas` is the standard, when Studio uses it vs the env base URL. Run this first if the user is unfamiliar with the concept.
- `setup-local-https-canvas`: optional, mkcert for local HTTPS
- `install-studio`: runs first, the SDK has to be installed
- `configure-studio`: covers Environment + Language alongside Canvas URL
- `verify-setup`: full layered smoke test
- `troubleshoot-canvas`: when the iframe doesn't render after setup
