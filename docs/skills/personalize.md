---
title: Personalize
description: "Integrate Contentstack Personalize: experiences, audiences, attributes, events, the Edge SDK and Edge API, the Management API, and edge middleware patterns."
---

# Personalize

**Slug:** `personalize` · **Product:** Personalize · **Type:** Advisory (acts through MCP tools on request)

Advises on integrating Contentstack Personalize so each visitor gets the right variant early in the request, the matching entry variants are fetched, and results are measured, without leaking personalized content into shared caches.

## When it triggers

When you ask about setting up Personalize, segmented vs A/B test experiences, audiences and attributes, impressions and conversions, the Personalize Edge SDK in Next.js, Launch Edge Functions, Vercel, Netlify or Cloudflare, the Management API, experience analytics, or a visitor seeing the wrong variant.

## What it covers

- **Concepts:** projects linked to a stack, experiences syncing as variant groups, segmented vs A/B (equal, custom split, Multi-Armed Bandit), first-match variant order, experience priority, experience tags.
- **Audiences and attributes:** preset attributes (City, Country, Region, Date and Time, Device Type, Operating System, Query Parameter, Referrer), custom attributes that must exist in the project, live vs stored attributes, Personalize vs Lytics audiences.
- **Edge SDK:** `@contentstack/personalize-edge-sdk` init options, instance methods, regional Edge API hosts via `setEdgeApiUrl`.
- **Request flow:** edge `init` with the request → variant param rewrite → `addStateToResponse` → `variantParamToVariantAliases` → Delivery SDK `.variants()`. On Launch, use an Edge Function rather than Next.js middleware. A worked example is in `references/edge-integration.md`.
- **Events and analytics:** impressions counted once per visitor, conversions via event keys, analytics summary and time series.
- **Management API:** regional hosts, OAuth scopes `personalize:read` / `personalize:manage` or authtoken, `x-project-uid`, 10 requests/second per organization.
- **Caching and debugging:** per-request rendering, `no-store` on browser responses, and a debugging chain from manifest → aliases → CDA → entry variants → cache.

## Example prompts

- "How do I add Personalize to my Next.js site on Launch?"
- "Should this be a segmented experience or an A/B test?"
- "How do I track a conversion when someone clicks the CTA?"
- "Why does every visitor get the base entry?"
- "How do I create experiences through the API?"

## MCP tools

With the `personalize` group of the Contentstack MCP server connected, the agent can read experiences, versions, priority, audiences, attributes, events and analytics, and on request create or update experiences, attributes and events or change priority. There is no tool for creating audiences. Entry variants on the CMS side use the `cma` group's variant tools.

## Safety notes

Advisory by default. Uses MCP tools to change the project only when asked, and confirms the project and items before deleting, pausing or reprioritizing anything. Management API credentials stay server-side; personalized responses never go into a shared cache without the variant in the cache key.

## Related

- [Variants & Personalization](cms-variants-personalization.md) · [Lytics](lytics.md) · [Delivery SDK](dx-delivery-sdk.md)
