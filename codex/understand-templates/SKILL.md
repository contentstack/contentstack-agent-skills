# understand-templates


## When to use

Explain Templates — they compose Sections into a page-shape, rendering against a content type at a derived URL pattern (one Template → N live pages).

Use before any template-building skill whenever the user is new to Studio. Also when the user asks "what is a template?" or "how do Sections become a page?". Do NOT use this skill to actually create a template — for that, run `build-connected-template`. Concept only.

# What is a Template?

## The one-line answer

**A Template is a page shape — a stack of Sections — that renders one whole page on your site.** A Connected Template binds to a content type and renders every entry of that CT at its URL pattern (one Template → N live pages).

If a Section is a *part* of a page (hero, feature grid, footer), a Template is a *whole* page made of Sections.

## Templates compose Sections

**A Template is a page-level container; Sections fill it.** Templates do not model fields directly — they hold one or more Sections, each bound to its own CT, Global Field, Group, Block, or Reference. Any "multi-section template", "many sections in one page", "combining sections" — all the canonical assembly.

**The workflow is fixed:**

1. Build each Section first via `build-section` — one per CT / slice of content the page needs.
2. Then add those Sections into a Template via `build-connected-template`.

A Template can hold one Section or many. Its only job: *which Sections, in what order, with what per-instance overrides*. If you want to bind raw fields directly on a Template, build a Section for that shape first — Sections carry bindings across Templates.

## A concrete example

You author a Template called **"Blog Post"** containing three Sections, top to bottom:

1. `BlogArticleHeader` (hero with title, subtitle, cover)
2. `ArticleBody` (the rich-text body + side rail)
3. `RelatedPosts` (grid of three other articles)

You connect this Template to the `blog_post` content type.

You publish 12 blog posts in Contentstack. Studio's catch-all (or your dedicated route) sees each blog post's URL (`/blog/the-launch-post`, `/blog/why-studio`, …) and renders the **same Template** against each entry. **One Template → 12 live pages**, each with its own content driven by its entry.

Authors never touched code to add a blog post. They created an entry; the Template renders it.

## Connected Template

Bound to a content type. One Template renders N pages — one per published entry. This is what every repeatable page shape uses, and what every one-off page uses too (via a single-entry CT).

| Connected Template | Example |
|---|---|
| `blog_post` | `/blog/the-launch-post`, `/blog/why-studio`, … |
| `product` | `/products/widget-a`, `/products/widget-b`, … |
| `case_study` | `/case-studies/acme`, `/case-studies/globex`, … |
| `author` | `/authors/jane-doe`, `/authors/john-roe`, … |

The Template defines the **shape**. Each entry's `url` field defines the **path**. Studio matches the URL pattern (`/blog/{{entry.url}}`) to render the right Template against the right entry.

## How Sections compose into a Template

Templates are *stacks of Sections*. Drag and drop:

```
Template "Blog Post"
├── BlogArticleHeader   (Section)
├── ArticleBody         (Section)
└── RelatedPosts        (Section)
```

When the Template renders, each Section renders in order, top to bottom. Each Section already knows how to bind to the entry data (via its `understand-linked-schemas` declaration). The Template's job is just *which Sections, in what order, with what per-instance prop overrides* (see `expose-section-props`).

You can also drop **individual registered components** outside of Sections — useful for one-off Template-only chrome. But for anything reusable across Templates, prefer a Section.

## How a Template becomes a live page

1. **You author the Template** in Studio — drop Sections, arrange, save.
2. **Studio stores the Template as a composition spec** (data, not code) in your CMS.
3. **Visitor hits `/blog/the-launch-post`** on your live site.
4. **Your app's route** (catch-all or dedicated — see `setup-template-preview-routes`) mounts `<StudioComponent />`, which calls `sdk.fetchCompositionData({ url: "/blog/the-launch-post" })`.
5. **Studio's SDK matches the URL** against your published Templates — finds `Blog Post` template (because its pattern is `/blog/{{entry.url}}` and the URL matches an entry).
6. **The SDK returns the composition spec** — every Section and registered component the Template uses, with bindings resolved against the entry's data.
7. **`<StudioComponent />` renders the spec** — your React components, your design system, your bundle.

The visitor sees a fully-rendered page. No special server, no static export, no per-page code change. Add a new blog post → it gets a live URL because the Template + the entry are enough.

## How a Template renders in Studio's canvas (preview)

When you open a Template in Studio:

- Studio iframes the **environment base URL + the resolved URL** (e.g. `https://localhost:5173/blog/the-launch-post`) — NOT the Canvas URL (which is sections-only; see `understand-canvas-url`).
- Your app's route mounts `<StudioComponent />` — same renderer as production.
- `<StudioComponent />` detects it's in Studio's iframe and switches to showing the **unsaved working spec** (instead of the published one).
- The PREVIEW ENTRY in Studio's top bar lets you swap entries; the canvas redraws against the new entry instantly.

This is why **what the author sees in the canvas IS what the visitor sees in production** — same renderer, same components, same data, just the unsaved-vs-published variant differs.

## Why Connected Templates work for every page

- **Scales with content** — one Template renders unlimited entries; add a new page = add an entry, not a new Template.
- **Auto-binds `template.*`** against the connected entry through linked schemas — no per-binding wiring.
- **Supports `{{entry.*}}` URL variables** (`/blog/{{entry.slug}}`, `/products/{{entry.handle}}`).
- **Content-first workflow** — authors edit the entry in Contentstack; the page updates automatically. Devs and authors don't need to touch the composition.
- **CT-level governance** — validation rules, locales, variants, publish workflows, scheduled publishing, role-based access all come for free.
- **Single-entry CTs cover one-off pages** — homepage, about page, contact page, even most "campaign" pages have a stable shape and should be modelled as a one-CT-one-entry Connected page.

## What a Template is NOT

| Misconception | Reality |
|---|---|
| "A Template is a React component" | No. Templates are *composition data* in Studio — a list of Sections + arrangement + per-instance overrides. The React components ARE in your repo (the atomic components Sections compose). Templates reference them by ID. |
| "I need one Template per published page" | No. One Connected Template renders N pages — one per entry of the connected CT. |
| "Templates and pages are the same thing" | Close, but: a Template is the *recipe*; a page is a *rendered instance*. A Connected Template's recipe + one entry = one page. Same recipe + a different entry = a different page. |
| "I can't change a Template after creating it" | You can. Templates are editable data. Save the Template → existing pages re-render with the new layout. Authors can iterate without engineering tickets. |

## Why this matters for "first-time" Studio users

A common mistake new users make: skip Sections + Templates and try to drop atomic components straight onto a route. That works on day one but kills reuse: every page becomes one-off composition that doesn't transfer.

**The Studio pattern is**: register atomic components → compose them into Sections → arrange Sections into Templates → Templates render live pages. Each layer compounds reuse.

If you're new and asking "do I really need Sections and Templates?" — yes, for any site beyond a one-off landing page.

## Next steps

| If you want to… | Skill |
|---|---|
| Create a Connected Template | `build-connected-template` |
| Wire up the route that renders Templates on the live site | `setup-template-preview-routes` |
| Make a Section field tweakable per Template instance | `expose-section-props` |

## See also

- `understand-sections` — what Sections are (the building blocks of Templates)
- `understand-linked-schemas` — how a Section declares its data shape
- `understand-auto-binding` — what happens when a Section drops on a Template
- `docs/31-templates/` — long-form reference
