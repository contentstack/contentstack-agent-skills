---
title: Asset Management
description: "Advise on the Contentstack Assets DAM: spaces and workspaces, metadata, localization, saved views, search, AI tags, duplicates, versions, trash and restore, and visual markups."
---

# Asset Management

**Slug:** `asset-management` · **Product:** Assets (DAM) · **Type:** Advisory (read-only)

Advises on Contentstack Assets, the standalone digital asset management product. It is separate from the CMS stack asset library covered by [Assets](cms-assets.md).

## When it triggers

When you ask about the Assets DAM: spaces and workspaces, folders, asset types and metadata, localization, saved views, AI tags and alt text, duplicate management, versions, trash and restore, visual markups, or linking Assets to CMS stacks.

## What it covers

- **Spaces and workspaces**: a space is the top-level container, and workspaces are isolated environments inside it, created from the main workspace or a parent workspace.
- **Folders and roles**: folder creation and least-privilege guidance.
- **Asset types and metadata**: system, general and user-defined metadata. The currently supported user-defined field types are single line text, number, select and group. Filters on user-defined fields can be saved as saved views.
- **Localization**: add a language in product settings, then add it per workspace under Space Settings > Workspaces > Manage Locales.
- **Search**: the public Assets API search endpoint, required headers, and filtering by user-defined field.
- **AI tags and alt text**: manual suggestions and auto-populate at upload, with their limits.
- **Duplicate management**: exact-duplicate sets for images, how to resolve them, and what is not detected.
- **Versions, trash and restore**: renaming and restoring versions, the 14-day trash window, and folder restore options.
- **Visual markups**: hotspots and bounding boxes, including AI-suggested markups.
- **CMS integration**: linking spaces to stacks and the `asset_fields[]` Content Delivery API parameter.

## Example prompts

- "How should I split my brands and regions across spaces and workspaces?"
- "How do I add a language to a workspace?"
- "How do I find and remove duplicate images?"
- "I deleted a folder by mistake. Can I get it back?"
- "How do I search assets by a custom field value?"

## Safety notes

Read-only advisory. Never uploads, moves, deletes, restores or modifies assets, spaces or settings. Warns before irreversible actions such as deleting a space or all markups. Never exposes tokens or API keys; examples use environment variables.

## Related

- [Assets](cms-assets.md) · [Localization](cms-localization.md) · [Roles & Permissions](cms-roles-permissions.md)
