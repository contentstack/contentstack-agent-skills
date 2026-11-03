---
title: Variants & Personalization
description: "Use Contentstack Variants and Personalize for audience-targeted content: variants vs separate entries, variant groups, A/B testing, and Personalize integration."
---

# Variants & Personalization

**Slug:** `cms-variants-personalization` · **Product:** CMS · **Type:** Advisory (acts through MCP tools on request)

Advises on delivering different content to different audiences without duplicating entire entries, and on integrating Personalize with the CMS.

## When it triggers

When you ask about content personalization, A/B testing, audience segmentation, variant creation, or integrating Personalize with the CMS.

## What it covers

- **Variants vs separate entries**: if ~80%+ of the content is shared and only headlines, images, or CTAs differ, use variants (lightweight overrides). If each audience needs a different page structure, references, and layout, use separate entries. Start with variants; split only when content diverges significantly.
- **Variant groups**: one per Personalize experience, created automatically; one variant per audience or A/B arm; entry variants hold field overrides only. A group must be linked to a content type before editors can create entry variants.
- **Fetching variants**: pass variant aliases (`cs_personalize_{experienceShortUid}_{variantShortUid}`) in the CDA `x-cs-variant-uid` header. A comma-separated list layers variants and the leftmost wins on conflict. The CMA accepts only one variant UID.
- **Personalize integration**: resolve aliases with `@contentstack/personalize-edge-sdk` (`init`, `set`, `setUserId`, `getVariantAliases`, `triggerImpression`, `triggerEvent`), usually in edge middleware.
- **Experiences and limits**: segmented vs A/B (with a multi-armed bandit option), experience priority for field conflicts, and default project limits of 100 experiences, 20 variants per experience and 100 audiences.
- **Start simple**: emphasizes maintainability; add complexity only when justified.

## Example prompts

- "How do I show different content to different user segments?"
- "Should I use variants or create separate entries per audience?"
- "How do I integrate Personalize with my frontend?"
- "What are variant groups?"
- "Can I A/B test content in Contentstack?"

## MCP tools

With the `cma` group, the agent can list, create, publish and delete entry variants (`get_all_variants_of_an_entry`, `create_an_entry_variant`, `publish_variants_of_an_entry`, `delete_an_entry_variant`). With the `personalize` group, it can read and manage experiences and their priority (`get_all_experiences`, `update_experience`, `update_experiences_priority`). Linking a variant group to a content type is done in the CMS.

## Safety notes

Advisory by default. Uses the MCP tools only when you ask for the change, and names the stack, entries, environments and experience before creating, publishing or deleting anything. Use environment variables for credentials; never hardcode stack API keys or Personalize project keys.

## Related

- [Entries](cms-entries.md) · [Delivery SDK](dx-delivery-sdk.md) · [Data Modeling Best Practices](cms-data-modeling-best-practices.md)
