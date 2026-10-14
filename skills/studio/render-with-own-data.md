---
name: render-with-own-data
---

## When to use

Render a Studio composition (page or standalone section) against data you already hold, via `<StudioComposition context={...} />` plus the spec-only `sdk.fetchComposition`.

Use when you already hold the data (a group-array element, a commerce record, a request-time value) and must render a composition against it with no SDK data fetch. Phrases: "render this section per array item", "section per product", "render a composition with my data". Do NOT use for route rendering: that's `setup-template-preview-routes` + `wire-external-data`.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Render a Composition With Your Own Data

## Context

`<StudioComposition />` renders a composition (a full page, or a section as the root) against a `context` object you pass in. No SDK data fetch, no hook, no route ownership. It runs in CSR and SSR.

You give it two things: which composition, and the data.

- **Which composition**: a pre-fetched `spec` from `sdk.fetchComposition`, or a `compositionUid` it fetches on the client.
- **The data**: `context`, placed internally at `dataSources.template`, so the composition's existing template bindings resolve against it. Embedded sections are auto-scoped from `context` (pure, no network). You never build `section_scoped_data`.

This is not `<StudioComponent />`. That one owns a route and resolves composition **and** CMS data through `sdk.fetchCompositionData`. `<StudioComposition />` owns a subtree and takes the data from you. If the choice of surface is still open, run `understand-bring-your-own-data` first.

## Task

1. **Prereq: `studioSdk.init(...)` runs before render, and every component the composition uses is registered.** Without init the `compositionUid` path logs `StudioComposition: SDK not initialized. Call studioSdk.init(config) before rendering with a compositionUid.` and renders `errorFallback`. `sdk.fetchComposition` throws when no `stackSdk` is configured. Run `install-studio` and `register-component` if either is missing.

2. **Identify the composition.** Get `compositionUid` from the composition's URL in Studio. `sdk.fetchComposition` also accepts `url` or `templateContentTypeUid` (same identifier shapes as `sdk.fetchCompositionData`) plus `searchQuery`. Pass `searchQuery: ""` when rendering on your own site. It exists to forward Studio's iframe overrides (locale, variant, preview entry, edit mode).

3. **Shape `context` to the composition's bindings.** A binding to `title` reads `context.title`. A binding that iterates `sub_items` reads `context.sub_items`. Pass the raw element you hold (one item of a multiple-group field, one API record) and the SDK wraps it. If the composition was authored against a `product` template, `context` is one product-shaped object with the same field names.

4. **Pick the fetch path by render strategy:**

   | Situation | Path |
   |---|---|
   | SSR / RSC / Remix loader / `getServerSideProps` | Pre-fetch `spec`: a `"use client"` component cannot fetch during a server render |
   | A loop rendering N instances of the same composition | Pre-fetch `spec` once above the loop |
   | A single client-rendered mount | `compositionUid` + `loadingFallback` + `errorFallback` |

5. **Pre-fetched spec (SSR, the default).** Resolve the spec and your own data in parallel, render immediately, no client loading state:

   ```tsx
   // app/products/page.tsx — Next App Router Server Component (no "use client")
   import { sdk } from "@/lib/contentstack";
   import { StudioComposition } from "@contentstack/studio-react";

   export default async function ProductsPage() {
     const [products, spec] = await Promise.all([
       getProducts(),                                                       // your data source
       sdk.fetchComposition({ compositionUid: "product_tile", searchQuery: "" }),
     ]);

     return (
       <div className="grid">
         {products.map((element, i) => (
           <StudioComposition key={i} spec={spec} context={element} />
         ))}
       </div>
     );
   }
   ```

   `sdk.fetchComposition(query, options?)` returns `Promise<StudioSpec>` whose `data` is intentionally empty: that's the bring-your-own-data path. `options` is the same `CompositionQueryOptions` as `sdk.fetchCompositionData` (`variantAlias`, `locale`, `templateEntryUid`, `extendQuery`, custom fetchers).

   Pages Router / Remix: call `sdk.fetchComposition` in `getServerSideProps` / `loader` and pass `spec` through props.

6. **`compositionUid` path (client only).** Always pair it with both fallbacks: the defaults are `null`, so a failed fetch renders nothing:

   ```tsx
   "use client";
   import { StudioComposition } from "@contentstack/studio-react";
   // Your own skeleton and not-found components:
   import { SectionSkeleton } from "@/components/SectionSkeleton";
   import NotFound from "@/components/NotFound";

   export function HeroFor({ element }: { element: Record<string, unknown> }) {
     return (
       <StudioComposition
         compositionUid="hero_section"
         context={element}
         loadingFallback={<SectionSkeleton />}
         errorFallback={<NotFound />}
       />
     );
   }
   ```

   In a CSR app you can also pre-fetch in `useEffect` and hold the `StudioSpec` in state, worth it when several mounts share one composition.

7. **Fetch the spec once per composition, never per item.** Each `<StudioComposition compositionUid={…} />` inside a loop fetches independently. Hoist the fetch, pass the same `spec` object to every item.

8. **Keep `spec` and `context` JSON-serializable.** `<StudioComposition />` is a `"use client"` component, so in RSC both props cross the server to client boundary. Class instances, functions, `Map`/`Set`, and `Date` objects break serialization: pass plain objects, arrays, strings, numbers, booleans, `null`.

9. **Verify in a normal browser tab** (not the Studio iframe): each mount renders the composition's own layout with your element's values, and item N shows item N's data.

## Inputs needed from the user

In this order. If any is missing, ask before editing code.

1. `compositionUid`: which composition to render (or the `url` / `templateContentTypeUid` that resolves it).
2. `dataShape`: the object you hand to `context`, so we can check it matches the composition's binding field names.
3. `renderPath`: CSR or SSR. Picks step 5 vs step 6.
4. `mountFile`: the file where `<StudioComposition />` mounts.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, surface the failure and stop.

- [ ] `mountFile` renders `<StudioComposition />` with `context` plus exactly one of `spec` / `compositionUid`.
- [ ] In SSR the spec is resolved with `sdk.fetchComposition` on the server and passed as `spec`, no `compositionUid` on a server-rendered mount.
- [ ] `context` field names match the bindings the composition was authored against.
- [ ] A loop fetches the spec once above it and reuses the same `spec` for every item.
- [ ] The `compositionUid` path passes both `loadingFallback` and `errorFallback`.
- [ ] `spec` and `context` are JSON-serializable end-to-end (no functions, class instances, `Date`/`Map`/`Set`).
- [ ] Loading the route in a normal browser tab renders every mount with its own data, verified by screenshot or by reading the rendered values, not by the absence of console errors.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Neither `spec` nor `compositionUid` passed | The component throws `StudioComposition requires either a 'spec' or a 'compositionUid'.` | Pass one: `spec` for SSR, `compositionUid` for client-only |
| `compositionUid` on a server-rendered mount | The fetch is a client effect. The server renders nothing and content pops in late | Pre-fetch with `sdk.fetchComposition`, pass `spec` |
| Passing `data={...}` instead of `context={...}` | `data` is the `<StudioComponent />` prop. `<StudioComposition />` ignores it and renders with no template data | Use `context`, see `understand-bring-your-own-data` § Why `context` is not `data` |
| `context` shape doesn't match the bindings | Bound nodes render blank with no error | Pass the element in the shape the composition was authored against (same field names) |
| Expecting `spec.data` to be populated | `fetchComposition` skips the data fetch by design | Supply the data through `context` |
| `sdk.public.fetchComposition(...)` | `studioSdk.init(...)` already returns the public surface | Call `sdk.fetchComposition(...)` |
| Spec fetched inside the loop body | One network call per item | Hoist the fetch above the loop |
| No `loadingFallback` / `errorFallback` | Both default to `null`: a failed or slow fetch renders an empty gap | Pass both on the `compositionUid` path |
| Non-serializable `context` in RSC | Next.js rejects the prop crossing the client boundary | Map to a plain object before passing |
| `compositionUid` path with no `studioSdk.init` | Console error `SDK not initialized`, then `errorFallback` | Initialize the SDK at app startup (`install-studio`) |
| Composition renders unstyled | Design tokens come from `spec.config` via the composition itself | Confirm the composition resolves (a real `spec`), and that breakpoints/tokens are registered (`import-design-tokens`) |

## See also

- `understand-bring-your-own-data`: which of the three data surfaces fits
- `wire-slot-data`: the other bring-your-own-data surface (per-slot)
- `embed-composition`: mount a composition inside a code-owned page when the SDK should fetch its data too
- `configure-csr-vs-ssr`: pick the render path before wiring step 5 vs 6
