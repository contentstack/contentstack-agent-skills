# Rendering modes

The Live Preview SDK ships no framework adapters. It declares no framework peer dependencies and
contains no per-framework code paths. What determines the correct integration is the rendering
mode of the affected route and the fetch layer underneath it, not the framework's name.

Diagnose against this file. Use `frameworks.md` only for where `init()` is allowed to run.

## The contract per mode

| Mode | `ssr` | How the hash travels | How updates arrive | Hard requirement |
|---|---|---|---|---|
| CSR + REST | `false` | postMessage; the SDK injects it into `stackSdk` | `onEntryChange` / `onLiveEdit` refetch, no reload | `stackSdk` is mandatory |
| SSR + REST | `true` | `live_preview` query parameter on the request | full iframe reload, parent-driven; `onEntryChange` never fires on edits | a fresh Delivery SDK instance per request |
| CSR + GraphQL | `false` | `ContentstackLivePreview.hash` | callback refetch | manual host swap plus headers |
| SSR + GraphQL | `true` | `request.query.live_preview` | full iframe reload | manual host swap plus headers |
| SSG | `false` | postMessage | runs in CSR mode at runtime | `stackSdk`, and `init()` must be browser-only |

## `onEntryChange` does not fire on edits under `ssr: true`

The SDK dispatches edit events to subscribers only when `ssr` is `false`. In SSR mode the parent
reloads the iframe with the new hash instead. A subscriber registered in an SSR app still runs once at
page load, which makes it look wired up, and then never runs again on an edit. A `router.refresh()` or
refetch wired into it does nothing. Drive SSR updates from the request; if client-driven refresh is
wanted, the route must be CSR.

## How `ssr` is resolved

Precedence is `stackSdk.live_preview.ssr`, then `init({ ssr })`, then the automatic default.

- An `ssr` in the Delivery SDK's `live_preview` config silently overrides `init({ ssr })`. Check
  both places before trusting either.
- The automatic default keys off `stackSdk`: present means `ssr: false`, absent means `ssr: true`.
  A CSR app that omits `stackSdk` silently gets SSR behaviour.
- An SSG site running with `ssr: true` reloads on every edit and re-serves its prerendered HTML, so
  edits never appear. Users report it as blank screens, flicker or "nothing happens".

Set `ssr` explicitly, in one place.

## Mode-specific failures worth knowing before you prescribe

### SSR: the shared instance

A module-level Stack instance is shared across requests. Applying a preview hash to it mutates
shared state, so one editor's draft leaks into other users' responses. This reaches public traffic,
not just the authoring session, and it presents as intermittent wrong content plus tracker-invalid
and branch-mismatch errors on the production site.

Build the Stack instance inside the request handler. This is the most damaging SSR mistake there is,
and the least obvious, because it works perfectly with one user.

### SSG: supported, in CSR mode

SSG is documented and supported. Do not tell users it is a dead end.

The confusion comes from the hash. In SSR mode the hash travels as the `live_preview` query
parameter, and a prerendered page never sees a query parameter, so the fetch is never switched.
The documented answer is not to fight that, it is to run the preview path in **CSR mode**, where
the hash arrives by postMessage instead and never needs the URL.

Per [Set Up Live Preview for Static-Site Generator (SSG)](https://www.contentstack.com/docs/headless-cms/set-up-live-preview-for-static-site-generator-ssg):

- Initialise Live Preview Utils with `ssr: false`
- Pass `stackSdk`, which is mandatory in CSR mode
- Configure the Delivery SDK with
  `live_preview: { preview_token, enable: true, host: <region preview host> }`
- Refresh through `onLiveEdit()`, so the browser refetches on each edit

So an SSG site previews without a rebuild. The static build serves the shell, and the preview
content is fetched client-side during the session.

The common failure here is not SSG itself, it is an SSG site running with `ssr: true`, which
reloads into the same prerendered HTML on every edit.

### ISR: the genuinely hard case

ISR is where there is no clean answer, and it should not be lumped in with SSG.

Contentstack's recorded position more broadly is that caching has to be off for Live Preview and
Visual Editor routes, and that integrating with a framework's own cache-invalidation feature is
out of scope. Do not send users toward a framework's draft mode expecting Contentstack to meet it
there.

In Next.js specifically, reading `searchParams` opts a route out of static rendering. Where a team
insists on a hybrid, the workable pattern is detecting `live_preview` and forcing that request
dynamic. No official hybrid recipe is published, so treat anything beyond this as unverified.

### Caching at the edge

Any cache on the preview path keeps serving published content after the host
switch is already correct. This produces "works on localhost, fails on the deployed environment",
which users reliably misread as a Contentstack outage.

The same misconfiguration has the inverse failure, which is worse: preview output reaching real
visitors. That is usually the shared-instance problem above rather than the cache itself, with the
cache widening the blast radius. Treat preview output on a public URL as urgent, and fix the
per-request instance first.

### GraphQL: edit tags do not survive connection wrappers

`addEditableTags()` bakes each traversed layer into the `data-cslp` path, and a GraphQL response
nests values under `Connection -> edges -> node`, so those wrapper layers end up in the path and no
tag resolves. This is by design and needs a response normalizer on the application side. The full
fix is `graphql-connection-wrappers-break-cslp` in `faq-visual-editor.md`.

### App Router soft navigation

SDK module-level singletons persist across client-side route changes, and soft navigation does not
re-run server-side gating. This is the recorded cause of the edit button appearing on production
pages after a client-side navigation, on setups where the server-rendered entry point gates it
correctly.

## Framework and mode coverage

Every framework is supported. The SDK has no framework-specific code, so support follows from the
rendering mode of each route: apply that mode's contract above. [frameworks.md](frameworks.md) covers
where `init()` goes in each one.

| Framework | CSR | SSR | SSG |
|---|---|---|---|
| Next.js App Router | client components | server components, dynamic routes | runs as CSR at runtime |
| Next.js Pages Router | client fetch | `getServerSideProps` | `getStaticProps`, runs as CSR |
| React SPA (Vite) | the default | — | — |
| Nuxt | `ssr: false` | default Nuxt | prerendered routes run as CSR |
| Angular | default | Angular SSR | prerendered routes run as CSR |
| SvelteKit | client-only routes | server `load` | prerendered routes run as CSR |
| Astro | client islands | server adapter | static output runs as CSR |
| Gatsby | runtime client fetch | — | the default; preview runs as CSR |
| .NET, Java, Python, PHP, Ruby | — | SSR contract; edit tags per [frameworks.md](frameworks.md) | — |

Edge runtimes follow the SSR contract; nothing in it needs a Node-only API.
