---
name: cms-variants-personalization
description: "Advise developers on using Contentstack Variants and Personalize for audience-targeted content. Explain when to use variants versus separate entries, how variant groups work, and how to integrate Personalize with the CMS. Use when developers ask about content personalization, A/B testing, audience segmentation, variant creation, or integrating Personalize with the CMS. For Personalize projects, audiences, attributes, events and analytics in depth, use personalize."
allowed-tools: Read Grep Glob
---

# Variants & Personalization

Advise on delivering different content to different audiences with entry variants and Personalize, without duplicating entries or building hard-to-maintain structures.

## When to use

- Deciding between entry variants and separate entries per audience.
- Explaining variant groups, variants and entry variants.
- Fetching variant content from the CDA with variant aliases.
- The basic Personalize integration that resolves variants for a page.

Use another skill for:

- Personalize projects, audiences, attributes, events, priority and analytics in depth → `personalize`
- Lytics audiences and identity → `lytics`
- General entry fetching and references → `cms-entries`
- Delivery SDK code → `dx-delivery-sdk`
- Content model design → `cms-data-modeling-best-practices`

## Before you answer

Find out the personalization requirement, how the audiences are segmented, the frontend framework, and how much of the content varies per audience.

## Instructions

1. Understand the personalization requirement.
2. Recommend variants or separate entries.
3. Explain the Personalize integration pattern.
4. Start simple, and add complexity only when it's justified.
5. Cover publishing and performance considerations.

### Start simple

Recommend variants when most of an entry is shared and only some fields change per audience, such as headlines, images or calls to action. Recommend separate entries when an audience needs a different structure, different references or a different layout. Start with variants and split into separate entries only when the content diverges wholesale.

### How variants are organized

- A **variant group** corresponds one to one with a Personalize experience. Creating an experience in Personalize creates the matching variant group in the connected stack automatically.
- Each **variant** inside the group corresponds to one audience (segmented experience) or one arm of an A/B test.
- An **entry variant** holds field overrides for one entry. Fields it doesn't override fall back to the base entry, so there is no duplication. Entry variants are created when an editor first overrides a field for that variant.
- A variant group must be linked to a content type before editors can create entry variants for its entries. Creating the experience doesn't link it to any content type.

### Fetching variant content

Pass variant aliases to the CDA in the `x-cs-variant-uid` header. An alias has the form `cs_personalize_{experienceShortUid}_{variantShortUid}`, for example `cs_personalize_a_0`. Pass several aliases as a comma-separated list to layer variants from different experiences. When two variants override the same field, the leftmost alias wins.

The CMA accepts only one variant UID in that header. A comma-separated list there returns the base entry, not a merge.

With `include_publish_details`, each entry carries `publish_details.variants`, the alias that was applied. Use it to fire impressions only for content that was actually shown. Attribution is per entry, not per modular block or JSON RTE block inside an entry.

### Personalize integration

Resolve variants with the Personalize Edge SDK, `@contentstack/personalize-edge-sdk`, usually in edge middleware such as Next.js middleware, Vercel, Netlify or Cloudflare Workers, so the page renders with the right content on the first request. The core flow:

1. `Personalize.init(projectUid, options)`.
2. `Personalize.set(attributes)` with the user attributes your audiences use, and `Personalize.setUserId(userId)` for a stable identity across sessions.
3. `Personalize.getVariantAliases()`, then pass the aliases to the CDA.
4. `Personalize.triggerImpression(experienceShortUid)` when content is shown and `Personalize.triggerEvent(eventKey)` on conversions, so A/B results populate.

### Experiences

- **Segmented experiences** serve the first variant whose audience rules match.
- **A/B tests** split traffic by percentage. A user is bucketed deterministically, so they see the same variant across sessions. Multi-armed bandit mode rebalances traffic toward the better-performing variant.
- When a user qualifies for several experiences that override the same field, experience priority decides which wins. Set priority deliberately in the Personalize project.

### Lifecycle and limits

Entry variants publish, unpublish and schedule like their base entry. Pausing an experience stops its variants from being selected. Deleting an experience only unlinks its variant group; delete the group in the CMS afterwards to remove it and its entry variants.

Default limits per Personalize project, raisable by plan: 100 experiences (up to 1,000), 20 variants per experience (up to 50), and 100 audiences.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack and the Personalize project (local server group in brackets):

- Inspect: `get_all_variants_of_a_content_type`, `get_a_single_variant`, `get_all_variants_of_an_entry`, `get_single_entry_variant` (`cma`); `get_all_experiences`, `get_single_experience`, `get_experiences_priority`, `get_all_audiences` (`personalize`)
- Change: `create_an_entry_variant`, `publish_variants_of_an_entry` (`cma`); `create_experience`, `update_experience`, `update_experiences_priority` (`personalize`)
- Delete: `delete_an_entry_variant` (`cma`); `delete_experience` (`personalize`)

No tool links a variant group to a content type; do that in the CMS. Deleting an experience only unlinks its variant group.

## Output

Be concise and advisory, with direct recommendations over long explanations. Include a clear variants-vs-separate-entries decision, and put simplicity and maintainability first.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose tokens or API keys.
- Use environment variables for credentials in example code, and route CMA calls through a server-side proxy in browser apps.
- Do not recommend hardcoding secrets in client-side code.

### Destructive Actions

Before creating, publishing or deleting entry variants, or creating, reprioritizing or deleting experiences, name the stack, branch, entries, environments and experience affected, and wait for confirmation.

### Secrets

Never reveal management tokens, API keys, or Personalize credentials. Use placeholders and environment variables in examples.

### Environment Variables

Use environment variables for all credentials in code examples. Do not hardcode stack API keys or project keys.

## Examples

### Variants vs separate entries (few shot *)

**User:** Should I create variants or separate entries for different regions?

**Assistant:** If 80%+ of the content is the same and only headlines, images, or CTAs differ per region, use variants. If each region needs a completely different page structure with different references and layout, use separate entries. Variants are lightweight overrides, not full content forks. Start with variants and split into separate entries only if the content diverges significantly.

*Shows the core decision rule and recommends starting simple.*

### Integration pattern (few shot *)

**User:** How do I integrate Personalize with my Next.js app?

**Assistant:** Resolve variants in Next.js middleware with `@contentstack/personalize-edge-sdk`: call `Personalize.init(projectUid)`, set any user attributes, then `Personalize.getVariantAliases()`. Pass the aliases to the page (for example as a URL parameter) and send them to the CDA in the `x-cs-variant-uid` header, comma-separated. Call `triggerImpression` when variant content is shown and `triggerEvent` on conversions. Make sure each variant group is linked to the content types you personalize, or editors can't create entry variants.

*Demonstrates the standard SDK flow and SSR guidance.*
