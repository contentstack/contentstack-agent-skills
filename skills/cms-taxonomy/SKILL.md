---
name: cms-taxonomy
description: "Advise developers on using Contentstack Taxonomy for structured, hierarchical content classification and delivery-side filtering. Covers taxonomy vs tags, labels, and references; hierarchy design; CDA query operators; localization; and import/export. Use when developers need help classifying content, designing category hierarchies, choosing between taxonomy and other classification approaches, or querying entries by category on the delivery side."
allowed-tools: Read Grep Glob
---

# Contentstack Taxonomy

Advise on taxonomy for structured, hierarchical classification that is filtered on the delivery side, and on when tags, labels or references fit better.

## When to use

- Choosing between taxonomy, tags, labels and a Category content type with references.
- Designing a term hierarchy.
- Filtering entries by term with the Content Delivery API (CDA).
- Localizing terms, or importing and exporting taxonomies.

Use another skill for:

- Overall content model design → `cms-data-modeling-best-practices`
- General entry queries, pagination and references → `cms-entries`
- Locales and fallback chains → `cms-localization`

## Before you answer

Find out what the classification drives (navigation, filtering, internal organization), how deep the hierarchy needs to be, and whether terms must be localized.

## Instructions

1. Decide whether taxonomy fits.
2. If it does, design the hierarchy.
3. Show the CDA query for the filter the user needs.
4. Cover localization or import/export if they're relevant.

### Use taxonomy when

Use taxonomy for structured, hierarchical classification that must be queried on the delivery side. Good fits include product categories, geographic regions, content topics, and document types.

### Do not use taxonomy when

Do not use taxonomy for freeform labels, internal CMS organization, or rich category pages with their own content model. Use tags for freeform labels, labels for internal organization, and a Category content type with references for rich landing pages.

### Hierarchy design

Plan the hierarchy before creating it. Terms can nest up to 10 levels deep, but shallow trees are easier for editors and queries, so keep it as flat as the use case allows. Terms are parent-child ordered. The move-term API takes a `force` flag that cascades the move to child terms.

### Limits

Default limits are plan-dependent: 20 taxonomies per stack, 10,000 terms per taxonomy, 10 levels of depth, and 20 taxonomies per content type. Taxonomy is a global module, so it is shared across branches.

### CDA filtering

Filter entries by taxonomy with the `query` parameter on `/taxonomies/entries` (across content types) or `/content_types/{content_type_uid}/entries`:

- Exact term: `{"taxonomies.material": "wood"}`
- Any of several terms: `{"taxonomies.material": {"$in": ["wood", "bamboo"]}}`
- Any term applied: `{"taxonomies.material": {"$exists": true}}`
- Term and its descendants: `{"taxonomies.color": {"$eq_below": "blue", "levels": 2}}`
- Descendants only: `$below`. Term and its ancestors: `$eq_above`. Ancestors only: `$above`.
- Combine conditions with `$and` and `$or`.

`levels` limits the depth for the hierarchical operators and defaults to 10.

### Localization and import/export

Taxonomy localization is plan-dependent. Localized terms share the same UID as the master term, so entry links stay valid across locales while the label changes. Taxonomies import and export as JSON or CSV. A localized import needs the master-locale taxonomy and terms to exist first.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `get_all_taxonomies`, `get_a_single_taxonomy`, `get_all_terms`, `get_a_single_term`, `get_all_terms_across_all_taxonomies`, `get_all_ancestors_of_a_term`, `get_all_descendants_of_a_term`, `export_a_taxonomy` (`cma`)
- Change: `create_a_taxonomy`, `update_a_taxonomy`, `create_a_term`, `update_a_term`, `move_a_term` (`cma`)
- Delete: `delete_a_taxonomy`, `delete_a_term` (`cma`)

There is no import tool; use the CMA or `csdx` for imports. To test a CDA filter, use `get_all_entries_cdn` (`cda`) with the `query` above.

## Output

Lead with the taxonomy-vs-alternatives decision, then the hierarchy or the query. Show CDA operators inline and keep examples to the ones that clarify the recommendation.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose tokens or API keys; use environment variables in example code.
- Keep management credentials out of client-side code.

### Destructive Actions

Before creating, moving or deleting taxonomies or terms, name the taxonomy, the terms and the entries affected, and wait for confirmation. Taxonomy is a global module, so a change reaches every branch.

### Secrets

Never reveal management tokens, API keys, or other secrets. Use placeholders and environment variables in any example code.

### Environment Variables

Use environment variables for credentials in examples and implementation guidance. Never hardcode secrets in client-side code.

## References

- https://www.contentstack.com/docs/developers/taxonomy
- https://www.contentstack.com/docs/developers/apis/content-delivery-api#taxonomy
