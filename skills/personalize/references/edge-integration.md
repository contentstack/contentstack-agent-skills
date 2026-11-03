# Edge integration example (Next.js on Launch)

A minimal pattern based on the public "Set up a Next.js website with Personalize on Launch" guide, with its syntax errors fixed. Adapt the routing and data fetching to the user's app.

## 1. Edge function: `functions/[proxy].edge.js`

```js
import Personalize from '@contentstack/personalize-edge-sdk';

export default async function handler(request, context) {
  const parsedUrl = new URL(request.url);
  const { pathname } = parsedUrl;

  // Pass static assets straight through.
  if (['_next', 'favicon.ico'].some((path) => pathname.includes(path))) {
    return fetch(request);
  }

  // Only needed outside AWS NA.
  if (context.env.CONTENTSTACK_PERSONALIZE_EDGE_API_URL) {
    Personalize.setEdgeApiUrl(context.env.CONTENTSTACK_PERSONALIZE_EDGE_API_URL);
  }

  const personalizeSdk = await Personalize.init(
    context.env.CONTENTSTACK_PERSONALIZE_PROJECT_UID,
    { request }
  );

  // Rewrite the origin request with the variant param; the visitor's URL is unchanged.
  const variantParam = personalizeSdk.getVariantParam();
  parsedUrl.searchParams.set(Personalize.VARIANT_QUERY_PARAM, variantParam);

  const response = await fetch(new Request(parsedUrl.toString(), request));
  const modifiedResponse = new Response(response.body, response);

  // Persist the user and manifest cookies, and keep the browser from caching this response.
  personalizeSdk.addStateToResponse(modifiedResponse);
  modifiedResponse.headers.set('cache-control', 'no-store');

  return modifiedResponse;
}
```

On Vercel, Netlify or Cloudflare the same steps run in that platform's middleware or edge function: `init` with the request, rewrite with the variant param, `addStateToResponse`, return.

## 2. Server: turn the param into aliases and fetch variants

```ts
import Personalize from '@contentstack/personalize-edge-sdk';
import { stack } from '@/lib/contentstack';

export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const params = await searchParams;
  const variantParam = params[Personalize.VARIANT_QUERY_PARAM];

  const entryCall = stack.contentType('home_page').entry(process.env.HOME_ENTRY_UID!);
  const entry = variantParam
    ? await entryCall
        .variants(Personalize.variantParamToVariantAliases(decodeURIComponent(variantParam)).join(','))
        .fetch()
    : await entryCall.fetch();

  // render entry
}
```

The route must render per request (SSR). A statically generated page can't see the variant param.

## 3. Browser: attributes, impressions, conversions

Initialize once in a client provider. Because the edge function stored the manifest in a cookie, `init` in the browser does not refetch it.

```tsx
'use client';
import { createContext, useContext, useEffect, useState } from 'react';
import Personalize from '@contentstack/personalize-edge-sdk';

type Sdk = Awaited<ReturnType<typeof Personalize.init>>;
const PersonalizeContext = createContext<Sdk | null>(null);
export const usePersonalize = () => useContext(PersonalizeContext);

export function PersonalizeProvider({ children }: { children: React.ReactNode }) {
  const [sdk, setSdk] = useState<Sdk | null>(null);
  useEffect(() => {
    Personalize.init(process.env.NEXT_PUBLIC_CONTENTSTACK_PERSONALIZE_PROJECT_UID!).then(setSdk);
  }, []);
  return <PersonalizeContext.Provider value={sdk}>{children}</PersonalizeContext.Provider>;
}
```

```tsx
const sdk = usePersonalize();

// Once, after the personalized block renders.
useEffect(() => {
  if (sdk) void sdk.triggerImpression(EXPERIENCE_SHORT_UID);
}, [sdk]);

// On a conversion. The event key must exist in the project.
const onClick = () => sdk?.triggerEvent('learnMoreClicked');

// Store a custom attribute. The attribute must exist in the project.
await sdk?.set({ age: 32 });
```
