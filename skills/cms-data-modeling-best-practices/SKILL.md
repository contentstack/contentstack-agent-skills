---
name: cms-data-modeling-best-practices
description: "Guide developers to model content in Contentstack using the simplest reusable structure. The skill explains when to use content types, references, global fields, groups, modular blocks, JSON RTE, taxonomy, and tags, and helps avoid over-modeling, deep reference chains, and channel-specific schema sprawl. Use when designing, reviewing, or refactoring Contentstack content models before creating or changing schemas. For taxonomy hierarchies and CDA taxonomy filters, use cms-taxonomy."
allowed-tools: Read Grep Glob
---

# Contentstack Data Modeling Best Practices

Help pick the simplest Contentstack construct that fits, so editors work efficiently, delivery code stays simple, and schemas stay reusable, governed and easy to query.

## When to use

- Designing a new content model, or reviewing and simplifying an existing one.
- Choosing between a content type, reference, global field, group, modular block, JSON RTE, taxonomy, tag or plain field.
- Planning localization and governance at the schema level.
- Checking a model against query impact and stack limits.

Use another skill for:

- Taxonomy hierarchy design and taxonomy filters on the CDA → `cms-taxonomy`
- Rendering JSON RTE content once it's modeled → `cms-json-rte`
- Personalization variants of an entry → `cms-variants-personalization`
- Locales and fallback chains → `cms-localization`
- Making schema changes safely on a branch → `cms-branches-aliases`
- Querying the entries a model produces → `cms-entries`

## Before you answer

Gather the business goal, the current or proposed model, target channels and delivery needs, localization, reuse and governance requirements, sample content, and any performance or query constraints.

## Instructions

1. Identify the domain concept, editorial workflow, delivery channels, localization needs, reuse requirements, and query constraints.
2. Choose the simplest fitting construct: content type, reference, global field, group, modular block, JSON RTE, taxonomy, tag, or plain field.
3. Prefer reusable structures only when content changes independently or appears across entries.
4. Check reference depth, API contract stability, and query impact.
5. Review localization and naming conventions.
6. Call out anti-patterns and suggest simpler alternatives.
7. Return a concise recommendation with migration cautions if needed.

### Understand the goal

Identify the domain concept, editorial workflow, delivery channels, localization needs, reuse requirements, and query constraints before recommending changes.

### Choose the right construct

Pick the simplest Contentstack construct that fits: content type, reference, global field, group, modular block, JSON RTE, taxonomy, tags, or plain field.

### Prefer reuse only when justified

Use reusable, governed structures when content changes independently or appears across multiple entries. Keep parent-owned data inline.

### Check query impact

Treat content types as API contracts. Avoid deep reference chains, oversized modular blocks, and hiding filterable facts inside rich text.

### Review localization and governance

Localize only fields that need translation. Keep names clear and avoid channel-specific schema pollution.

### Explain tradeoffs

State why the recommended option is better, what it avoids, and what maintenance or query cost it reduces.

### Return a practical answer

Give a concise recommendation, compare alternatives only when useful, and include migration cautions when schema changes are implied.

### Fast decision rules

Use a content type for a real domain concept with its own lifecycle. Use a reference for reusable content with independent ownership. Use a global field for the same nested field set across multiple content types. Use a group for parent-owned nested data inside one content type. Use modular blocks for page-local composition. Use JSON RTE for narrative content. Use taxonomy for governed classification. Use tags for lightweight internal labels.

### Limits to design around

- A content type schema can have up to 500 fields. A content type UID can be up to 200 characters.
- The number of content types per stack and the number of block types in one modular blocks field are plan limits. Product defaults are around 100 content types per stack and 10 block types per modular blocks field, so check the plan before designing a model that depends on more.
- Taxonomies can nest up to 10 levels deep.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `get_all_content_types`, `get_a_single_content_type`, `get_all_references_of_ct`, `export_content_type`, `get_all_global_fields`, `get_a_single_global_field` (`cma`); `export_global_field` (`cma-extended`)
- Change: `create_a_content_type`, `update_content_type` (`cma`); `create_a_global_field`, `update_a_global_field` (`cma-extended`)
- Delete: `delete_content_type` (`cma`); `delete_a_global_field` (`cma-extended`)

Read the existing model with the inspect tools before reviewing it. Make schema changes on a development branch first, and run `get_all_references_of_ct` before changing or deleting a content type that other types reference.

## Output

Use concise, structured, instruction-oriented prose. Prefer bullets and short sections. State the recommended choice first when comparing options. Include warnings for anti-patterns and migration cautions when relevant, and optionally a sample model or decision summary.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose management tokens or API keys.
- Never ask users to paste secrets into the prompt.
- Use environment variables for credentials in any example code.
- Route CMA calls through server-side proxies in browser apps.
- Never hardcode stack API keys in client-side code.
- Do not recommend unsafe workarounds that bypass governance or access controls.

### Destructive Actions

Before creating, updating or deleting a content type or global field, name the stack, branch and schema, explain the impact (removing a field or content type can remove the content stored in it, and every schema change is an API contract change for delivery code), and wait for confirmation.

### Secrets

Treat all credentials as sensitive. Never request or display management tokens, delivery tokens, API keys, or webhook secrets. Use placeholders and environment variables only.

### Environment Variables

Use environment variables for any credentialed examples or integrations. Prefer placeholders such as CONTENTSTACK_API_KEY, CONTENTSTACK_MANAGEMENT_TOKEN, and CONTENTSTACK_DELIVERY_TOKEN. Never hardcode secrets in examples or instructions.
