---
title: Data Modeling Best Practices
description: Model Contentstack content with the simplest reusable structure: when to use content types, references, global fields, groups, modular blocks, JSON RTE, taxonomy, and tags.
---

# Data Modeling Best Practices

**Slug:** `cms-data-modeling-best-practices` · **Product:** CMS · **Type:** Advisory (read-only)

Guides developers to model content using the simplest reusable structure and avoid over-modeling, deep reference chains, and channel-specific schema sprawl.

## When it triggers

When designing, reviewing, or refactoring content models before creating or changing schemas.

## What it covers

The skill applies fast decision rules to pick the simplest construct that fits:

| Use… | When… |
| --- | --- |
| **Content type** | A real domain concept with its own lifecycle. |
| **Reference** | Reusable content with independent ownership. |
| **Global field** | The same nested field set across multiple content types. |
| **Group** | Parent-owned nested data inside one content type. |
| **Modular blocks** | Page-local composition. |
| **JSON RTE** | Narrative content. |
| **Taxonomy** | Governed classification. |
| **Tags** | Lightweight internal labels. |

Core principles:

- Prefer reuse only when content changes independently or appears across entries; keep parent-owned data inline.
- Treat content types as API contracts: avoid deep reference chains, oversized modular blocks, and hiding filterable facts inside rich text.
- Localize only fields that need translation; keep names clear; avoid channel-specific schema pollution.
- Explain tradeoffs and include migration cautions when schema changes are implied.

## Example prompts

- "How should I model a landing page with reusable sections?"
- "Should this data be a global field, group, or content type?"
- "Review this content model and tell me what to simplify."
- "What's the best way to handle localization for shared content?"
- "How do I model product categories for filtering and reuse?"

## Safety notes

Read-only advisory. Never performs schema changes, publishing, or destructive actions. Uses placeholders and environment variables for any example credentials.

## Related

- [Taxonomy](cms-taxonomy.md) · [Localization](cms-localization.md) · [Entries](cms-entries.md)
