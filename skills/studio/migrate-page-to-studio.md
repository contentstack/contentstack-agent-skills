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

> **Structure: the [Section rule](SKILL.md#section-rule) applies to migrations too.** One Section per page region, on the first pass. Inside a Section, the production component is reused whole only when it is interactive or computes its values. Everything else is rebuilt from the project's primitive library ([`plan-studio-architecture`](plan-studio-architecture.md) Step 2c). Don't restate or relax that rule here.
>
> **Design-fidelity contract: the migrated render MUST be visually identical to the original page.** Migration re-homes the SAME UI into Studio. It never redraws it. This is the definition of done, and the user should never have to point out that the design drifted:
> - **A component kept whole is the EXACT production component**, registered as-is (see [`register-component`](register-component.md)). Never a lookalike or a "close enough" reimplementation.
> - **A decomposed region gets its fidelity from the library**, not from approximation: the library's design props carry the original classes and tokens, with defaults that reproduce today's render.
> - **A list whose layout depends on item position or count** (a bento mosaic, 1-big-plus-small) is a component that computes its layout: keep it whole and bind the array. A uniform list is a Repeater inside a layout primitive.
> - **Per-field bindings reproduce the original's structure and order**, not an approximation.
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
   - **Route-level SEO and build exports.** `generateMetadata` / `metadata`, JSON-LD `<script>` tags, `generateStaticParams`, `revalidate`. They are not blockers: they stay in the route through the swap (step 5). List them so none is dropped.
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

   KEPT IN THE ROUTE:
     generateMetadata, JSON-LD (BlogPosting), generateStaticParams

   BLOCKERS: none
   ```

   If the **BLOCKERS** section is non-empty, **STOP**. Print the blockers, explain that this route isn't a clean migration candidate, and suggest manual conversion or skipping it. Do not attempt to scaffold.

3. **Register any unregistered components.** For each `⚠ not registered` line, invoke `register-component` (chain the skill) with the component's source file. If a component's source can't be located, stop and ask the user where it lives.

4. **Scaffold the Studio composition.** With every component now registered, create the Connected template via Studio's web UI flow OR by chaining `build-connected-template`:
   - Connected content type: `contentTypeUid`
   - URL pattern: `urlPattern`
   - Template root: **one Section per page region**, in the route's render order ([Section rule](SKILL.md#section-rule)). Never one Section for the whole route
   - **For each region:** build its Section from the library primitives (or the production component the rule keeps whole) and apply the bindings detected in step 1, so the user does not re-author them
   - **Bind one field per prop.** See § Studio fetches only the fields your bindings name, below, before binding any whole entry or reference to an `object` prop
   - Save the template

5. **Generate the swap: server-rendered, with the route's SEO kept.** Rewrite `routeFilePath` so the server fetches the composition through the canonical [`resolveComposition`](configure-csr-vs-ssr.md#resolve-composition-helper) helper (it lives in `configure-csr-vs-ssr`, don't write a second one) and renders through the `"use client"` wrapper from [`configure-csr-vs-ssr`](configure-csr-vs-ssr.md) step 3. Next.js App Router shown. Other frameworks: same contract, that skill's recipe for the framework.

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

   // app/blog/[slug]/page.tsx — a Server Component: NO "use client"
   import { notFound } from "next/navigation";
   import { getSSRStyles } from "@contentstack/studio-react";
   import { sdk } from "@/lib/studio.server";                      // server-only Studio init
   import { resolveComposition } from "@/lib/resolve-composition"; // configure-csr-vs-ssr
   import { ClientRender } from "@/components/studio/ClientRender"; // "use client" wrapper, configure-csr-vs-ssr step 3
   import { getPost, blogPostingJsonLd } from "@/lib/blog";          // the app's own helpers, unchanged

   // KEPT from the original route, unchanged: they read the entry, not the composition.
   export async function generateStaticParams() { /* original body */ }
   export async function generateMetadata({ params }) { /* original body */ }

   export default async function BlogPost({ params, searchParams }) {
     const { slug } = await params;                                  // a Promise on Next 15+
     const searchQuery = new URLSearchParams((await searchParams) as Record<string, string>).toString();
     const { specOptions, notFound: miss } = await resolveComposition(sdk, {
       url: `/blog/${slug}`,
       templateContentTypeUid: "blog_post",                          // narrows resolution to this CT
       searchQuery,
     });
     if (miss) notFound();      // no composition or no entry at this URL: the app's 404, never a 500
     const post = await getPost(slug);                               // the app's own fetch, for JSON-LD only
     return (
       <>
         <script type="application/ld+json"
           dangerouslySetInnerHTML={{ __html: JSON.stringify(blogPostingJsonLd(post)) }} />
         <style dangerouslySetInnerHTML={{ __html: getSSRStyles(specOptions.spec) }} />
         <ClientRender specOptions={specOptions} />
       </>
     );
   }
   ```

   Rules for the swap:

   - **A missing page stays a 404.** `fetchCompositionData` throws on a miss. `resolveComposition` turns only the not-found case (`isCompositionNotFound`, exported by `@contentstack/studio-react`) into `notFound()` and rethrows every real failure. Never `if (error) throw error` on a client hook: every bad URL becomes a 500.
   - **SEO survives.** Keep `generateMetadata`, the JSON-LD and `generateStaticParams` exactly as the original route had them. If the composition's own SEO fields should drive the head instead, build it from the fetched `specOptions` with `getCompositionMetadata(specOptions, { baseUrl })` (exported by `@contentstack/studio-react` and `@contentstack/studio-react/rsc`; it returns `title`, `description`, `ogImage`, `canonical` and `tags`). `renderMetadataToHtml` renders the same object to a string for non-React hosts. Pick one source per tag, never both.
   - **Reading `searchParams` makes this route dynamic.** That is what lets Live Preview and the editor pass their hash. What it does to static generation and caching, and how to keep the app's strategy: [`configure-csr-vs-ssr`](configure-csr-vs-ssr.md).
   - **Client-only fallback.** On a framework with no server render, use the CSR recipe in `configure-csr-vs-ssr` step 2, which classifies `error` with `isCompositionNotFound` and renders the app's 404 for a miss.

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
- [ ] The route file is rewritten - new render is `<StudioComponent specOptions={…} />` (through the client wrapper), fetched server-side via `resolveComposition`. Original JSX is preserved as a commented block above so the user can diff.
- [ ] **A bad URL returns the app's 404, not a 500**, checked with `curl -s -o /dev/null -w '%{http_code}'` on a slug that doesn't exist.
- [ ] **The route's metadata, JSON-LD and static params survived the swap**: every item under KEPT IN THE ROUTE in the report is still exported or rendered.
- [ ] **One Section per page region**, per the [Section rule](SKILL.md#section-rule), and every whole-entry `object` prop either replaced by per-field bindings or backed by an explicit field request (§ Studio fetches only the fields your bindings name), verified on the live route.
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
| Declaring success on "it renders" without comparing to the ORIGINAL design | Design drift ships (a crude lookalike, a position-dependent layout flattened to a uniform Repeater, a section rendering blank because a prop collapsed or received only some fields) and the USER catches it, re-prompting "the design doesn't match" | Run the before/after visual-parity gate (step 6). Capture the original render first, compare after, fix any drift before declaring done |
| Rebuilding an interactive or computing component as a hand-authored lookalike | Loses its behavior and exact layout. The user sees a "close but wrong" render and has to correct it | Register the app's actual component whole, as the [Section rule](SKILL.md#section-rule) says for these two cases |
| Registering a presentational component whole "for fidelity" | One block an author can't restructure, and a coarse prop that only receives the fields bound to it (§ Studio fetches only the fields your bindings name) | Rebuild it from the library primitives with per-field bindings. The library's design props carry the original classes |
| Client-rendered swap with `if (error) throw error` | Every bad URL becomes a 500, and the route loses its metadata, JSON-LD and static params | Server-rendered swap through `resolveComposition` (step 5), SEO exports kept |
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

## Studio fetches only the fields your bindings name

This bites migrations more than any other build, because the original route passed whole entries to its components. On the live site the SDK projects the Delivery API query (`only[]`) down to the fields the composition's bindings name. Inside the editor it fetches everything. So a whole referenced entry bound to one `object` prop renders fully while you author and arrives as little more than its `uid` on the published page, with no error. Measured on a product card: no title, price or images.

- **Bind one field per prop**: the default, and what the [Section rule](SKILL.md#section-rule) already asks for on presentational components.
- **A component kept whole that genuinely needs the whole entry** (interactive, or computing from many fields): request the extra fields explicitly. The options in 2.0.1, `extendQuery.only` (deprecated, still honoured) or fetching the data yourself through the `data` prop, and their caveats are defined once in [`register-component-prop-contracts`](register-component-prop-contracts.md) § Studio fetches only the fields your bindings name. Pass `extendQuery` as the third argument of `resolveComposition`, which forwards it to `fetchCompositionData`.

Verify on the published route in a plain browser tab, not in the editor: the editor fetches everything and hides the gap.

## Migration shape: region by region

Every pass produces one Section per page region ([Section rule](SKILL.md#section-rule)). A route rendered by a **compound component** (an outer wrapper that iterates and dispatches to inner components) is split at its regions first, never wrapped in one Section. For a modular-blocks body, [`decompose-blocks-page`](decompose-blocks-page.md) gives one Section per block type, and leaves the render byte-identical.

Work one region at a time: author its Section, preview it on `/canvas`, compare it against the original, then move to the next. Inside a region, the component the rule keeps whole stays whole. Everything else is built from the primitive library.

For each Section you author along the way, use [`build-section`](build-section.md) or [`build-repeating-section`](build-repeating-section.md).

## See also

- `register-component`: chained by this skill for unregistered components
- `build-section` / `build-repeating-section`: chained per Section written during the migration
- `build-connected-template`: chained by this skill for the template scaffold
- `verify-setup`: chained by this skill at the end
