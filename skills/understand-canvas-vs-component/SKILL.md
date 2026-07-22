---
name: understand-canvas-vs-component
description: "`<StudioCanvas />` mounts Sections inside Studio's iframe; `<StudioComponent />` renders Templates on visitor routes AND Studio's template-preview iframe. The split is by kind, not surface."
allowed-tools: Read Grep Glob
---

## When to use

`<StudioCanvas />` mounts Sections inside Studio's iframe; `<StudioComponent />` renders Templates on visitor routes AND Studio's template-preview iframe. The split is by kind, not surface.

Use when the user asks "what's the difference between StudioCanvas and StudioComponent", "which one for Sections vs Templates", "do I render Templates with StudioCanvas inside Studio", or before `setup-section-preview` / `setup-template-preview-routes` if the two mounts haven't been contrasted yet. Concept only — for routes, run those skills.

# `<StudioCanvas />` vs `<StudioComponent />` — the Sections-vs-Templates axis

## The one-line answer

**`<StudioCanvas />` is for Sections. `<StudioComponent />` is for Templates.** The split is along the **Section vs Template** axis — *what* you're rendering — not along authoring vs visitor.

- `<StudioCanvas />` renders **Sections only**. It's used inside Studio's iframe for Section building, authoring, and previewing. Templates never render through `<StudioCanvas />`.
- `<StudioComponent />` renders **Templates**. It's used everywhere a Template renders — your live visitor routes AND Studio's template-preview iframe (which iframes the env Base URL + Template URL, hitting the same route a visitor would).

There IS still an authoring-vs-visitor distinction for Templates, but it's the SAME mount (`<StudioComponent />`) in both cases — Studio's iframe injects edit-mode signals; the visitor's browser doesn't. Both go through the same `<StudioComponent />`-mounted route.

## The two mounts side-by-side

| | `<StudioCanvas />` | `<StudioComponent />` |
|---|---|---|
| **What it renders** | Sections — and only Sections | Templates (which internally render their Sections) |
| **Where it lives** | One dedicated route in your canvas-app (default `/canvas`) | Your real routes — a catch-all `[...slug]`, or per-template files like `app/blog/[slug]/page.tsx` |
| **Used by** | Studio's iframe — for building, authoring, and previewing Sections | (a) Real visitors on your live site; (b) Studio's iframe when previewing Templates — both go through this same mount |
| **Inside Studio?** | Yes — always inside Studio's iframe | Yes when Studio previews a Template (Studio iframes env Base URL + Template URL); also rendered to real visitors outside Studio |
| **Edit overlays** | Yes — hover handles, drop targets, Property panel hooks for Section editing | Studio's iframe injects edit signals so the same render shows overlays in the iframe; a visitor's browser sees the clean render |
| **Reachable URL** | `<env Base URL>` + `<Canvas URL path>` (e.g. `https://localhost:5173/canvas`) | `<env Base URL>` + the Template's resolved URL (e.g. `https://localhost:5173/blog/my-post`) — the same URL a visitor would type |
| **Set up via** | `setup-section-preview` | `setup-template-preview-routes` |

## Why Templates never go through `<StudioCanvas />`

A Section is a *unit* of composition — a reusable piece with a linked schema and bindings to it. A Template is the *page-level container* that assembles one or more Sections into a complete page shape.

Studio designed two separate iframe paths for these:

- **Section preview** — Studio iframes `<env Base URL>` + `<Canvas URL path>`. That route mounts `<StudioCanvas />`. Studio sends the Section UID in URL params; `<StudioCanvas />` reads them and renders the requested Section in edit mode.
- **Template preview** — Studio iframes `<env Base URL>` + `<Template URL>`. That route mounts `<StudioComponent />` — the exact same route a real visitor would hit. Studio's iframe injects edit-mode signals on top of the live render.

The benefit of the second design is that Studio's "preview" of a Template is rendered through your real visitor code path. If it renders correctly for a visitor, it renders correctly in Studio. There's no separate authoring renderer for Templates to drift out of sync.

So `<StudioCanvas />` is **strictly** for Sections, **strictly** inside Studio's iframe. It has no role in Template rendering, anywhere.

## Why only Templates render through `<StudioComponent />`

Visitors hit URLs that resolve to **pages**, not Sections. So the live-render path needs the Template (the page). That Template internally renders its Sections. There's no public route for "give me Section X by itself" — Sections only ever appear *inside* a Template, and the Template renders through `<StudioComponent />`.

If a user asks "how do I render a Section on my live site standalone," the answer is: you don't. Put it in a Template (even a tiny one-Section Template if you must), then render that Template via `<StudioComponent />`. That's the only path.

## Common misconceptions

| Statement | Right or wrong? | Why |
|---|---|---|
| "I use `<StudioCanvas />` for authoring (both Sections and Templates) and `<StudioComponent />` for visitors only" | **Wrong** | The split is Section vs Template, not authoring vs visitor. Templates author through the *same* `<StudioComponent />` route a visitor hits — Studio just iframes it with edit signals. `<StudioCanvas />` never renders Templates. |
| "I need a separate `<StudioCanvas />` route for Templates" | **Wrong** | There's no such route. Templates use `<StudioComponent />`, even when previewed inside Studio. |
| "Sections show up on visitor pages standalone" | **Wrong** | Sections only render inside a Template. The visitor sees the Template (via `<StudioComponent />`), and the Template renders its Sections. |
| "`<StudioCanvas />` is only used during dev" | **Wrong** | It's used whenever an author opens a Section in Studio — dev, staging, or prod. The canvas-app needs the `/canvas` route in every environment Studio is allowed to point at. |
| "I can replace `<StudioComponent />` with `<StudioCanvas />` on my live route" | **Wrong** | `<StudioCanvas />` expects to be inside Studio's iframe with its post-message channel. On a live route it has nothing to talk to and won't render correctly. Also, it only renders Sections — visitors need Templates. |
| "Templates compose Sections" | **Right** | This is the canonical assembly direction. Build each Section first, then assemble them into a Template. |
| "Studio's Template preview hits the same route a visitor hits" | **Right** | Studio iframes env Base URL + Template URL — that's your visitor route, mounting `<StudioComponent />`. Edit overlays come from signals Studio injects into the iframe, not from a separate authoring renderer. |

## Where each mount lives in a typical app

```
your-canvas-app/
├── app/                               # (Next.js App Router shown; Vite/Remix are similar)
│   ├── canvas/
│   │   └── page.tsx                   # <StudioCanvas />        ← Section mount, ONE route
│   ├── [[...slug]]/
│   │   └── page.tsx                   # <StudioComponent />     ← Template mount, catch-all
│   └── blog/
│       └── [slug]/
│           └── page.tsx               # <StudioComponent />     ← OR per-template mount
```

- The `/canvas` route is created by `setup-section-preview` and mounts `<StudioCanvas />`. **One** such route, regardless of how many Sections the project has — Studio passes the Section UID in URL params.
- The visitor / template-preview routes are created by `setup-template-preview-routes`. Either a single catch-all (renders any Template by URL) or per-template routes (more control, more boilerplate). Both mount `<StudioComponent />`. These are the same routes Studio iframes when previewing a Template.

## Quick decision questions

- **"An author is editing a Section in Studio."** → Studio's iframe is loading your `/canvas` route → `<StudioCanvas />` renders the Section.
- **"An author is editing/previewing a Template in Studio."** → Studio's iframe is loading `<env Base URL>` + `<Template URL>` → `<StudioComponent />` on your real route renders the Template. Same code path a visitor hits; edit signals injected by Studio.
- **"A visitor typed my URL into a browser."** → Your app's normal routing hits a `<StudioComponent />` mount → live-render the Template (which renders its Sections inside).
- **"I'm rendering a Section directly on my live site."** → You don't. Put the Section in a Template; render the Template via `<StudioComponent />`.

## See also

- `understand-sections` — what a Section is
- `understand-templates` — what a Template is + Templates-compose-Sections
- `understand-canvas-url` — the path-only Canvas URL setting that points Studio at the `<StudioCanvas />` route
- `setup-section-preview` — creates the `/canvas` route mounting `<StudioCanvas />`
- `setup-template-preview-routes` — creates the visitor / template-preview route(s) mounting `<StudioComponent />`
- `configure-csr-vs-ssr` — choosing how `<StudioComponent />` renders (CSR / SSR / RSC)
