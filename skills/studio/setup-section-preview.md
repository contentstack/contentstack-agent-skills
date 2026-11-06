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

**Two unrelated "Base URLs": don't confuse them.** (1) The Custom Preview URL under Visual Experience (set by `enable-visual-experience`) is used by Live Preview, and by Visual Editor for entries no Studio template shows. For an entry a template shows, Visual Editor uses the template's URL and doesn't apply the Custom Preview URL's Advanced Config rules, the same as Studio. Not relevant here. (2) The **canvas** Base URL is the per-locale URL on the environment your Studio project targets (in Contentstack, open the stack's Settings, go to Environments, open `<env>`, and read the URL for `<locale>`). Studio composes the canvas iframe address as **canvas Base URL (origin) + Canvas URL (path)**. This skill sets the path. The origin must already exist on the targeted environment, or the canvas stays blank.

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

   **The canvas route MUST be isolated from your app's global chrome, but not from its styles.** The route that mounts `<StudioCanvas />` should render no site header/footer, no analytics tags (Lytics / Segment / GA), no third-party embeds, no global `<Script>`s (FontAwesome kits, commerce widgets, chat popups), no auth-gated wrappers. Every one of those runs inside Studio's canvas iframe when the user opens Studio, and any script that `throw`s on failure surfaces as a runtime overlay INSIDE Studio's canvas (looks like Studio is broken, isn't).

   **What the canvas still needs:** the site's global CSS, fonts, and the React providers your registered components read (theme, i18n, cart, query client). Sections render the app's own components on the canvas; strip those and every component renders unstyled or throws on a missing context.

   **Framework-specific isolation patterns:**

   - **Next.js App Router: gate the chrome in the root layout.** A route group can't opt out of the **root** `app/layout.tsx`: every route renders inside it, and that's where most apps put the header, footer, CSS imports and providers. A `(studio)` group with its own `layout.tsx` adds a layer inside the root one; it removes nothing. Instead, keep one root layout and let a small client component drop the chrome on the canvas path:

     ```tsx
     // app/site-chrome.tsx
     "use client";
     import type { ReactNode } from "react";
     import { usePathname } from "next/navigation";

     const CANVAS_PATH = "/canvas";   // your <canvasPath>

     export function SiteChrome({ header, footer, children }: {
       header: ReactNode; footer: ReactNode; children: ReactNode;
     }) {
       const pathname = usePathname();
       // endsWith covers a locale-prefixed canvas (/en/canvas).
       const onCanvas = pathname === CANVAS_PATH || pathname.endsWith(CANVAS_PATH);
       return (
         <>
           {onCanvas ? null : header}
           {children}
           {onCanvas ? null : footer}
         </>
       );
     }
     ```

     ```tsx
     // app/layout.tsx — Server Component; stays the one root layout
     import "./globals.css";                       // CSS and fonts: kept on the canvas
     import { SiteChrome } from "./site-chrome";
     import { StudioInit } from "./studio-init";   // from install-studio step 8
     // Providers, Header, Footer: the app's own, imported as they are today

     export default function RootLayout({ children }: { children: React.ReactNode }) {
       return (
         <html lang="en">
           <body>
             <Providers>                            {/* kept on the canvas */}
               <StudioInit />
               <SiteChrome header={<Header />} footer={<Footer />}>{children}</SiteChrome>
             </Providers>
           </body>
         </html>
       );
     }
     ```

     `Header` and `Footer` are passed as props, so they stay Server Components. Gate analytics and third-party `<Script>`s the same way (render them through `SiteChrome`, or check the pathname in their own client wrapper).
     - **Heavier alternative: multiple root layouts.** Remove `app/layout.tsx` and give each top-level route group its own root layout with `<html>` and `<body>`, e.g. `app/(site)/layout.tsx` with chrome and `app/(studio)/layout.tsx` without. The studio one must import the same global CSS, fonts and providers itself. Every page moves under a group, and navigating between groups is a full page load. Use it only when the chrome gate can't work.
   - **Next.js Pages Router:** use `_app.tsx` with a pathname guard (`router.pathname === "/canvas" ? <Component/> : <ChromeWrapper><Component/></ChromeWrapper>`).
   - **Vite / React Router / Remix:** the CanvasRoute component sits at the router level, above your app chrome: the chrome only wraps the visitor routes.

   **Verify isolation before proceeding.** Open `http://localhost:<port><canvasPath>` in a browser, open DevTools, then the Network tab. You should see **only** the framework's assets + `@contentstack/*`, NO calls to `kit.fontawesome.com`, `c.lytics.io`, GA, chat providers, commerce embeds. If you see any of those, follow the isolation pattern above and re-verify. Skipping this step is fine short-term but every wrong-network-request shows up as a scary overlay to whoever opens Studio next.

   **Next.js App Router** (`app/<canvasPath>/page.tsx`):
   ```tsx
   // app/canvas/page.tsx
   "use client";
   import { StudioCanvas } from "@contentstack/studio-react";

   export default function CanvasRoute() {
     return <StudioCanvas />;
   }
   ```

   **Next.js Pages Router** (`pages/<canvasPath>.tsx`), same body without the directive:
   ```tsx
   import { StudioCanvas } from "@contentstack/studio-react";
   export default function CanvasRoute() {
     return <StudioCanvas />;
   }
   ```

   No `dynamic({ ssr: false })` needed on studio-react 2.x: `StudioCanvas` is a client component that renders `null` on the server and on the first client render, and builds the canvas only after mount, so there is nothing to mismatch. Older snippets that wrap it in `dynamic()` still work; they're just unnecessary.

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

   **No token `<style>` on studio-react 2.x.** `StudioCanvas` writes the design-token `:root` variables itself once it mounts. Don't add `<style>{getSSRStyles(null)}</style>` to a client canvas page: the server and the browser hold different token registries, so the string differs between them and React reports a hydration error on every load. Only on studio-react 1.9.x, where `StudioCanvas` wrote no token variables, add them **after mount**: `const [css, setCss] = useState(""); useEffect(() => setCss(getSSRStyles(null)), []);`, then render `{css ? <style>{css}</style> : null}`.

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
       ];
       return [
         { source: '/canvas', headers: canvasHeaders },
         { source: '/canvas/:path*', headers: canvasHeaders },
       ];
     },
   };
   ```

   The Vite blocks above are for local use only and allow framing by Studio's origin, nothing wider. Don't add `frame-ancestors *` or `Access-Control-Allow-Origin: *`: framing is governed by `frame-ancestors` alone, and CORS headers on the page play no part in it. Don't ship a global framing policy to production either: scope it to the canvas route.

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
- [ ] The file mounts `<StudioCanvas />` and nothing else (no required props, no token `<style>` on studio-react 2.x)
- [ ] Next.js App Router: the canvas path renders without the site header/footer but with the site's CSS, fonts and providers (chrome gate in step 2)
- [ ] If a dev server was running, the route returns 200
- [ ] Canvas URL is set in Studio Project Settings, under Configuration, to match the path
- [ ] The canvas route sends `Content-Security-Policy: frame-ancestors 'self' https://*.contentstack.com`, scoped to the canvas route, with no `Access-Control-Allow-Origin` header added for it. `allowedHosts` (Vite) only lists explicit non-localhost hostnames, never `true`. Plain `http://localhost` is fine; HTTPS is needed only when the app itself requires it (`setup-local-https-canvas`)
- [ ] Opening a section in Studio loads the canvas iframe without errors (no blank frame, no "host not allowed", no mixed-content block)

If the Studio API call wasn't possible (no auth), the manual step is printed and the skill explicitly tells the user to complete it before claiming success.

## See also

- `understand-canvas-url`: concept explainer: what Canvas URL is, why a relative path, why `/canvas` is the standard, when Studio uses it vs the env base URL. Run this first if the user is unfamiliar with the concept.
- `setup-local-https-canvas`: optional, mkcert for local HTTPS
- `install-studio`: runs first, the SDK has to be installed
- `configure-studio`: covers Environment + Language alongside Canvas URL
- `verify-setup`: full layered smoke test
- `troubleshoot-canvas`: when the iframe doesn't render after setup
