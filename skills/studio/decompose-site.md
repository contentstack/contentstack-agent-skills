---
name: decompose-site
---

## When to use

Take a **whole-site design** (multiple templates / page kinds) and emit one consolidated schema plan plus per-template build sheets. Orchestrator around [`decompose-design`](decompose-design.md): loops it per template, deduplicates atomics + Layer-2 components across pages, identifies cross-page shapes for Global Fields, and produces a single site-wide build plan the agent can execute end-to-end.

Use when the greenfield build has 3+ page kinds sharing common atoms (Hero, Cards, Footer), **or when the input is one Figma board holding many section shapes rather than whole pages** (§ Step 1b). Phrases: "decompose this whole site", "here are all the page designs", "build the marketing site", "multi-page decomposition", "site-wide plan", "here's the whole Figma board", "build every section in this file", "all the hero variants", "turn this design file into sections". Do NOT use for single-page builds (use `decompose-design` directly). Do NOT use as a substitute for the taxonomy. This skill assumes you already understand Layer 1 / 2 / 3.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Reuse preflight: mandatory when the project already has compositions.** Before naming a single new atomic, component or Section, run [`match-existing-pattern`](match-existing-pattern.md) § Step 1b: it groups existing Sections by the schema they bind and ranks the component palette by real usage. Decomposition is where reuse has to bite. Once this step names `Heading` instead of the project's `alpha-atom-heading`, the duplicate survives into the plan and into the build. Mark every row reuse, extend, or new, and never new without having looked.

# Decompose an entire site: one schema, N build sheets, zero duplicate registrations

> **The sheet is not the build.** A decomposition that names N Sections and then gets authored as one component bound to the whole page body renders correctly and passes every render-time check. Whoever executes this sheet must count `section-composition` nodes before reporting done: [`build-connected-template`](build-connected-template.md) § Post-build structural check. When the page body is one modular-blocks field, [`decompose-blocks-page`](decompose-blocks-page.md) is the recipe.

> ## Verification status
>
> Orchestrator over verified skills. Trust is inherited from the underlying skills. The orchestration logic itself is verified against one synthetic 6-page design.
>
> - Underlying [`decompose-design`](decompose-design.md) is verified. This skill just loops it per template + dedupes.
> - Verified: chain-in skills at the closing offer (`provision-studio-stack`, `register-component`, `author-composition-via-api`, `import-content`, `verify-setup`, `deploy-studio-site`) all exist and are documented. Their individual verification status is stated in their own frontmatter callouts.
> - **Full orchestration logic runtime-verified** against a synthetic **6-page design** (homepage + blog_post + product_detail + author_bio + category_listing + contact). 18/18 acceptance-criteria claims pass: page-kind rows emitted, component registry ≤ 15 entries (produced 6 at N=6 pages, so dedup holds under scale), atomics + layer-2 deduped across pages by prop-shape, `hero` / `seo` / `footer` identified as Global Fields (each embedded in all 6 CTs), build order strictly topologically sorted, `site-build-plan.md` + one build sheet per page kind emitted.
> - **Real-design edge cases runtime-verified.** Three failure modes the skill's guidance addresses were checked in the same run:
>   - **Variant-choice-prop merge**: 3 button variants (primary / secondary / tertiary) collapse into ONE `button` component via a `variant: choice` prop, not three separate components.
>   - **Slot-shape divergence**: `Card` is deduped by prop-shape (identical props on every usage), and the plan tracks the 3 distinct slot content-shapes it carries per usage (`text+image+cta`, `icon+text`, `image+text+price+cta`) so section authors pick the right slot content.
>   - **Single-usage roles**: `body`, `features`, `contact_form`, `author_card`, etc. (roles that appear on only ONE CT) are NOT wrongly promoted to Global Fields. GF extraction requires the 2+-CT threshold to hold.
> - Verified with **N > 5 page kinds**: the verification run covered 6 CTs, dedup holds under scale (6-entry registry, well below the 15-entry budget), all 3 GFs consistent across all 6 CTs. Structural claims scale linearly.

## Context

`decompose-design` handles one template at a time. A real marketing site has 5-30 page kinds: blog post, product, case study, campaign, author, category listing, etc. Running `decompose-design` per page in isolation produces:

- **Duplicate atomics.** Every page has a Heading, Text, Image. Registering them 5 times is wrong.
- **Duplicate Layer-2 components.** A Card appears on 6 pages. Registering `BlogCard / ProductCard / TestimonialCard / …` as separate components misses the reuse.
- **Fragmented schemas.** Every page proposes its own `hero: group`, but if 4 CTs share the same hero shape, that shape wants a **Global Field**.
- **No build order.** Which Sections to build first? Which components block what?

This skill fixes all four by decomposing site-wide, not page-wide. It emits **one consolidated schema plan** + **one shared component registry** + **N build sheets** (one per template), with the site-level dependency order encoded.

## The four-question decision framework, applied site-wide

Every fragment on every page is walked through the [four-question decision framework](design-component-library.md). The framework is an open validator (works on any input, no assumed registry). The multi-page context adds a deduplication dimension the single-template `decompose-design` doesn't have:

- **Q1. Classify: Atom, Layout, or Compound?** Applied per distinct shape across ALL templates. A `Card` shape identified on 6 pages is classified once as a layout. Compounds (marketing sections, page hero blocks) always decompose recursively until every leaf is an atom or a layout.
- **Q2. Does the shared registry already have it?** Two layers: (a) does the customer's existing project registry cover it? (b) has it already been proposed for the shared registry by an EARLIER template in this pass? Aggressively dedup: 6 pages proposing "Card" produce one Card entry, not six.
- **Q3. Which props?** For each proposed prop on a proposed new primitive: does the value vary across the SITE (not just across one template) AND represent functional/content intent? Site-wide invariants (e.g. Section spacing is always `comfortable` across all 30 templates) are hardcoded, not exposed as a prop.
- **Q4. Which are Exposed?** For each schema prop: author-understandable + DS-portable? Additionally: does any template on the site actually need to override this prop? If zero templates need override, keep static globally. Site-wide "exposed for one template only" is a valid reason.

**The shared component registry every skill invocation produces has one Q1 to Q4 verdict PER PROPOSED PRIMITIVE**, not per template use. The build sheets reference the registry by name. Each template's build order just says "drop Section S3 (registered per registry)" and stops.

**Halt if any Q1 to Q4 answer is ambiguous** across templates. Ask the user to disambiguate before committing to the shared registry.

## Task

### Step 1: Ingest all page designs

Accept the whole-site design as one of:

- **A Figma file with multiple frames**, one per page kind. List every frame that maps to a template.
- **A folder of screenshots / PDF pages**, named per page kind (e.g. `blog-post.png`, `product-detail.png`).
- **A design description document** listing pages + their contents.
- **A live sitemap URL**: crawl every unique route and treat each as a page kind.

Output: a numbered list of page kinds. **STOP: end your turn with the list and a question; write nothing until the user confirms.** False positives (same kind counted twice) waste effort. False negatives (missed page kind) require another pass.

### Step 1b. Variant boards: collapse before you count

A design file is often **not** one frame per page. It is a board of section shapes: twelve hero treatments, four product heroes, two product templates. Counting frames here and building one Section each is how a 10-component library turns into 40 one-off components.

**Detecting a variant board**: any of these means the frames are variants, not page kinds:

- **Repeated frame names.** Four frames literally named `Product hero`, two named `Product Template`. Observed on a real Contentstack board: 22 top-level nodes, of which `Product hero` appeared 4× and `Alpha` and `Product Template` 2× each.
- **A text label acting as a group header**: a `Hero options:` text node sitting above six frames named `Hero Full View`, `Hero Half View`, `Hero Form`, `Hero Product View`, `Hero Center small or no image`, `Hero Blog type`. The label names the family. The frames are its axes.
- **Names encoding a modifier**: `… Full / Half / Center`, `… With Form`, `… Expanded`, `… small or no image`. The words after the family name are the variant axis.

**Name the axes, then classify each one.** For the hero family above the axes are: media size (full / half / none), media kind (image / product), action (CTA / form), and body type (marketing / blog). For each axis ask **does it change what an author types, or only how it looks?**

| Axis changes | Becomes | Why |
|---|---|---|
| Only appearance: alignment, media side, spacing, emphasis | A `choice` prop on the existing component, static on the canvas | Design decisions live in the library, not the schema. See [`design-component-library`](design-component-library.md) § content binds, design stays static. |
| Which region is filled: image present or absent, form instead of buttons | A **slot**, or an omitted optional prop | One structure renders both. The author fills what applies |
| What fields exist: a form variant needs `form_id`, a blog variant needs `author` + `read_time` | A **separate block** in the page CT's Modular Block | Different content shape is the one case that earns a new Section |

Only the third row produces a new Section. **The first two rows collapse.** Six hero frames typically resolve to one or two Sections carrying two or three `choice` props, not six.

**Emit a variant table before Step 2**, and confirm it with the user:

| Family | Frames | Axes | Collapses to |
|---|---|---|---|
| Hero | 6 | media size, media kind, action, body type | 2 Sections (`hero`, `hero_form`) + `media` choice + optional image slot |
| Product hero | 4 | layout only | 1 Section + `layout` choice |
| Product template | 2 | layout only | 1 Section |

Then run Step 2 over the **collapsed** list. A board of 22 frames that yields 22 Sections means Step 1b was skipped.

Sections that survive collapse are block types on the page CT. Assemble them with [`build-page-builder-template`](build-page-builder-template.md), which is what lets an author pick and order them per page.

### Step 2: Run `decompose-design` in dry-mode per page

For each page kind, invoke [`decompose-design`](decompose-design.md) in a **plan-only** mode (don't emit build sheets yet). Collect:

- List of atomics proposed per page (with proposed prop shape).
- List of Layer-2 containers + layout components proposed per page.
- Proposed Section boundaries + their schema scopes.
- Proposed CT / Group / Reference / Modular Block fields.

### Step 3: Deduplicate atomics + Layer-2 components across pages

Merge by **prop-shape match**, not by proposed name. Two atomics with the same prop types (`string` maps to text) render the same visual. They're one component.

Emit a **shared component registry** table:

| Component | Tier | Prop shape | Used on pages |
|---|---|---|---|
| Heading | Layer 1 atomic | `text: string, level: choice` | Blog, Product, Case Study, Campaign |
| Image | Layer 1 atomic | `src: imageurl, alt: string` | Every page |
| Card | Layer 2 slot-based | `body: slot, title: string` | Blog related, Product PDP, Case Study grid |
| ThreeColumn | Layer 2 layout | `col1/col2/col3: slot` | Blog related, Case Study grid, Homepage |
| … | … | … | … |

**Registration budget:** the shared registry should have ~5-15 components for a typical marketing site. If it has 50, you're proposing too many one-offs. Merge more aggressively by prop-shape.

### Step 4: Identify Global Field candidates

A field shape appearing on 2+ CTs is a **Global Field candidate**. From the per-page decomposition:

- Every `hero: group` proposed independently on 3 CTs becomes one Global Field `hero` referenced by all three.
- Every `seo: group` (title, description, og_image) becomes one Global Field `seo`.
- Any structural shape recurring across CTs becomes a GF.

**Emit a GF table** showing which fields become GFs + which CTs embed them. GF-linked Sections auto-bind across every CT embedding the GF. This is the single biggest reuse win at the Section layer.

### Step 5: Emit the consolidated schema plan

One document listing:

- **Global Fields** (with their sub-field structure).
- **Content Types**, each with its fields (referring to GFs by UID for shared groups + declaring CT-specific fields).
- **Reference relationships** between CTs (e.g. `blog_post.author → author`, `product.related_products → product multi`).

The schema plan is the **first thing to provision** on the target stack. Every other step depends on it existing.

### Step 6: Determine build order

Some Sections + Templates depend on others. The build order is deterministic:

1. **Register components**: every atomic + Layer-2 in the shared registry, in tier order (atomics first, containers next, layouts last).
2. **Provision the schema**: GFs first, then CTs referencing them.
3. **Author Sections**: build Sections in dependency order:
   - Sections bound to CT root or Group scopes (no dependencies).
   - Sections bound to Reference scopes (depend on the target CT existing).
   - Sections bound to Global Fields (depend on the GF being embedded in ≥1 CT).
4. **Author Templates**: one per page kind, composing the already-built Sections.
5. **Verify per page**: `verify-setup` after each Template lands.

Emit this order as a numbered list in the site plan.

### Step 7: Emit the site plan + per-template build sheets

Two output artifacts:

**Site plan (`docs/site-build-plan.md`):**

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

**Per-template build sheet (`docs/<template-slug>-build-sheet.md`), one per page kind:**

Same format as `decompose-design` § Step 9: Decisions made, Components table (referencing the shared registry, not per-page duplicates), Sections, Template, Unmapped fields. Every reference to a component says "reuses `Card` from shared registry" or "builds new, see shared registry".

### Step 8: Close with orchestrated offers

After all artifacts land, emit the closing offers in one block:

> **Site scope:** N page kinds, M shared components (K new, M-K existing), G global fields, X content types.
>
> **Offer 1: schema.** Provision the schema (Global Fields + Content Types) on the target stack? Chains [`provision-studio-stack`](provision-studio-stack.md).
> **Offer 2: components.** Scaffold + register the K new components? Chains [`register-component`](register-component.md) per component.
> **Offer 3: compositions.** Author every Section + Template per the build order? Uses the API path (default) or Playwright MCP canvas path per [`decompose-design`](decompose-design.md) § Execution paths.
> **Offer 4: content.** Populate the CTs with real entries? Chains [`import-content`](import-content.md) if source data exists. Otherwise leaves entries for manual authoring.
> **Offer 5: verify + deploy.** Run [`verify-setup`](verify-setup.md) end-to-end and [`deploy-studio-site`](deploy-studio-site.md).

An agent accepting all five drives the full site build with no manual canvas clicks. Failures at any offer stop the pipeline and report which step needs attention, see [`import-content`](import-content.md) for the resume semantics.

## Inputs needed from the user

1. The whole-site design (Figma URL, folder of screenshots, description doc, or sitemap).
2. Target Contentstack stack UID + a CMA credential resolved per [`authenticate-cma`](authenticate-cma.md) (OAuth first); a management token only if the user prefers one.
3. Any existing schema / components in the stack that should be reused rather than re-created.
4. Which page kinds are in scope (in case the design has out-of-scope pages).

## Acceptance

- [ ] Every page kind from the design has a corresponding row in the Site plan's page-kinds table.
- [ ] Shared component registry has ≤ 15 entries for a typical marketing site. If more, aggressive merging by prop-shape wasn't done.
- [ ] Every field shape appearing on 2+ CTs is a Global Field, not a duplicate.
- [ ] Build order is a strict topological sort. No Section depends on a Section built later. No Template depends on a Section not yet authored.
- [ ] `docs/site-build-plan.md` + one `docs/<template-slug>-build-sheet.md` per page kind emitted.
- [ ] Every page's build sheet references the shared registry for reused components, not new proposals.
- [ ] Closing offer block accurately counts new vs existing components.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Proposing per-page atomic variants (`BlogHeading`, `ProductHeading`) | Registration explosion, brand-drift risk, template authors confused which to use | Merge by prop-shape into one `Heading` component with a `level` choice prop. Same for `Text`, `Image`, `Button`. |
| Missing GF opportunities | Every CT has its own `hero: group`. Editing the hero shape means 5 schema changes. Zero cross-page auto-binding. | Any group appearing on 2+ CTs is a GF candidate. Extract before finalizing the schema. |
| Circular dependencies in build order | Section A binds to a Reference to CT B, but B references A. Chicken-and-egg. | Order: register components first, then provision the schema all at once, then author Sections in topological order. If two Sections depend on each other, one must be extractable to a Layer-2 container inside the other. |
| Emitting one giant build sheet instead of per-template files | Unusable for per-page focus. Downstream skills expect one sheet per template. | One `<template-slug>-build-sheet.md` per page kind. Site plan is the index. |
| Skipping the "confirm page kinds" step | User's design has 30 frames but only 8 are unique page kinds. You decompose 30 identical things | Ask the user to confirm the list of page kinds after Step 1 before proceeding. |
| Treating a variant board as N page kinds | Six hero treatments become six Sections and six near-identical component sets. The palette becomes unusable and a copy change means six edits | Run Step 1b first. Collapse appearance-only axes into `choice` props. Only a different field set earns a new Section. |
| Waiting for the content model before building any Section | The board has 22 frames and the CT does not exist yet, so nothing gets built and the design is never validated against the primitives | Author skeletons first: structure with static values, bind later. [`author-composition-practice`](author-composition-practice.md) § Skeleton first, bind later. |

## See also

- [`design-component-library`](design-component-library.md): the pattern the multi-page decomposition converges on. Every atom + layout deduplicated across templates should map to one of the 10 primitives (or become a candidate addition to the library, per the additive-growth rule).
- [`decompose-design`](decompose-design.md): per-template skill this orchestrator loops. Same output format per template.
- [`build-page-builder-template`](build-page-builder-template.md): assembles the collapsed Sections into one template an author can compose per page.
- [`author-composition-practice`](author-composition-practice.md) § Skeleton first, bind later: build the Sections before the schema exists.
- [`plan-studio-architecture`](plan-studio-architecture.md): requirements-first planner. Complementary. Use `plan-studio-architecture` when the input is a requirements doc. Use `decompose-site` when the input is a visual design covering multiple pages.
- [`provision-studio-stack`](provision-studio-stack.md): schema provisioning. Chained by Offer 1.
- [`register-component`](register-component.md): component registration. Chained by Offer 2.
- [`import-content`](import-content.md): content ingestion. Chained by Offer 4.
- [`decompose-design`](decompose-design.md): the three-layer taxonomy this skill applies at scale.
- [`decompose-design`](decompose-design.md): the three-layer taxonomy this skill applies at scale.
