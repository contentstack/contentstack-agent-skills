# decompose-site


## When to use

Take a **whole-site design** (multiple templates / page kinds) and emit one consolidated schema plan plus per-template build sheets. Orchestrator around [`decompose-design`](../decompose-design/SKILL.md) — loops it per template, deduplicates atomics + Layer-2 components across pages, identifies cross-page shapes for Global Fields, and produces a single site-wide build plan the agent can execute end-to-end.

Use when the greenfield build has 3+ page kinds sharing common atoms (Hero, Cards, Footer). Phrases — "decompose this whole site", "here are all the page designs", "build the marketing site", "multi-page decomposition", "site-wide plan". Do NOT use for single-page builds (use `decompose-design` directly). Do NOT use as a substitute for the taxonomy — this skill assumes you already understand Layer 1 / 2 / 3.

# Decompose an entire site — one schema, N build sheets, zero duplicate registrations

> ## Verification status
>
> Orchestrator over verified skills. Trust is inherited from the underlying skills; the orchestration logic itself is verified against one synthetic 3-page design.
>
> - ✅ Underlying [`decompose-design`](../decompose-design/SKILL.md) is verified — this skill just loops it per template + dedupes.
> - ✅ Chain-in skills at the closing offer (`provision-studio-stack`, `register-component`, `author-composition-via-api`, `import-content`, `verify-setup`, `deploy-studio-site`) all exist and are documented. Their individual verification status is stated in their own frontmatter callouts.
> - ✅ **Full orchestration logic runtime-verified** against a synthetic **6-page design** (homepage + blog_post + product_detail + author_bio + category_listing + contact). 18/18 acceptance-criteria claims pass: page-kind rows emitted, component registry ≤ 15 entries (produced 6 at N=6 pages, so dedup holds under scale), atomics + layer-2 deduped across pages by prop-shape, `hero` / `seo` / `footer` identified as Global Fields (each embedded in all 6 CTs), build order strictly topologically sorted, `site-build-plan.md` + one build sheet per page kind emitted. Reproduce with `npx ts-node scripts/verify-decompose-site.ts` (input at `scripts/synth-site-design.json`, artefacts land under `docs/_decompose-verification/`).
> - ✅ **Real-design edge cases runtime-verified** — three failure modes the skill's guidance addresses are checked by the reproducer:
>   - **Variant-choice-prop merge**: 3 button variants (primary / secondary / tertiary) collapse into ONE `button` component via a `variant: choice` prop, not three separate components.
>   - **Slot-shape divergence**: `Card` is deduped by prop-shape (identical props on every usage), and the plan tracks the 3 distinct slot content-shapes it carries per usage (`text+image+cta`, `icon+text`, `image+text+price+cta`) so section authors pick the right slot content.
>   - **Single-usage roles**: `body`, `features`, `contact_form`, `author_card`, etc. — roles that appear on only ONE CT — are NOT wrongly promoted to Global Fields. GF extraction requires the 2+-CT threshold to hold.
> - ✅ **N > 5 page kinds** exercised: reproducer covers 6 CTs, dedup holds under scale (6-entry registry, well below the 15-entry budget), all 3 GFs consistent across all 6 CTs. Structural claims scale linearly.

## Context

`decompose-design` handles one template at a time. A real marketing site has 5-30 page kinds — blog post, product, case study, campaign, author, category listing, etc. Running `decompose-design` per page in isolation produces:

- **Duplicate atomics.** Every page has a Heading, Text, Image. Registering them 5 times is wrong.
- **Duplicate Layer-2 components.** A Card appears on 6 pages; registering `BlogCard / ProductCard / TestimonialCard / …` as separate components misses the reuse.
- **Fragmented schemas.** Every page proposes its own `hero: group` — but if 4 CTs share the same hero shape, that shape wants a **Global Field**.
- **No build order.** Which Sections to build first? Which components block what?

This skill fixes all four by decomposing site-wide, not page-wide. It emits **one consolidated schema plan** + **one shared component registry** + **N build sheets** (one per template), with the site-level dependency order encoded.

## Task

### Step 1 — Ingest all page designs

Accept the whole-site design as one of:

- **A Figma file with multiple frames**, one per page kind. List every frame that maps to a template.
- **A folder of screenshots / PDF pages**, named per page kind (e.g. `blog-post.png`, `product-detail.png`).
- **A design description document** listing pages + their contents.
- **A live sitemap URL** — crawl every unique route and treat each as a page kind.

Output: a numbered list of page kinds. Ask the user to confirm the list before decomposing — false positives (same kind counted twice) waste effort; false negatives (missed page kind) require another pass.

### Step 2 — Run `decompose-design` in dry-mode per page

For each page kind, invoke [`decompose-design`](../decompose-design/SKILL.md) in a **plan-only** mode (don't emit build sheets yet). Collect:

- List of atomics proposed per page (with proposed prop shape).
- List of Layer-2 containers + layout components proposed per page.
- Proposed Section boundaries + their schema scopes.
- Proposed CT / Group / Reference / Modular Block fields.

### Step 3 — Deduplicate atomics + Layer-2 components across pages

Merge by **prop-shape match**, not by proposed name. Two atomics with the same prop types (`string` → text) render the same visual; they're one component.

Emit a **shared component registry** table:

| Component | Tier | Prop shape | Used on pages |
|---|---|---|---|
| Heading | Layer 1 atomic | `text: string, level: choice` | Blog, Product, Case Study, Campaign |
| Image | Layer 1 atomic | `src: imageurl, alt: string` | Every page |
| Card | Layer 2 slot-based | `body: slot, title: string` | Blog related, Product PDP, Case Study grid |
| ThreeColumn | Layer 2 layout | `col1/col2/col3: slot` | Blog related, Case Study grid, Homepage |
| … | … | … | … |

**Registration budget:** the shared registry should have ~5-15 components for a typical marketing site. If it has 50, you're proposing too many one-offs — merge more aggressively by prop-shape.

### Step 4 — Identify Global Field candidates

A field shape appearing on 2+ CTs is a **Global Field candidate**. From the per-page decomposition:

- Every `hero: group` proposed independently on 3 CTs → one Global Field `hero` referenced by all three.
- Every `seo: group` (title, description, og_image) → one Global Field `seo`.
- Any structural shape recurring across CTs → GF.

**Emit a GF table** showing which fields become GFs + which CTs embed them. GF-linked Sections auto-bind across every CT embedding the GF — this is the single biggest reuse win at the Section layer.

### Step 5 — Emit the consolidated schema plan

One document listing:

- **Global Fields** (with their sub-field structure).
- **Content Types**, each with its fields (referring to GFs by UID for shared groups + declaring CT-specific fields).
- **Reference relationships** between CTs (e.g. `blog_post.author → author`, `product.related_products → product multi`).

The schema plan is the **first thing to provision** on the target stack — every other step depends on it existing.

### Step 6 — Determine build order

Some Sections + Templates depend on others. The build order is deterministic:

1. **Register components** — every atomic + Layer-2 in the shared registry, in tier order (atomics first, containers next, layouts last).
2. **Provision the schema** — GFs first, then CTs referencing them.
3. **Author Sections** — build Sections in dependency order:
   - Sections bound to CT root or Group scopes (no dependencies).
   - Sections bound to Reference scopes (depend on the target CT existing).
   - Sections bound to Global Fields (depend on the GF being embedded in ≥1 CT).
4. **Author Templates** — one per page kind, composing the already-built Sections.
5. **Verify per page** — `verify-setup` after each Template lands.

Emit this order as a numbered list in the site plan.

### Step 7 — Emit the site plan + per-template build sheets

Two output artefacts:

**Site plan — `docs/site-build-plan.md`:**

```
SITE PLAN · <Site name>

## Page kinds (N templates)
| # | Page kind | Template UID | CT |
|---|---|---|---|
| 1 | Blog post | blog_post_template | blog_post |
| 2 | Product PDP | product_template | product |
| ... |

## Global Fields
| UID | Fields | Embedded in CTs |
|---|---|---|
| hero | eyebrow, headline, subcopy, image, cta | blog_post, product, case_study, campaign |
| seo | title, description, og_image | every CT |
| ... |

## Content Types
| UID | Fields | Sections |
|---|---|---|
| blog_post | title, excerpt, cover, body, hero(GF), seo(GF), author(ref), related_posts(multi-ref) | Hero, Body, Author Card, Related Posts |
| ... |

## Shared component registry (register once, use everywhere)
[Component table from Step 3]

## Build order
1. Register components (atomics → containers → layouts): ...
2. Provision schema (GFs first, then CTs): ...
3. Author Sections in dependency order: ...
4. Author Templates: ...
5. Verify: ...
```

**Per-template build sheet — `docs/<template-slug>-build-sheet.md`, one per page kind:**

Same format as `decompose-design` § *Step 9* — Decisions made, Components table (referencing the shared registry, not per-page duplicates), Sections, Template, Unmapped fields. Every reference to a component says *"reuses `Card` from shared registry"* or *"builds new — see shared registry"*.

### Step 8 — Close with orchestrated offers

After all artefacts land, emit the closing offers in one block:

> **Site scope:** N page kinds, M shared components (K new, M-K existing), G global fields, X content types.
>
> **Offer 1 — schema.** Provision the schema (Global Fields + Content Types) on the target stack? Chains [`provision-studio-stack`](../provision-studio-stack/SKILL.md).
> **Offer 2 — components.** Scaffold + register the K new components? Chains [`register-component`](../register-component/SKILL.md) per component.
> **Offer 3 — compositions.** Author every Section + Template per the build order? Uses the API path (default) or Playwright MCP canvas path per [`decompose-design`](../decompose-design/SKILL.md) § Execution paths.
> **Offer 4 — content.** Populate the CTs with real entries? Chains [`import-content`](../import-content/SKILL.md) if source data exists; otherwise leaves entries for manual authoring.
> **Offer 5 — verify + deploy.** Run [`verify-setup`](../verify-setup/SKILL.md) end-to-end and [`deploy-studio-site`](../deploy-studio-site/SKILL.md).

An agent accepting all five drives the full site build with no manual canvas clicks. Failures at any offer stop the pipeline and report which step needs attention — see `agent-idempotency` for the resume semantics.

## Inputs needed from the user

1. The whole-site design (Figma URL, folder of screenshots, description doc, or sitemap).
2. Target Contentstack stack UID + management token (via env or explicit).
3. Any existing schema / components in the stack that should be reused rather than re-created.
4. Which page kinds are in scope (in case the design has out-of-scope pages).

## Acceptance

- [ ] Every page kind from the design has a corresponding row in the Site plan's page-kinds table.
- [ ] Shared component registry has ≤ 15 entries for a typical marketing site; if more, aggressive merging by prop-shape wasn't done.
- [ ] Every field shape appearing on 2+ CTs is a Global Field, not a duplicate.
- [ ] Build order is a strict topological sort — no Section depends on a Section built later; no Template depends on a Section not yet authored.
- [ ] `docs/site-build-plan.md` + one `docs/<template-slug>-build-sheet.md` per page kind emitted.
- [ ] Every page's build sheet references the shared registry for reused components, not new proposals.
- [ ] Closing offer block accurately counts new vs existing components.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Proposing per-page atomic variants (`BlogHeading`, `ProductHeading`) | Registration explosion, brand-drift risk, template authors confused which to use | Merge by prop-shape into one `Heading` component with a `level` choice prop. Same for `Text`, `Image`, `Button`. |
| Missing GF opportunities | Every CT has its own `hero: group`. Editing the hero shape means 5 schema changes. Zero cross-page auto-binding. | Any group appearing on 2+ CTs is a GF candidate. Extract before finalising the schema. |
| Circular dependencies in build order | Section A binds to a Reference to CT B, but B references A. Chicken-and-egg. | Order: register components → provision schema (all at once) → author Sections in topological order. If two Sections depend on each other, one must be extractable to a Layer-2 container inside the other. |
| Emitting one giant build sheet instead of per-template files | Unusable for per-page focus. Downstream skills expect one sheet per template. | One `<template-slug>-build-sheet.md` per page kind. Site plan is the index. |
| Skipping the "confirm page kinds" step | User's design has 30 frames but only 8 are unique page kinds; you decompose 30 identical things | Ask the user to confirm the list of page kinds after Step 1 before proceeding. |

## See also

- [`decompose-design`](../decompose-design/SKILL.md) — per-template skill this orchestrator loops. Same output format per template.
- [`plan-studio-architecture`](../plan-studio-architecture/SKILL.md) — requirements-first planner. Complementary — use `plan-studio-architecture` when the input is a requirements doc; use `decompose-site` when the input is a visual design covering multiple pages.
- [`provision-studio-stack`](../provision-studio-stack/SKILL.md) — schema provisioning; chained by Offer 1.
- [`register-component`](../register-component/SKILL.md) — component registration; chained by Offer 2.
- [`import-content`](../import-content/SKILL.md) — content ingestion; chained by Offer 4.
- `agent-idempotency` — resume semantics if the orchestrated build fails midway.
- `from-designs-to-sections` — the three-layer taxonomy this skill applies at scale.
