---
title: Taxonomy
description: "Use Contentstack Taxonomy for hierarchical content classification and delivery-side filtering: taxonomy vs tags/labels/references, hierarchy design, CDA operators, localization, import/export."
---

# Taxonomy

**Slug:** `cms-taxonomy` · **Product:** CMS · **Type:** Advisory (acts through MCP tools on request)

Advises on using Taxonomy for structured, hierarchical classification and delivery-side filtering, and on when taxonomy is the right mechanism versus tags, labels, or references.

## When it triggers

When you need help classifying content, designing category hierarchies, choosing between taxonomy and other classification approaches, or querying entries by category on the delivery side.

## What it covers

- **Use taxonomy when**: you need structured, hierarchical classification queryable on the delivery side (product categories, geographic regions, content topics, document types).
- **Don't use taxonomy for**: freeform labels (use tags), internal CMS organization (use labels), or rich category pages with their own model (use a Category content type with references).
- **Hierarchy design**: plan before creating; terms can nest up to 10 levels, but keep the tree as shallow as the use case allows. Terms are parent-child ordered; the move API's `force` flag cascades the move to child terms.
- **Limits** (plan-dependent defaults): 20 taxonomies per stack, 10,000 terms per taxonomy, 20 taxonomies per content type. Taxonomy is a global module shared across branches.
- **CDA filtering**: `query` on `/taxonomies/entries` or `/content_types/{uid}/entries`. Exact term `{"taxonomies.material": "wood"}`; `$in`, `$exists`, `$and`, `$or`; hierarchy operators `$eq_below`, `$below`, `$eq_above`, `$above` with optional `levels` (default 10).
- **Localization & import/export**: localization is plan-dependent; localized terms share the master term's UID. Import/export supports JSON and CSV; a localized import needs the master-locale taxonomy and terms to exist first.

## Example prompts

- "Should I use taxonomy or tags for product categories?"
- "How do I query entries by taxonomy term on the CDA?"
- "How do I design a taxonomy hierarchy for my site?"
- "Can I localize taxonomy terms?"
- "Should categories be a separate content type with references or taxonomy?"

## MCP tools

With the Contentstack MCP server connected, the `cma` group reads taxonomies and terms (`get_all_taxonomies`, `get_all_terms`, ancestor and descendant lookups, `export_a_taxonomy`) and can create, update, move and delete them. There is no import tool; use the CMA or `csdx`. `get_all_entries_cdn` (`cda`) tests a taxonomy filter.

## Safety notes

Advisory by default. Changes taxonomies or terms through MCP only when you ask, after naming the taxonomy and terms and getting confirmation. Taxonomy is global, so changes reach every branch. Use environment variables for credentials in examples.

## Related

- [Data Modeling Best Practices](cms-data-modeling-best-practices.md) · [Entries](cms-entries.md) · [Localization](cms-localization.md)
