---
title: JSON Rich Text Editor
description: "Render and convert Contentstack JSON RTE content: document structure, jsonToHTML and render options, embedded entries and assets, GraphQL, React, the JSON RTE serializer, Live Preview tags and XSS-safe rendering."
---

# JSON Rich Text Editor

**Slug:** `cms-json-rte` · **Product:** CMS · **Type:** Advisory (acts through MCP tools on request) · **Ships references**

Helps you turn JSON RTE documents into HTML, Markdown or components, resolve embedded entries and assets, and convert content between HTML and JSON without opening an XSS hole.

## When it triggers

When you render, serialize or transform JSON RTE content, write a custom `renderOption`, debug embedded items that render empty, render JSON RTE from GraphQL, or migrate an HTML RTE field to JSON RTE.

## What it covers

- **Document structure**: `doc` root, block nodes with `uid`, `type`, `attrs` and `children`, text leaves with marks, `reference` nodes for embedded entries and assets, and the empty-field check.
- **Rendering**: `jsonToHTML` from `@contentstack/utils` (also `contentstack.Utils` in the Delivery SDK), field `paths`, and the fact that it replaces the JSON with HTML in place.
- **Render options**: overrides per node type, mark, display type (`block`, `inline`, `link`, `display`, `download`) and content type, plus a `reference` fallback.
- **Embedded items**: `includeEmbeddedItems()` (`include_embedded_items[]=BASE`), `_embedded_items`, why items render empty, and the limits (100 embedded entries, 15 referenceable content types, 30 KB per field by default).
- **GraphQL**: `json` plus `embedded_itemsConnection` with `system` UIDs, `GQL.jsonToHTML` and `updateAssetURLForGQL`.
- **React**: an HTML string vs a component tree, with a sample renderer.
- **Escaping**: the default sanitizer's limits (it doesn't check URL schemes) and escaping in custom render functions.
- **Conversion**: `@contentstack/json-rte-serializer` (`jsonToHtml`, `htmlToJson`, `jsonToMarkdown`) and the `cli-cm-migrate-rte` CLI plugin.
- **Live Preview**: `addEditableTags` and tagging the RTE wrapper element.

## Example prompts

- "How do I render a JSON RTE field to HTML with the TypeScript SDK?"
- "My embedded entries don't show up in the rendered rich text."
- "How do I render embedded products differently from other entries in the RTE?"
- "How do I render JSON RTE from a GraphQL response?"
- "How do I convert HTML into JSON RTE for an import?"
- "Should I use dangerouslySetInnerHTML or map JSON RTE nodes to React components?"

## MCP tools

Rendering runs in your code, so there are no rendering tools. To see the delivered JSON, the agent can use `get_a_single_entry_cdn` (`cda`) or `get_single_entry` (`cma`), and `get_a_single_content_type` (`cma`) to find JSON RTE field paths. `update_an_entry` (`cma`) can write converted JSON back, after confirmation.

## Safety notes

Advisory by default. Treats RTE content as untrusted: custom render functions escape what they interpolate, and URLs are checked before going into `href` or `src`. Writing converted content back to entries, or running the HTML to JSON migration, needs a named target, a backup or non-production branch, and explicit confirmation.

## Related

- [Entries](cms-entries.md) · [Delivery SDK](dx-delivery-sdk.md) · [GraphQL Content Delivery](cms-graphql.md) · [Live Preview & Visual Editor](cms-live-preview-visual-editor-support-assistant.md) · [Developer Hub App Architect](developer-hub-app-architect.md)
