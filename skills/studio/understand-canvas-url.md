---
name: understand-canvas-url
---

## When to use

Explain the Canvas URL: why it must be a relative path (not a full URL), why `/canvas` is standard, and how it differs from the env Base URL (origin).

Concept on-ramp when someone asks "what is the Canvas URL", "why is my canvas blank", sets it wrong, or creating/configuring a project or setting a Canvas URL or Base URL (UI or API), so path/origin aren't merged. Phrases: "Canvas URL", "/canvas vs full origin". Do NOT use to wire the route. Run `setup-section-preview`. Concept only.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# What is the Canvas URL?

## The one-line answer

**Canvas URL is a relative path (default `/canvas`): the route inside your canvas-app where `<StudioCanvas />` is mounted. Just a path, nothing else.** It tells Studio which route to load for section preview. The canvas-app's origin (e.g. `http://localhost:5173`) is a **separate** setting handled elsewhere. Don't put it here.

Concrete: Canvas URL = `/canvas`. That's it. No `https://`, no hostname, no port, just `/canvas`.

## What it must be

- **A relative path**: starts with `/`, no scheme, no host, no port.
- **Pointing to a route in your canvas-app** that renders `<StudioCanvas />` and nothing else (no header, footer, nav: just the canvas mount).
- **The same in every environment.** Local dev, staging, prod: they all use the same Canvas URL (e.g. `/canvas`). Only the **origin** changes per environment.

| Correct | Wrong | Why wrong |
|---|---|---|
| `/canvas` | `https://localhost:5173/canvas` | Including the origin hard-codes it to one environment. Studio joins the path with the project's environment-aware origin at runtime. |
| `/studio-canvas` | `localhost:5173/canvas` | Missing scheme + missing leading `/`, won't parse. |
| `/preview` | `canvas` | No leading slash, so the value is ambiguous. Studio refuses. |

## Why the standard is `/canvas`

- **Recognizable**: anyone reading the codebase sees `/canvas` and knows it's the Studio mount.
- **Unlikely to clash**: most apps don't have a public `/canvas` route already.
- **Same across teams**: every Contentstack reference project and recipe uses `/canvas`, so support and docs assume it.

Use a different path **only if** `/canvas` collides with an existing route. Common alternatives: `/studio-canvas`, `/preview/canvas`, `/_studio`. Whatever you pick, document it in your team's README. The value is per-project and lives in `Studio → Project → Settings → Configuration`.

## What lives at the Canvas URL

A minimal route mounting `<StudioCanvas />`:

```tsx
// Vite + React Router — src/routes/CanvasRoute.tsx
import { StudioCanvas } from "@contentstack/studio-react";
export default function CanvasRoute() {
  return <StudioCanvas />;
}
```

`<StudioCanvas />` is client-only: it reads the post-message channel with Studio's parent frame and `window.location`. For SSR frameworks (Next, Remix), load it client-only via `next/dynamic({ ssr: false })` or `ClientOnly`. `setup-section-preview` emits the right shape per framework.

The route should NOT include nav, header, footer, or any other layout chrome. Those would push the canvas down and clip Studio's overlays. Bare `<StudioCanvas />` and nothing else.

## Where Studio uses the Canvas URL

| Studio feature | Uses Canvas URL? | Notes |
|---|---|---|
| **Section preview** (Sections tab, then click any section) | **Yes** | Studio iframes `<canvas-app-origin>/<Canvas URL>` |
| **Component preview / palette tile previews** | Yes: inside the same section canvas iframe | |
| **Connected template preview** (Templates tab, then a connected template) | **No**: uses the **environment base URL + template URL** | `Stack → Settings → Environments → <env> → Base URL` + the template's resolved path. See `setup-template-preview-routes`. |
| **Live website rendering** | No | The live site uses whatever route(s) you set up to serve `<StudioComponent />`, not the canvas mount |

**Canvas URL is sections-only.** Templates preview at the **environment base URL** plus the template's own URL. That's the same path a real visitor would hit. They render through a route on your app that mounts `<StudioComponent />`, usually the catch-all that `setup-template-preview-routes` configures by default, but **a dedicated per-template route works too** (e.g. `app/blog/[slug]/page.tsx` mounting `<StudioComponent />` for blog URLs only). Either approach renders templates. Neither uses Canvas URL.

The most common confusion: a user sets the Canvas URL correctly, sections render in Studio, then a template fails. That's because the template preview iframes the **env base URL + the template's resolved path**, completely separate from Canvas URL. See `build-connected-template` §15 for the env-base-URL scheme-match fix.

## Where it's stored

| Surface | Where to set it |
|---|---|
| In the Studio UI | `Studio → Project → Settings → Configuration → Canvas URL` |
| Via the provisioning API | `PATCH /v1/projects/{projectId} { canvas_url: "/canvas" }` |
| In the canvas-app | Nowhere: the canvas-app doesn't need to know its own Canvas URL. It just needs the route to exist at the matching path. |

## "Where does the canvas-app's origin come from then?"

That's a **separate** Studio setting, not the Canvas URL field. The origin (e.g. `http://localhost:5173` for local dev, `https://staging.example.com` for staging) is configured per Contentstack environment, distinct from the Canvas URL path.

Keep them mentally separate when reading the docs:

- **Canvas URL** = path. `/canvas`. Lives in Studio Project Settings, under Configuration. That's all this skill is about.
- The canvas-app's origin = a different Contentstack setting in a different place. Out of scope here.

If a Studio screenshot or instruction tells you to put `http://localhost:5173` in the Canvas URL field, it's wrong. That's an origin, not a Canvas URL. Canvas URL stays `/canvas`.

For local dev origins specifically: `http://localhost:<port>` works fine. Modern browsers treat localhost as a trusted origin per the W3C Secure Contexts spec, so no HTTPS / mkcert is required for the basic case. Use `setup-local-https-canvas` only if your app separately needs HTTPS-on-localhost (service workers, secure cookies, strict policy).

## Quick sanity check before setting Canvas URL

1. Decide the path: default `/canvas` unless it collides.
2. Confirm your canvas-app has (or will have) a route at that path mounting `<StudioCanvas />`. If it doesn't yet, run `setup-section-preview`.
3. Confirm the canvas-app's origin (the environment base URL) is reachable from a browser. For local dev, `http://localhost:<port>` works. Use `setup-local-https-canvas` only if you separately need HTTPS-on-localhost (service workers, etc.).
4. Then set the Canvas URL in Studio Project Settings, under Configuration.

## What if I get this wrong?

| Symptom | Likely cause |
|---|---|
| Canvas iframe is blank, no console error | Canvas URL is a full URL (with `https://`) instead of a relative path, **or** the path doesn't exist on the canvas-app yet, **or** (rare) a corporate browser policy overrides the localhost secure-context exemption and a mkcert HTTPS cert is needed |
| Canvas iframe shows the host app's home page | Canvas URL is `/` or empty, no dedicated canvas route |
| "host not allowed" 403 | Canvas URL is correct but the canvas-app's dev server rejects the iframe origin. See `setup-section-preview` for the `frame-ancestors` header and (for tunnel hostnames only) `allowedHosts` config |
| Sections render, templates don't | Canvas URL is fine. The failure is the **environment base URL** scheme (HTTP vs HTTPS mismatch). Templates use the env base URL + their own URL, not Canvas URL. |

## See also

- `setup-section-preview`: creates the route file and sets Canvas URL in Studio
- `setup-local-https-canvas`: required prereq for local dev (mkcert)
- `setup-template-preview-routes`: connected templates use the env base URL, not Canvas URL
- `troubleshoot-canvas`: blank-iframe symptom rows
