---
name: embed-composition
description: "Embed a Studio-managed editable region inside a code-owned page using `useCompositionData({ compositionUid })`. Section-in-Slot, not raw component."
allowed-tools: Read Grep Glob
---

## When to use

Embed a Studio-managed editable region inside a code-owned page using `useCompositionData({ compositionUid })`. Section-in-Slot, not raw component.

Use when exposing ONE editable region inside a code-owned page — marketing band on a PDP, promo strip, recommendations shelf — without making the whole page Studio-managed. Phrases — "embed a Studio band", "marketer-editable PDP region", "promo strip", "one editable section". Skip if the user wants the whole page in Studio (`migrate-page-to-studio`) or every URL through Studio (`setup-template-preview-routes`).

# Embed a Studio-managed region inside a code-owned page

## Context

This skill operationalizes the Embed composition recipe. The user has a code-owned page (PDP, checkout, home, account); one region should be marketer-editable without code changes.

Mechanism: `useCompositionData({ compositionUid })` resolves a known composition by its slug; the result hands to `<StudioComponent specOptions={specOptions} />` rendered inline. A Section composition renders correctly through this path.

## Pre-flight checks

Stop and report if any are missing:

1. **`install-studio` already ran.** Check `package.json` for `@contentstack/studio-react`, and verify a stack init exists (typically `lib/contentstack.ts` or `lib/studio.ts` with `export const sdk = studioSdk.init({...})`).
2. **Components are registered** at the app shell — at least the components that the embedded composition uses.
3. **Studio project is configured** — Project Settings → Configuration filled in (Environment, Language, Canvas URL pointing at the section-authoring route).
4. **Target page file exists** and contains the `insertionAnchor`. If the anchor isn't found, report the file's first 20 lines and ask the user to specify a better anchor.

## Task

### Step 1 — Show the user the Studio UI steps for creating the composition

Print this VERBATIM (substitute `{bandName}` and `{compositionFlavor}`):

```
First, you'll create the composition manually in Studio. Open
https://app.contentstack.com → your stack → Studio → your project →
Templates → "+ New Template" → pick {compositionFlavor}.

Configure it as:
  Display Name:    {bandName} (use Title Case — Studio will auto-fill)
  composable_uid:  {bandName}   ← THIS is the slug the embed will reference
  Description:     "Embedded band inside <target page>. Edited by marketing;
                    rendered inline by code via useCompositionData."

default. The URL is never visited by a visitor in the embed case; it
only exists for Studio's iframe to preview the composition during
authoring.

If you chose section: there's no URL to configure. Studio uses the
section-authoring canvas to preview it.

SAVE the composition. Then come back here and I'll wire the React side.
```

Then PAUSE and wait for the user to confirm: *"Composition created."* Do NOT proceed until they confirm — the embed code references the `composable_uid` that doesn't exist yet.

### Step 2 — Scaffold the `<StudioEmbed>` wrapper (if not present)

> **⚠ Clarification — `<StudioEmbed>` is NOT an SDK export.** This skill scaffolds a thin wrapper component **inside the user's codebase** that bundles the SDK's `useCompositionData` hook + `<StudioComponent />` renderer. The SDK ships only those two primitives; the wrapper exists purely to avoid repeating loading/error boilerplate on every embed. The wrapper can be named anything — `<StudioEmbed>`, `<ManagedBand>`, `<EditableRegion>`, etc. — this skill uses `StudioEmbed` as a sensible default. If the user prefers a different name, accept it.

Check whether the project already has such a wrapper component at `src/components/StudioEmbed.tsx` (Vite/CRA) or `app/_components/StudioEmbed.tsx` (Next.js App Router) or any path containing both `useCompositionData` AND `StudioComponent` AND `compositionUid` (`grep -rEn "useCompositionData.*compositionUid" src/ app/ 2>/dev/null | head -3`). If found, reuse it. If not, emit one:

**Vite / React Router / CRA — `src/components/StudioEmbed.tsx`:**

```tsx
"use client";  // harmless in non-Next; Next App Router needs it
import {
  useCompositionData,
  StudioComponent,
} from "@contentstack/studio-react";

interface StudioEmbedProps {
  /** composable_uid slug of the Studio composition to embed */
  compositionUid: string;
  /** rendered while the composition is loading; default: null (no layout shift) */
  fallback?: React.ReactNode;
}

/**
 * Render a Studio-managed composition inline inside a code-owned page.
 * Verified pattern (see docs/40-recipes/embedding-a-composition-in-a-code-owned-page.md).
 *
 *   <StudioEmbed compositionUid="pdp_marketing_band" />
 */
export function StudioEmbed({ compositionUid, fallback = null }: StudioEmbedProps) {
  const { specOptions, isLoading, error } = useCompositionData({ compositionUid });

  if (isLoading) return <>{fallback}</>;
  if (error || !specOptions?.spec) {
    if (process.env.NODE_ENV === "development") {
      console.warn(
        `[StudioEmbed] No composition found for compositionUid="${compositionUid}". ` +
        `Either it's not created yet, the slug is misspelled, or it was deleted in Studio.`,
      );
    }
    return null;
  }
  return <StudioComponent specOptions={specOptions} />;
}
```

**Next.js App Router CSR variant** — same file content, marked `"use client"` (already shown above).

**Next.js App Router SSR variant (when the embed must render server-side)** — emit BOTH a server fetcher and a client wrapper. Use this when the surrounding page is a Server Component:

```tsx
// app/_components/StudioEmbed.tsx — Server Component (no "use client")
import { sdk } from "@/lib/contentstack";    // or @/lib/studio for additive integrations
import { StudioEmbedClient } from "./StudioEmbedClient";

export async function StudioEmbed({ compositionUid }: { compositionUid: string }) {
  const specOptions = await sdk.fetchCompositionData({
    compositionUid,
    searchQuery: "",       // required on server (no window.location.search)
  });
  if (!specOptions?.spec) return null;
  return <StudioEmbedClient specOptions={specOptions} />;
}
```

```tsx
// app/_components/StudioEmbedClient.tsx — Client Component
"use client";
import { StudioComponent } from "@contentstack/studio-react";
export function StudioEmbedClient({ specOptions }: { specOptions: any }) {
  return <StudioComponent specOptions={specOptions} />;
}
```

Detect the framework (Next App Router vs Vite/CRA) before picking. Same rule as `install-studio`: presence of `app/` dir + `next` in package.json → App Router; else default to the client-only variant.

### Step 3 — Insert the embed into the target page

Read the target page file. Find the `insertionAnchor`. Insert the `<StudioEmbed compositionUid="{bandName}" />` line at `insertionPosition` (before/after the anchor).

Also add the import at the top of the file:
- Relative path inferred from where the wrapper landed in step 2 (e.g. `import { StudioEmbed } from "@/components/StudioEmbed"`).

Show the user the diff before writing:

```
target page changes (preview before write):

  + import { StudioEmbed } from "@/components/StudioEmbed";

  …
      <ProductSpecs specs={product.specs} />
  +   <StudioEmbed compositionUid="{bandName}" />
      <BuyBox product={product} />
  …

Proceed? [y/n]
```

Wait for explicit confirmation. Then write.

### Step 4 — Verify the embed renders

1. Print: *"Start your dev server (`npm run dev`) if it isn't running, then visit the target page in a browser — `<embed should appear at insertion point>`."*
2. Tell the user: *"Open Studio in another tab → Templates → open `{bandName}` → make a visible change (drop a Hero, change static text) → Save → reload the visitor page. The change should appear without any code redeploy."*
3. If nothing renders, the debugging checklist (run these in order):
   - Browser DevTools Console → look for `[StudioEmbed]` warning (slug mismatch / not created)
   - Network tab → look for the CDA fetch for the composition; check status code
   - Studio → verify the composition's `composable_uid` exactly matches `{bandName}` (case-sensitive)
   - If iframe error appears: composition exists but is empty — drop at least one component in Studio + Save

### Step 5 — Register the embed in `STUDIO_EMBEDS.md`

For projects with multiple embeds, a single registry file keeps the (page → compositionUid) mapping visible. Create or append to `STUDIO_EMBEDS.md` at the repo root:

```markdown
# Studio Embeds Registry

Each row = one Studio-managed band embedded inside a code-owned page.
Update when adding/removing/renaming embeds.

| Composition UID (slug) | Flavor   | Embedded in                          | Component             | Notes |
|---|---|---|---|---|
| {bandName}             | {compositionFlavor} | `{targetPageFile}`         | `<StudioEmbed compositionUid="{bandName}" />` |  |
```

If the file already exists, append the row before the closing of the table. Print: *"Added a row to `STUDIO_EMBEDS.md`. Keep this file updated when the embed list changes."*

## Inputs needed from the user

In order. Stop and ask if any is missing.

1. `targetPageFile` — exact file path; the skill reads + modifies it.
2. `bandName` — kebab-case slug. Validate: lowercase, underscores or hyphens only, ≤32 chars. Reject invalid (would break Studio's composable_uid validation).
3. `compositionFlavor` — always `section`. Sections are the intended shape for embedded compositions.
4. `insertionAnchor` — string the skill greps for in the target page file. If multiple matches → ask the user to disambiguate.
5. `insertionPosition` — `before` or `after`. Default `after`.

## Acceptance

This skill succeeds only when ALL are true:

- [ ] User confirmed the Studio composition exists (step 1 — explicit "Composition created" response).
- [ ] `<StudioEmbed>` wrapper exists (either reused or scaffolded in step 2).
- [ ] Target page file imports `StudioEmbed` AND renders `<StudioEmbed compositionUid="{bandName}" />` at the chosen position.
- [ ] Visiting the target page in a browser renders the embed (step 4 visual confirmation).
- [ ] `STUDIO_EMBEDS.md` has a row for this embed.

If the embed doesn't render visually, do NOT claim success — surface the debugging checklist from step 4.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Slug typo between Studio + code | `compositionUid` is case-sensitive; `pdp_marketing_band` ≠ `Pdp_Marketing_Band` | Copy the `composable_uid` directly from Studio's composition list; keep `bandName` in lowercase_snake_case |
| Composition is empty in Studio | `specOptions.spec` resolves but `<StudioComponent>` renders nothing | Drop at least one component in Studio and Save before testing the embed |
| Embed renders during SSR, disappears after hydration | Mixing the SSR variant + CSR variant inadvertently | Use the SSR pattern (server-fetch + client render) when the surrounding page is a Server Component; use the CSR variant when the surrounding page is `"use client"` |
| Layout shift when band loads | Default `fallback={null}` → page reflows when content arrives | Pass `fallback={<div style={{height: 200}} />}` (or a skeleton) matching expected band height |
| Embed breaks after rename in Studio | Renaming a composition changes its `composable_uid`; embed still references the old slug | Don't rename embedded compositions. If you must, do a global find-replace in the codebase AND update `STUDIO_EMBEDS.md` in the same commit |
| Author edits but no live updates | CDA cache | Republish the composition (Save in Studio is draft; Publish is what visitors fetch) |
| Embed in a Server Component page calls the client-only hook | `useCompositionData` is CSR-only by definition (uses React state) | Use the SSR variant (server-fetch via `sdk.fetchCompositionData` + client-wrap) when the parent is RSC |

## See also

- `docs/40-recipes/embedding-a-composition-in-a-code-owned-page.md` — the recipe this skill operationalizes
- `docs/40-recipes/partial-adoption-coexisting-with-a-code-driven-app.md` — when to embed vs use catch-all vs full route swap
- `migrate-page-to-studio` — when you want the WHOLE page Studio-managed instead of just one band
- `setup-template-preview-routes` — for the catch-all route pattern that handles full pages
- `install-studio` — prerequisite (SDK + init must be wired before any embed works)
