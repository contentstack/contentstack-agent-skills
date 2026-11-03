---
title: Marketplace Apps
description: "Choose, install, configure and use first-party Contentstack Marketplace apps: the catalog by category, install permissions, configuration and per-field overrides, webhooks, delivery data and when to build a custom app."
---

# Marketplace Apps

**Slug:** `marketplace-apps` · **Product:** Developer Hub · **Type:** Advisory (acts through MCP tools on request)

Helps you pick the right first-party Marketplace app, install and configure it with the right permissions, and use the data it stores in your entries.

## When it triggers

When you ask which Marketplace app fits a need, how to install or configure an app such as Bynder, Cloudinary, Shopify, commercetools, Algolia or Trados, why an app field is empty or a sync isn't running, or how to read app data on the frontend.

## What it covers

- **Catalog**: documented apps by category: DAM, video, commerce and PIM, search, translation, AI, analytics and experimentation, forms, editor and JSON RTE utilities, and stack tools.
- **Install permissions**: stack apps vs organization apps, who can install each, and the Request Install and App Requests flow.
- **Configuration**: app configuration, multiple configurations with a default, `legacy_config`, the per-field **Config Parameter** override, and what each app saves in the entry.
- **UI locations and webhooks**: enabling locations, adding custom fields to content types, webhook branch scope and logs.
- **App specifics**: Algolia's environment and index mapping, and what Trados converts and skips.
- **Delivery**: reading app field JSON with the CDA, SDK and GraphQL, and fetching live data from the source system.
- **Lifecycle**: updates, uninstalling, and revoking authorized apps.
- **Build vs install**: when a custom app is the better fit.

## Example prompts

- "Which Marketplace app should we use to connect Bynder assets to our entries?"
- "I'm not an admin. How do I get the Shopify app installed on our stack?"
- "How do I use two Shopify stores in the same stack?"
- "Our Algolia index isn't updating when we publish."
- "What does the commercetools field return in the CDA response?"
- "Should we build our own app or use a Marketplace app?"

## MCP tools

The `developerhub` group covers apps your organization owns: `get_all_apps`, `get_an_app`, `get_app_installations`, `install_an_app`, `update_an_app_installation` and `uninstall_an_app`. Third-party listings may not appear in `get_all_apps`, so those are installed from the Marketplace UI. Entry and content type read tools show stored app data and which fields use an app.

## Safety notes

Advisory by default. Never echoes app credentials; `get_app_installations` can return them. Uninstalling an app, deleting a configuration (especially `legacy_config`) or changing one that fields depend on needs a named target and explicit confirmation, because stored app data can be lost.

## Related

- [Developer Hub App Architect](developer-hub-app-architect.md) · [Asset Management](asset-management.md) · [Assets](cms-assets.md) · [Localization](cms-localization.md) · [JSON Rich Text Editor](cms-json-rte.md)
