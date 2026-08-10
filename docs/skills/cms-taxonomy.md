---
title: Taxonomy
description: Use Contentstack Taxonomy for hierarchical content classification and delivery-side filtering: taxonomy vs tags/labels/references, hierarchy design, CDA operators, localization, import/export.
---

# Taxonomy

**Slug:** `cms-taxonomy` · **Product:** CMS · **Type:** Advisory (read-only)

Advises on using Taxonomy for structured, hierarchical classification and delivery-side filtering, and on when taxonomy is the right mechanism versus tags, labels, or references.

## When it triggers

When you need help classifying content, designing category hierarchies, choosing between taxonomy and other classification approaches, or querying entries by category on the delivery side.

## What it covers

- **Use taxonomy when**: you need structured, hierarchical classification queryable on the delivery side (product categories, geographic regions, content topics, document types).
- **Don't use taxonomy when**: for freeform labels (use tags), internal CMS organization (use labels), or rich category pages with their own model (use a Category content type with references).
- **Hierarchy design**: plan before creating; keep it practical (usually 3–4 levels). Terms are parent-child ordered. Moving a term with children is blocked unless the force flag is used.
- **CDA filtering operators**: `$taxonomy_exists` (any term), `$taxonomy_equal` (specific term), `$taxonomy_below` (a term and descendants), `$taxonomy_above` (ancestors).
- **Localization & import/export**: localization is plan-dependent; localized terms share the master term's UID. Import/export supports JSON and CSV; invalid CSV rows are skipped while valid rows process.

## Example prompts

- "Should I use taxonomy or tags for product categories?"
- "How do I query entries by taxonomy term on the CDA?"
- "How do I design a taxonomy hierarchy for my site?"
- "Can I localize taxonomy terms?"
- "Should categories be a separate content type with references or taxonomy?"

## Safety notes

Read-only advisory. Never creates, modifies, moves, deletes, or imports taxonomy data. Use environment variables for credentials in examples.

## Related

- [Data Modeling Best Practices](cms-data-modeling-best-practices.md) · [Entries](cms-entries.md) · [Localization](cms-localization.md)
