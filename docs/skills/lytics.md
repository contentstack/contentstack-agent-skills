---
title: Lytics
description: "Use Lytics, Contentstack's customer data platform: the JavaScript tag, identity, schema, audiences, the Segment API, consent, deletion, and the Personalize connection."
---

# Lytics

**Slug:** `lytics` · **Product:** Lytics (Data & Insights) · **Type:** Advisory (acts through MCP tools on request)

Advises on getting behavioral and identity data into Lytics, resolving it into unified profiles, building audiences, and activating them, including in Contentstack Personalize, while respecting consent and deletion requests.

## When it triggers

When you ask about Lytics projects, installing or debugging the Lytics JavaScript tag, sending events or identities, schema fields and mappings or LQL, audiences and SegmentQL, the Segment API, profile lookups, importing Contentstack entries, recommendations, consent, identity deletion, or using Lytics audiences in Personalize.

## What it covers

- **Projects:** Lytics projects in Contentstack (the Lytics app calls them accounts), connections to stacks, Launch and Personalize, and per-project roles.
- **JavaScript tag:** installation through Launch, `<head>` or a tag manager; verification; `jstag.send`, `identify`, `page`; opt-in client-side integrations.
- **Identity:** merging anonymous `_uid` history with known identifiers, and identity key ranks.
- **Schema:** fields and mappings in Schema Studio, with LQL still available through the API.
- **Audiences:** the audience builder, SegmentQL, map-field conditions, Enable for Personalization, what Expires After does, and the Segment API.
- **Personalize connection:** the project connection, plus the `cs-lytics-audiences` cookie read by the Edge SDK.
- **Contentstack entries:** importing entries and taxonomies as context layers, content collections for recommendations.
- **API:** `https://api.lytics.io`, tokens in the `Authorization` header, least-privilege tokens with expiry.
- **Consent and deletion:** consent events, `DELETE /v2/identity/{table}/{field}/{value}`, bulk deletion and status.

## Example prompts

- "How do I install the Lytics tag on my Next.js site?"
- "How do I merge an anonymous visitor with the known user on login?"
- "How do I get Lytics audiences into Personalize?"
- "How do I delete a user's data for a GDPR request?"
- "Can I create audiences through the API?"

## MCP tools

With the `lytics` group of the Contentstack MCP server connected, the agent can read accounts, schema tables and fields, audiences, profiles and content topics, and classify or enrich content (`classify_content`, `enrich_content`). There are no tools for creating audiences, changing schema, sending events or deleting identities.

## Safety notes

Advisory by default; uses MCP tools only when asked. API tokens stay server-side. Identity deletion is permanent and needs explicit confirmation of the exact profile. Looks up profiles only when the user names one.

## Related

- [Personalize](personalize.md) · [Variants & Personalization](cms-variants-personalization.md)
