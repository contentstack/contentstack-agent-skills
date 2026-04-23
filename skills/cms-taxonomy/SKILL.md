---
name: cms-taxonomy
description: "Advise developers on using Contentstack Taxonomy for structured, hierarchical content classification and delivery-side filtering. Covers taxonomy vs tags, labels, and references; hierarchy design; CDA query operators; localization; and import/export."
allowed-tools: Read Grep Glob
---

# Contentstack Taxonomy

## Description

Advise developers on using Contentstack Taxonomy for structured, hierarchical content classification and delivery-side filtering. Covers taxonomy vs tags, labels, and references; hierarchy design; CDA query operators; localization; and import/export.

## When to Use

Use when developers need help classifying content, designing category hierarchies, choosing between taxonomy and other classification approaches, or querying entries by category on the delivery side.

## User Problem

Developers need a governed way to classify content so it can be filtered, navigated, and organized in delivery experiences. They also need guidance on when taxonomy is the right mechanism versus tags, labels, or references.

## Success Criteria

Recommends taxonomy only when it fits the use case
Explains hierarchy design and term relationships clearly
Uses CDA taxonomy operators for filtering examples
Distinguishes taxonomy from tags, labels, and references
Covers localization and import/export when relevant

## Expected Inputs

- Classification or filtering requirements
- Hierarchy depth and structure
- Delivery-side query needs
- Localization requirements
- Migration or import needs

## Expected Outputs

- Taxonomy vs alternatives recommendation
- Hierarchy design guidance
- CDA query operator examples
- Localization guidance
- Import/export advice

## Example User Requests

- Should I use taxonomy or tags for product categories?
- How do I query entries by taxonomy term on the CDA?
- How do I design a taxonomy hierarchy for my site?
- Can I localize taxonomy terms?
- Should categories be a separate content type with references or taxonomy?

## Workflow Summary

Understand the classification need and delivery requirements.
Recommend the right mechanism: taxonomy, tags, labels, or references.
If taxonomy fits, guide hierarchy design and term modeling.
Show CDA taxonomy query operators for filtering.
Cover localization and import/export if relevant.

## Instructions

### Use taxonomy when

Use taxonomy for structured, hierarchical classification that must be queried on the delivery side. Good fits include product categories, geographic regions, content topics, and document types.

### Do not use taxonomy when

Do not use taxonomy for freeform labels, internal CMS organization, or rich category pages with their own content model. Use tags for freeform labels, labels for internal organization, and a Category content type with references for rich landing pages.

### Hierarchy design

Plan the hierarchy before creating it. Keep it practical, usually 3-4 levels max. Terms are parent-child ordered. Moving a term with children is blocked by default unless the force flag is explicitly used.

### CDA filtering

Use taxonomy query operators instead of manual filtering: $taxonomy_exists for any term, $taxonomy_equal for a specific term, $taxonomy_below for a term and descendants, and $taxonomy_above for ancestors.

### Localization and import/export

Note that taxonomy localization is plan-dependent. Localized terms share the same UID as the master term. Import/export supports JSON and CSV; invalid CSV rows are skipped while valid rows are processed.

## Output Format

Be concise and practical.
State the taxonomy-vs-alternatives decision first.
Show CDA query operators inline.
Use examples only when they clarify the recommendation.

## Tooling Notes

Read-only advisory skill.
Do not create, modify, or delete taxonomies or terms.
Restrict tool use to read/search tools when possible.

## Security

### Defaults

Never expose tokens or API keys.
Use environment variables for credentials in example code.
Do not perform destructive actions.
Avoid suggesting client-side access to management credentials.

### Destructive Actions

Do not create, update, move, delete, or import taxonomy data. Provide guidance only.

### Secrets

Never reveal management tokens, API keys, or other secrets. Use placeholders and environment variables in any example code.

### Environment Variables

Use environment variables for credentials in examples and implementation guidance. Never hardcode secrets in client-side code.

## Product Context

- - Product: CMS
- - Description: Contentstack headless CMS: content types, entries, assets, environments, publishing, workflows, webhooks, and the Content Management API (CMA).
- - Product safety rules: - Never expose management tokens or API keys.
- Always use environment variables for credentials.
- Route all CMA calls through server-side proxies in browser apps.
- Never hardcode stack API keys in client-side code.
- - Default tools: ["CMA API", "Content Types", "Entries", "Assets", "Workflows", "Webhooks", "Environments", "Releases", "Publish Queue"]
- - Default connectors: ["CMA Proxy", "Webhooks"]