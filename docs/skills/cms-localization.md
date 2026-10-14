---
title: Localization
description: Design multilingual delivery in Contentstack: language setup, fallback chains, localized vs unlocalized entries, non-localizable fields, and multi-locale publishing.
---

# Localization

**Slug:** `cms-localization` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on Contentstack localization with correct fallback behavior, efficient editorial workflows, and minimal redundancy. The skill distinguishes CMS editorial behavior from CDA delivery behavior, and clarifies which you mean before answering.

## When it triggers

When you ask about languages, fallback chains, localizing entries, non-localizable fields, or multi-locale publishing.

## What it covers

- **Master language**: permanent, set at stack creation, and ends every fallback chain.
- **Fallback chain design**: each language can have one fallback; inheritance is a chain (e.g. `fr-ca → fr-fr → en-us`). Changing fallback relationships later affects existing content inheritance.
- **Localized vs unlocalized entries**: a localized entry is an independent copy with its own version history, publishing status, and workflow state; an unlocalized entry inherits from its fallback chain. Localizing is one-way per locale and entry.
- **Non-localizable fields**: mark structural/shared data non-localizable (SKUs, prices, dates, coordinates, boolean flags, shared assets, identifiers); keep human-readable text localizable.
- **CDA locale queries**: pass `locale` explicitly; use `include_fallback=true` to apply the full fallback chain (without it, only the exact locale is checked).
- **Multi-locale publishing**: editors can publish multiple locale versions from the master-language entry (subject to plan limits). Only the latest version of each localized entry is published; localized versions can be deleted only from the master entry's delete modal.

## Example prompts

- "How do I set up languages with fallback in Contentstack?"
- "What's the difference between a localized and unlocalized entry?"
- "Which fields should I mark as non-localizable?"
- "How do I publish content in multiple languages at once?"
- "What happens if a locale has no content?"

## Safety notes

Read-only advisory. Requires explicit confirmation before any destructive action and never auto-executes delete/overwrite/publish. Use environment variables for all credentials.

## Related

- [Entries](cms-entries.md) · [Data Modeling Best Practices](cms-data-modeling-best-practices.md) · [Taxonomy](cms-taxonomy.md)
