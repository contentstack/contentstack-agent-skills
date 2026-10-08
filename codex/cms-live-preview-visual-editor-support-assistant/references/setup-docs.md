# New integrations

SKILL.md step 2 sends new integrations here: nothing integrated yet, or Visual Editor or Timeline
being added to a working Live Preview site.

The official documentation is the source of truth. Link the right page and check the requirements
below against it. Do not write setup procedures from memory.

## Steps

1. **Product.** Live Preview, Visual Editor, Timeline, or more than one. Visual Editor and Timeline
   both build on a working Live Preview, so set that up first.
2. **Framework and rendering mode.** Read them from the code when it is available (`package.json`,
   `app/` vs `pages/`, how each route fetches). If the mode is not decided yet, as on a new site,
   give both candidate pages with one line on how to choose, and ask nothing else.
3. **Documentation page.** Pick it from the tables below.
4. **Requirements for that mode.** Walk the matching sections under "Requirements the docs make easy
   to miss" and confirm each one, in the code or with the user.
5. **Verify.** Use the checks under "Verify". If verification fails, continue at step 3 of
   SKILL.md with the check result you already have.

## Documentation pages

### Start here

- [Set Up Live Preview for Your Website](https://www.contentstack.com/docs/headless-cms/set-up-live-preview-for-your-website), the setup hub
- [How Live Preview Works](https://www.contentstack.com/docs/headless-cms/how-live-preview-works)
- [How Live Preview Works with SDK](https://www.contentstack.com/docs/headless-cms/how-live-preview-works-with-sdk), how `ssr` is resolved and how the hash travels

### By framework and mode

| Framework and mode | Page |
|---|---|
| Next.js App Router, CSR | [Live Preview Implementation for Next.js CSR App Router](https://www.contentstack.com/docs/headless-cms/live-preview-implementation-for-nextjs-csr-app-router) |
| Next.js App Router, SSR | [Live Preview Implementation for Next.js SSR App Router](https://www.contentstack.com/docs/headless-cms/live-preview-implementation-for-nextjs-ssr-app-router) |
| React, CSR | [Live Preview Implementation for ReactJS CSR Website](https://www.contentstack.com/docs/headless-cms/live-preview-implementation-for-reactjs-csr-website) |
| Any framework, SSG | [Set Up Live Preview for Static-Site Generator (SSG)](https://www.contentstack.com/docs/headless-cms/set-up-live-preview-for-static-site-generator-ssg), which runs in CSR mode with `ssr: false` |
| Any framework, SSR over REST | [Set Up Live Preview with REST for Server-Side Rendering](https://www.contentstack.com/docs/headless-cms/set-up-live-preview-with-rest-for-server-side-rendering) |
| Next.js Pages Router | No dedicated page. Use the SSR page for `getServerSideProps` and the SSG page for `getStaticProps` |
| .NET | [Get Started with .Net SDK and Live Preview](https://www.contentstack.com/docs/developers/sdks/content-delivery-sdk/dot-net/get-started-with-dot-net-sdk-and-live-preview); edit tags come from `Contentstack.Utils` |

Where `init()` goes in each framework: [frameworks.md](frameworks.md).

Routing that does not map 1:1 onto `Base URL + entry.url`, or `setPageContext()`:
[Custom Preview URLs](https://www.contentstack.com/docs/headless-cms/custom-preview-urls). It is
plan-gated; point to it rather than restating its pattern syntax.

### Visual Editor

- [Set Up Visual Editor for Your Website](https://www.contentstack.com/docs/headless-cms/set-up-visual-editor-for-your-website)
- [Set Up Live Edit Tags for Entries with REST](https://www.contentstack.com/docs/headless-cms/set-up-live-edit-tags-for-entries-with-rest), the `addEditableTags()` reference

### Timeline

- [Set Up Timeline for Your Website](https://www.contentstack.com/docs/headless-cms/set-up-timeline-for-your-website)

### Other

- **Preview Sharing** is not an integration task. A content manager shares the link from the editor;
  nothing on the site changes. [About Preview Sharing](https://www.contentstack.com/docs/headless-cms/about-preview-sharing).
- **Starters.** [Kickstart Next.js](https://www.contentstack.com/docs/headless-cms/next) and its
  siblings are working references. When a user's setup disagrees with a kickstart, the kickstart is
  right.

## Requirements the docs make easy to miss

Confirm only the sections that apply.

### Stack settings (every product)

- Live Preview enabled under Settings → Visual Experience, with a default preview environment.
- A Preview Token generated against the Delivery Token the site already uses. Never a management
  token in client code.
- Every environment and locale to preview has a Base URL, including the scheme (`https://`) and any
  locale path segment.
- Versions: Live Preview Utils v3.0+ for Visual Editor, v4.4.4+ for `setPageContext()`. On the legacy
  `contentstack` JavaScript SDK, v3.20.3+; `@contentstack/delivery-sdk` releases are all newer. One
  copy of the preview SDK on the page.

### Every rendering mode

- `init()` runs in the browser, once. In Next.js App Router that means a `"use client"` component.
- Every content fetch goes through the Stack instance configured with `live_preview: { enable: true,
  preview_token, host: <region preview host> }`. No second instance, no fetch helper that bypasses it.
- Hosts match the stack's region: delivery, preview, GraphQL and the app host
  (`clientUrlParams.host`). Region host names are in `wrong-region-hosts-in-sdk-and-preview-config`
  in [faq-integration.md](faq-integration.md#wrong-region-hosts-in-sdk-and-preview-config).
- No cache on the preview path: no CDN caching for the preview deployment, `cache: "no-store"` on
  preview fetches.
- Set `ssr` in one place. An `ssr` in the Stack's `live_preview` config overrides `init({ ssr })`.

### CSR and SSG

- `ssr: false` and `stackSdk` passed to `init()`. Without `stackSdk` the SDK defaults to SSR.
- Refetch on edit with `ContentstackLivePreview.onEntryChange(fetchFn)`. Read the current route
  inside the callback, not from a value captured at mount.

### SSR

- `ssr: true`. Updates arrive as a parent-driven reload, so do not rely on `onEntryChange`.
- Build the Stack instance **per request**. A module-level instance leaks one editor's draft into
  other visitors' responses.
- Read `live_preview` (and `content_type_uid`, `entry_uid`, `preview_timestamp`) from each request
  and call `stack.livePreviewQuery(query)` on every request, even when there is no hash, so the
  instance resets. In Next.js 15, `searchParams` is a Promise: await it first. Snippet:
  [frameworks.md](frameworks.md#nextjs-app-router).
- `init()` takes `ssr: true` and no `stackSdk`.

### GraphQL or a custom fetch layer

- When the hash is present, switch to the region's preview host and add the `live_preview` and
  `preview_token` headers. Otherwise use the delivery host. In a BFF or proxy, forward the hash end to
  end.

### Visual Editor (on top of Live Preview)

- `mode: "builder"` and `stackDetails: { apiKey, environment }` in `init()`, where `environment` is
  the environment being previewed. `mode` defaults to `"preview"`, which fails Visual Editor's Verify
  Mode check, so a Live Preview config without `mode` needs it added. Builder mode throws without
  `stackDetails`.
- The environment's Base URL origin matches the previewed site exactly: scheme, `www` and port.
  Visual Editor checks this; Live Preview does not.
- `addEditableTags(entry, contentTypeUid, true, locale)` from `@contentstack/utils`, once per
  top-level entry and after every refetch; `true` for React and JSX. GraphQL responses need
  normalising first.
- Spread `entry.$.field` onto the element that renders each value, plus container tags on multiple,
  reference and block fields, or add and reorder controls never appear. Read
  [edit-tags.md](edit-tags.md) before answering: it has the key conventions and the empty-block
  contract.
- Pass `include_applied_variants=true` on content requests if the stack uses variants.

### Timeline (on top of Live Preview)

- Forward `preview_timestamp` next to the hash on every request, and keep both on the URL across
  client-side navigation.

### Production

- Do not initialize preview on the production build (`enable: false`), or add
  `editButton: { exclude: ["outsideLivePreviewPortal"], includeByQueryParameter: false }`, or the
  Edit button renders for visitors.

## Reply shape

Docs link first, then only the requirements that apply to the user's framework, mode and product,
each with a one-line reason, then the verification. Skip requirements the user already showed they
meet. Snippets only where the docs make the shape easy to get wrong (`init()` options, tag spreading).

## Verify

- **Live Preview:** the Onboarding Check card reads **Setup Complete**, and editing a field without
  saving updates the pane.
- **Visual Editor:** its check reaches **All Set!**, and hovering a field outlines it; clicking it
  focuses that field in the form.
- **Timeline:** its check reaches **All Set!**, and picking a future date shows the scheduled
  content.
- **Production:** the public site shows no Edit button and no `data-cslp` attributes when preview is
  disabled there.

Any failure here continues at SKILL.md step 3 with the check result.

## Not covered by any setup page

Say so plainly rather than guessing:

- **ISR and framework draft or cache modes.** Caching must be off on preview routes; no official
  hybrid recipe exists. See [rendering-modes.md](rendering-modes.md).
- **Edge runtimes.** No dedicated page; they follow the SSR contract. See [frameworks.md](frameworks.md#edge-runtimes).
- **GraphQL with edit tags.** Needs an application-side response normaliser. See
  `graphql-connection-wrappers-break-cslp` in `faq-visual-editor.md`.
