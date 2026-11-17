---
name: personalize
description: "Advise developers on Contentstack Personalize: projects, segmented and A/B test experiences, audiences, preset and custom attributes, impression and conversion events, priority, the Personalize Edge SDK and Edge API, the Management API, and edge middleware patterns that resolve variants before rendering. Use when developers ask how to set up Personalize, integrate the Edge SDK in Next.js, Launch Edge Functions, Vercel, Netlify or Cloudflare, track impressions or conversions, pass user attributes, manage experiences through the API, read experience analytics, or debug wrong or missing variants. For modeling and fetching entry variants in the CMS (variant groups, x-cs-variant-uid, layering), use cms-variants-personalization. For Lytics data collection and audience building, use lytics."
allowed-tools: Read Grep Glob
---

# Personalize

Advise on Contentstack Personalize, the edge personalization engine: projects, experiences, audiences, attributes, events, the Personalize Edge SDK and Edge API, the Management API, and the request flow that turns a visitor into variant aliases for the Content Delivery API, without leaking per-user content into shared caches.

## When to use

- Setting up or integrating Personalize, including the Edge SDK in Next.js, Launch Edge Functions, Vercel, Netlify or Cloudflare.
- Choosing between segmented and A/B test experiences, and defining audiences, attributes and priority.
- Tracking impressions and conversions, and reading experience analytics.
- Automating experiences through the Management API.
- Debugging a visitor who sees the wrong or missing variant.

Use another skill for:

- Linking variant groups to content types, creating entry variants, `x-cs-variant-uid` and variant layering → `cms-variants-personalization`
- The Lytics tag, schema and audience building → `lytics`
- Launch Edge Functions and hosting in general → `launch-platform`
- Delivery SDK queries outside the variant flow → `dx-delivery-sdk`

## Before you answer

Find out the framework and hosting (Next.js, Launch, Vercel, Netlify, Cloudflare, other), the rendering mode (SSR, SSG, CSR), the project region, the experience goal (segmented targeting or A/B test), the attributes and audiences involved, and the symptoms when debugging.

## Instructions

1. Confirm the stack, hosting, rendering mode and region.
2. Lay out the flow: edge decision → variant aliases → CDA fetch → impressions and conversions.
3. Recommend experience type, audiences, attributes and priority.
4. Provide SDK or API code for the user's runtime, using the real Edge SDK API and the correct regional hosts.
5. Cover caching, cookies, attribute registration and tracking before they cause bugs.
6. Debug in order: manifest, aliases, CDA request, entry variants, cache.


### Concepts

A Personalize project connects to one CMS stack. Each experience in the project syncs to the stack as a variant group, and each of its variants maps to a CMS variant. Experiences come in two types: segmented experiences show a variant to visitors who match its audience, and A/B test experiences split traffic across variants (equal split, custom percentages, or Multi-Armed Bandit, which shifts traffic toward better performers). Within an experience only one variant is active per visitor: the first match in the variant order wins. Across experiences, variants that target different content layer together; when two experiences target the same content, the higher-priority experience wins. Experience tags (free-form strings such as `env:production`) group experiences and can limit which ones are evaluated at runtime.

### Audiences and attributes

Audiences are rules over attributes. Preset attributes are always available and cannot be edited: City, Country, Region, Date and Time, Device Type, Operating System, Query Parameter and Referrer. Custom attributes must be created in the project before they can be used; audiences can only use keys that exist in the project. Set custom attributes with the Edge SDK or Edge API, or through Google Tag Manager or a CDP integration. Attributes passed at `init` as `liveAttributes` apply to the current request only and are not stored on the profile; attributes set with `set()` are stored and may take up to a second to apply.

Personalize audiences are evaluated at the edge on the first request; membership is not stored, so they have no analytics. Lytics audiences come from a connected Lytics project, carry unified customer data, and do support analytics.

### Edge SDK

Install `@contentstack/personalize-edge-sdk`. Call `Personalize.setEdgeApiUrl()` before `init` when the project is outside AWS NA. Regional Edge API hosts: `personalize-edge.contentstack.com` (AWS NA), `eu-personalize-edge`, `au-personalize-edge`, `azure-na-personalize-edge`, `azure-eu-personalize-edge`, `gcp-na-personalize-edge`, `gcp-eu-personalize-edge` (all `.contentstack.com`).

`await Personalize.init(projectUid, options)` fetches the visitor's manifest and returns an SDK instance. Options: `request` (the incoming Web `Request`, used at the edge to read cookies and derive preset attributes), `userId`, `liveAttributes`, `tags` (up to 10, OR match), `customVariantQueryParam`, and `lyticsIdField` / `lyticsIdValue`. Instance methods: `getVariantAliases()`, `getVariantParam()`, `variantParamToVariantAliases()`, `getVariants()`, `getActiveVariant(experienceShortUid)`, `getExperiences()`, `set(attributes)`, `setUserId(userId, { preserveUserAttributes })`, `triggerImpression(experienceShortUid)`, `triggerImpressions({ experienceShortUids | aliases })`, `triggerEvent(eventKey)` and `addStateToResponse(response)`. The static helpers on `Personalize` other than `init`, `setEdgeApiUrl`, `variantParamToVariantAliases` and `getInitializationStatus` are deprecated; use the instance methods.

### Request flow

Resolve variants before rendering:

1. In an edge function or middleware, `init` with the incoming `request`.
2. Read `getVariantParam()` (a compact string such as `a_0,b_1`) and rewrite the request URL with it under `Personalize.VARIANT_QUERY_PARAM`, so the visitor's URL doesn't change.
3. Call `addStateToResponse(response)` so the SDK's user and manifest cookies persist. The browser SDK then initializes from the cookie without another manifest call.
4. On the server, convert the param with `variantParamToVariantAliases()` and pass the aliases to the Delivery SDK (`.variants(aliases)`) or the CDA. With no variants, fetch the base entry.

On Launch, use an Edge Function (`functions/[proxy].edge.js`) for this step, not Next.js middleware, because Next.js middleware runs at the origin on Launch. See [references/edge-integration.md](references/edge-integration.md) for a worked example.

Browser-only (CSR) integrations can `init` without `request` and fetch variants client-side, at the cost of a content flash.

### Events and analytics

Impressions record that a visitor saw a variant and are counted once per visitor. Fire `triggerImpression` after the personalized content renders, once per experience, not on every re-render. Conversions are events created in the project with a key; fire them with `triggerEvent(eventKey)`. A/B test analytics compare variants by conversions; Personalize audiences have no analytics. The Management API exposes experience analytics as a summary and as a time series.

### Identity

The SDK generates an anonymous user ID at the edge. When a visitor logs in, call `setUserId(id, { preserveUserAttributes: true })` to carry their attributes over to the known ID.

### Management API

Use it to automate project configuration: attributes, audiences, events, experiences, experience versions, experience priority, analytics and geolocation lookups. Regional hosts: `personalize-api.contentstack.com` (AWS NA), `eu-personalize-api`, `au-personalize-api`, `azure-na-personalize-api`, `azure-eu-personalize-api`, `gcp-na-personalize-api`, `gcp-eu-personalize-api` (all `.contentstack.com`); the OpenAPI spec is at `/openapi` on the NA host. Authenticate with OAuth (`authorization` header, scopes `personalize:read` or `personalize:manage`, recommended) or an `authtoken`, plus `x-project-uid` for project resources. The limit is 10 requests per second per organization; back off on 429. The Edge API, by contrast, needs no authentication because it runs on public sites, and takes the project in `x-project-uid` and the visitor in `x-cs-personalize-user-uid`.

### Caching

A personalized response must never be served from a shared cache to another visitor. Render personalized routes per request (SSR), keep the variant param in the cache key when caching at the CDN, set `cache-control: no-store` on the browser response from the edge function, and prefer `must-revalidate` over `stale-while-revalidate` for personalized pages. Static (SSG) pages can only be personalized at the edge or in the browser.

### Pitfalls

- Edge middleware resolves variants but does not track. Impressions and conversions still need browser code.
- A/B bucketing relies on the SDK's user cookie. Forcing it to `SameSite=Strict` (for example through a consent tool) drops it on cross-site navigation, so returning visitors can land in a different variant.
- On runtimes that reuse isolates between requests, create a fresh SDK instance per request with `init`; never keep one at module scope.
- Lytics audience membership arrives in a cookie written by the Lytics tag, so it is missing on a visitor's very first request.

### Debugging

Work through the chain in order:

1. **Manifest:** does `getExperiences()` show the experience with an active variant? If not, check that the experience is active, the audience rules match (including custom attributes registered in the project), and the region host is right.
2. **Aliases:** does the server receive the variant param and turn it into aliases?
3. **CDA:** does the delivery request carry the aliases?
4. **CMS:** does the entry have an entry variant for that variant, is the variant group linked to the content type, and is the variant published? (see `cms-variants-personalization`)
5. **Cache:** is a cached base response being served?

## MCP tools

When the Contentstack MCP server is connected with the `personalize` group (it needs the Personalize project ID), these tools act on the project:

- Inspect: `get_all_experiences`, `get_single_experience`, `get_experience_versions`, `get_experiences_priority`, `get_all_audiences`, `get_all_attributes`, `get_all_events`, `get_analytics_summary`, `get_analytics_timeseries`, `get_countries`, `get_regions`, `get_cities` (`personalize`)
- Change: `create_experience`, `update_experience`, `update_experiences_priority`, `create_attribute`, `update_attribute`, `create_event`, `update_event` (`personalize`)
- Delete: `delete_experience`, `delete_experience_version` (drafts only), `delete_audience`, `delete_attribute`, `delete_event` (`personalize`)

There is no tool for creating audiences; use the Personalize UI or the Management API. For the CMS side, `get_all_variants_of_a_content_type`, `get_all_variants_of_an_entry`, `create_an_entry_variant` and `publish_variants_of_an_entry` (`cma`) cover entry variants. When debugging, read the experience, its audiences and its versions with the inspect tools before changing anything.

## Output

Lead with the request flow or the failing step. Give runnable TypeScript or JavaScript for the user's runtime, with credentials and project UIDs from environment variables. Use short checklists for setup and debugging.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose authtokens or OAuth tokens. The Management API is server-side only.
- The Edge API and the project UID are safe in browser code; Management API credentials are not.
- Keep personalized responses out of shared caches, and never cache them without the variant in the cache key.

### Destructive Actions

Before deleting or pausing experiences, audiences, attributes or events, or changing experience priority, name the project and the items affected, explain the impact, and wait for confirmation. Pausing an experience stops delivery of its variants; deleting one unlinks its variant group in the CMS but leaves the group and its entry variants in place.

### Secrets

Never echo authtokens, OAuth tokens or delivery tokens. Use placeholders and environment variables.

### Environment Variables

Use variables such as `CONTENTSTACK_PERSONALIZE_PROJECT_UID`, `CONTENTSTACK_PERSONALIZE_EDGE_API_URL`, `CONTENTSTACK_API_KEY` and `CONTENTSTACK_DELIVERY_TOKEN`. Keep authtokens and OAuth tokens server-side.

## References

- [Edge integration example](references/edge-integration.md): a worked edge-function integration that resolves variants before rendering.
