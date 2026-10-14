---
name: configure-csr-vs-ssr
---

## When to use

**Whole BYOC plan** ("BYOC", "use my components in Studio")? Read [`byoc-end-to-end`](byoc-end-to-end.md) instead.

Pick and wire a Studio page's render path: CSR (client, `useCompositionData`) or SSR/RSC (server, `sdk.fetchCompositionData`), on Next.js (App/Pages), Remix, Astro or Vite/SPA. Phrases: "CSR or SSR", "Next App Router setup", "hydration mismatch", "SEO meta missing", "Live Preview broken after switching render mode". Also diagnoses broken Studio iframe overrides after a render-mode change.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Configure CSR vs SSR for a Studio composition route

## Read this first: SSR is available on every host

The SDK ships two App Router paths (client-component SSR via the main entry, and an RSC entry with a ~142-byte structural bundle), plus recipes for Node/Express/Fastify, Next Pages Router, Remix, Astro, and Gatsby. Every host renders the full composition into the server HTML. `curl` returns real content, SEO works, no placeholder-defer.

Pick your recipe from the framework recipes chapter and copy it verbatim:

- **Next.js Pages Router**, **Remix / React Router 7**, **Astro**, **Gatsby**: adapted recipes.
- **Next.js App Router: RSC entry**: CI-tested on Next 14 + Next 16. Smallest possible client bundle.
- **Next.js App Router: client-component SSR**: main-entry path, simplest wiring, full SEO.

Same three-call contract everywhere (`fetchCompositionData`, then `<StudioComponent />`, then `getSSRStyleTags` or `<StudioServerStyles>`), plus `getCompositionMetadata` for SEO. Sections below cover the render-strategy decision itself. The mechanics live in the recipes above.

## Context

A Studio composition can be rendered via two data-fetching paths. Both return the same `StudioComponentSpecOptions` shape. Only where the fetch runs differs.

- **CSR**: `useCompositionData({ url })` hook. Runs in the browser. Best for Vite SPAs / routes where SEO is not required.
- **SSR / RSC**: `sdk.fetchCompositionData({ url, searchQuery }, { locale })`. Runs on the server. Required for SEO and for routes where the initial HTML must contain the rendered composition.

`<StudioComponent specOptions={...} />` is the single renderer for both visitor pages and pages opened inside Studio's builder iframe. It auto-detects mode and attaches the Visual Editor overlay when needed. `<StudioCanvas />` is a separate client-only component for the Studio canvas route and is **not** a render-strategy decision.

**SDK shape.** `studioSdk` is the imported namespace. You must call `studioSdk.init({ stackSdk, contentTypeUid })` once at boot and use the **returned** object. Server fetches go through `sdk.fetchCompositionData(...)` on that returned object.

```ts
import { studioSdk } from "@contentstack/studio-react";
export const sdk = studioSdk.init({ stackSdk, contentTypeUid });
// later, server-side:
const specOptions = await sdk.fetchCompositionData({ url, searchQuery }, { locale });
```

## The render-pipeline rule (read this first)

What determines **true SSR** (the composition DOM in the server HTML) is whether `<StudioComponent>` renders through a **`renderToString` pipeline** (Pages Router / Vite custom server / Remix: server React dispatcher present, built-ins execute server-side) OR through **React Server Components** (App Router: built-ins are `"use client"` and the SDK renderer detects them as `Symbol.for("react.client.reference")` and so emits `data-cs-defer-builtin` placeholders, deferring real render to client hydration). The data-fetch function (`fetchCompositionData` vs `useCompositionData`) is orthogonal and does **not** by itself produce SSR.

**Net:** every mainstream host, including Next App Router (main entry and RSC entry), Pages Router, Remix, Astro, Gatsby, and plain Node, renders the composition into the server HTML via the SDK's three-call contract. See [`install-studio`](install-studio.md) for the per-host wiring. The historical `data-cs-defer-builtin` placeholder path was removed in a later SDK release.

## Decision table

| Situation | Path | True SSR? (composition DOM in server HTML) |
| --- | --- | --- |
| Vite / React SPA, no SEO | **CSR**: `useCompositionData` | No (client only) |
| **Next.js Pages Router** | **SSR**: `sdk.fetchCompositionData` inside `getServerSideProps` | **Yes**: `renderToString` |
| **Next.js App Router (main entry)** | `sdk.fetchCompositionData` in a Server Component, then a client wrapper renders `<StudioComponent />` | **Yes**: Next server-renders the client component's initial output |
| **Next.js App Router (RSC entry)** | `sdk.fetchCompositionData` in a Server Component, then `<StudioServerStyles />` plus `<StudioComponent />` from `@contentstack/studio-react/rsc` | **Yes**: ~142B client bundle for structural content. Custom components register as client islands automatically |
| Vite custom-server SSR | `renderToString` + `hydrateRoot` + `sdk.fetchCompositionData` | **Yes** |
| Remix | `sdk.fetchCompositionData` inside the `loader` | **Yes**: `renderToString` |
| Static / rarely changing | **SSG/ISR**: `getStaticProps` + `revalidate` | **Yes** (at build/revalidate. Via `renderToString`) |

CSR works on **any** framework including App Router. The `isLoading` gate keeps built-ins out of the server prerender entirely. Use CSR as the universal fallback when true SSR isn't viable on a given framework.

<a id="resolve-composition-helper"></a>

## `fetchCompositionData` does not return "not found": it throws. Wrap it.

On a miss, `sdk.fetchCompositionData` **throws**. It does not resolve with `hasSpec: false`. Every `if (!specOptions.hasSpec) notFound()` line is therefore dead code on the path it was written for: the `await` throws first, the framework's error boundary catches it, and the visitor gets a **500 where a 404 belongs**.

What it throws is a `ComposableStudioError`. **Do not branch on a list of names.** Call `isCompositionNotFound(err)`, exported for exactly this decision:

```ts
import { isCompositionNotFound } from "@contentstack/studio-client";
```

It answers *did we establish that nothing is here?* and is the only thing that should decide a 404. A list of names has to be kept in step with the SDK, and the cost of drift is one-way: mistake a setup failure for a missing page and a wrong api key or a delivery outage returns **404 on pages that exist**, de-indexing a working site.

Also on the error: `err.code` (the precise case, for logs and support) and `err.errorClass`, of which only `NOT_FOUND` is a 404. `err.causes` carries `{ cause, fix }` pairs for that failure, most likely first: log it in dev, it is the fastest diagnosis available.

```ts
// lib/resolve-composition.ts
import { isCompositionNotFound } from "@contentstack/studio-client";

export async function resolveComposition(sdk, args, opts = {}) {
  try {
    const specOptions = await sdk.fetchCompositionData(args, opts);
    return { specOptions, notFound: false }; // resolved ⇒ renderable
  } catch (err) {
    if (isCompositionNotFound(err)) return { specOptions: null, notFound: true };
    throw err;   // real failure — must stay a 500
  }
}
```

**Do not blanket-catch.** A bare `try { … } catch { notFound() }` turns every CDA outage, expired delivery token, and network blip into a silent 404. The site looks empty instead of broken, and monitoring sees nothing. Ask the predicate. Rethrow the rest.

**`content_type_url_pattern` moves the failure, it doesn't remove it.** With `url_metadata.url_source: "content_type_url_pattern"`, the composition's pattern matches a whole family of URLs (`/blog/{{entry.title}}` matches any `/blog/*`), so a bad slug sails past **pattern match** and dies at **entry lookup** — a different code, `URL_MATCHED_NO_ENTRY` rather than `NO_COMPOSITION_FOR_URL`. Both are `NOT_FOUND`, so the predicate covers both without you listing either; this is the case that used to catch people out when they hand-rolled the list. See [`troubleshoot-composition-resolution`](troubleshoot-composition-resolution.md) § Runtime error taxonomy.

**`useCompositionData` doesn't throw: it hands you the same object.** The hook catches the rejection and stores it verbatim in `error`, so `isCompositionNotFound(error)` classifies identically. An `if (error) return <ErrorState/>` branch renders an error state for URLs that simply have no composition.

Every fetch snippet below is written against `resolveComposition`. If you copy a raw `sdk.fetchCompositionData` call from elsewhere, wrap it.

## A server with a preview token can serve drafts to visitors

The Delivery stack is shared by every request on a server process. `fetchCompositionData` sets a request's preview hash on it and never clears it when the next request has none (by design), so later visitor requests go to the preview host with the last hash. Measured: one request with `?live_preview=<hash>`, then the next plain request went to `rest-preview.contentstack.com`. Mechanism: [`troubleshoot-canvas`](troubleshoot-canvas.md) § shared stack instance hazard.

A deployment with **no** preview token is safe ([`deploy-studio-site`](deploy-studio-site.md)). On a preview deployment, clear the hash when a request has none:

```ts
// `stack` is the Delivery stack your Studio sdk was initialized with
// (contentstack.stack({...}) in lib/studio.server.ts); `searchQuery` is the raw request query string.
const q = new URLSearchParams(searchQuery);
if (!q.get("hash") && !q.get("live_preview")) stack.livePreviewQuery({ live_preview: "" });
```

Measured: the plain request then stayed on the CDN. Requests in flight at the same time still share the stack, so on a preview server under concurrent load, create the stack and the Studio sdk **per request** instead of sharing one module-level instance:

```ts
// lib/studio.server.ts — sketch: one stack + sdk per request on a preview deployment
import contentstack from "@contentstack/delivery-sdk";
import { studioSdk } from "@contentstack/studio-react";

export function createStudioSdk() {
  const stack = contentstack.stack({
    apiKey: process.env.CONTENTSTACK_API_KEY!,
    deliveryToken: process.env.CONTENTSTACK_DELIVERY_TOKEN!,
    environment: process.env.CONTENTSTACK_ENVIRONMENT!,
    live_preview: { enable: true, preview_token: process.env.CONTENTSTACK_PREVIEW_TOKEN, host: process.env.CONTENTSTACK_PREVIEW_HOST },
  });
  return studioSdk.init({ stackSdk: stack, contentTypeUid: "<compositions-CT-uid>" });
}
```

## Task

1. **Pick the path** from the decision table using `framework`. Run only the matching block below. Skip the others.

2. **CSR (Vite / SPA, also the universal fallback on any framework, including App Router).**
   ```tsx
   "use client";
   import { useCompositionData, StudioComponent } from "@contentstack/studio-react";
   import { isCompositionNotFound } from "@contentstack/studio-client";
   // Loading, ErrorState and NotFound are your app's own components.
   import { Loading, ErrorState, NotFound } from "@/components/states";

   export default function Page() {
     // window is browser-only — guard for any framework that prerenders this page (Next does, even with "use client").
     const url = typeof window !== "undefined" ? window.location.pathname : "/";
     const { specOptions, isLoading, error } = useCompositionData({ url });
     if (isLoading) return <Loading />;
     // The hook surfaces the rejection as `error`, so a plain `if (error)` branch
     // renders an error state for a URL that simply has no composition. Classify
     // first — a miss is a 404, everything else is a real error.
     const isMiss = isCompositionNotFound(error);
     if (error && !isMiss) return <ErrorState message={error instanceof Error ? error.message : String(error)} />;
     if (isMiss || !specOptions?.spec) return <NotFound />;
     return <StudioComponent specOptions={specOptions} />;
   }
   ```
   The hook reads `window.location.search` automatically, no `searchQuery` argument required. CSR is the safe universal path: built-ins never enter a server pre-render, so the App-Router RSC crash from registering basics on the server can't happen.

   Ensure **built-ins + custom components are registered before render** (see `register-component`). On CSR, the registration must run client-side at module init.

   **Live Preview wiring is separate.** If this route needs to reflect author edits in real time, add the `onEntryChange` bridge from `install-live-preview` (step 7). CSR pages call the hook's `refetchData` inside the loop-safe callback — it re-fetches just the bound data, which is all a live edit changes.

3. **App Router (main entry): SSR through a client wrapper.** A Server Component fetches, a `"use client"` wrapper renders, and Next puts that output in the initial HTML (verified with `curl` in the App Router recipe). Initialize the sdk in a server-only module (no `"use client"`). Register components in a `"use client"` module the wrapper imports. Rendering `<StudioComponent />` directly in a Server Component makes built-ins `react.client.reference` proxies: the SDK emits `data-cs-defer-builtin` placeholders, filled only on hydration.
   ```tsx
   // app/[[...slug]]/page.tsx — NO "use client"
   import { sdk } from "@/lib/studio.server";
   import { resolveComposition } from "@/lib/resolve-composition";
   import { ClientRender } from "./ClientRender";
   import { notFound } from "next/navigation";

   export default async function Page({ params, searchParams }) {
     const { slug } = await params;   // a Promise on Next 15+
     const url = "/" + (slug?.join("/") ?? "");
     const searchQuery = new URLSearchParams((await searchParams) as Record<string,string>).toString();
     const { specOptions, notFound: miss } = await resolveComposition(
       sdk,
       { url, searchQuery },
       { locale: "en-us" },
     );
     // resolveComposition rethrows real failures, so reaching here with miss=true
     // genuinely means "no composition at this URL" — 404 is the right answer.
     // Do NOT add `|| !specOptions.hasTemplate` here. hasTemplate is false for
     // every FREEFORM composition (no connected content type), so that guard
     // 404s every freeform page however it is published. `miss` already carries
     // the only not-found answer there is.
     if (miss) notFound();
     return <ClientRender specOptions={specOptions} />;
   }

   export async function generateMetadata({ params, searchParams }) {
     const { slug } = await params;
     const url = "/" + (slug?.join("/") ?? "");
     // Metadata must never throw — a miss here should degrade to empty tags,
     // not take down the page that resolves fine one line later.
     const { specOptions } = await resolveComposition(sdk, {
       url,
       searchQuery: new URLSearchParams(await searchParams).toString(),
     });
     const seo = specOptions?.seo;
     return seo
       ? { title: seo.pageTitle, description: seo.pageDescription,
           openGraph: { images: seo.openGraphImage ? [seo.openGraphImage] : [] } }
       : {};
   }
   ```
   Client wrapper (just renders, no Live Preview wiring here):
   ```tsx
   "use client";
   import { StudioComponent } from "@contentstack/studio-react";

   export function ClientRender({ specOptions }) {
     return <StudioComponent specOptions={specOptions} />;
   }
   ```

   **Live Preview wiring is separate.** If this route needs real-time author updates, mount the `LivePreviewBridge` from `install-live-preview` (step 7) once in the app shell (e.g. in `app/layout.tsx` inside a client boundary). App Router routes call `router.refresh()` in the loop-safe callback. Do NOT put `[router]` in the effect deps. It produces an infinite refetch loop.
   Canvas route stays client-only:
   ```tsx
   // app/studio-canvas/page.tsx
   "use client";
   import { StudioCanvas } from "@contentstack/studio-react";
   export default function Canvas() { return <StudioCanvas />; }
   ```

4. **SSR: Next.js Pages Router.** Also full SSR: the composition DOM lands in the server HTML via `renderToString`. Register all components (built-ins + custom) at module scope in `pages/_app.tsx` with **static imports** so the same React instance runs server + client.
   ```ts
   // pages/blog/[slug].tsx
   import { sdk } from "@/lib/studio.server";
   import { resolveComposition } from "@/lib/resolve-composition";

   export async function getServerSideProps(context) {
     const searchQuery = context.req.url.split("?")[1] ?? "";
     const url = `/blog/${context.params.slug}`;
     const { specOptions, notFound } = await resolveComposition(sdk, { url, searchQuery });
     if (notFound) return { notFound: true };
     return { props: { specOptions } };
   }
   ```
   Page component renders `<StudioComponent specOptions={specOptions} />`. `specOptions` is JSON-serializable.

   **Live Preview wiring is separate.** If this route needs real-time author updates, mount the `LivePreviewBridge` from `install-live-preview` (step 7) in `pages/_app.tsx` inside a client boundary. Pages Router routes call `router.replace(router.asPath, undefined, { scroll: false })` in the loop-safe callback. Do NOT put `[router]` in the effect deps. The router identity changes on every replace, which would produce an infinite refetch loop.

   Verify true SSR with a **prod build** (`next build && next start`), not `next dev`. Dev is per-boot racy (recompile + module-init order + StrictMode double-invoke). Prod is deterministic. Acceptance: `curl <url>` returns 200 with the composition DOM (incl. Repeater iteration items) in `<body>` after stripping `<script>` tags, **no `data-cs-defer-builtin`** attributes.

5. **SSR (Remix).** Put sdk init in `app/lib/studio.server.ts` so secrets tree-shake out of the browser bundle.
   ```ts
   import { json } from "@remix-run/node";
   import { sdk } from "~/lib/studio.server";
   import { resolveComposition } from "~/lib/resolve-composition";

   export async function loader({ request }) {
     const url = new URL(request.url);
     const { specOptions, notFound } = await resolveComposition(sdk, {
       url: url.pathname,
       searchQuery: url.search.replace(/^\?/, ""),
     });
     if (notFound) throw new Response("Not Found", { status: 404 });
     return json({ specOptions });
   }
   ```
   Component: `const { specOptions } = useLoaderData(); return <StudioComponent specOptions={specOptions} />;`

6. **SSG / ISR.** Pass `searchQuery: ""` (no Studio iframe at build time), set `revalidate: 60` for ISR, and wire a Contentstack publish webhook to `res.revalidate(path)` for instant invalidation. Live Preview won't update SSG output until revalidation. If that matters, move the route to SSR.

7. **Hydration discipline.** Pass the **same** `specOptions` the server fetched straight to the client wrapper. Do **not** re-fetch on mount with `useCompositionData` after an SSR fetch. That produces a hydration mismatch. Pin `locale` and `variantAlias` to identical values on both sides.

8. **Iframe override forwarding.** On every SSR/RSC path, forward the full request query string into `searchQuery`. Studio's builder iframe appends its own params (locale, variant, preview entry) to the iframe URL. The SDK reads them itself. Your code must not parse or rely on specific param names. They're an internal contract between Studio and the SDK that may change. Just pass the raw query string through and the SDK does the rest.

9. **Repeater iteration bindings.** If the composition includes a Repeater, the same `<StudioComponent />` resolves `repeater.<fieldUid>` bindings against each iteration's data, no extra wiring at the page level.

10. **Verification.** Open the route in a regular tab and `view-source:`. For SSR/RSC/SSG the composition HTML must be in the initial response (not just a shell). `curl -A "Twitterbot" <url>` returns the og: meta tags. Open the same route inside Studio's preview iframe. The iframe's override params flow through `searchQuery` and the right entry/locale renders. Edit an entry in Live Preview. The page updates without a full reload. No React hydration warning in the console.

    **Verify SSR with `curl`, not a browser screenshot.** Next injects a FOUC guard (`body{display:none}` via `data-next-hide-fouc`) during SSR and removes it on hydration. A pre-hydration screenshot shows blank even when the real content is in the HTML. `curl -s <url> | grep -q '<known-text>'` (for a local mkcert dev cert, add `--cacert "$(mkcert -CAROOT)/rootCA.pem"`; never `-k`) executes no JS and returns the truth. A blank browser screenshot does NOT mean SSR failed.

## Inputs needed from the user

1. `framework`: one of `next-app`, `next-pages`, `remix`, `vite-spa`, `astro`, `ssg`
2. `routePath`: the route file you'll write
3. `contentTypeUid`: Studio composition content type uid (defaults to `compositions`)
4. `defaultLocale`: defaults to `en-us`

If `framework` is unclear, inspect `package.json`: `next` plus an `app/` dir means next-app, `next` plus a `pages/` dir means next-pages, `@remix-run/*` means remix, `vite` means vite-spa, and `astro` means astro.

## Studio-authored styles on a server-rendered route: `getSSRStyles`

Anything an author sets in the Design panel is generated at render time, not shipped in your stylesheet. A server render that emits only markup therefore arrives unstyled and restyles on hydration: a visible flash, worst on the slowest connections.

`getSSRStyles(spec)` returns that CSS as a string. Emit it with the markup.

```tsx
import { getSSRStyles, StudioComponent } from "@contentstack/studio-react";

const css = getSSRStyles(specOptions.spec);   // design-token :root vars + component styles

return (
  <>
    {css ? <style precedence="default">{css}</style> : null}
    <StudioComponent specOptions={specOptions} />
  </>
);
```

It takes one spec or an array of them, so a page assembled from several compositions emits one stylesheet. Outside React (Express, a custom server) `getSSRStyleTags(spec)` returns the same CSS already wrapped in a `<style>` tag, to concatenate into an HTML template after `renderToString`.

CSR routes need neither: there is no server pass to be unstyled.

## Acceptance

Succeeds only when ALL of the following are true:

- [ ] The route file uses the fetch path that matches the framework row in the decision table
- [ ] Server-rendered routes emit `getSSRStyles(specOptions.spec)` alongside the markup, checked by loading the route with JavaScript disabled, or `curl`, and confirming Design-panel styling is already applied
- [ ] Server-side paths forward `searchQuery` from the incoming request to `fetchCompositionData`
- [ ] **Every `fetchCompositionData` call is wrapped**, via `resolveComposition` or an equivalent try/catch that classifies known not-found ids as 404 and **rethrows everything else**. No bare `await sdk.fetchCompositionData(...)` on a route, and no blanket `catch { notFound() }`
- [ ] **Verified with a real miss:** request a URL with no composition (e.g. `/no-such-page`) and a valid-prefix-but-bad-slug URL under a connected template (e.g. `/blog/zzz-not-an-entry`). **Both return 404, not 500.** The second one is the `content_type_url_pattern` case and fails at a different stage. Testing only the first proves nothing about it
- [ ] `<StudioComponent />` is rendered inside a `"use client"` boundary on App Router / RSC paths
- [ ] If Live Preview is in scope for this route, the `LivePreviewBridge` from `install-live-preview` (step 7) is mounted in the app shell. Not needed for pure public SSR routes without Live Preview.
- [ ] No `useCompositionData` call exists on a route that already fetched server-side (no double-fetch)
- [ ] App Router routes export `generateMetadata` populated from `specOptions.seo`
- [ ] Management tokens, if any, only appear in `*.server.ts` (Remix) or non-`"use client"` modules (Next.js)
- [ ] Canvas route, if present, is a separate `"use client"` route mounting `<StudioCanvas />`
- [ ] Browser console shows no hydration mismatch warning on the rendered route

If acceptance fails, report exactly which step broke and stop.

## Common pitfalls

| Pitfall | Symptom | Fix |
| --- | --- | --- |
| `useCompositionData` in a Server Component | "Hooks can only be called inside a function component" | Switch to `sdk.fetchCompositionData` + client wrapper |
| `<StudioComponent />` directly in a Server Component | Next.js client-component error | Wrap in a `"use client"` child taking `specOptions` as prop |
| `searchQuery` not forwarded | Iframe shows wrong locale/variant. Edit mode doesn't engage | Forward `request.url.search` / `new URLSearchParams(searchParams).toString()` |
| Re-fetched on the client after SSR | Hydration mismatch warning | Pass server `specOptions` straight to the client wrapper |
| Different `locale` server vs client | Mismatch warning, content flash | Pin both sides via the second arg of `fetchCompositionData` |
| Live Preview never updates the running page | Missing `onEntryChange` bridge | Wire the `LivePreviewBridge` from `install-live-preview` (step 7). Not a CSR-vs-SSR issue, same fix regardless of framework. |
| **Infinite `_next/data/<id>/<route>.json` (Pages) or RSC payload refetch: Network tab fires hundreds of times per edit** | `onEntryChange` wired in a `[router]`-dep effect | Move the wiring to the loop-safe pattern in `install-live-preview` (step 7): subscribe ONCE with empty deps, hold router in a `useRef`, skip the register-time fire, unsubscribe in cleanup. |
| **App Router route renders fine in the browser but `view-source` shows no composition DOM**: bound content only in `self.__next_f` flight payload | `<StudioComponent />` is rendered directly in a Server Component: the RSC pass sees every built-in as `react.client.reference`, emits `data-cs-defer-builtin` placeholders, and defers the real render to hydration. **Not true SSR.** | Render it through a `"use client"` wrapper (step 3), or move the route to **Pages Router** (or Vite custom-server / Remix). |
| **`transpilePackages: ['@contentstack/studio-*']` on App Router** | 500 with `Cannot read properties of null (reading 'useContext')` at `useData → RepeaterPreview` during the RSC server prerender | Don't transpile the SDK on App Router. It defeats the SDK's safe client-deferral (the basics resolve to real components, run on the server, and read a null React dispatcher). On Pages Router, transpiling is fine. |
| **Coexisting `app/` dir while SSR-ing a `pages/` route** | The Pages-Router SDK React resolves to the app-page runtime, which gives a null dispatcher and a crash | Make the project Pages-Router-only for the Studio SSR route (remove `app/` from that workspace). |
| **Judging SSR from `next dev`**: Repeater items intermittently render field defaults ("Your text here") | Per-boot dev race (recompile + module-init order + React StrictMode double-invoke) | Verify and ship from a **prod build**: `next build && next start`. Prod is deterministic. Dev is racy. |
| **`dynamic(() => import('@contentstack/studio-react'))` for the canvas, prod build fails** | `Package path "." is not exported from package` | `studio-react`'s `exports` map only exposes `.` under the `import` condition. Dynamic-import a **local wrapper** that statically imports `StudioCanvas`. |
| **Bare `await sdk.fetchCompositionData(...)` with an `if (!hasSpec) notFound()` guard below it** | Every unmatched URL returns **500, not 404**. The fetch rejects, so the guard line never executes. Error boundary shows a generic failure. Nothing names the missing composition | Wrap with [`resolveComposition`](#resolve-composition-helper). The guard was written for a resolve-with-falsy contract the SDK doesn't have |
| Blanket `try { … } catch { notFound() }` around the fetch | Every CDA outage, expired delivery token, and network blip silently becomes a 404. The site reads as "empty" instead of "broken" and monitoring stays green | Ask `isCompositionNotFound(err)`: true is a 404. Rethrow the rest so real failures stay 500s |
| Testing 404 handling only with a totally unmatched URL | Passes, while every bad slug under a `content_type_url_pattern` template still 500s if you hand-rolled a list of names. That path matches the pattern and fails later, at entry lookup, with a different code | Test both shapes. Use the predicate rather than a list, and both are covered |
| **Server-rendered route paints unstyled, then snaps into place on hydration** | Design-panel styles are generated at render time, not in your stylesheet. Markup alone carries none of them | Emit `getSSRStyles(specOptions.spec)` with the markup. See § Studio-authored styles on a server-rendered route |
| **Every bound image 400s through `next/image`** (`"hostname … is not configured under images"`) | Assets come from a Contentstack CDN host the optimizer doesn't trust by default. Nothing in the composition is wrong | Add the asset hosts to `images.remotePatterns` in `next.config.mjs`: `images.contentstack.io` plus your region's `*-images.contentstack.com`. Region-dependent, so read the URL the binding actually returned rather than guessing |
| SSG never updates after publish | Stale content | Configure ISR `revalidate` or wire a publish webhook to `res.revalidate(path)` |
| Management token in client module | Token shipped to browser | Move sdk init into `*.server.ts` / non-`"use client"` module |

## See also

- `install-studio`: installs the three SDKs and wires `studioSdk.init`
- `setup-section-preview`: adds the `<StudioCanvas />` route
- `troubleshoot-canvas`: when the iframe still doesn't render after both skills are run
