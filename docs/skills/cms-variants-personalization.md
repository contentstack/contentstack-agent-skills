---
title: Variants & Personalization
description: Use Contentstack Variants and Personalize for audience-targeted content: variants vs separate entries, variant groups, A/B testing, and Personalize integration.
---

# Variants & Personalization

**Slug:** `cms-variants-personalization` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on delivering different content to different audiences without duplicating entire entries, and on integrating Personalize with the CMS.

## When it triggers

When you ask about content personalization, A/B testing, audience segmentation, variant creation, or integrating Personalize with the CMS.

## What it covers

- **Variants vs separate entries**: if ~80%+ of the content is shared and only headlines, images, or CTAs differ, use variants (lightweight overrides). If each audience needs a different page structure, references, and layout, use separate entries. Start with variants; split only when content diverges significantly.
- **Variant groups**: how variants are organized.
- **Personalize integration**: initialize the Contentstack SDK with stack credentials and the Personalize SDK with your project key. On each request, resolve the active experience from audience rules and pass the variant context when fetching entries. For SSR, use the Personalize Edge API to resolve variants at the CDN for best performance.
- **Start simple**: emphasizes maintainability; add complexity only when justified.

## Example prompts

- "How do I show different content to different user segments?"
- "Should I use variants or create separate entries per audience?"
- "How do I integrate Personalize with my frontend?"
- "What are variant groups?"
- "Can I A/B test content in Contentstack?"

## Safety notes

Read-only advisory. Never creates, modifies, or publishes variants. Use environment variables for credentials; never hardcode stack API keys or Personalize project keys.

## Related

- [Entries](cms-entries.md) · [Delivery SDK](dx-delivery-sdk.md) · [Data Modeling Best Practices](cms-data-modeling-best-practices.md)
