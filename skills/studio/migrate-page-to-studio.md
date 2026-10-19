---
name: migrate-page-to-studio
---

## When to use

FINAL step of a section-first migration: swap one route from hand-coded JSX to `<StudioComponent />` after components, sections, and template exist in Studio.

Use ONLY after section-first setup is done: "migrate my blog route to Studio", "swap this page to <StudioComponent />". Pre-requisites: components registered, sections built, template built, Studio installed and project configured. Per-route by design, never invoke across multiple routes. Does NOT build sections/templates. If missing, stop and run `build-section` first.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Migrate one hand-coded page to a Studio template

> **Approved plan required.** This skill builds. It does not decide. If there is no plan the user has explicitly approved (Sections with their linked schemas, Section Slots, per-Section components, registered vs built-in, bindings, and the template kind), **stop and run [`plan-studio-architecture`](plan-studio-architecture.md) first**, then come back with the approved block for this piece. Building without it is how a project ends up as one monolithic template with no Sections, no slots and no reuse. Exception: the user is explicitly iterating on a piece already in an approved plan.

## Context

If the ask is the whole project rather than one route ("convert my project", "make it Studio-compatible"), stop and run [`convert-project-to-studio`](convert-project-to-studio.md) first. Its minimal conversion wires Studio behind the existing routes without touching them, and this skill is the option-2 follow-on.

This skill is the **final step** of a section-first migration. The order is:

1. **Register components** (`register-component`), one-off, per component.
2. **Build sections** (`build-section`), Studio sections that mirror recurring compositions across your routes.
3. **Build templates**: almost always `build-connected-template` (the default. Migrate INTO Connected even for one-off pages, via a single-entry CT).
4. **Swap the route file** (this skill). Only NOW does the route file change.

If sections or templates don't exist yet, STOP. Run the relevant skills first (`discover-sections`, `build-section`, `build-connected-template`). This skill is the last step of a section-first migration.

**Catch-all is the destination.** This skill swaps ONE route file at a time, useful for incremental migration. Once you've migrated more than a handful of routes, consolidate to a single catch-all (`app/[[...slug]]/page.tsx` for Next.js, `<Route path="*">` for React Router) via [`setup-template-preview-routes`](setup-template-preview-routes.md). The catch-all lets Studio resolve every URL via its CDA query. You stop maintaining one route file per URL. Per-route swapping is the path. The catch-all is the destination.

**The consolidation step is not just a route swap.** A catch-all takes over every URL the app didn't explicitly claim, so the header/footer that the replaced pages rendered, and the app's own 404 page, both need re-wiring. `setup-template-preview-routes` step 4a handles this and will ask you to choose wildcard vs dedicated first. Per-route swapping (this skill) leaves chrome and 404 untouched. That's exactly why it's the safe incremental path.

The route-swap itself is a four-step transform:

1. **Inventory**: read the route, list the components it uses, list the entry-field-to-prop bindings.
2. **Decide**: for each component: is it registered with Studio? For the route as a whole: does it do anything Studio can't represent (custom fetching, route-level state, A/B in tree)?
3. **Scaffold**: create a Studio Connected template + section structure with the bindings pre-populated.
4. **Swap**: replace the route's JSX with `<StudioComponent specOptions={…} />`. Preserve the original as a commented block above the new render so the user can diff.

> **Design-fidelity contract: the migrated render MUST be visually identical to the original page.** Migration re-homes the SAME UI into Studio. It never redraws it. This is not aspirational. It is the definition of done, and the user should never have to point out that the design drifted. For every block:
> - **1:1 reuse is the DEFAULT. Decomposition is opt-in.** Each component the original route renders maps to the SAME registered component in Studio, bound to the whole object/array, so the layout is identical by construction, right on the first render, with no correction round-trip. Do NOT split a block into a Repeater + per-item components or child Sections **unless the user explicitly asked to make items author-editable.** Decomposition re-lays-out the block (a uniform sequence instead of the original's bespoke arrangement) and is the #1 cause of first-render drift, the exact failure that makes a user re-prompt "the design doesn't match." When in doubt, reuse whole.
> - **Reuse the EXACT production component**: register it and bind the whole object/array (see [`register-component`](register-component.md)). Never hand-author a lookalike, a "close enough" reimplementation, or a built-in stand-in for a component the app already ships. Registering the real component is the only way brand styling + layout survive.
> - **Never substitute a uniform Repeater for a bespoke/asymmetric layout** (a bento mosaic, a 1-big-plus-small grid, a carousel). A Repeater renders items uniformly in sequence. Different design. Bind the whole array/object to the real component and let its own markup + CSS run (see [`register-component-prop-contracts`](register-component-prop-contracts.md) § Array & object props: binding rules).
> - **Slots and per-field bindings reproduce the original's structure and order**, not an approximation.
>
> "It renders" is not the bar. "It renders identically to the current site" is.

The skill is conservative. It stops on anything it can't represent cleanly. Better to surface a blocker than silently strip behavior.

## Task

1. **Read `routeFilePath`.** Parse the JSX. Build an inventory:
   - **Components used.** Every JSX element that's a capital-letter identifier (`<Hero>`, `<Body>`, `<RelatedPosts>`, not `<div>`, `<a>`).
   - **Prop bindings.** For each component, every prop and the expression assigned to it. Two patterns to recognize:
     - Direct field reads: `headline={entry.title}` becomes the binding `headline ← template.title`
     - Nested object reads: `cover={entry.featured_image.url}` becomes the binding `cover ← template.featured_image.url`
   - **Data fetching.** The entry lookup at the top of the route (`stack.entry(...)`, `useCompositionData(...)`, `getStaticProps`, etc.). Confirm it's a single-entry fetch by uid/slug. Flag anything else.
   - **Blockers.** Anything that isn't "render an entry's fields through components":
     - `useState`, `useEffect`, `useReducer` inside the route
     - Conditional component switches based on runtime state (`{flag ? <A /> : <B />}`)
     - Calls to external APIs in the route body
     - Custom middleware imports
     - A/B / experiment / feature-flag checks affecting the component tree

2. **Print the convertibility report.** Three sections:

   ```
   ROUTE: app/blog/[slug]/page.tsx
   Content type: blog_post

   COMPONENTS USED:
     ✅ Hero          (registered as `site-hero`)
     ⚠ Body          (not registered — will run register-component before scaffolding) <!-- style-lint: allow -->
     ✅ RelatedPosts  (registered as `related-posts`)

   BINDINGS DETECTED:
     Hero.headline       ← template.title
     Hero.subhead        ← template.tagline
     Hero.cover          ← template.featured_image.url
     Body.markdown       ← template.body
     RelatedPosts.ids    ← template.related

   BLOCKERS: none
   ```

   If the **BLOCKERS** section is non-empty, **STOP**. Print the blockers, explain that this route isn't a clean migration candidate, and suggest manual conversion or skipping it. Do not attempt to scaffold.

3. **Register any unregistered components.** For each `⚠ not registered` line, invoke `register-component` (chain the skill) with the component's source file. If a component's source can't be located, stop and ask the user where it lives.

4. **Scaffold the Studio composition.** With every component now registered, create the Connected template via Studio's web UI flow OR by chaining `build-connected-template`:
   - Connected content type: `contentTypeUid`
   - URL pattern: `urlPattern`
   - Template root: one section (or a sequence of sections) matching the route's render order
   - **For each component in the inventory:** drop the registered component onto the section canvas and apply the binding that was detected in step 1 (so the user does not re-author bindings)
   - Save the template

5. **Generate the swap.** Rewrite `routeFilePath`:

   ```tsx
   // Before — preserved as a reference comment so you can diff:
   // export default async function BlogPost({ params }) {
   //   const entry = await stack.entry('blog_post', params.slug);
   //   return (
   //     <>
   //       <Hero headline={entry.title} subhead={entry.tagline} cover={entry.featured_image.url} />
   //       <Body markdown={entry.body} />
   //       <RelatedPosts ids={entry.related} />
   //     </>
   //   );
   // }

   "use client";
   import { use } from "react";
   import { StudioComponent, useCompositionData } from "@contentstack/studio-react";

   export default function BlogPost({ params }) {
     const { slug } = use(params);   // params is a Promise on Next 15+
     const { specOptions, isLoading, error } = useCompositionData({
       url: `/blog/${slug}`,        // or the pathname for this route
       templateContentTypeUid: "blog_post", // narrows resolution to this CT
     });
     if (isLoading) return null;
     if (error) throw error;
     if (!specOptions) return null;   // hook may return null before resolving
     return <StudioComponent specOptions={specOptions} />;
   }
   ```

   Print the diff to chat for review before writing the file.

6. **Verify: visual parity against the original, not just "it renders."** BEFORE the swap, capture the current render (Playwright MCP screenshot if available, plus a note of each section's order, key text, and images. Otherwise have the user capture it). AFTER the swap, capture the Studio render the same way and **compare the two**. The migration succeeds only when they match: same sections in the same order, same images, same text, same layout. Then invoke `verify-setup` (Layer 4 canvas). If the renders differ, that is a binding / component / layout defect, not a pass. Common causes: a prop typed `any` collapsing structured data ([`register-component`](register-component.md) § The `any` flatten trap), an unwired container `props.children` ([`author-composition-bindings`](author-composition-bindings.md) § Node anatomy), or a Repeater swapped in for a bespoke layout. Fix it and re-compare before declaring success. **Do NOT hand the user a "done" they have to visually reject.** If a layer fails outright, restore the original JSX from the preserved comment and report which layer broke.

   For a rigorous section-by-section comparison against a still-shipping production URL, each drift classified by cause and fixed at the source (unbound prop, prop-routing, or **layout-wrapper CSS transcribed line-by-line**), looping until no new drift appears, chain [`verify-visual-parity`](verify-visual-parity.md). That skill reads the real design and closes the gap. This step is the gate, `verify-visual-parity` is the tool it hands off to.

7. **Output the next-step checklist**: a short list of:
   - Other routes in the same file tree that look like migration candidates (same content type, similar shape)
   - The estimated complexity for each
   - The order the user should tackle them in

## Inputs needed from the user

In order:

1. `routeFilePath`: required. Must be a real file the skill can read.
2. `contentTypeUid`: required. Skill does not infer this. The user knows the right CT.
3. `urlPattern`: required. Default to the route's filesystem path with Next.js-style `[slug]` segments converted to `{{entry.slug}}` if obvious. Ask if not.
4. `studioProjectId`: required.

Do NOT proceed past step 1 (inventory) if the route file cannot be read or parsed.

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] The convertibility report listed every JSX component the route uses, no component dropped silently.
- [ ] **Every Section created by this skill has a `ui_preview`**, a blank tile in the Sections accordion otherwise. UI-created sections get one from Studio on Save. API-created ones need one attached explicitly. See [`author-composition-thumbnails`](author-composition-thumbnails.md) (Fixes A–D).
- [ ] Every prop assignment in the original JSX was either represented as a Studio binding OR explicitly listed as a blocker.
- [ ] If any blocker was reported, the skill stopped and did NOT proceed to scaffold.
- [ ] If the skill proceeded - a new Connected template exists in the Studio project with bindings populated. The user did NOT re-author bindings in the canvas.
- [ ] The route file is rewritten - new render is `<StudioComponent specOptions={…} />`. Original JSX is preserved as a commented block above so the user can diff.
- [ ] `verify-setup` ran and Layer 4 (Studio canvas) renders the converted template successfully.
- [ ] **Visual parity confirmed**: the Studio render was compared against the pre-migration render and matches (same sections, order, images, text, layout), not merely "renders." Any drift was traced to a binding / component / layout defect and fixed BEFORE declaring success.
- [ ] A next-step checklist of further route candidates was printed.
- [ ] **The skill operated on exactly ONE route file. Never attempted to migrate multiple routes in one invocation.**

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Trying to migrate multiple routes in one call | Skill is per-route by design. Bulk migration burns the team out and hides per-route blockers | Invoke once per route. Use the next-step checklist to schedule the next one. |
| Silently dropping JSX behavior that doesn't fit (a `useEffect`, a conditional, an A/B check) | The migrated route renders differently than the original. Bugs land in prod | Stop on blockers. Surface them. Migrate manually, or skip this route. |
| Inferring `defaultValue` or static text from the route's literal strings | Hard-coded strings in JSX are often placeholders for entry fields the dev forgot to bind | Mark hard-coded strings as TODO bindings in the report. Ask the user before scaffolding |
| Skipping `register-component` for already-registered components but using a different `type` UID | Registration silently overrides the existing one | Match the registered component's existing `type` UID exactly. Don't invent a new one |
| Scaffolding the template without first running `register-component` for unregistered ones | The template's bindings reference unregistered types and render as "Component Loading Error" | Always chain `register-component` first. Never assume registration |
| Discarding the original JSX without preserving it as a comment | Rollback requires git history. User can't easily diff visually | Always keep the original as a commented block in the rewritten file |
| Failing to invoke `verify-setup` after the swap | The route may render blank in prod and you wouldn't know until a visitor hits it | Verify before declaring success |
| Declaring success on "it renders" without comparing to the ORIGINAL design | Design drift ships (a crude lookalike, a bespoke layout flattened to a uniform Repeater, a section rendering blank because a prop collapsed) and the USER catches it, re-prompting "the design doesn't match" | Run the before/after visual-parity gate (step 6). Capture the original render first, compare after, fix any drift before declaring done. Reuse the real production component. Never hand-roll or decompose a bespoke layout |
| Rebuilding a block as a hand-authored lookalike instead of registering the real component | Loses the exact styling/layout. The user sees a "close but wrong" render and has to correct it | Register the app's actual component and bind the whole object/array. The design comes for free. See the Design-fidelity contract above |
| Inferring `templateEntryUid` wrong (e.g. passing `params.slug` when the entry is looked up by a different field) | The route fetches the wrong entry or 404s | Re-read the original entry-fetch code carefully. Use the same lookup key Studio's spec resolver expects |

## Where does call-site display logic go?

Hand-coded pages routinely do data massage at the call site (before passing to the wrapper) that Studio bindings (bare `field → prop` paths) cannot express. If that logic is silently dropped on migration, the composed page renders with wrong or missing values. Route every piece of call-site logic to one of these five homes, in order:

| Call-site pattern | Where it goes in Studio |
|---|---|
| **Prop reroute**: `props.copy = entry.short_description ?? entry.description` | Inside the leaf adapter: accept `copy` as prop, adapter selects the source field. |
| **String composition**: `subtitle = "Related to " + entry.title`, `title = "How to " + method` | Bind the raw entry field (`entry.title`, `entry.url`) directly to a component's scalar prop and let the component do the composition (`"Related to " + props.title`). If the composition happens inside a nested section-scope context, expose the composed value as a `string` prop on the section and set it per-composition. |
| **Per-CT / per-branch fallbacks**: `image = entry.tile_data?.thumb ?? entry.image` where the shape differs per content type | Per-branch bindings inside a Condition Block: each branch points at the right path for that CT. See `use-condition-block`. |
| **Boolean flags / literal props**: `<Card isInteractive={false} variant="compact" />` | Registered scalar prop with the call-site literal as `defaultValue`. Missed literals are the #1 cause of "looks similar but off." See `register-component` § Acceptance (call-site literal sweep). |
| **Computed values**: anything requiring runtime data massage the picker can't do (URL builders, formatters, external lookups) | Flag as a **product gap**, don't hack. Options: (a) do the massage in the host app before passing via `<StudioComponent data={…} />`, (b) do it in the leaf adapter body, (c) report the missing picker coercion to Contentstack. Do not re-implement complex logic inside the wrapper adapter. That's how drift accumulates unbounded. |

Rule of thumb: **if the call site is doing anything the Data Picker can't express in a bare path, the migration must decide where that logic lives: adapter / static / branch / product-gap.** Silently dropping it is not an option.

## Recommended migration shape: top-down

If the route you're migrating is rendered by a **compound component** (an outer wrapper that iterates and dispatches to inner components), start by authoring ONE Section that wraps the whole compound. Studio renders the existing page inside its canvas in ~5 minutes with no source-code changes. Marketing gains a real win (change bound content, publish without a deploy) at that first checkpoint.

Only decompose further when a specific inner level needs to become author-editable: reorder body blocks, swap a variant, add a new block type. At each drill-down step: author the next Section, preview it in Studio's canvas, verify the inner sub-tree still renders, then decide whether to go deeper. Every step is opt-in. Every step is reversible.

For each Section you author along the way, use [`build-section`](build-section.md) or [`build-repeating-section`](build-repeating-section.md). 

## See also

- `register-component`: chained by this skill for unregistered components
- `build-section` / `build-repeating-section`: chained per Section written during the migration
- `build-connected-template`: chained by this skill for the template scaffold
- `verify-setup`: chained by this skill at the end
