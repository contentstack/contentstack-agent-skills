# migrate-page-to-studio


## When to use

FINAL step of a section-first migration: swap one route from hand-coded JSX to `<StudioComponent />` after components, sections, and template exist in Studio.

Use ONLY after section-first setup is done — "migrate my blog route to Studio", "swap this page to <StudioComponent />". Pre-requisites: components registered, sections built, template built, Studio installed and project configured. Per-route by design — never invoke across multiple routes. Does NOT build sections/templates; if missing, stop and run `build-section` first.

# Migrate one hand-coded page to a Studio template

## Context

This skill is the **final step** of a section-first migration. The order is:

1. **Register components** (`register-component`) — one-off, per component.
2. **Build sections** (`build-section`) — Studio sections that mirror recurring compositions across your routes.
3. **Build templates** — almost always `build-connected-template` (the default; migrate INTO Connected even for one-off pages, via a single-entry CT).
4. **Swap the route file** (this skill) — only NOW does the route file change.

If sections or templates don't exist yet, STOP — run the relevant skills first. See `docs/40-recipes/migrating-hand-coded-pages-to-studio.md` for the full section-first migration recipe; this skill is its Step 5.

**Catch-all is the destination.** This skill swaps ONE route file at a time — useful for incremental migration. Once you've migrated more than a handful of routes, consolidate to a single catch-all (`app/[[...slug]]/page.tsx` for Next.js, `<Route path="*">` for React Router) via [`setup-template-preview-routes`](../setup-template-preview-routes/SKILL.md). The catch-all lets Studio resolve every URL via its CDA query — you stop maintaining one route file per URL. Per-route swapping is the path; the catch-all is the destination.

The route-swap itself is a four-step transform:

1. **Inventory** — read the route, list the components it uses, list the entry-field-to-prop bindings.
2. **Decide** — for each component: is it registered with Studio? For the route as a whole: does it do anything Studio can't represent (custom fetching, route-level state, A/B in tree)?
3. **Scaffold** — create a Studio Connected template + section structure with the bindings pre-populated.
4. **Swap** — replace the route's JSX with `<StudioComponent specOptions={…} />`. Preserve the original as a commented block above the new render so the user can diff.

The skill is conservative — it stops on anything it can't represent cleanly. Better to surface a blocker than silently strip behaviour.

Reference: `docs/40-recipes/migrating-hand-coded-pages-to-studio.md` (the multi-route playbook), `docs/31-templates/overview.md`, `docs/32-sections/overview.md`.

## Task

1. **Read `routeFilePath`.** Parse the JSX. Build an inventory:
   - **Components used.** Every JSX element that's a capital-letter identifier (`<Hero>`, `<Body>`, `<RelatedPosts>` — not `<div>`, `<a>`).
   - **Prop bindings.** For each component, every prop and the expression assigned to it. Two patterns to recognise:
     - Direct field reads: `headline={entry.title}` → binding `headline ← template.title`
     - Nested object reads: `cover={entry.featured_image.url}` → binding `cover ← template.featured_image.url`
   - **Data fetching.** The entry lookup at the top of the route (`stack.entry(...)`, `useCompositionData(...)`, `getStaticProps`, etc.). Confirm it's a single-entry fetch by uid/slug — flag anything else.
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
   import { StudioComponent, useCompositionData } from "@contentstack/studio-react";

   export default function BlogPost({ params }) {
     const { specOptions, isLoading, error } = useCompositionData({
       url: `/blog/${params.slug}`,        // or the pathname for this route
       templateContentTypeUid: "blog_post", // narrows resolution to this CT
     });
     if (isLoading) return null;
     if (error) throw error;
     if (!specOptions) return null;   // hook may return null before resolving
     return <StudioComponent specOptions={specOptions} />;
   }
   ```

   Print the diff to chat for review before writing the file.

6. **Verify.** Invoke `verify-setup` once the rewrite is applied. If Layer 4 (Studio canvas) renders the template, the migration succeeded. If anything fails, restore the original JSX from the preserved comment and report which layer broke.

7. **Output the next-step checklist** — a short list of:
   - Other routes in the same file tree that look like migration candidates (same content type, similar shape)
   - The estimated complexity for each
   - The order the user should tackle them in

## Inputs needed from the user

In order:

1. `routeFilePath` — required. Must be a real file the skill can read.
2. `contentTypeUid` — required. Skill does not infer this; the user knows the right CT.
3. `urlPattern` — required. Default to the route's filesystem path with Next.js-style `[slug]` segments converted to `{{entry.slug}}` if obvious; ask if not.
4. `studioProjectId` — required.

Do NOT proceed past step 1 (inventory) if the route file cannot be read or parsed.

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] The convertibility report listed every JSX component the route uses — no component dropped silently.
- [ ] Every prop assignment in the original JSX was either represented as a Studio binding OR explicitly listed as a blocker.
- [ ] If any blocker was reported, the skill stopped and did NOT proceed to scaffold.
- [ ] If the skill proceeded - a new Connected template exists in the Studio project with bindings populated; the user did NOT re-author bindings in the canvas.
- [ ] The route file is rewritten - new render is `<StudioComponent specOptions={…} />`; original JSX is preserved as a commented block above so the user can diff.
- [ ] `verify-setup` ran and Layer 4 (Studio canvas) renders the converted template successfully.
- [ ] A next-step checklist of further route candidates was printed.
- [ ] **The skill operated on exactly ONE route file. Never attempted to migrate multiple routes in one invocation.**

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Trying to migrate multiple routes in one call | Skill is per-route by design; bulk migration burns the team out and hides per-route blockers | Invoke once per route. Use the next-step checklist to schedule the next one. |
| Silently dropping JSX behaviour that doesn't fit (a `useEffect`, a conditional, an A/B check) | The migrated route renders differently than the original; bugs land in prod | Stop on blockers. Surface them. Migrate manually, or skip this route. |
| Inferring `defaultValue` or static text from the route's literal strings | Hard-coded strings in JSX are often placeholders for entry fields the dev forgot to bind | Mark hard-coded strings as TODO bindings in the report; ask the user before scaffolding |
| Skipping `register-component` for already-registered components but using a different `type` UID | Registration silently overrides the existing one | Match the registered component's existing `type` UID exactly; don't invent a new one |
| Scaffolding the template without first running `register-component` for unregistered ones | The template's bindings reference unregistered types and render as "Component Loading Error" | Always chain `register-component` first; never assume registration |
| Discarding the original JSX without preserving it as a comment | Rollback requires git history; user can't easily diff visually | Always keep the original as a commented block in the rewritten file |
| Failing to invoke `verify-setup` after the swap | The route may render blank in prod and you wouldn't know until a visitor hits it | Verify before declaring success |
| Inferring `templateEntryUid` wrong (e.g. passing `params.slug` when the entry is looked up by a different field) | The route fetches the wrong entry or 404s | Re-read the original entry-fetch code carefully; use the same lookup key Studio's spec resolver expects |

## Where does call-site display logic go?

Hand-coded pages routinely do data massage at the call site — before passing to the wrapper — that Studio bindings (bare `field → prop` paths) cannot express. If that logic is silently dropped on migration, the composed page renders with wrong or missing values. Route every piece of call-site logic to one of these five homes, in order:

| Call-site pattern | Where it goes in Studio |
|---|---|
| **Prop reroute** — `props.copy = entry.short_description ?? entry.description` | Inside the leaf adapter — accept `copy` as prop, adapter selects the source field. |
| **String composition** — `subtitle = "Related to " + entry.title`, `title = "How to " + method` | Bind the raw entry field (`entry.title`, `entry.url`) directly to a component's scalar prop and let the component do the composition (`"Related to " + props.title`). If the composition happens inside a nested section-scope context, expose the composed value as a `string` prop on the section and set it per-composition. |
| **Per-CT / per-branch fallbacks** — `image = entry.tile_data?.thumb ?? entry.image` where the shape differs per content type | Per-branch bindings inside a Condition Block — each branch points at the right path for that CT. See `use-condition-block`. |
| **Boolean flags / literal props** — `<Card isInteractive={false} variant="compact" />` | Registered scalar prop with the call-site literal as `defaultValue`. Missed literals are the #1 cause of "looks similar but off." See `register-component` § *Call-site literal sweep*. |
| **Computed values** — anything requiring runtime data massage the picker can't do (URL builders, formatters, external lookups) | Flag as a **product gap**, don't hack. Options: (a) do the massage in the host app before passing via `<StudioComponent data={…} />`, (b) do it in the leaf adapter body, (c) file it against the picker's missing coercion (Part 1 #2 in improvements). Do not re-implement complex logic inside the wrapper adapter — that's how drift accumulates unbounded. |

Rule of thumb: **if the call site is doing anything the Data Picker can't express in a bare path, the migration must decide where that logic lives — adapter / static / branch / product-gap.** Silently dropping it is not an option.

## Recommended migration shape — top-down

If the route you're migrating is rendered by a **compound component** (an outer wrapper that iterates and dispatches to inner components), start by authoring ONE Section that wraps the whole compound. Studio renders the existing page inside its canvas in ~5 minutes with no source-code changes. Marketing gains a real win (change bound content, publish without a deploy) at that first checkpoint.

Only decompose further when a specific inner level needs to become author-editable — reorder body blocks, swap a variant, add a new block type. At each drill-down step: author the next Section, preview it in Studio's canvas, verify the inner sub-tree still renders, then decide whether to go deeper. Every step is opt-in; every step is reversible.

For each Section you author along the way, use [`build-section`](../build-section/SKILL.md) or [`build-repeating-section`](../build-repeating-section/SKILL.md). Full worked example with a 4-level nested schema: From components to Studio compositions.

## See also

- `docs/40-recipes/migrating-hand-coded-pages-to-studio.md` — the multi-route migration playbook (this skill is per-route; that recipe is the program around it)
- `docs/40-recipes/add-studio-to-a-visual-editor-app.md` — Visual Editor projects don't migrate; they layer Studio on top of VE. This skill is optional on VE projects (use it only for routes where you want to switch from hand-coded JSX to a Studio-authored composition).
- `register-component` — chained by this skill for unregistered components
- `build-section` / `build-repeating-section` — chained per Section written during the migration
- `build-connected-template` — chained by this skill for the template scaffold
- `verify-setup` — chained by this skill at the end
- `docs/31-templates/connected-content-type.md` — the model this skill produces
