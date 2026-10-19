---
name: discover-sections
---

## When to use

Scan all route files and propose Studio Section candidates by finding components that recur across routes. Outputs a section inventory prioritized by reuse count.

Use at the START of a migration from hand-coded / Visual Editor pages to Studio, BEFORE building any sections. Phrases: "which components should be sections", "migration inventory". Produces the section list `register-component` / `build-section` / `build-connected-template` assume you have. Run once per codebase. Do NOT use for greenfield installs.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them), and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Discover sections: propose a build-order from your existing routes

## Context

Section-first migration depends on knowing which compositions repeat across your routes. This skill produces that inventory automatically.

**Reuse count orders the build. It does not decide what becomes a Section.** A Hero on three routes is Section #1 because it pays off three times. A Hero on one route is still a Section, just later in the queue. Every recognizable page part gets one. See [`plan-studio-architecture`](plan-studio-architecture.md) § Golden rule for why (authoring surface, independent preview, scoped data, retrofit cost). A route whose components all appear exactly once is not a route that skips Sections. It's a route whose Sections are all priority-1-instance. Do not report "no section candidates" for it.

The output is a **section build plan**: a prioritized list of sections to build, with the routes each section will cover, and the components each section needs. You hand the top entry to `build-section`, ship it, then hand the next entry to `build-section`. The plan stays valid until you add a new route shape.

This skill is **discovery, not authoring**. It doesn't write any code or touch Studio's UI. It produces a markdown report.

## Task

1. **Find all route files** under `appRoot` matching `routeGlob`. List each file path.

2. **Extract component usage from each route.** For each file, parse the JSX (acceptable to use a simple regex pass for capital-letter JSX element names (`<Hero>`, `<ProductCard>`, etc.) since this is a heuristic inventory, not a binding-grade parser). Build a `componentToFiles` map: `{ "Hero": [routeA, routeB, routeC], "ProductDetails": [routeB], ... }`.

3. **Score each component.** Sort by route-file count (descending). The score = number of routes that import or use it.

4. **Classify.** For each component:
   - `score >= minOccurrencesForSection` AND component qualifies as a Section (see below) means a **section candidate**
   - `score == 1` **and the component is genuinely atomic** (renders one piece of content) means register-only, no Section needed
   - `score == 1` **and the component is coarse**: a page-level component, or anything rendering several distinct regions is **NOT register-only.** Send it to [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md) first, then re-score its parts
   - Fails qualification for another reason: see the drop list below

   **`score == 1` is not an exemption from decomposition.** This step counts how many routes use a component name. It cannot see inside one. A whole page written as a single `<RewardsPage>` scores 1, and that makes it the **strongest** decomposition candidate, not a register-only singleton. Treating it as one produced the classic outcome: one Section covering an entire page, nothing reusable, authors unable to reorder anything, and one coarse prop swallowing the whole entry. Judge coarseness by what the component renders, not by how many routes reference it.

   Quick test before calling anything register-only: does it render **more than one** heading / image / body / list? If yes, it's coarse. Decompose it.

   **Qualification filter: count the bound props per component.** A Section pays off when the binding work amortizes. The practical test is "how many bindings would an author wire by hand on the next drop?": ≥2 qualifies, 1 does not.

   **Drop from section candidates:**

   - **Components with 1 bound prop to a scalar field**: `<Heading>{entry.title}</Heading>`, `<Image src={entry.cover.url} />`, `<Text>{entry.tagline}</Text>`. One bind = no amortization. Use inline as Basic field components or registered atoms. Studio's picker rejects scalar fields anyway.
   - **Layout-only / no-CMS-binding components**: `<Container>`, `<Stack>`, `<Spacer>` with no entry references in their props.
   - **Framework primitives**: `<Link>` from `next/link`, `<Image>` from `next/image` when used as plain primitives without composition.

   **Keep as section candidates:**

   - **Components with ≥2 bound props**: `<Hero>` with `headline + subhead + cover`, `<ProductCard>` with `image + title + price + cta`. Author would otherwise wire each prop on every drop.
   - **Components with 1 prop bound to a structural shape**: Group / Global Field / Modular Block / Block / Reference. Outer bind is 1 click, but the inside walks N sub-fields per iteration. That work amortizes. Multi-field destructuring is the tell: `<Hero {...entry.hero} />` where `entry.hero` is a Group, `<CardList items={entry.related_posts} />` where `related_posts` is a multi-Reference.

   See [`understand-sections`](understand-sections.md) § What qualifies as a Section for the canonical rule.

5. **Detect co-occurrence groups.** For section candidates, find pairs/triples that **always appear together** across the same files (e.g. `Hero` + `Body` always co-occur on /blog AND /products, so they're likely one section, not two). Group co-occurring candidates into a single proposed section.

6. **Infer linked-schema kind for each candidate.** For each proposed section:
   - Look at the props the component receives on each route. If all routes pass `entry.<fieldname>` for prop X, the section's linked schema needs a field named `<fieldname>`.
   - If the section consistently binds against fields of one content type, propose `linkedSchemaKind: content-type`.
   - If the props come from a nested group on the entry, propose `global-field` (and recommend creating that Global Field in Contentstack first).
   - If unsure, mark as TBD and ask the user during `build-section`.

7. **Order the build plan.** Highest reuse first. Flag dependencies: e.g. Card Grid section depends on Card component being registered + bound, so Card registration comes before Card Grid section.

8. **Emit the report.** Markdown, in this exact shape, easy to copy into a migration spec:

   ```
   ## Section build plan — N sections proposed

   ### Section 1: Hero Strip (reuse: 4 routes)
   - Routes: /blog/[slug], /products/[sku], /case-studies/[slug], /
   - Components to drop: Hero
   - Proposed linkedSchemaKind: global-field
   - Proposed Global Field UID: hero_strip
   - Run next: `register-component` for Hero, then `build-section` Hero Strip

   ### Section 2: Card Grid (reuse: 3 routes)
   - Routes: /blog/[slug] (related), /products/[sku] (related), / (highlights)
   - Components to drop: Card, inside a Repeater
   - Proposed linkedSchemaKind: reference (multi-entry)
   - Run next: `register-component` for Card, then `build-section` Card Grid + `use-repeater`

   ### Section 3: Testimonial Strip (reuse: 2 routes)
   - ...

   ## Singleton components — register-only, no section needed
   - ProductDetails (1 route — /products/[sku])
   - CartSummary (1 route — /checkout)
   - PaymentForm (1 route — /checkout)

   ## Total: 3 sections, 5 singletons, 8 components to register
   ```

9. **Pause for user review.** Don't auto-invoke any other skill. The user reads the plan, may merge or split candidates, then explicitly invokes `register-component` + `build-section` skills for each entry.

## Inputs needed from the user

1. `appRoot`: required. If `app/` exists, default to that. Otherwise ask.
2. `routeGlob`: required (with a sensible default per framework).
3. `minOccurrencesForSection`: default 2. Larger codebases may set 3 or 4.

If the route files use a different convention (e.g. React Router with `Route.tsx` files in nested dirs), broaden the glob with the user's input.

## Acceptance

- [ ] Every route file under `appRoot/routeGlob` was scanned.
- [ ] Component usage table lists every JSX component (capital-letter element name) appearing in at least one file.
- [ ] Section candidates are correctly classified (count >= minOccurrencesForSection).
- [ ] Singletons are listed separately with a "register-component only, no section" note.
- [ ] Co-occurring components (always appear together across files) are proposed as a single section, not two.
- [ ] For each candidate, the proposed `linkedSchemaKind` is one of: `content-type` / `global-field` / `group` / `modular-block` / `reference` / `tbd`. If `tbd`, the report says "ask the user during build-section."
- [ ] Build order is reuse-descending. Dependencies are flagged.
- [ ] The report is plain markdown the user can copy into a spec.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Treating every multi-route component as its own section | Co-occurring components (Hero + Body always on the same routes) should be ONE section, not two | Detect co-occurrence. Group into a single proposed section |
| Inferring `content-type` linked schema when the component binds to nested fields | The author has to refactor mid-build-section | If props come from a group or nested object, propose `global-field` or `group` |
| Proposing sections for components used only on /admin or /internal routes | Internal-tooling routes usually don't need to be authorable | Optional: exclude routes under user-supplied path patterns |
| Counting `<div>`, `<span>`, native HTML elements as components | Inflates the report. Not section material | Filter to capital-letter JSX element names only |
| Re-running on a partially-migrated codebase and counting `<StudioComponent />` as a section candidate | StudioComponent is the renderer, not a section | Skip `StudioComponent`, `StudioCanvas`, `<Suspense>`, and other framework primitives |

## See also

- [`design-component-library`](design-component-library.md): the pattern the discovery targets. This skill runs **Q1 of the [four-question framework](design-component-library.md)** implicitly: components recurring across ≥ 2 routes ARE section candidates (Q1 answer = "compose from existing primitives across routes"). Components appearing on 1 route only fail Q1 and route to `design-component-library` for potential atom/layout registration instead.
- `register-component`: invoke for each component the report lists
- `build-section`: invoke for each section the report proposes
- `design-section-from-jsx`: sibling skill. Given a proposed section, designs the linked-schema shape from the existing JSX
- `migrate-page-to-studio`: final route-swap step, after all sections + templates exist
