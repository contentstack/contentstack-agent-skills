---
name: wire-external-data
description: "Bring external (non-Contentstack) data into a composition by fetching in the host app and passing via the `data` prop on `<StudioComponent />` — surfaced as Component Default Data."
allowed-tools: Read Grep Glob
---

## When to use

Bring external (non-Contentstack) data into a composition by fetching in the host app and passing via the `data` prop on `<StudioComponent />` — surfaced as Component Default Data.

Use when a composition needs values outside Contentstack — live pricing, A/B variants, user profile, geolocation, feature flags, URL query params. Works in BOTH CSR and SSR. Phrases — "show data from X here", "external API in composition", "use query params", "feature flag value". Pattern is fetch-then-pass-through `data={...}`, bind under Component Default Data.

# Wire External Data

## Context

Studio compositions natively bind to Contentstack entries, but most apps also need non-CMS data — live pricing, URL parameters, A/B flags, user region, weather. Studio handles this through one mechanism: the `data` prop on `<StudioComponent />`. Whatever object you pass becomes available in the canvas Data Picker under **Component Default Data**, alongside the usual Contentstack roots (Linked Template Entry, Additional Entry Data, Contentstack Query, Repeater Data). The host app owns the fetch — Studio just renders. The same pattern works in CSR (Vite/SPA) and every SSR flavour (Next App Router, Next Pages Router, Remix, Astro); only the fetch location moves.

Reference: `docs/20-bring-your-own-components/set-component-default-data.md`.

## Task

1. **Prereq: `<StudioComponent specOptions={...} />` already renders on this route.** If not, run `setup-template-preview-routes` first — there is nothing to attach `data` to until the renderer is mounted.

2. **Construct the data object.** It must be **JSON-serialisable** — plain objects, arrays, strings, numbers, booleans, null. No functions, no class instances, no Dates that aren't serialised, no React elements. Examples by `dataSource`:

   ```ts
   // Live pricing API
   const data = { livePricing: await getLivePricing(sku) };

   // URL query params — Next App Router (server component)
   const data = { params: Object.fromEntries(new URLSearchParams(searchParams)) };

   // URL query params — Next Pages Router (getServerSideProps)
   const data = { params: context.query };

   // URL query params — Vite SPA (client)
   const [searchParams] = useSearchParams();
   const data = { params: Object.fromEntries(searchParams) };

   // User region from request headers
   const data = { region: getRegionFromRequest(request) };

   // Feature flags for the current user
   const data = { flags: await flagsClient.getAllForUser(userId) };
   ```

3. **Pass `data` to `<StudioComponent />` per `renderPath`:**

   **CSR (Vite / SPA)** — fetch composition with `useCompositionData`, fetch external data via `useState` + `useEffect`, render once both resolve:

   ```tsx
   const { specOptions } = useCompositionData(/* ... */);
   const [extData, setExtData] = useState(null);
   useEffect(() => { getLivePricing(sku).then(setExtData); }, [sku]);
   if (!specOptions?.spec || !extData) return null;
   return <StudioComponent specOptions={specOptions} data={{ livePricing: extData }} />;
   ```

   **SSR — Next App Router** — server component awaits both in parallel, hands off to a client wrapper:

   ```tsx
   // app/[[...slug]]/page.tsx (server)
   const [specOptions, livePricing] = await Promise.all([
     sdk.fetchCompositionData(/* ... */),
     getLivePricing(sku),
   ]);
   return <StudioClient specOptions={specOptions} data={{ livePricing }} />;

   // StudioClient.tsx (client)
   "use client";
   export function StudioClient({ specOptions, data }) {
     return <StudioComponent specOptions={specOptions} data={data} />;
   }
   ```

   **SSR — Next Pages Router / Remix** — same shape via `getServerSideProps` / `loader`; pass `data` through props.

4. **Bind in the Studio canvas.** Open the composition, **select the component** on the canvas (the Component Default Data root only appears when a component is selected AND that component has registered props in its `registerComponent` schema — verified by Studio tests: `hides Component Default Data tab when component has no props`). In the right panel, open the **Data** tab. Click the binding chip on the prop you want to wire and pick **Component Default Data → `<yourKey>.<field>`** — e.g. `livePricing.unit_price`, `params.utm_source`, `flags.checkout_v2`. Save.

5. **Verify.** Open the route in a normal browser tab. The component renders with the external value. For URL params, change the query string — the bound props update on reload (CSR) or next request (SSR).

## URL parameters — extra notes

- Capture from the request → put into `data.params` → bind components to `params.<key>` in the picker.
- **SSR**: read on the server (`searchParams` prop in App Router, `context.query` in Pages Router, `request.url` in Remix loader) and forward into `data`. Do **NOT** call `useSearchParams` in a server component.
- **CSR**: `useSearchParams` from `react-router-dom` is fine; convert to a plain object with `Object.fromEntries`.

## Inputs needed from the user

In this order. If any is missing, ask before editing code.

1. `dataSource` — where the external data comes from.
2. `dataShape` — sketch of the object so we know the binding keys.
3. `renderPath` — picks the code shape in step 3.
4. `routePath` — the file to edit.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, surface the failure and stop.

- [ ] `routePath` fetches `dataSource` and passes the result through `data={...}` on `<StudioComponent />`.
- [ ] The data object is JSON-serialisable end-to-end (no functions / class instances / non-serialisable values).
- [ ] In SSR, fetch happens on the server; the client wrapper only renders.
- [ ] Opening the route's composition in Studio and selecting a component shows **Component Default Data** as a root in the Data Picker.
- [ ] A prop bound to `<key>.<field>` displays the external value in a normal browser tab — verified by reload/screenshot.
- [ ] For URL params: changing the query string changes the bound prop value.

## Common pitfalls

| Pitfall | Symptom | Fix |
| --- | --- | --- |
| Component Default Data root missing in picker | No "Component Default Data" entry when binding | Select a component first; ensure the component declares props in its `registerComponent` schema (the root is gated on registered props, not on the `data` prop itself) |
| Non-JSON values in `data` | SSR serialization error / hydration crash | Strip functions, class instances, Dates; pass plain objects only |
| Hydration mismatch on data-driven props | React warning + flicker on first paint | Compute the value once server-side; do not recompute differently on the client |
| Fetching external data inside a registered component | Component re-fetches on every render; can't reuse elsewhere | Move the fetch to the route, pass through `data` prop |
| `useSearchParams` in a server component | Build / runtime error | Read `searchParams` prop (App Router) or `context.query` (Pages Router) instead |
| Binding chip points at `template.*` or `contentstack.*` | Wrong picker root selected | Re-open picker, choose **Component Default Data** explicitly |
| **Binding a `file` (multiple) field directly to an `imageurl` / scalar URL prop** — renders "No image" or shows the array `.toString()` | A multiple-file field is an asset *array*, not a scalar URL. Binding to `images` yields the whole array; the prop expects a single string. | Bind to the **first asset's URL**: `entryBind("imageurl", "images.0.url")`. If the prop should iterate (multiple images shown), use a **Repeater** bound to the array and bind `imageurl` to `repeater.url` inside the repeater item. `.0.url` is for single-image props only. |
| **Binding a `file` (SINGLE) field directly to an `imageurl` / scalar URL prop** — `<img>` renders broken / `src` is `[object Object]` / built-in `Image` renders the default placeholder | A single-file field is an **asset object** (`{ uid, url, content_type, filename, title, ... }`), NOT a URL string. Binding `featured_image` to a string-expecting prop yields the whole object; the data binder treats `imageurl` as a string — there's no special unwrap. Built-in `Image` then renders `<img src="[object Object]">` (or falls back to the default-placeholder URL when the asset object stringifies to empty). | **Bind the `.url` subfield**: `entryBind("imageurl", "featured_image.url")`. For the built-in `Image` component (prop `src` typed `imageurl`), bind to `<file_field>.url` — e.g. `featured_image.url`. For custom registered components consuming the asset object, you can also accept the full object and read `asset.url` yourself; a small `assetUrl()` helper handling `string \| { url }` is the safest cross-binding signature. |

## See also

- `docs/20-bring-your-own-components/set-component-default-data.md` — full reference.
- `docs/90-reference/composition-rendering-reference.md` — the `data` prop's exact shape + how authors see it in the Data Picker, alongside the other prop (`specOptions`).
- Pair with `setup-template-preview-routes` if `<StudioComponent />` is not yet mounted on the route.
- Pair with `configure-csr-vs-ssr` when choosing the render path for a new project.
