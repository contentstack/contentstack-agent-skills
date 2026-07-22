# wire-variant-alias


## When to use

Replace a route-level user-state branch with a Contentstack Personalize-driven render — read variant alias from cookies/headers, pass to `<StudioComponent />` via `variantAlias` query option.

Use during a hand-coded migration when `migrate-page-to-studio` surfaces a user-driven JSX branch (logged-in tier, persona, A/B, geolocation). Personalize handles audiences + variants; Studio renders whichever alias resolves. Do NOT use for content-driven branching (use Condition Block). Do NOT use for layout-shift needing different sections — that's a separate-template decision.

# Wire a route-level branch to variant aliases

## Context

A common hand-coded pattern is to branch on user state inside the JSX:

```tsx
{user.tier === "premium" ? <PremiumHero {...entry.hero} /> : <Hero {...entry.hero} />}
```

Three things are happening at once: (1) a visitor segment is computed, (2) a component swap is wired into the render, (3) the entry data is reused across both branches. Migration to Studio splits these:

- **(1) Visitor segmentation** stays in route code — your cookie/header/middleware logic doesn't change.
- **(2) Component swap** becomes a Contentstack variant alias — each variant has its own version of the entry; the Studio template renders the variant's overrides on top of the base entry.
- **(3) Entry data reuse** is automatic — Studio merges variant overrides onto the base entry; unchanged fields fall through.

The result: ONE template, ONE route, N variants per entry. No code branch in the JSX. No template per persona.

This skill is for **user-driven branching only** — the variant is chosen based on who the visitor is (tier, persona, cookie, A/B). For **content-driven branching** (the variation lives in the entry's own fields), use [`use-condition-block`](../use-condition-block/SKILL.md) instead — that stays in the Studio canvas, no variant aliases needed.

Reference: `docs/50-advanced/variant-aliases-deep-dive.md` (full deep-dive), `docs/40-recipes/migrating-hand-coded-pages-to-studio.md` Step 6 (handling edges).

## Task

1. **Read `routeFilePath`** and locate the `branchExpression`. Confirm it's a user-driven branch (the condition references runtime state — `user`, `cookies`, `headers`, `experiment`, `persona`). If the condition references `entry.<field>`, STOP — that's content-driven branching. Recommend `use-condition-block` instead.

2. **Point the user at Contentstack Personalize** to set up audiences + variant aliases. This skill does NOT call CMA, does NOT write to the stack, and does NOT touch entry data. Personalize is Contentstack's product feature for audience-driven variants; configure it in the Contentstack web app:

   ```
   Open https://app.contentstack.com → your stack → Personalize.

   1. Create an Experience targeted at the routes you're migrating (e.g.
      "<contentTypeUid> personalization"). An Experience is the wrapper
      that holds audiences + variant aliases together.

   2. Define one or more Audiences. An Audience is the visitor-segment
      definition (e.g. "logged-in premium tier", "experiment B cohort").
      Personalize lets you define audiences from cookies, query params,
      headers, or external signals.

   3. For each non-base name in your variants list, create a Variant
      under the Experience:
        - Variant alias UID: <variant>      ← match what your route will pass
        - Display name:      <variant>      ← what authors see in Studio
        - Targeting:         link to one of the Audiences from step 2

   4. Publish the Experience. Personalize handles the cookie/header
      orchestration server-side; your route only needs to read the
      variant cookie/header Personalize sets and forward it to
      <StudioComponent />.
   ```

3. **Per-entry variant overrides** are authored in Contentstack's normal entry editor, in the "Variants" tab of each entry of `contentTypeUid`. Print:

   ```
   Open https://app.contentstack.com → Content → <contentTypeUid> → pick an entry → "Variants" tab.

   For each variant alias you created in Personalize:
   - Click "+ Add Variant".
   - Pick the alias UID (e.g. "premium").
   - Override the fields that differed in your original JSX branch:
     <list the fields the original branch differed on — derived from the branchExpression>
   - Leave other fields empty — they inherit from the base entry.
   - Save.
   ```

   The skill never touches entries; the user configures Personalize + populates variant content themselves.

4. **Generate the route swap.** Rewrite `routeFilePath`:

   ```diff
   - export default async function ProductPage({ params }) {
   -   const user = await getCurrentUser();
   -   const entry = await fetchEntry(params.sku);
   -   return (
   -     <>
   -       {user.tier === "premium"
   -         ? <PremiumHero {...entry.hero} />
   -         : <Hero {...entry.hero} />}
   -       <Body {...entry.body} />
   -     </>
   -   );
   - }
   + import { cookies } from "next/headers";
   + import { sdk } from "@/lib/contentstack";
   + import { StudioComponent } from "@contentstack/studio-react";
   +
   + export default async function ProductPage({ params }) {
   +   const variant = (await cookies()).get("variant-alias")?.value;
   +   const specOptions = await sdk.fetchCompositionData(
   +     { templateContentTypeUid: "product" },
   +     { templateEntryUid: params.sku, variantAlias: variant || undefined },
   +   );
   +   return <StudioComponent specOptions={specOptions} />;
   + }
   ```

   Match the resolver style to `visitorSegmentSource`:
   - `cookie:variant-alias` → read from `cookies()` (App Router) / `req.cookies` (Pages Router) / `useCookies()` (CSR)
   - `header:x-variant` → read from `headers()`
   - `searchParam:variant` → read from URL search params
   - `custom` → leave a TODO comment where the user wires their own resolver

5. **Print the before/after diff** for review. Wait for explicit confirmation before writing the file.

6. **Hand off to the user:**
   - "Open Contentstack → Content Models → `<contentTypeUid>` → an entry → Variants tab. Fill in per-variant overrides for the fields the original branch differed on (e.g. for the `premium` variant: set a different `hero.headline`, swap `hero.cover`, etc.)."
   - "Open Studio → the template the route maps to → use the navbar's variant picker to preview each variant against the preview entry. Confirm the layout renders the variant's overrides."
   - "Wire your middleware / authentication layer to set the `variant-alias` cookie (or whichever segmentation source you picked) per visitor segment."

7. **Run `verify-setup`** at the end. Layer 4 should render the template; switching the cookie value in DevTools should re-fetch the page with the new variant on next request.

## Inputs needed from the user

1. `routeFilePath` — required, real path.
2. `branchExpression` — required. If the user pastes a content-driven branch by mistake (`entry.is_premium ? ...`), redirect to `use-condition-block`.
3. `variants` — required. The first name is the base (the entry's default state); subsequent names are the variants you're authoring overrides for.
4. `contentTypeUid` — required.
5. `visitorSegmentSource` — required. Pre-default to `cookie:variant-alias`; ask if their app uses a different convention.

## Acceptance

- [ ] The skill pointed the user at **Contentstack Personalize** for setting up the Experience + Audiences + Variant Aliases — and made clear it does NOT touch the stack itself, does NOT call CMA, and does NOT need auth tokens or Management Tokens.
- [ ] The skill printed step-by-step UI instructions for scaffolding per-variant entry overrides on one representative entry (via the entry editor's "Variants" tab — the same UI authors use day-to-day).
- [ ] Route file is rewritten with the variant resolver matching `visitorSegmentSource`, and the JSX branch is removed.
- [ ] Before/after diff was shown to the user and they confirmed before write.
- [ ] `verify-setup` ran and Layer 4 (Studio canvas) renders the template against the base entry.
- [ ] User was given the three hand-off tasks: (1) fill in per-variant content in Contentstack, (2) preview each variant in Studio, (3) wire their middleware to set the segment source.
- [ ] If the supplied branch was content-driven (entry-field-based), the skill STOPPED and redirected to `use-condition-block`.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Using variant aliases for content-driven variation | Variant aliases are a per-VISITOR mechanism; using them for entry-shape variation conflates the two concerns and makes future authoring confusing | Content-driven → `use-condition-block`. Visitor-driven → this skill. |
| Forking the template per variant | One template per variant = N times the structural change cost; the whole point of variants is the same template renders all | Always one template; variants live on the entry, not the composition |
| Resolving the variant client-side AFTER the server rendered | Hydration mismatch + content-flash; variant must be resolved BEFORE the SSR fetch | Read cookie/header/middleware before `fetchCompositionData`; pass `variantAlias` to the fetcher |
| Forgetting to set the variant in the cache key | CDN serves all visitors the variant of the first request | `Vary` on the segmentation header, or include the variant in the URL/cache key, or revalidate per request for variant-aware routes |
| Creating variants on the stack but not on the entry | Studio's variant picker shows the alias but no overrides exist; the canvas renders the base everywhere | Step 3 of this skill scaffolds the entry-override skeleton — confirm it ran |

## See also

- `docs/50-advanced/variant-aliases-deep-dive.md` — full deep dive: A/B, personalisation, seasonal variants, cache strategy, edge cases
- `use-condition-block` — for content-driven branching (the variant decision lives in the entry, not in visitor state)
- `migrate-page-to-studio` — the final route-swap skill; this skill handles ONE specific edge that surfaces during migration (user-driven branch)
- `docs/40-recipes/migrating-hand-coded-pages-to-studio.md` Step 6 — the recipe section that names this skill as the translation for user-driven branches
- `wire-external-data` — sibling skill for cases where the branch needs external data (not just visitor state) to decide
