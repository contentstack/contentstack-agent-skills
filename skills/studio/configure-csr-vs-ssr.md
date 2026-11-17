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

Same contract everywhere: `fetchCompositionData`, `<StudioComponent />` (`<StudioServerComponent />` on the RSC entry), then the server styles (`getSSRStyles` in React, `getSSRStyleTags` outside React, or `<StudioServerStyles />` on the RSC entry), plus `getCompositionMetadata` for SEO. Sections below cover the render-strategy decision itself. The mechanics live in the recipes above.

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

What determines **true SSR** (the composition DOM in the server HTML) is whether `<StudioComponent>` renders through a **`renderToString` pipeline** (Pages Router / Vite custom server / Remix) or, on App Router, through a **`"use client"` wrapper**, which Next also renders to HTML on the server. The RSC entry (`@contentstack/studio-react/rsc`) is the other App Router path: its `<StudioServerComponent />` renders in a Server Component. `@contentstack/studio-react` ships no `"use client"` directive and its renderer calls hooks, so a Server Component cannot render it directly. The data-fetch function (`fetchCompositionData` vs `useCompositionData`) is orthogonal and does **not** by itself produce SSR.

**Net:** every mainstream host, including Next App Router (main entry and RSC entry), Pages Router, Remix, Astro, Gatsby, and plain Node, renders the composition into the server HTML via the SDK's contract. See [`install-studio`](install-studio.md) for the per-host wiring. The main entry's `<StudioComponent />` can't render straight from a Server Component (its renderer calls hooks): put it behind a `"use client"` wrapper, or render `<StudioServerComponent />` from `@contentstack/studio-react/rsc`.

## Decision table

| Situation | Path | True SSR? (composition DOM in server HTML) |
| --- | --- | --- |
| Vite / React SPA, no SEO | **CSR**: `useCompositionData` | No (client only) |
| **Next.js Pages Router** | **SSR**: `sdk.fetchCompositionData` and `getSSRStyles` inside `getServerSideProps` | **Yes**: `renderToString` |
| **Next.js App Router (main entry)** | `sdk.fetchCompositionData` and `getSSRStyles` in a Server Component, then a client wrapper renders `<StudioComponent />` | **Yes**: Next server-renders the client component's initial output |
| **Next.js App Router (RSC entry)** | `sdk.fetchCompositionData` in a Server Component, then `<StudioServerStyles />` plus `<StudioServerComponent />` from `@contentstack/studio-react/rsc` | **Yes**: ~142B client bundle for structural content. Custom components register as client islands automatically |
| Vite custom-server SSR | `renderToString` + `hydrateRoot` + `sdk.fetchCompositionData` | **Yes** |
| Remix | `sdk.fetchCompositionData` inside the `loader` | **Yes**: `renderToString` |
| Static / rarely changing | **SSG/ISR**: `getStaticProps` + `revalidate` | **Yes** (at build/revalidate. Via `renderToString`) |

CSR works on **any** framework including App Router. The `isLoading` gate keeps built-ins out of the server prerender entirely. Use CSR as the universal fallback when true SSR isn't viable on a given framework.

<a id="resolve-composition-helper"></a>

## `fetchCompositionData` does not return "not found": it throws. Catch it.

On a miss, `sdk.fetchCompositionData` **throws**. It never resolves with an empty result, so a guard on the returned object (`if (!specOptions?.spec) notFound()`) is dead code on the path it was written for: the `await` throws first, the framework's error boundary catches it, and the visitor gets a **500 where a 404 belongs**.

What it throws is a `ComposableStudioError`. **Do not branch on a list of names.** Catch it and call `isCompositionNotFound(err)`, exported from `@contentstack/studio-react` for exactly this decision: `true` is a 404, `false` is a real failure that must stay a 500.

It answers *did we establish that nothing is here?* and is the only thing that should decide a 404. A list of names has to be kept in step with the SDK, and the cost of drift is one-way: mistake a setup failure for a missing page and a wrong api key or a delivery outage returns **404 on pages that exist**, de-indexing a working site.

Also on the error: `err.code` (the precise case, for logs and support) and `err.errorClass`, of which only `NOT_FOUND` is a 404. `err.causes` carries `{ cause, fix }` pairs for that failure, most likely first: log it in dev, it is the fastest diagnosis available.

The pattern every server fetch on SDK 2.x uses, written at the route:

```ts
import { isCompositionNotFound, type StudioComponentSpecOptions } from "@contentstack/studio-react";
// The sdk and the Delivery stack it was initialized with (`stackSdk`).
// On the minimal-add branch that module is lib/studio.ts.
import { sdk, stack } from "@/lib/studio.server";

// The stack is shared by every request this server handles. The SDK SETS a
// request's preview hash on it but never clears it, so without this line the
// next visitor is served the last editor's drafts. Clearing first is always
// safe: when this request carries a hash, the SDK sets it again itself.
stack.livePreviewQuery({ live_preview: "" });

let specOptions: StudioComponentSpecOptions;
try {
  specOptions = await sdk.fetchCompositionData({ url, searchQuery }, { locale });
} catch (err) {
  if (!isCompositionNotFound(err)) throw err; // a real failure stays a 500
  // A miss: the framework's 404 here (notFound(), { notFound: true }, a 404 Response).
}
```

**Inside Studio's editor, gate the empty page on `isStudioEditorMode(query)`**, also imported from `@contentstack/studio-react`. Pass it the request's query on the server. An unsaved template in the editor is the one miss that must not 404: render the editor's empty page there and the 404 for visitors ([`setup-template-preview-routes`](setup-template-preview-routes.md) step 5a (iii)).

**Every call on one request must forward the same `searchQuery`.** A layout or an embedded composition that passes `""` while the page passes the preview hash clears the hash the page's fetch just set, since both run concurrently on the same stack, and part of the page renders published content inside the editor ([`troubleshoot-canvas`](troubleshoot-canvas.md) § Live Preview state resets mid-request). Thread the page's query string down to them.

**Do not blanket-catch.** A bare `try { … } catch { notFound() }` turns every CDA outage, expired delivery token, and network blip into a silent 404. The site looks empty instead of broken, and monitoring sees nothing. Ask the predicate. Rethrow the rest.

**`content_type_url_pattern` moves the failure, it doesn't remove it.** With `url_metadata.url_source: "content_type_url_pattern"`, the composition's pattern matches a whole family of URLs (`/blog/{{entry.url}}` matches any `/blog/*`), so a bad slug sails past **pattern match** and dies at **entry lookup** — a different code, `URL_MATCHED_NO_ENTRY` rather than `NO_COMPOSITION_FOR_URL`. Both are `NOT_FOUND`, so the predicate covers both without you listing either; this is the case that used to catch people out when they hand-rolled the list. See [`troubleshoot-composition-resolution`](troubleshoot-composition-resolution.md) § Runtime error taxonomy.

**`useCompositionData` doesn't throw: it hands you the same object.** The hook catches the rejection and stores it verbatim in `error`, so `isCompositionNotFound(error)` classifies identically. An `if (error) return <ErrorState/>` branch renders an error state for URLs that simply have no composition.

Every fetch snippet below uses this pattern. If you copy a raw `sdk.fetchCompositionData` call from elsewhere, add the catch and the hash reset.

**Older SDKs (deprecated).** `hasSpec` and `hasTemplate` on the spec options are deprecated in studio-client 4.1.0 and never decide a 404: a resolved fetch always has a spec, and `hasTemplate` is `false` for every Freeform page, so gating on it 404s them. Read `connectedContentTypeUid` if you need the composition's kind. Earlier versions of these guides also routed every fetch through a hand-written `resolveComposition(sdk, args, opts)` helper in `lib/resolve-composition.ts` (hash reset, then the same try/catch, returning `{ specOptions, notFound }`). A site that already has one can keep it while it calls `isCompositionNotFound`; new code writes the catch at the route.

## A server with a preview token can serve drafts to visitors

The Delivery stack is shared by every request on a server process. `fetchCompositionData` sets a request's preview hash on it and never clears it when the next request has none (by design), so later visitor requests go to the preview host with the last hash. Measured: one request with `?live_preview=<hash>`, then the next plain request went to `rest-preview.contentstack.com`. Mechanism: [`troubleshoot-canvas`](troubleshoot-canvas.md) § shared stack instance hazard.

A deployment with **no** preview token is safe ([`deploy-studio-site`](deploy-studio-site.md)). Everywhere else, clear the hash before every fetch, as the [pattern above](#resolve-composition-helper) does: `stack.livePreviewQuery({ live_preview: "" })`, after which the SDK re-applies the request's own `hash` / `live_preview` param when there is one (it only ever sets a hash that is present). Every route that calls `sdk.fetchCompositionData` or `sdk.fetchComposition` needs that line in front of the call. Up to and including 2.0.1 the SDK doesn't clear the hash itself; the next release does, and the line can go once the site runs it ([`upgrade-studio-sdk`](upgrade-studio-sdk.md)).

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

With a per-request stack nothing carries over between requests, so the hash reset has nothing to clear on it. Keep the `isCompositionNotFound` catch for the 404.

<a id="preview-link-not-accepted"></a>
### A preview link whose code is no longer accepted

A preview link carries its code in the query (`hash` or `live_preview`). Once that code expires, or when someone copies the link to a visitor, the preview host turns it down with a 4xx. The SDK throws `UPSTREAM_ERROR`, which is not a not-found, so the catch above rethrows it and the page is a **500**. Measured: `/?live_preview=x&hash=x` answered 500.

Only on a request that carries `hash` or `live_preview`, retry once as a plain visitor request:

- **Retry when** the error's `code` is `UPSTREAM_ERROR` and `findings.status` is a 4xx other than 404. On SDK 1.x the same case arrives as `COMPOSITION_NOT_FOUND` with `details.statusCode` 400.
- **Before retrying,** clear the hash on the stack and remove `live_preview`, `hash`, `preview_timestamp`, `content_type_uid` and `entry_uid` from the query. Keep the locale.
- **Decide the 404 and `isStudioEditorMode` from the query actually fetched**, so a made-up address with a made-up code is still a 404.
- **Rethrow everything else.**

```ts
import { isCompositionNotFound, type StudioComponentSpecOptions } from "@contentstack/studio-react";
import { sdk, stack } from "@/lib/studio.server";

const PREVIEW_PARAMS = ["live_preview", "hash", "preview_timestamp", "content_type_uid", "entry_uid"];

// The preview host turned the link's code down: a 4xx that isn't a 404.
function previewCodeRefused(err: unknown): boolean {
  const e = err as { code?: string; findings?: { status?: number } };
  const status = e?.findings?.status;
  return e?.code === "UPSTREAM_ERROR" && typeof status === "number" && status >= 400 && status < 500 && status !== 404;
}

// specOptions is undefined on a miss; decide the 404 (and the editor's empty page) from `query`.
export async function fetchPage(url: string, query: Record<string, string>, locale: string):
  Promise<{ specOptions?: StudioComponentSpecOptions; query: Record<string, string> }> {
  const attempt = async (q: Record<string, string>) => {
    stack.livePreviewQuery({ live_preview: "" });
    try {
      const searchQuery = new URLSearchParams(q).toString();
      return { specOptions: await sdk.fetchCompositionData({ url, searchQuery }, { locale }), query: q };
    } catch (err) {
      if (isCompositionNotFound(err)) return { specOptions: undefined, query: q };
      throw err;
    }
  };
  try {
    return await attempt(query);
  } catch (err) {
    const isPreview = "hash" in query || "live_preview" in query;
    if (!isPreview || !previewCodeRefused(err)) throw err;
    const plain = Object.fromEntries(Object.entries(query).filter(([k]) => !PREVIEW_PARAMS.includes(k)));
    return attempt(plain);
  }
}
```

At the route, a missing `specOptions` is the miss: `isStudioEditorMode(result.query)` renders the editor's empty page, and anything else is the framework's 404. Measured after the change: the expired link answered 200 with the published page, a made-up address with a made-up code answered 404, and a real preview opened from Visual Editor still showed the draft.

<a id="static-generation-and-caching"></a>

## Static generation and caching on a Studio route (Next.js)

Three things change when a route starts rendering Studio compositions. None of them errors; they show up as a slower site or stale pages.

- **Reading the request query makes the render dynamic.** Studio needs the query string (editor mode, preview hash, locale, variant) on server-rendered routes, and awaiting `searchParams` in an App Router page (or using `getServerSideProps` in Pages Router) opts that render out of static prerendering. A greenfield catch-all is dynamic, and that is the price of in-place editing. On an app whose catch-all also serves its own pages, read `searchParams` only inside the Studio branch ([`setup-template-preview-routes`](setup-template-preview-routes.md) § Existing catch-all), so the app's own pages keep rendering the way they did.
- **Studio's fetches bypass Next's data cache.** The Delivery SDK uses axios, not `fetch`, so `fetch`-level `revalidate` and cache tags never apply to composition or entry reads. Cache at the route level (`export const revalidate = <seconds>` on a route that doesn't read `searchParams`, or the host's CDN). Don't expect a tag-based `revalidateTag` to touch Studio content.
- **The app's publish webhook doesn't cover compositions.** Compositions are entries of the compositions content type, and an author publishing a page publishes those entries, often without touching any entry the existing webhook listens for. If the app revalidates on publish, add the compositions content type to the webhook and revalidate the composition's `url` (or the whole catch-all) when one is published. A composition with a URL pattern (`/blog/{{entry.url}}`) also changes every page its template serves, so revalidate that path prefix.

Preview and editor requests must never be served from a cache: they carry `hash` / `live_preview` / `cs-composable-studio` params, and a cached copy shows the wrong draft or no editor at all. Keep any CDN rule keyed on the full query string, or bypass the cache when one of those params is present.

## Task

1. **Pick the path** from the decision table using `framework`. Run only the matching block below. Skip the others.

2. **CSR (Vite / SPA, also the universal fallback on any framework, including App Router).**
   ```tsx
   "use client";
   import { useCompositionData, StudioComponent, isCompositionNotFound } from "@contentstack/studio-react";
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
     if (error) return isCompositionNotFound(error)
       ? <NotFound />
       : <ErrorState message={error instanceof Error ? error.message : String(error)} />;
     return <StudioComponent specOptions={specOptions} />;
   }
   ```
   The hook reads `window.location.search` automatically, no `searchQuery` argument required. CSR is the safe universal path: built-ins never enter a server pre-render, so the App-Router RSC crash from registering basics on the server can't happen.

   Ensure **built-ins + custom components are registered before render** (see `register-component`). On CSR, the registration must run client-side at module init.

   **Live Preview wiring is separate.** If this route needs to reflect author edits in real time, add the `onEntryChange` bridge from `install-live-preview` (step 7). CSR pages call the hook's `refetchData` inside the loop-safe callback — it re-fetches just the bound data, which is all a live edit changes.

3. **App Router: SSR through a client wrapper.** A Server Component fetches and computes the styles, a `"use client"` wrapper renders, and Next puts that output in the initial HTML (verified with `curl` in the App Router recipe). Initialize the sdk in a server-only module (no `"use client"`). Register components in a `"use client"` module the wrapper imports. Rendering `<StudioComponent />` directly in a Server Component fails with a Next.js client-component error: the renderer calls hooks.
   ```tsx
   // app/[[...slug]]/page.tsx — NO "use client"
   import { cache } from "react";
   import { notFound } from "next/navigation";
   import { getSSRStyles, isCompositionNotFound, type StudioComponentSpecOptions } from "@contentstack/studio-react";
   import { sdk, stack } from "@/lib/studio.server";
   import { ClientRender } from "./ClientRender";

   // One fetch per request, shared by the page and generateMetadata.
   const getComposition = cache((url: string, searchQuery: string) => {
     stack.livePreviewQuery({ live_preview: "" }); // shared stack: drop the last request's preview hash
     return sdk.fetchCompositionData({ url, searchQuery }, { locale: "en-us" });
   });

   async function toQuery({ params, searchParams }) {
     const { slug } = await params;   // a Promise on Next 15+
     const url = "/" + (slug?.join("/") ?? "");
     const searchQuery = new URLSearchParams((await searchParams) as Record<string,string>).toString();
     return { url, searchQuery };
   }

   export default async function Page(props) {
     const { url, searchQuery } = await toQuery(props);
     let specOptions: StudioComponentSpecOptions;
     try {
       specOptions = await getComposition(url, searchQuery);
     } catch (err) {
       if (!isCompositionNotFound(err)) throw err; // a real failure stays a 500
       notFound(); // in catch, never in try: it works by throwing
     }
     // getSSRStyles here, never in ClientRender: hydration mismatch on the <style>.
     return (
       <>
         <style dangerouslySetInnerHTML={{ __html: getSSRStyles(specOptions.spec) }} />
         <ClientRender specOptions={specOptions} />
       </>
     );
   }

   export async function generateMetadata(props) {
     const { url, searchQuery } = await toQuery(props);
     // Metadata must never throw — a miss here should degrade to empty tags;
     // the page itself sends the 404 or the 500.
     try {
       const { seo } = await getComposition(url, searchQuery);
       return seo
         ? { title: seo.pageTitle, description: seo.pageDescription,
             openGraph: { images: seo.openGraphImage ? [seo.openGraphImage] : [] } }
         : {};
     } catch {
       return {};
     }
   }
   ```
   A wildcard catch-all also needs the editor exemption: an unsaved template opened in Studio misses too. Gate that branch on `isStudioEditorMode(query)` ([`setup-template-preview-routes`](setup-template-preview-routes.md) step 5a (iii)).

   Client wrapper (renders only; no styles or Live Preview here):
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
   // pages/[[...slug]].tsx
   import { sdk, stack } from "@/lib/studio.server";
   import { getSSRStyles, isCompositionNotFound, type StudioComponentSpecOptions } from "@contentstack/studio-react";

   export async function getServerSideProps({ resolvedUrl }) {
     // NOT req.url: on client-side navigation it is /_next/data/<build>/....json.
     const { pathname, search } = new URL(resolvedUrl, "http://localhost");
     let specOptions: StudioComponentSpecOptions;
     try {
       stack.livePreviewQuery({ live_preview: "" }); // shared stack: drop the last request's preview hash
       specOptions = await sdk.fetchCompositionData({ url: pathname, searchQuery: search.replace(/^\?/, "") });
     } catch (err) {
       if (!isCompositionNotFound(err)) throw err; // a real failure stays a 500
       return { notFound: true as const };
     }
     return {
       props: {
         // holds `undefined` values, which next dev refuses to serialize
         specOptions: JSON.parse(JSON.stringify(specOptions)),
         css: getSSRStyles(specOptions.spec),
       },
     };
   }
   ```
   Page renders `<style dangerouslySetInnerHTML={{ __html: css }} />` then `<StudioComponent specOptions={specOptions} />`. The JSON round trip drops `undefined` values (e.g. an unset image), matching what production sends anyway.

   **Live Preview wiring is separate.** If this route needs real-time author updates, mount the `LivePreviewBridge` from `install-live-preview` (step 7) in `pages/_app.tsx` inside a client boundary. Pages Router routes call `router.replace(router.asPath, undefined, { scroll: false })` in the loop-safe callback. Do NOT put `[router]` in the effect deps. The router identity changes on every replace, which would produce an infinite refetch loop.

   Verify true SSR with `next dev` or a prod build (`next build && next start`): both render the same server HTML (checked across five requests and three cold `next dev` boots). Acceptance: `curl <url>` returns 200 with the composition DOM (incl. Repeater iteration items) in `<body>` after stripping `<script>` tags.

5. **SSR (Remix).** Put sdk init in `app/lib/studio.server.ts` so secrets tree-shake out of the browser bundle.
   ```ts
   import { json } from "@remix-run/node";
   import { isCompositionNotFound } from "@contentstack/studio-react";
   import { sdk, stack } from "~/lib/studio.server";

   export async function loader({ request }) {
     const url = new URL(request.url);
     let specOptions;
     try {
       stack.livePreviewQuery({ live_preview: "" }); // shared stack: drop the last request's preview hash
       specOptions = await sdk.fetchCompositionData({ url: url.pathname, searchQuery: url.search.replace(/^\?/, "") });
     } catch (err) {
       if (!isCompositionNotFound(err)) throw err; // a real failure stays a 500
       throw new Response("Not Found", { status: 404 });
     }
     return json({ specOptions });
   }
   ```
   Component: `const { specOptions } = useLoaderData(); return <StudioComponent specOptions={specOptions} />;`

6. **SSG / ISR.** Pass `searchQuery: ""` (no Studio iframe at build time), set `revalidate: 60` for ISR, and wire a Contentstack publish webhook to `res.revalidate(path)` for instant invalidation. The webhook must fire on the compositions content type too ([§ Static generation and caching](#static-generation-and-caching)). Live Preview won't update SSG output until revalidation. If that matters, move the route to SSR.

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

**Compute it on the server only**: the Server Component (App Router) or `getServerSideProps` (Pages Router). In a `"use client"` component the browser computes different CSS, a hydration mismatch.

It takes one spec or an array of them, so a page assembled from several compositions emits one stylesheet. Outside React (Express, a custom server) `getSSRStyleTags(spec)` returns the same CSS already wrapped in a `<style>` tag, to concatenate into an HTML template after `renderToString`.

CSR routes need neither: there is no server pass to be unstyled.

## Acceptance

Succeeds only when ALL of the following are true:

- [ ] The route file uses the fetch path that matches the framework row in the decision table
- [ ] Server-rendered routes emit `getSSRStyles(specOptions.spec)` alongside the markup, checked by loading the route with JavaScript disabled, or `curl`, and confirming Design-panel styling is already applied
- [ ] Server-side paths forward `searchQuery` from the incoming request to `fetchCompositionData`
- [ ] **Every `fetchCompositionData` call is in a `try` / `catch`** that sends the 404 only when `isCompositionNotFound(err)` and **rethrows everything else**. No bare `await sdk.fetchCompositionData(...)` on a route, no blanket `catch { notFound() }`, and no 404 decided from the returned object
- [ ] **Verified with a real miss:** request a URL with no composition (e.g. `/no-such-page`) and a valid-prefix-but-bad-slug URL under a connected template (e.g. `/blog/zzz-not-an-entry`). **Both return 404, not 500.** The second one is the `content_type_url_pattern` case and fails at a different stage. Testing only the first proves nothing about it
- [ ] On App Router, the main entry's `<StudioComponent />` is rendered inside a `"use client"` boundary (the RSC entry's `<StudioServerComponent />` renders in a Server Component instead)
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
| `<StudioComponent />` directly in a Server Component | Next.js client-component error | Wrap in a `"use client"` child taking `specOptions` as prop, or use `<StudioServerComponent />` from `@contentstack/studio-react/rsc` |
| RSC entry route: components registered through the main entry or a `"use client"` module | Those components don't render in `<StudioServerComponent />` output: the RSC renderer keeps its own registry | Register them with `registerComponents` from `@contentstack/studio-react/rsc`, in a server module (no `"use client"`) |
| `searchQuery` not forwarded | Iframe shows wrong locale/variant. Edit mode doesn't engage | Forward `request.url.search` / `new URLSearchParams(searchParams).toString()` |
| Re-fetched on the client after SSR | Hydration mismatch warning | Pass server `specOptions` straight to the client wrapper |
| Different `locale` server vs client | Mismatch warning, content flash | Pin both sides via the second arg of `fetchCompositionData` |
| Live Preview never updates the running page | Missing `onEntryChange` bridge | Wire the `LivePreviewBridge` from `install-live-preview` (step 7). Not a CSR-vs-SSR issue, same fix regardless of framework. |
| **Infinite `_next/data/<id>/<route>.json` (Pages) or RSC payload refetch: Network tab fires hundreds of times per edit** | `onEntryChange` wired in a `[router]`-dep effect | Move the wiring to the loop-safe pattern in `install-live-preview` (step 7): subscribe ONCE with empty deps, hold router in a `useRef`, skip the register-time fire, unsubscribe in cleanup. |
| **`transpilePackages: ['@contentstack/studio-*']` on App Router** | 500 with `Cannot read properties of null (reading 'useContext')` at `useData → RepeaterPreview` during the RSC server prerender | Don't transpile the SDK on App Router. It defeats the SDK's safe client-deferral (the basics resolve to real components, run on the server, and read a null React dispatcher). On Pages Router, transpiling is fine. |
| **Coexisting `app/` dir while SSR-ing a `pages/` route** | The Pages-Router SDK React resolves to the app-page runtime, which gives a null dispatcher and a crash | Make the project Pages-Router-only for the Studio SSR route (remove `app/` from that workspace). |
| **Judging SSR from `next dev`**: Repeater items intermittently render field defaults ("Your text here") | Per-boot dev race (recompile + module-init order + React StrictMode double-invoke) | Verify and ship from a **prod build**: `next build && next start`. Prod is deterministic. Dev is racy. |
| **`dynamic(() => import('@contentstack/studio-react'))` for the canvas, prod build fails** | `Package path "." is not exported from package` | Older `studio-react` releases exposed `.` only under the `import` condition (2.0.1 adds `default`). On 2.x the dynamic import isn't needed at all: `StudioCanvas` is a client component that renders `null` until mount ([`setup-section-preview`](setup-section-preview.md) step 2). On an older SDK, dynamic-import a **local wrapper** that statically imports `StudioCanvas`. |
| **Bare `await sdk.fetchCompositionData(...)` with a guard on the returned object below it** | Every unmatched URL returns **500, not 404**. The fetch rejects, so the guard line never executes. Error boundary shows a generic failure. Nothing names the missing composition | Catch the error and call `isCompositionNotFound(err)` ([pattern](#resolve-composition-helper)). The guard was written for a resolve-with-falsy contract the SDK doesn't have |
| Blanket `try { … } catch { notFound() }` around the fetch | Every CDA outage, expired delivery token, and network blip silently becomes a 404. The site reads as "empty" instead of "broken" and monitoring stays green | Ask `isCompositionNotFound(err)`: true is a 404. Rethrow the rest so real failures stay 500s |
| Testing 404 handling only with a totally unmatched URL | Passes, while every bad slug under a `content_type_url_pattern` template still 500s if you hand-rolled a list of names. That path matches the pattern and fails later, at entry lookup, with a different code | Test both shapes. Use the predicate rather than a list, and both are covered |
| **Server-rendered route paints unstyled, then snaps into place on hydration** | Design-panel styles are generated at render time, not in your stylesheet. Markup alone carries none of them | Emit `getSSRStyles(specOptions.spec)` with the markup. See § Studio-authored styles on a server-rendered route |
| `getSSRStyles` in the App Router `"use client"` wrapper | Hydration mismatch on the `<style>` | Call it in the Server Component `page.tsx` |
| Pages Router reads `context.req.url` | 404 on client-side navigation: `req.url` is `/_next/data/<build>/....json` | Use `context.resolvedUrl` |
| Pages Router returns raw `specOptions` | `next dev`: "Error serializing ... `undefined` cannot be serialized as JSON" | Return `JSON.parse(JSON.stringify(specOptions))` |
| **Every bound image 400s through `next/image`** (`"hostname … is not configured under images"`) | Assets come from a Contentstack CDN host the optimizer doesn't trust by default. Nothing in the composition is wrong | Add the asset hosts to `images.remotePatterns` in `next.config.mjs`: `images.contentstack.io` plus your region's `*-images.contentstack.com`. Region-dependent, so read the URL the binding actually returned rather than guessing |
| SSG never updates after publish | Stale content | Configure ISR `revalidate` or wire a publish webhook to `res.revalidate(path)`, including publishes of the compositions content type ([§ Static generation and caching](#static-generation-and-caching)) |
| Management token in client module | Token shipped to browser | Move sdk init into `*.server.ts` / non-`"use client"` module |

## See also

- `install-studio`: installs the three SDKs and wires `studioSdk.init`
- [`csr-and-ssr-requirements`](csr-and-ssr-requirements.md): what each mode needs in Live Preview, Visual Editor and the canvas, and converting between them
- [`handle-404-pages`](handle-404-pages.md): the 404 branch on every framework
- `setup-section-preview`: adds the `<StudioCanvas />` route
- `troubleshoot-canvas`: when the iframe still doesn't render after both skills are run
