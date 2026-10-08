# Init placement by framework

The SDK has no framework adapters. Framework choice decides exactly two things: where `init()` is
allowed to run, and whether the framework's hydration preserves the edit-tag attributes you spread
into the markup. Everything else follows from the rendering mode, covered in `rendering-modes.md`.

`init()` touches `window`. It must run in the browser, once, before the first content render that
needs to be previewable.

## Next.js, App Router

The most common mistake in this framework, and the one that produces "the SDK is installed and
nothing happens" with no error in the browser. On the server, `init()` logs "The SDK is not
initialized in the browser." and returns.

`init()` cannot run in a server component. Put it in a client component and import that into the
layout so it runs once per app load. The options differ by mode.

CSR (content fetched in the browser):

```tsx
"use client";

import { useEffect } from "react";
import ContentstackLivePreview from "@contentstack/live-preview-utils";

export function LivePreviewInit() {
  useEffect(() => {
    ContentstackLivePreview.init({
      ssr: false,
      mode: "builder",
      stackSdk: stack.config,
      stackDetails: { apiKey: API_KEY, environment: ENVIRONMENT },
    });
  }, []);

  return null;
}
```

SSR (server components fetch at request time). `init()` takes no `stackSdk`; the server applies
the hash per request instead:

```tsx
// LivePreviewInit.tsx
"use client";
import { useEffect } from "react";
import ContentstackLivePreview from "@contentstack/live-preview-utils";

export function LivePreviewInit() {
  useEffect(() => {
    ContentstackLivePreview.init({
      ssr: true,
      mode: "builder",
      stackDetails: { apiKey: API_KEY, environment: ENVIRONMENT },
    });
  }, []);
  return null;
}

// app/[...slug]/page.tsx
export default async function Page({ searchParams }) {
  const params = await searchParams; // a Promise since Next.js 15
  const stack = createStack();       // new Delivery SDK instance per request
  stack.livePreviewQuery(params);    // reads live_preview, content_type_uid, entry_uid, preview_timestamp
  // fetch through `stack` ...
}
```

Watch for three things here:

- Soft navigation does not re-run server-side gating, and the SDK's module-level state persists
  across route changes. Gate the edit button on something that is re-evaluated client-side, or it
  will appear on production pages after a client-side navigation.
- App Router metadata is produced by `generateMetadata()`, which has no hook for injecting window
  globals. If you are using the `window.__CS_PAGE_CONTEXT__` route for page context, set it from a
  client component, or use the `<meta>` tag form instead. The SDK always sends page context, but
  Visual Editor uses it only when **Custom Preview URLs** is enabled for the stack; otherwise it is
  silently ignored.
- Reading `searchParams` opts the route out of static rendering. Expect that when you add the SSR
  hash path.

For SSR, build the Stack instance inside the request rather than at module scope. See
`rendering-modes.md`.

## Next.js, Pages Router

Works, in both of its data-fetching modes. Which contract applies depends on the method the route
uses, not on the router:

- **`getServerSideProps`** is SSR. Apply the SSR contract from `rendering-modes.md`: build the Stack
  inside the function so it is per request, read the hash from `context.query.live_preview`, apply it
  with `livePreviewQuery()`, and initialise with `ssr: true`.
- **`getStaticProps`** is SSG. The page is prerendered and never sees the query string, so run
  Live Preview in CSR mode: `ssr: false`, `stackSdk` passed, content refetched in `onEntryChange`.
  No rebuild is needed for preview.

Initialise once in `_app`, guarded to the client, since `init()` touches `window`.

There is no page dedicated to the Pages Router in the Contentstack docs. Use the general pages for
the mode in play — Set Up Live Preview with REST for SSR for `getServerSideProps`, and the SSG page
for `getStaticProps` — and the same contracts hold.

## React SPA with Vite

The simplest case and the reference implementation. Init at the app entry point, before the first
render:

```ts
ContentstackLivePreview.init({
  ssr: false,
  mode: "builder",
  stackSdk: stack.config,
  stackDetails: { apiKey: API_KEY, environment: ENVIRONMENT },
});
```

`stackSdk` is mandatory in CSR mode. Omitting it also flips the automatic `ssr` default to `true`,
which is a silent misconfiguration rather than an error.

Refresh content through `onEntryChange`. If edits only appear after a manual reload, the callback
was never registered, or it closed over a pathname captured at mount and is refetching the previous
route.

## Nuxt

Init in a client-only plugin (`plugins/live-preview.client.ts`). Nuxt in SSR mode follows the SSR
contract: read the hash from the request in the server fetch and build the Stack per request. Nuxt
with `ssr: false` follows the CSR contract. Visual Editor overlays are drawn by the SDK inside the
iframe, so they work in both modes once edit tags are spread onto the rendered elements.

For page context, `useHead()` is the natural place to emit the `<meta>` tags. Page context only takes
effect when **Custom Preview URLs** is enabled for the stack.

## Angular

Init in `APP_INITIALIZER` or the root component. A client-rendered Angular app follows the CSR
contract: `ssr: false`, `stackSdk` passed, `onEntryChange` for refresh.

Angular with server rendering (Angular SSR, formerly Universal) follows the SSR contract: guard
`init()` to the browser with `isPlatformBrowser`, read the hash from the server request, and build
the Stack per request.

## SvelteKit and Astro

Both follow the contract of the rendering mode in use. Server-rendered routes (SvelteKit `load` on
the server, Astro with a server adapter) take the SSR contract: hash from the request, fresh Stack
instance per request, full reload on update. Client-only routes take the CSR contract. Init in
`onMount` (SvelteKit) or a client-side `<script>` (Astro).

On some hosts the enable flag reaches the deployed Astro build as a string rather than a boolean, and
`"false"` is truthy. If init appears not to run, check the parsed value first.

## Gatsby

Gatsby pages are prerendered, so preview runs in CSR mode: `ssr: false`, `stackSdk` passed, content
refetched on edit through `onEntryChange`. No rebuild is needed. Fetch preview content with the
Delivery SDK on the client; GraphQL data from the build is published content.

Visual Editor needs edit tags on the client-fetched entries, as in any CSR app. The published Gatsby
starter pins Live Preview Utils v1.x, which predates Visual Editor; upgrade to v3+ before adding
`mode: "builder"`.

`getGatsbyDataFormat` still appears in the SDK's README but no longer exists in the source (removed
in v3). Do not recommend it.

## Edge runtimes

Nothing in the integration depends on a Node-only API. `init()` runs in the browser, and the server
side is the fetch from contract 3: read the hash, switch host, add the `live_preview` and
`preview_token` headers. That works the same in an edge function. Two things to confirm: the edge
platform does not cache the preview response, and the Stack instance is created per request.

## Non-JavaScript backends, BFFs and proxies

Supported. The server-side integration is the fetch branch from contract 3 in SKILL.md: read the hash
from the request, switch host, add the `live_preview` and `preview_token` headers, and bypass cache.
A backend that proxies Contentstack must forward the hash end to end. The JavaScript Live Preview
Utils SDK still runs in the rendered page, whatever the backend, because it is what talks to the
editor.

Edit tags are plain attributes: `data-cslp="<content_type_uid>.<entry_uid>.<locale>.<field_path>"`.
Any server language can render them. Where a utils package has a helper, use it:

| Backend | Live Preview | Edit tags |
|---|---|---|
| .NET | `LivePreviewQueryAsync(dict)` on the Delivery SDK client, with the request's query parameters. [Docs](https://www.contentstack.com/docs/developers/sdks/content-delivery-sdk/dot-net/get-started-with-dot-net-sdk-and-live-preview) | `Contentstack.Utils.addEditableTags(entry, contentTypeUid, tagsAsObject, locale, options)` |
| Java | the Delivery SDK's live preview query with the request's query parameters | `Utils.addEditableTags(entry, contentTypeUid, tagsAsObject, locale)` in `contentstack-utils-java` |
| Python | the Delivery SDK's live preview query with the request's query parameters | `addEditableTags(entry, contentTypeUid, tagsAsObject, locale)` from `contentstack_utils` |
| PHP, Ruby | the Delivery SDK's live preview query with the request's query parameters | no helper in the utils package; render `data-cslp` with the format above |

All helpers match the JavaScript `addEditableTags`, so [edit-tags.md](edit-tags.md) applies to them
unchanged.
