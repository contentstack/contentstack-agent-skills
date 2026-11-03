---
title: Assets
description: "Organize, deliver, and transform assets in Contentstack: folders, Image Delivery API, publishing lifecycle, CDN behavior, and limits."
---

# Assets

**Slug:** `cms-assets` · **Product:** CMS · **Type:** Advisory (acts through MCP tools on request)

Advises developers on organizing, delivering, and transforming assets in Contentstack: folder structure, Image Delivery API transformations, publishing lifecycle, CDN behavior, and common limits.

## When it triggers

When you ask about uploading, organizing, delivering, transforming, publishing, or troubleshooting images and other media files in Contentstack.

## What it covers

- **Folder organization**: clear structures like `/images/heroes`, `/images/products`, `/documents/legal`. Moving assets between folders preserves UIDs and references.
- **Image Delivery API**: `images.contentstack.io` with on-the-fly transforms via URL params (`width`, `height`, `quality`, `format`, `auto`, `crop`, `trim`, `orient`, `overlay`, `pad`, `canvas`, `fit`, `dpr`, `blur`, `sharpen`, `brightness`, `contrast`, `saturation`). Chain multiple transforms in one URL; prefer WebP for modern browsers. Non-image assets serve from `assets.contentstack.io`.
- **Publishing lifecycle**: assets publish independently of entries. An asset must be published to an environment before referenced entries display it live. Unpublishing removes it from delivery but doesn't delete the file.
- **Replacing vs deleting**: replacing creates a new version but keeps the same UID and references; deleting breaks all references. Check references before deleting.
- **Key limits**: max file size 700 MB (UI) / 100 MB (API); max 10 assets per batch upload; default 10,000 assets per stack; filenames can't change after upload. Image Delivery transforms don't apply to images inserted directly into Rich Text Editor fields. The Assets (DAM) product has its own limits (1.5 GB per asset, 100 per upload, 500,000 per workspace).

## Example prompts

- "How do I serve responsive images from Contentstack?"
- "What image transformations does Contentstack support?"
- "How should I organize my assets into folders?"
- "Does deleting an asset break references in entries?"
- "What is the maximum file size I can upload?"

## MCP tools

With the Contentstack MCP server connected, the agent can list and inspect assets, folders, versions and references (`get_all_assets`, `get_asset_reference`, folder tools in `cma-extended`), check delivery with `get_all_assets_cdn`, publish or unpublish assets, manage folders and asset details, and delete assets. There is no upload tool; upload through the UI, the CMA or `csdx`.

## Safety notes

Advisory by default; uses the MCP tools only when you ask for the change. Before deleting, unpublishing or replacing an asset or deleting a folder, it names the asset, environments and referencing entries and waits for confirmation. Delivery tokens and asset URLs are client-safe; never expose management tokens or API keys. Use environment variables for credentials in examples.

## Related

- For the standalone Assets DAM (spaces, workspaces, duplicate sets), see [Asset Management](asset-management.md). Reading or updating user-defined fields isn't supported by the stack asset library; use the Assets (DAM) API described there.
- [Environments & Publishing](cms-environments-publishing.md) · [Entries](cms-entries.md) · [Data Modeling Best Practices](cms-data-modeling-best-practices.md)
