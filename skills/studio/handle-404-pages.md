---
name: handle-404-pages
---

## When to use

Show the site's 404 page for any URL whose composition can't be loaded, on CSR and SSR routes. Phrases: "404 page", "not found page", "page not found", "unknown URL shows 500", "unknown URL shows a blank page", "unknown URL shows an error", "bad slug", "my 404 page stopped working after adding Studio", "Studio-authored 404". Covers wildcard (catch-all) and dedicated routes on Next.js (App and Pages Router), Remix and Vite / React Router.

Do NOT use for: choosing CSR or SSR ([`configure-csr-vs-ssr`](configure-csr-vs-ssr.md)), or wiring the catch-all route itself ([`setup-template-preview-routes`](setup-template-preview-routes.md)).

# Handle 404 pages on a Studio site

## The rule

**If no composition exists for the URL, render the 404 page. Any other failure stays an error.**

- `useCompositionData` (CSR) returns the failure in `error`.
- `sdk.fetchCompositionData` (SSR) throws it. Call it through the [`resolveComposition`](configure-csr-vs-ssr.md#resolve-composition-helper) helper, which returns `notFound: true` for a miss and rethrows everything else.

Decide with `isCompositionNotFound(error)` from `@contentstack/studio-react`, the check the SDK documents for the 404 decision, and nothing else. A bad token, a wrong region or a network failure is not a missing page: show it as a 500 (SSR) or an error state (CSR), or an outage looks like every page was deleted. Never check `specOptions.spec`, `hasSpec` or `hasTemplate`: a successful fetch always returns a spec, and `hasTemplate` is `false` for every freeform composition (the SDK marks it deprecated for this reason).

## Why this matters

A Studio catch-all route matches every URL, including ones with no composition behind them. Without this branch, unknown URLs render a blank page, an error screen or a 500, and the site's own 404 page never shows. Under a connected template, a mistyped slug (`/blog/no-such-post`) matches the URL pattern and fails later at entry lookup, so it needs the same branch.

## Task

1. **Find the site's existing 404 page and reuse it.**

   ```bash
   find app src/app pages src -name 'not-found.*' -o -name '404.*' -o -name 'NotFound.*' 2>/dev/null
   ```

   Create one only when nothing exists. Next.js App Router: `app/not-found.tsx`. Pages Router: `pages/404.tsx`. React Router: a `NotFound` component.

2. **Add the branch to every route that fetches a composition.** Use the CSR or SSR block below that matches the route.

3. **Retire the old catch-all 404 route** (React Router only). See § React Router: one `path="*"`.

4. **Run the acceptance checks.**

## CSR: `useCompositionData`

Vite / React Router:

```tsx
// src/routes/StudioPage.tsx
import { useLocation } from "react-router-dom";
import { useCompositionData, StudioComponent, isCompositionNotFound } from "@contentstack/studio-react";
import NotFound from "../pages/NotFound"; // the site's existing 404 page
import ErrorPage from "../pages/ErrorPage"; // the site's error state

export function StudioPage() {
  const { pathname } = useLocation();
  const { specOptions, isLoading, error } = useCompositionData({ url: pathname });

  if (error) return isCompositionNotFound(error) ? <NotFound /> : <ErrorPage />;
  if (isLoading || !specOptions) return <div>Loading…</div>;

  return <StudioComponent specOptions={specOptions} />;
}
```

Next.js client page: the same component with `"use client"` at the top and `usePathname()` from `next/navigation` instead of `useLocation()`.

The hook reads the query string from `window.location` itself. Don't pass `searchQuery`.

**A CSR page can't send a 404 status.** The server has already answered 200 with the app shell before the browser fetches the composition. Tell search engines not to index the page instead:

```tsx
// pages/NotFound.tsx
export default function NotFound() {
  return (
    <main>
      <meta name="robots" content="noindex" />
      <h1>Page not found</h1>
      <a href="/">Back to home</a>
    </main>
  );
}
```

React 19 hoists the `<meta>` into `<head>`. On React 18, set it with your head manager (`react-helmet-async` or similar). If a real 404 status matters for SEO, make the route SSR.

## SSR: `sdk.fetchCompositionData`

Fetch through [`resolveComposition`](configure-csr-vs-ssr.md#resolve-composition-helper) and send the 404 when it returns `notFound: true`. The helper also clears the shared stack's preview hash before each fetch, so a visitor is never served an editor's drafts. Pass the full request query string as `searchQuery`: Studio's editor context (locale, variant, edit mode) and the preview hash reach the server only that way.

### Next.js App Router

```tsx
// app/[[...slug]]/page.tsx — Server Component, no "use client"
import { notFound } from "next/navigation";
import { getSSRStyles } from "@contentstack/studio-react";
import { sdk } from "@/lib/studio.server";
import { resolveComposition } from "@/lib/resolve-composition";
import { StudioRender } from "./StudioRender";

type Props = {
  params: Promise<{ slug?: string[] }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

async function load({ params, searchParams }: Props) {
  const { slug } = await params;
  const url = "/" + (slug ?? []).join("/");
  const searchQuery = new URLSearchParams(
    Object.entries(await searchParams).flatMap(([k, v]) => (Array.isArray(v) ? v.map((x) => [k, x]) : v === undefined ? [] : [[k, v]])),
  ).toString();
  return resolveComposition(sdk, { url, searchQuery });
}

export default async function Page(props: Props) {
  const result = await load(props); // a real failure throws here and stays a 500
  if (result.notFound) notFound(); // renders app/not-found.tsx with status 404
  const { specOptions } = result;

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: getSSRStyles(specOptions.spec) }} />
      <StudioRender specOptions={specOptions} />
    </>
  );
}

export async function generateMetadata(props: Props) {
  const result = await load(props);
  if (result.notFound) return {}; // the page itself sends the 404
  const { seo } = result.specOptions;
  return seo ? { title: seo.pageTitle, description: seo.pageDescription } : {};
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

Call `notFound()` outside any `try`. It works by throwing, so inside a `try` your own `catch` swallows it. Branching on `resolveComposition`'s result keeps it outside.

### Next.js Pages Router

```tsx
// pages/[[...slug]].tsx
import type { GetServerSidePropsContext } from "next";
import { getSSRStyles, StudioComponent, type StudioComponentSpecOptions } from "@contentstack/studio-react";
import { sdk } from "@/lib/studio.server";
import { resolveComposition } from "@/lib/resolve-composition";

export async function getServerSideProps({ resolvedUrl }: GetServerSidePropsContext) {
  // resolvedUrl, not req.url: on client-side navigation req.url is /_next/data/....json
  const { pathname, search } = new URL(resolvedUrl, "http://localhost");

  const result = await resolveComposition(sdk, { url: pathname, searchQuery: search.slice(1) });
  if (result.notFound) return { notFound: true as const }; // renders pages/404.tsx with status 404
  const { specOptions } = result;

  return {
    props: {
      specOptions: JSON.parse(JSON.stringify(specOptions)), // drops undefined values Next can't serialize
      css: getSSRStyles(specOptions.spec),
    },
  };
}

export default function Page({ specOptions, css }: { specOptions: StudioComponentSpecOptions; css: string }) {
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: css }} />
      <StudioComponent specOptions={specOptions} />
    </>
  );
}
```

### Remix

```tsx
// app/routes/$.tsx
import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { getSSRStyles, StudioComponent } from "@contentstack/studio-react";
import { sdk } from "~/lib/studio.server";
import { resolveComposition } from "~/lib/resolve-composition";

export async function loader({ request }: LoaderFunctionArgs) {
  const { pathname, search } = new URL(request.url);

  const result = await resolveComposition(sdk, { url: pathname, searchQuery: search.slice(1) });
  if (result.notFound) throw new Response("Not Found", { status: 404 }); // rendered by the route's ErrorBoundary
  const { specOptions } = result;

  return json({ specOptions, css: getSSRStyles(specOptions.spec) });
}

export default function Page() {
  const { specOptions, css } = useLoaderData<typeof loader>();
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: css }} />
      <StudioComponent specOptions={specOptions} />
    </>
  );
}
```

## React Router: one `path="*"`

The Studio catch-all and the old 404 route are both `path="*"`. The first match wins, so the old `<NotFound />` route can never render. Delete it. The catch-all's `error` branch now shows `NotFound`:

```tsx
<Routes>
  <Route path="/canvas" element={<CanvasRoute />} />
  <Route path="*" element={<StudioPage />} />
  {/* deleted: <Route path="*" element={<NotFound />} /> */}
</Routes>
```

## Dedicated routes

A dedicated route (`/blog/:slug` rather than a catch-all) still fetches, and a bad slug still fails. Add the same branch to that route's component. URLs that no route matches keep falling through to the framework's own 404.

## Inside Studio's canvas

- **CSR:** the hook reports the failure to Studio, so the canvas shows the cause and the page shows `NotFound`.
- **SSR:** a 404 stops the page before it renders, so nothing on that page starts the browser SDK. Call the browser `studioSdk.init()` from the root layout, as [`install-studio`](install-studio.md) wires it, so Studio still connects. With init only inside the page component, Studio reports "Studio Can't Connect to Your Site", which points at the wrong problem.

## Optional: a 404 page authors can edit

Build a freeform composition at `/404` ([`build-freeform-template`](build-freeform-template.md)). In the 404 branch, fetch `{ url: "/404" }` (through `resolveComposition` on SSR) and render it. Keep the hard-coded page as the fallback when that fetch also fails. On SSR, still return status 404.

## Acceptance

Succeeds only when ALL of the following are true:

- [ ] `/definitely-not-a-page` shows the site's 404 page with its header and footer.
- [ ] A bad slug under a connected template (`/blog/zzz-not-an-entry`) shows the same page.
- [ ] SSR: both URLs return status 404. Check with `curl -s -o /dev/null -w '%{http_code}' <url>`.
- [ ] CSR: the 404 page carries `<meta name="robots" content="noindex">`.
- [ ] A real page still renders, and its `generateMetadata` (App Router) returns its title.
- [ ] A broken credential (temporarily wrong delivery token) shows an error (SSR: status 500), not the 404 page.
- [ ] A new, unpublished template opens in Studio's canvas without showing the 404 page.
- [ ] React Router: only one `path="*"` route exists.
- [ ] No route checks `specOptions.spec`, `hasSpec` or `hasTemplate` to decide a 404. Every 404 decision goes through `isCompositionNotFound` (directly, or via `resolveComposition`).

If acceptance fails, report which check broke and stop.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| `await sdk.fetchCompositionData()` with no `try` | The fetch throws on a miss, so the framework's error page shows a 500 | Use `resolveComposition` and branch on `notFound` |
| `catch { notFound() }` around the fetch | A bad token, wrong region or network failure becomes a 404 on every page, so an outage looks like deleted content and search engines drop the pages | 404 only when `isCompositionNotFound(err)`; rethrow the rest (`resolveComposition` does both) |
| `if (!specOptions?.spec)`, `!hasSpec` or `!hasTemplate` as the 404 test | A successful fetch always has a spec, so the check never fires. `hasTemplate` is `false` on every freeform composition, so that one 404s working pages | `isCompositionNotFound(error)` (CSR) or `resolveComposition`'s `notFound` (SSR) only |
| `if (error) return <ErrorState />` on the CSR hook | Every unknown URL looks like a crash | `isCompositionNotFound(error) ? <NotFound /> : <ErrorState />` |
| `notFound()` inside `try` | It throws, and your own `catch` swallows it | Call it outside the `try` |
| `generateMetadata` calls the fetch with no not-found branch | A miss throws there first, and the page errors instead of 404ing | Return `{}` when `resolveComposition` says `notFound` |
| Calling `sdk.fetchCompositionData` directly on a server with a preview token | The SDK sets a request's preview hash on the shared stack and never clears it, so later visitors get drafts | Fetch through `resolveComposition`, which clears it first |
| Old `<Route path="*" element={<NotFound />} />` kept | The Studio catch-all matches first, so it never renders | Delete it. The catch-all's `error` branch renders `NotFound` |
| A new 404 page when the site already has one | Two designs, and the old one silently stops showing | Reuse the existing page |
| SSR `searchQuery` not forwarded | Studio's editor context never reaches the server, so the canvas renders the wrong locale or variant | Pass the full request query string |
| Testing with one unknown URL only | A bad slug under a connected template fails at a later step | Test both URLs in Acceptance |
| SSR browser init only inside the page component | On a 404 the page never mounts, and Studio shows "Can't Connect" | Init from the root layout |

## See also

- [`setup-template-preview-routes`](setup-template-preview-routes.md): the catch-all route and site chrome
- [`configure-csr-vs-ssr`](configure-csr-vs-ssr.md): choosing and wiring CSR or SSR
- [`csr-and-ssr-requirements`](csr-and-ssr-requirements.md): what a CSR or SSR page needs, including Live Preview and Visual Editor
- [`troubleshoot-composition-resolution`](troubleshoot-composition-resolution.md): why a URL that should resolve doesn't
