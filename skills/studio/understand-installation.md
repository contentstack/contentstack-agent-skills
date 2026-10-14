---
name: understand-installation
---

## When to use

Explain what installing Contentstack Studio adds to a project: three SDKs (delivery / live-preview / studio-react), one shared init, two component mounts (StudioCanvas + StudioComponent). Concept on-ramp before `install-studio`.

Use when a new user asks "what does installing Studio do", "what packages are added", "which SDKs do I need", "what's StudioCanvas vs StudioComponent", or is about to run `install-studio` without context. Concept only: for the actual install run `install-studio`. Do NOT use to fix an install (use `troubleshoot-canvas` or `verify-setup`). Do NOT use for component registration (use `register-component`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# What installing Studio adds to your project

## The three SDKs

Installing Studio adds **three packages** to your app. They're effectively one install. Each owns a distinct piece:

| Package | What it does | Whose credentials |
|---|---|---|
| `@contentstack/delivery-sdk` | Reads published content from Contentstack's CDA. | Stack API Key + Delivery Token |
| `@contentstack/live-preview-utils` | Real-time edit channel: Studio's iframe pushes edits to your running app within ~1s. | Preview Token (paired with the Delivery Token) |
| `@contentstack/studio-react` | The Studio bridge: `studioSdk` (init), `<StudioCanvas />` (canvas mount), `<StudioComponent />` (visitor + template-preview mount), plus hooks like `useCompositionData`. | (uses the other two via `studioSdk.init({ stackSdk })`) |

You don't install one without the others: install-studio wires all three.

## The two React components, and where each goes

This is the single most-confused part of the install:

- **`<StudioCanvas />`** mounts on **ONE canvas route** (e.g. `/canvas`). It's the surface Studio's iframe uses to author Sections. Visitors never hit this route. A project has one Canvas URL: set it in Project Settings to the path you mount it on. See [`setup-section-preview`](setup-section-preview.md).
- **`<StudioComponent />`** mounts on your visitor routes. The default is **ONE catch-all route** (`app/[[...slug]]/page.tsx` for Next App Router, `<Route path="*">` for React Router): Studio resolves every visitor URL through this one mount via `sdk.fetchCompositionData({ url })`. Per-template routes (e.g. `app/blog/[slug]/page.tsx`) also work, since `fetchCompositionData` only needs the URL. They mean more boilerplate. See [`setup-template-preview-routes`](setup-template-preview-routes.md).

Two mounts in the default setup. The install does not add per-template routes.

## What gets wired at install time

After `install-studio` completes:

1. **Three SDK packages** in `package.json`.
2. **`src/lib/contentstack.ts`** (or framework equivalent): the single bootstrap module. Exports `stack`, `sdk`, optionally `ContentstackLivePreview`. This is where `studioSdk.init({ stackSdk, contentTypeUid })` happens.
3. **A side-effect import** at the app shell so the bootstrap runs once. Next App Router needs a `"use client" StudioInit` boundary. Vite / Pages Router / Remix import directly.
4. **`.env.local`** with the five credentials.

The two route mounts are SEPARATE skills: `setup-section-preview` adds the canvas route. `setup-template-preview-routes` adds the visitor route (catch-all by default). `install-studio` deliberately stops before them so each route is an explicit decision.

## What install does NOT do

- Does NOT register any of your components. That's [`register-component`](register-component.md).
- Does NOT configure the Studio project (Environment, Canvas URL). That's [`configure-studio`](configure-studio.md), done in `app.contentstack.com`.
- Does NOT enable Live Preview at the stack level. That's [`enable-visual-experience`](enable-visual-experience.md), done in Stack settings BEFORE the app-side install.

## The expected install order

1. [`analyze-project-fit`](analyze-project-fit.md): preflight, picks greenfield vs minimal-add path.
2. [`enable-visual-experience`](enable-visual-experience.md): turn on Live Preview at stack level (otherwise app install succeeds silently but nothing flows).
3. [`install-studio`](install-studio.md): adds the three SDKs, writes the bootstrap module.
4. [`register-component`](register-component.md): register the customer's components so Studio's palette uses them.
5. [`setup-section-preview`](setup-section-preview.md): adds the `/canvas` route.
6. [`setup-template-preview-routes`](setup-template-preview-routes.md): adds the catch-all visitor route.
7. [`configure-studio`](configure-studio.md): set Environment, Canvas URL in the Studio web app.
8. [`verify-setup`](verify-setup.md): confirm all four layers green.

This sequence is also walked by [`studio-tour`](studio-tour.md) and [`byoc-end-to-end`](byoc-end-to-end.md) orchestrators when you want one skill driving the whole flow. On an existing app, [`convert-project-to-studio`](convert-project-to-studio.md) runs steps 1 to 3 and 5 to 8 as a minimal conversion that leaves every current page untouched.

## What this skill is NOT

- Not the install itself. Run `install-studio`.
- Not a troubleshooting guide. Run [`troubleshoot`](troubleshoot.md) router if something's broken.
- Not the conceptual onboarding for new-to-Studio users. That's [`start-here-zero-knowledge`](start-here-zero-knowledge.md).
