# Init placement by framework

The SDK has no framework adapters. Framework choice decides exactly two things: where `init()` is
allowed to run, and whether the framework's hydration preserves the edit-tag attributes you spread
into the markup. Everything else follows from the rendering mode, covered in `rendering-modes.md`.

`init()` touches `window`. It must run in the browser, once, before the first content render that
needs to be previewable.

## Next.js, App Router

The most common setup mistake in this framework, and the one that produces "the SDK is installed
and nothing happens" with no error anywhere.

`init()` cannot run in a server component. Put it in a client component and import that into the
layout so it runs once per app load:

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

Watch for three things here:

- Soft navigation does not re-run server-side gating, and the SDK's module-level state persists
  across route changes. Gate the edit button on something that is re-evaluated client-side, or it
  will appear on production pages after a client-side navigation.
- App Router metadata is produced by `generateMetadata()`, which has no hook for injecting window
  globals. If you are using the `window.__CS_PAGE_CONTEXT__` route for page context, set it from a
  client component, or use the `<meta>` tag form instead. Page context is only honoured when
  **Custom Preview URLs** is configured and enabled on the plan; without that it is silently ignored.
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
for `getStaticProps` — and the same contracts hold. Contentstack's own Live Preview sanity fixture
runs on the Pages Router.

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

Init in a client-only plugin. For page context, `useHead()` is the natural place to emit the
`<meta>` tags, since Nuxt produces head tags natively and has no built-in hook for injecting window
globals. As everywhere, page context only takes effect with **Custom Preview URLs** configured and
enabled on the plan.

The Nuxt CSR and SSR stories differ on whether Visual Editor overlays appear, and Contentstack's
own material is inconsistent on this point. Verify against the actual app before promising overlay
support.

## Angular

Init in `APP_INITIALIZER` or the root component. By contract this is the same as the React SPA
case: CSR, `stackSdk` mandatory, `onEntryChange` for refresh. Only the placement idiom differs.

Angular Universal (SSR) is not covered by documentation. Apply the SSR contract from
`rendering-modes.md` and verify.

## SvelteKit and Astro

Both are SSR with a Node adapter in their documented form, so the SSR contract applies unchanged:
hash from the request, fresh Stack instance per request, full reload on update.

Astro on some hosting platforms has an environment-variable parsing trap where the enable flag does
not arrive as a boolean in the deployed build. If init appears not to run there, check the parsed
value before checking anything else.

Neither has support history. Do not present either as proven.

## Gatsby

Gatsby uses its own path via `ContentstackGatsby`, which previews without a rebuild. It needs
`__typename` and `uid` in the GraphQL query, plus `addContentTypeUidFromTypename`.

Two cautions. The published Gatsby starter is pinned to a Live Preview Utils v1.x release that
predates Visual Editor, so it is not a valid Visual Editor reference. And whether Visual Editor
works on a Gatsby static architecture is an open question internally, not a settled yes. Scope
Gatsby answers to Live Preview unless the user has verified Visual Editor themselves.

Note that `getGatsbyDataFormat` still appears in the SDK's README and configuration docs but has no
implementation in the current source. It was removed in v3. Do not recommend it.

## No SDK, or a non-JavaScript backend

A first-class population, not a fallback. This shape covers every BFF, middleware, proxy, and
non-JavaScript server.

There is no `init()` to place on the server. The whole server-side integration is the fetch branch
from contract 3 in the parent skill: read the hash from the request, switch host, add the
`live_preview` and `preview_token` headers, and bypass cache for that request. If the application
proxies Contentstack through its own backend, the hash has to be forwarded end to end, from the
browser through the backend and into the outbound header. The JavaScript Live Preview Utils SDK is
still required in the rendered page, whatever the backend is — it is what talks to the editor.

### .NET

The best-covered non-JavaScript stack. Verified against the SDK sources, not inferred:

- **Live Preview** is documented for both SSR and CSR in
  [Get Started with .Net SDK and Live Preview](https://www.contentstack.com/docs/developers/sdks/content-delivery-sdk/dot-net/get-started-with-dot-net-sdk-and-live-preview).
  The hash is applied with `await contentstackClient.LivePreviewQueryAsync(dict)`, where `dict`
  carries the request's query parameters. The same per-request-instance rule as every SSR stack
  applies. Timeline is supported by the same SDK.
- **Edit tags, and therefore Visual Editor,** are supported through the `Contentstack.Utils` package:
  `Contentstack.Utils.addEditableTags(entry, contentTypeUid, tagsAsObject, locale, options)`, with an
  `addTags` alias and an `AddEditableTagsOptions.UseLowerCaseLocale` flag. It is written for parity
  with the JavaScript `addEditableTags` and emits the same `data-cslp` and `data-cslp-parent-field`
  attributes, so everything in the edit-tag entries applies unchanged.
- **Two gaps to be honest about.** The .NET Live Preview docs page does not mention edit tags or
  Visual Editor at all, and none of the public .NET example apps (Blazor starter, Razor Pages,
  GraphQL) wire up Live Preview. So a user setting up Visual Editor on .NET is working from the
  utils SDK rather than from a walkthrough. Point them at `Contentstack.Utils` and the edit-tag
  entries, and do not promise a reference app.

### Other server SDKs

Java, PHP, Python and Ruby have Live Preview get-started pages in the same SSR shape. Whether their
utils packages implement edit tags has not been verified here — check the package before promising
Visual Editor on those stacks, and say so if it is absent.
