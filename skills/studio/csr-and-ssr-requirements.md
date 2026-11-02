---
name: csr-and-ssr-requirements
---

## When to use

What a Studio page needs to work as a CSR page or an SSR page, everywhere it runs: the visitor site, the Live Preview pane, Visual Editor and Studio's canvas. Also covers converting a page from one mode to the other. Phrases: "what does a CSR page need", "what does an SSR page need", "CSR vs SSR with Live Preview", "Visual Editor with SSR", "convert to SSR", "switch to CSR", "Live Preview doesn't update", "Visual Editor doesn't show my edits", "edit button shows in Visual Editor", "Edit button missing on the preview site", "Visual Editor shows Live Preview behaviour".

Do NOT use for: framework-specific route wiring for Pages Router, Remix and SSG ([`configure-csr-vs-ssr`](configure-csr-vs-ssr.md)), or 404 handling ([`handle-404-pages`](handle-404-pages.md)).

# What a Studio page needs: CSR and SSR

## At a glance

| Need | CSR | SSR |
| --- | --- | --- |
| Fetch | `useCompositionData({ url })` in the browser | `sdk.fetchCompositionData({ url, searchQuery })` on the server, after clearing the shared stack's preview hash ([`resolveComposition`](configure-csr-vs-ssr.md#resolve-composition-helper) does both) |
| Query string | The hook reads `window.location` itself | Pass the full request query string as `searchQuery` |
| Unknown URL (`isCompositionNotFound`) | Render the 404 page, status 200 + `noindex` | Real 404 ([`handle-404-pages`](handle-404-pages.md)) |
| Studio-authored styles | Nothing to add | `getSSRStyles(specOptions.spec)` on the server |
| SEO metadata | `specOptions.seo` in the browser. Crawlers that don't run JavaScript miss it | `generateMetadata` or `getCompositionMetadata` on the server |
| Live Preview `ssr` | `false` | `true` |
| Live Preview `stackSdk` | `stack.config` | Leave it out |
| How the preview hash arrives | In the URL inside Visual Editor; through Live Preview's handshake in the Live Preview pane, written onto the stack via `stackSdk` | In the URL, as `live_preview`. Reaches the server only if `searchQuery` is forwarded |
| Showing an author's edit | `onEntryChange` → `refetchData()` (connected template) or `refetchSpec()` (freeform) | Nothing to wire. The editor reloads the page |
| Preview hash on a shared server | Not applicable | Clear it before every fetch |
| Hydration | Not applicable | Never fetch again in the browser |

## In each editor

| | Live Preview pane | Visual Editor |
| --- | --- | --- |
| **CSR** | The page loads published content, then `onEntryChange` fires and `refetchData()` loads the draft entries. Each edit refetches the data. Edit button shows | The preview hash is already in the URL, so the first load is the draft. Each edit refetches the data. Edit button hidden |
| **SSR** | The hash is in the URL, so the server's first fetch is the draft. Each edit reloads the page. Edit button shows | Same. Edit button hidden |

Studio's canvas needs no Live Preview setup. `<StudioComponent />` handles it in both modes, as long as SSR pages forward `searchQuery`.

## Five settings that all have to be right

Visual Editor and Live Preview work on a Studio page only when all five agree. Each one fails silently.

| Setting | Where it lives | Right value | When it's wrong |
| --- | --- | --- | --- |
| Live Preview on for the stack | Stack Settings › Visual Experience › General ([`enable-visual-experience`](enable-visual-experience.md)) | On | No Live Preview or Visual Editor at all |
| The Delivery stack's `live_preview` | The stack passed to `studioSdk.init` | `enable: true`, the preview token, your region's preview host | Studio shows published content in the editors |
| Edit tags | `studioSdk.init({ cslp: { appendTags: true } })` | `true` (the default is `false`) | Nothing is clickable, and no Edit button appears |
| `mode` | Live Preview `init` | `"builder"` | Visual Editor can't edit the page and shows Live Preview's Edit button |
| `ssr` | Live Preview `init`, overridden by `live_preview.ssr` on the stack passed as `stackSdk` | `true` for server-fetched routes, `false` for browser-fetched ones | Edits don't show up |

They're separate switches: turning on Live Preview for the stack doesn't set `mode`, and `mode` doesn't set `ssr`.

**A site that mixes both fetches still has one `init`, so one `ssr` value.** Pick the value for the site's main Studio route. A route using the other fetch has to cope with it: under `ssr: true`, a browser-fetched route updates only when the editor reloads the page.

## Preview mode and builder mode

| `mode` | What runs | Inside Visual Editor | Needs |
| --- | --- | --- | --- |
| `"preview"` (default) | Live Preview: content updates, and the hover Edit button opens the entry | Shows Live Preview's Edit button; the editor can stay on "Initializing the editor…" | `stackSdk` for CSR pages |
| `"builder"` | Visual Editor's editing layer: click a field on the page to edit it | Works | `stackDetails.apiKey` and `stackDetails.environment`, or `init` throws (the environment falls back to `stackSdk`'s; the API key never does) |

**Visual Editor decides which one runs, not `mode` alone.** In builder mode, Live Preview asks the page around it which editor it's in. Visual Editor answers `builder`; the Live Preview pane answers `preview`. So the same page shows Live Preview behaviour in the pane and Visual Editor behaviour in Visual Editor, by design. With no answer (the page isn't in an editor, or the handshake fails), no editing layer starts.

A Studio page fetched by URL also tells Visual Editor it's a Studio page, so Visual Editor can offer to open it in Studio. Editing on the page works either way.

## Needed in both modes

**One Live Preview module, browser only, loaded only with a preview token.** Two lines differ by mode:

```ts
// lib/live-preview.ts
import { useEffect } from "react";
import type { IStackSdk } from "@contentstack/live-preview-utils";
import { stack } from "./stack";

// Vite names shown. On Next.js use NEXT_PUBLIC_… via process.env.
const previewToken = import.meta.env.VITE_CONTENTSTACK_PREVIEW_TOKEN;
const apiKey = import.meta.env.VITE_CONTENTSTACK_API_KEY;
const environment = import.meta.env.VITE_CONTENTSTACK_ENVIRONMENT;
const appHost = import.meta.env.VITE_CONTENTSTACK_APP_HOST ?? "app.contentstack.com"; // your region's app host

// Imported here, not at the top: Live Preview draws its Edit button as soon as it's imported.
const livePreview =
  previewToken && typeof window !== "undefined"
    ? import("@contentstack/live-preview-utils")
        .then(({ default: lp }) => {
          lp.init({
            enable: true,
            mode: "builder",                              // both modes
            ssr: false,                                   // CSR: false · SSR: true
            stackSdk: stack.config as IStackSdk,          // CSR only · SSR: remove this line
            stackDetails: { apiKey, environment },        // both required in builder mode, or init throws
            clientUrlParams: { host: appHost },
            editButton: { enable: true },
            editInVisualBuilderButton: { enable: false }, // else a "Start Editing" link on every page
          });
          return lp;
        })
        // init throws on a bad config; without this the rejection is easy to miss and the page
        // silently runs without Live Preview or Visual Editor
        .catch((err) => {
          console.warn("[live-preview] init failed", err);
          return null;
        })
    : null;

// CSR pages: refetch the data after each author edit.
export function useLivePreviewEdits(refetch: () => void) {
  useEffect(() => {
    let uid: string | undefined;
    livePreview?.then((lp) => { if (lp) uid = lp.onEntryChange(refetch); });
    return () => void livePreview?.then((lp) => lp && uid && lp.unsubscribeOnEntryChange(uid));
  }, [refetch]);
}
```

Region and non-production hosts: [`install-live-preview`](install-live-preview.md).

- **`mode: "builder"`.** Without it, Live Preview never completes Visual Editor's handshake. Visual Editor can't edit the page, and the Edit button stays visible inside it.
- **`stackDetails: { apiKey, environment }`.** In builder mode `init` throws "api key is required" or "environment is required" without them. The environment falls back to `stackSdk`'s when it isn't in `stackDetails`, so a CSR init gets it from `stack.config`; an SSR init has no `stackSdk` and must pass it. The API key never falls back: always pass it. A throw stops Live Preview completely, so `mode: "builder"` is in the code and Visual Editor still can't edit the page.
- **The dynamic import.** A static `import` of Live Preview draws the Edit button for every visitor, even when `init` never runs. The `PURGE_PREVIEW_SDK` build flag from the Live Preview docs doesn't remove it on Vite.
- **Exactly one `init`.** A second call doesn't restart Live Preview, but it can overwrite the first one's settings. Search first: `grep -rn "ContentstackLivePreview.init\|lp.init(" src app lib`.
- **`ssr` that matches how the page renders.** It tells the Live Preview pane and Visual Editor whether to reload the page or send it the change. Live Preview reads `live_preview.ssr` on the stack passed as `stackSdk` before `init({ ssr })`, so don't set it on the stack, or keep both the same. Always pass `ssr`: left out, it defaults to `false` when `stackSdk` is passed and `true` when it isn't.
- **Restart the dev server after changing `init`.** Live Preview keeps the instance from its first `init`: a second `init`, which is what hot reload runs, takes the new settings but returns the old instance, and Visual Editor's part is only created by the first one. So `mode: "builder"` added while the dev server runs never sends Visual Editor's handshake until a restart. `NEXT_PUBLIC_` / `VITE_` values are also read at server start.
- **A canvas route** with `<StudioCanvas />`, client-only ([`setup-section-preview`](setup-section-preview.md)).

### Where the Edit button shows

| Where the page is open | Edit button | What controls it |
| --- | --- | --- |
| Production site (no preview token) | Hidden | Live Preview isn't imported |
| Preview site in its own browser tab | Shown on hover | `editButton: { enable: true }` with no `exclude` |
| Live Preview pane | Shown on hover | Same |
| Visual Editor | Hidden | `mode: "builder"`: Visual Editor answers the handshake as the builder, and Live Preview removes the button |

`exclude: ["outsideLivePreviewPortal"]` hides the button on the preview site in its own tab. Leave `exclude` out.

### Edit button settings

| Setting | What it does | Default |
| --- | --- | --- |
| `enable` (the whole `init`) | `false` turns Live Preview off; with `cleanCslpOnProduction`, it also strips the edit tags | `true` |
| `editButton.enable` | The hover Edit button | `true` |
| `editButton.exclude` | `"outsideLivePreviewPortal"` hides it outside the editors; `"insideLivePreviewPortal"` hides it inside | `[]` |
| `editButton.includeByQueryParameter` | Lets `?cslp-buttons=false` hide the button on a page, and `?cslp-buttons=true` force it on, overriding `exclude` | `true` |
| `editButton.position` | Where the button sits: `top`, `top-left`, `top-right`, `top-center`, `left`, `right`, `bottom`, `bottom-left`, `bottom-right`, `bottom-center`. One element can override it with `data-cslp-button-position` | `"top"` |
| `editInVisualBuilderButton.enable` / `.position` | The floating "Start Editing" link that opens the page in Visual Editor | on, `"bottom-right"` |
| `cleanCslpOnProduction` | Removes `data-cslp` edit tags when `init` runs with `enable: false` | `true` |

Gate the import on the preview token rather than relying on `enable: false`: importing Live Preview is enough to draw the Edit button.

## What a CSR page needs

1. `useCompositionData({ url })`, with no `searchQuery`.
2. `if (error)`: `NotFound` when `isCompositionNotFound(error)`, the error state otherwise ([`handle-404-pages`](handle-404-pages.md)).
3. The Live Preview module with `ssr: false` and `stackSdk: stack.config`, imported once when the app starts.
4. `useLivePreviewEdits(refetch)`, where `refetch` is `refetchData` on a connected template and `refetchSpec` on a freeform composition (§ Which refetch on studio-react 2.0.1).

```tsx
// src/routes/StudioPage.tsx
import { useLocation } from "react-router-dom";
import { useCallback } from "react";
import { useCompositionData, StudioComponent, isCompositionNotFound } from "@contentstack/studio-react";
import { useLivePreviewEdits } from "../lib/live-preview";
import NotFound from "../pages/NotFound";
import ErrorState from "../pages/ErrorState";

export function StudioPage() {
  const { pathname } = useLocation();
  const { specOptions, isLoading, error, refetchData, refetchSpec } = useCompositionData({ url: pathname });
  // 2.0.1: refetchData only refreshes a connected template's entry; it does nothing
  // on a freeform composition or before the first load succeeds.
  const connected = Boolean(specOptions?.connectedContentTypeUid);
  const refetch = useCallback(() => (connected ? refetchData() : refetchSpec()), [connected, refetchData, refetchSpec]);
  useLivePreviewEdits(refetch);

  if (error) return isCompositionNotFound(error) ? <NotFound /> : <ErrorState />;
  if (isLoading || !specOptions) return <div>Loading…</div>;

  return <StudioComponent specOptions={specOptions} />;
}
```

The hook fetches again when the URL changes, so a catch-all route keeps working across client-side navigation: `<Route path="*" element={<StudioPage />} />`.

### Which refetch on studio-react 2.0.1

**Use `refetchData` for author edits on a connected template.** An edit changes an entry, not the composition, so `refetchData` fetches only the data and keeps the composition on screen: one request for a linked composition where `refetchSpec` makes four. Use `refetchSpec` when the composition itself changed.

**On 2.0.1, `refetchData` does nothing unless a connected composition has loaded.** It refetches only when the loaded composition has a connected content type. On a freeform composition, or when the first load failed, the call is silently ignored, so an edit never appears. That's why the snippet falls back to `refetchSpec` when `connectedContentTypeUid` is empty. Edits made while a fetch is running are not queued on 2.0.1: each one starts its own refetch. Recheck this section when you upgrade: a later SDK release is expected to make `refetchData` handle all three cases.

**The Live Preview pane shows the published composition.** The first load comes from the CDN, before Live Preview passes its preview hash, and `refetchData` refreshes only the entries. Layout changes made in Studio appear in the pane once the composition is published. On 2.0.1 an unpublished composition doesn't open in the pane: its first load fails, so the page shows `NotFound` and the edit callback has nothing to refetch. Publish the composition, or edit it in Studio's canvas.

## What an SSR page needs

1. `sdk.fetchCompositionData({ url, searchQuery })` on the server, with the full request query string.
2. `try` / `catch`: a real 404 when `isCompositionNotFound(err)`, rethrow anything else so it stays a 500 ([`handle-404-pages`](handle-404-pages.md)).
3. `getSSRStyles(specOptions.spec)` and metadata, both on the server.
4. `<StudioComponent />` in a `"use client"` wrapper (App Router).
5. The Live Preview module with `ssr: true` and no `stackSdk`, imported once from a client component in the root layout.
6. On a deployment with a preview token, clear the shared stack's preview hash before every fetch: `stack.livePreviewQuery({ live_preview: "" })`. The SDK sets a request's hash but never clears it, so without this the next visitor gets the last editor's drafts. When the request carries a hash, the SDK sets it again itself ([`configure-csr-vs-ssr`](configure-csr-vs-ssr.md) § A server with a preview token can serve drafts to visitors).

Next.js App Router:

```tsx
// app/[[...slug]]/page.tsx — Server Component, no "use client"
import { notFound } from "next/navigation";
import { getSSRStyles, isCompositionNotFound, type StudioComponentSpecOptions } from "@contentstack/studio-react";
import { sdk, stack } from "@/lib/studio.server";
import { StudioRender } from "./StudioRender";

type Props = {
  params: Promise<{ slug?: string[] }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function Page({ params, searchParams }: Props) {
  const { slug } = await params;
  const url = "/" + (slug ?? []).join("/");
  const searchQuery = new URLSearchParams(
    Object.entries(await searchParams).flatMap(([k, v]) => (Array.isArray(v) ? v.map((x) => [k, x]) : v === undefined ? [] : [[k, v]])),
  ).toString();

  let specOptions: StudioComponentSpecOptions;
  try {
    stack.livePreviewQuery({ live_preview: "" }); // shared stack: drop the last request's preview hash
    specOptions = await sdk.fetchCompositionData({ url, searchQuery });
  } catch (err) {
    if (!isCompositionNotFound(err)) throw err; // a real failure stays a 500
    notFound();
  }

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: getSSRStyles(specOptions.spec) }} />
      <StudioRender specOptions={specOptions} />
    </>
  );
}
```

```tsx
// app/[[...slug]]/StudioRender.tsx
"use client";
import { StudioComponent, type StudioComponentSpecOptions } from "@contentstack/studio-react";

export function StudioRender({ specOptions }: { specOptions: StudioComponentSpecOptions }) {
  return <StudioComponent specOptions={specOptions} />;
}
```

```tsx
// app/LivePreviewInit.tsx — render once in app/layout.tsx
"use client";
import "@/lib/live-preview";

export function LivePreviewInit() {
  return null;
}
```

**No `onEntryChange` on SSR pages.** With `ssr: true`, Live Preview never calls it. The Live Preview pane and Visual Editor reload the page after each edit, the new preview hash arrives in the URL, and `fetchCompositionData` fetches the draft.

Pages Router, Remix and SSG: [`configure-csr-vs-ssr`](configure-csr-vs-ssr.md).

## Converting between CSR and SSR

Converting means swapping one "What … needs" list for the other.

**CSR to SSR:**

1. Move the fetch to the server, and pass `searchQuery`.
2. Remove `useCompositionData` and `useLivePreviewEdits` from the route.
3. Add `getSSRStyles` and server metadata.
4. Change the 404 branch to a real 404.
5. In the Live Preview module, set `ssr: true` and remove `stackSdk`. Import it from the root layout.
6. Keep the delivery token in a server-only module.
7. On a preview deployment, clear the shared stack's preview hash before every server fetch.

**SSR to CSR:**

1. Fetch in the browser with `useCompositionData({ url })`. Remove the server fetch.
2. Remove `getSSRStyles` and server metadata.
3. Change the 404 branch to `NotFound` + `noindex`.
4. In the Live Preview module, set `ssr: false` and add `stackSdk: stack.config`.
5. Add `useLivePreviewEdits(refetch)` (§ Which refetch on studio-react 2.0.1).
6. Keep CSR routes under their own path prefix. Don't switch a whole SEO site to CSR.

## Acceptance

Succeeds only when ALL of the following are true:

- [ ] Production build with no preview token: the page renders and no Live Preview code loads (Network tab). SSR: `curl -s <url> | grep '<known text>'` finds the content.
- [ ] Preview site in its own tab: the Edit button shows on hover.
- [ ] Live Preview pane: after load the page shows the draft, an edit appears without a manual reload, and the Edit button shows. Reload the pane three times; every load reaches the draft.
- [ ] Visual Editor: the page is editable, an edit appears, and **no Edit button** shows.
- [ ] Studio's canvas: a template opens and renders.
- [ ] Unknown URL: shows the 404 page (SSR: status 404).
- [ ] Exactly one Live Preview `init`, with `mode: "builder"`, `stackDetails: { apiKey, environment }` and the `ssr` value that matches the route.
- [ ] Framed with `?builder=true`, the page sends Visual Editor's `init` handshake with `isSSR` matching `ssr` (§ Troubleshooting).
- [ ] SSR: no `useCompositionData` on a route that fetched on the server, and no hydration warning in the console.

If acceptance fails, report which check broke and stop.

## Troubleshooting: Visual Editor shows Live Preview behaviour

**First, without signing in:** on any page of the site, frame the same page with `?builder=true` and listen for Visual Editor's handshake:

```js
// in the console of a page on the site (e.g. http://localhost:3000/)
window.addEventListener("message", (e) => {
  if (e.data?.channel === "visual-builder") console.log(e.data.type, e.data.payload);
});
const f = document.createElement("iframe");
f.src = location.pathname + "?builder=true";
document.body.append(f);
```

Builder mode logs `init` with `{ isSSR: … }` (matching your `ssr`) within a few seconds. Only `live-preview` messages, or nothing, means the page isn't in builder mode, its `init` threw, or the dev server still runs an older setup.

Then open the page in Visual Editor. In the console of the **site's frame** (pick it in the DevTools context menu):

1. `location.search` contains `builder=true`. If not, the page isn't open in Visual Editor; it's probably the Live Preview pane, where Live Preview behaviour is correct.
2. `document.getElementById("cslp-tooltip")` returns `null`. If it returns an element, the builder handshake didn't happen: check `mode: "builder"`, then the next steps.
3. No "You have already initialized the Live Preview SDK" warning. If it's there, a second `init` ran (another module, or hot reload) and may have changed `mode` or `ssr`, while the first one's instance stays: restart the dev server.
4. No "Live preview SDK: api key is required" or "environment is required" error: builder mode needs both in `stackDetails`.
5. Live Preview loaded at all. If the preview token was added after the dev server started, the import never ran. Restart the dev server, then hard-reload the editor.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Live Preview off for the stack | Every piece works locally and nothing reaches the editors | Turn it on ([`enable-visual-experience`](enable-visual-experience.md)) |
| `cslp.appendTags` not set | The default is `false`: no edit tags, so nothing to click and no Edit button | `studioSdk.init({ …, cslp: { appendTags: true } })` |
| `init` without `mode: "builder"` | Visual Editor's handshake never completes: the page isn't editable and the Edit button shows inside Visual Editor | Add `mode: "builder"` |
| `stackDetails.apiKey` or `.environment` missing in builder mode | `init` throws: the API key never comes from `stackSdk`, and without `stackSdk` (SSR) neither does the environment | Always pass `stackDetails: { apiKey, environment }` |
| `init` inside `.then()` with no `.catch` | A throw becomes an unhandled rejection: the page renders, Live Preview never starts, and Visual Editor can't edit it although the code says `mode: "builder"` | Add `.catch` and log the error |
| A second `init` call elsewhere | It can overwrite the first one's settings, so `mode` or `ssr` silently changes | Keep one `init`. Search for others |
| `editButton.exclude: ["outsideLivePreviewPortal"]` | Hides the Edit button on the preview site in its own tab | Remove `exclude` |
| Static `import` of Live Preview | It draws the Edit button on import, so production visitors see it. `PURGE_PREVIEW_SDK` doesn't help on Vite | Import it dynamically, only with a preview token |
| `clientUrlParams.host` hard-coded to the US host | Edit and Start Editing open the wrong region's app | Use your region's Contentstack app host |
| `ssr` doesn't match how the page renders | The editors push changes to a page that needs a reload, or reload a page that needed a callback. Edits don't appear | Set `ssr` to the route's render mode |
| `live_preview.ssr` set on the Delivery stack | It takes precedence over `init({ ssr })` | Remove it, or keep both the same |
| CSR page calls `refetchSpec` on every edit of a connected template | It reloads the composition and its sections each time: four requests per edit instead of one | Call `refetchData` |
| CSR freeform page calls only `refetchData` (2.0.1) | `refetchData` ignores a composition with no connected content type, so edits never appear | Fall back to `refetchSpec` when `connectedContentTypeUid` is empty |
| SSR fetch without clearing the preview hash | The SDK sets a request's hash on the shared stack and never clears it, so later visitors get drafts | `stack.livePreviewQuery({ live_preview: "" })` before each fetch, or use `resolveComposition` |
| SSR `catch { notFound() }` with no check | A bad token or an outage becomes a 404 on every page | 404 only when `isCompositionNotFound(err)`; rethrow the rest |
| CSR `init` without `stackSdk` | Live Preview can't write the preview hash onto the stack, so refetches return published content | Pass `stackSdk: stack.config` |
| SSR route with an `onEntryChange` → `router.refresh()` bridge | With `ssr: true`, Live Preview never calls `onEntryChange` | Delete it. The editor reloads the page |
| SSR `searchQuery` not forwarded | The preview hash and Studio's editor context never reach the server | Pass the full request query string |
| Fetching again in the browser after an SSR fetch | Hydration mismatch | Pass the server's `specOptions` to the client wrapper |
| `init` changed but nothing changed in the editor | Live Preview keeps its first instance: a hot-reloaded `init` never creates Visual Editor's part | Restart the dev server and hard-reload the editor |

## See also

- [`configure-csr-vs-ssr`](configure-csr-vs-ssr.md): route wiring for Pages Router, Remix and SSG
- [`handle-404-pages`](handle-404-pages.md): unknown URLs in both modes
- [`install-live-preview`](install-live-preview.md): Delivery SDK preview settings, regions and hosts
- [`enable-visual-experience`](enable-visual-experience.md): turning on Live Preview for the stack
- [`deploy-studio-site`](deploy-studio-site.md): production builds without Live Preview
