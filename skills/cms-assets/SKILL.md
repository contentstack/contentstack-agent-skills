---
name: cms-assets
description: "Advise developers on organizing, delivering, and transforming assets in Contentstack. Cover folder structure, Image Delivery API transformations, publishing lifecycle, CDN behavior, and common limits. Use when developers ask about uploading, organizing, delivering, transforming, publishing, or troubleshooting images and other media files in a stack's asset library. For the standalone Assets DAM (spaces, workspaces, duplicate sets, saved views, visual markups), use asset-management instead. Reading or updating user-defined fields is not supported here; use asset-management and the Assets API."
allowed-tools: Read Grep Glob
---

# Contentstack Assets

Advise on organizing, delivering, transforming and publishing files in a stack's asset library, and on the limits and reference risks that come with them.

## When to use

- Organizing assets into folders and naming them.
- Serving responsive or optimized images with the Image Delivery API.
- Publishing, unpublishing, replacing or deleting assets, and what that does to references.
- Upload limits and other asset library gotchas.

Use another skill for:

- The standalone Assets DAM (spaces, workspaces, duplicate sets, saved views, visual markups) and any reading or updating of user-defined fields → `asset-management`
- Images embedded in JSON Rich Text Editor content → `cms-json-rte`
- Fetching assets in code with the Delivery SDK → `dx-delivery-sdk`
- Asset fields in a GraphQL query → `cms-graphql`
- Environments and the publishing model in general → `cms-environments-publishing`
- Third-party DAM connectors such as Bynder or Cloudinary → `marketplace-apps`

## Before you answer

Find out the asset type and use case, any image optimization requirements, how assets are organized today, and whether the question is about publishing or CDN delivery.

## Instructions

1. Identify the asset type and use case.
2. Recommend a folder organization if needed.
3. For images, explain the Image Delivery API transforms.
4. Describe publishing and CDN behavior.
5. Flag limits, gotchas and reference risks.

### Folder organization

Recommend a clear folder structure early in the project, such as `/images/heroes`, `/images/products` and `/documents/legal`. Moving assets between folders preserves UIDs and references.

### Image Delivery API

Use `images.contentstack.io` for image delivery, with on-the-fly transforms through URL parameters such as `width`, `height`, `quality`, `format`, `auto`, `crop`, `trim`, `orient`, `overlay`, `pad`, `canvas`, `fit`, `dpr`, `blur`, `sharpen`, `brightness`, `contrast` and `saturation`. Recommend responsive delivery with width/height and dpr, WebP for modern browsers, and quality tuning for file size. Chain multiple transforms in one URL. Non-image assets serve from `assets.contentstack.io`.

### Publishing lifecycle

Assets have their own publishing lifecycle, independent of entries. An asset must be published to an environment before referenced entries display it on the live site. Unpublishing removes it from delivery for that environment but does not delete the file.

### Replacing vs deleting

Replacing an asset creates a new version while keeping the same UID and references intact. Deleting an asset breaks all references to it in entries. Advise checking references before deletion.

### Key limits

State the main stack asset library limits clearly: max file size is 700 MB via the UI and 100 MB via the API, max 10 assets per batch upload, 10,000 assets per stack by default, and filenames cannot be changed after upload. Image Delivery API transforms do not apply to images inserted directly into Rich Text Editor fields. The standalone Assets (DAM) product has different limits (up to 1.5 GB per asset, 100 assets per upload, 500,000 assets per workspace); route those questions to `asset-management`.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `get_all_assets`, `get_a_single_asset`, `get_asset_reference` (`cma`); `get_assets_of_a_specific_folder`, `get_assets_and_subfolders_of_a_parent_folder`, `get_all_versions_of_an_asset` (`cma-extended`); `get_all_assets_cdn`, `get_a_single_asset_cdn` (`cda`)
- Change: `publish_an_asset`, `unpublish_an_asset` (`cma`); `update_asset_details`, `create_asset_folder`, `update_asset_folder`, `set_asset_version_name` (`cma-extended`)
- Delete: `delete_an_asset` (`cma`); `delete_asset_folder`, `delete_asset_version_name` (`cma-extended`)

There is no upload tool; upload through the UI, the CMA or `csdx`. Run `get_asset_reference` before deleting an asset to see which entries use it.

## Output

Be concise and practical. Show Image Delivery API parameters inline when helpful. Prefer direct answers with short bullets when listing options or limits.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose tokens or API keys.
- Delivery tokens and asset URLs are safe for client-side code.
- Use environment variables for credentials in example code, and route CMA calls through a server-side proxy in browser apps.

### Destructive Actions

Before deleting, unpublishing or replacing an asset, or deleting a folder, name the asset, the environments and the entries that reference it, explain the impact (a deleted asset breaks every reference to it), and wait for confirmation.

### Secrets

Never reveal management tokens, API keys, or other secrets. If code examples need credentials, reference environment variables only.

### Environment Variables

Use environment variables for any credentialed examples. Never hardcode stack API keys, management tokens, or delivery tokens in client-side code.
