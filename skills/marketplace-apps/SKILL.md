---
name: marketplace-apps
description: "Help teams choose, install, configure and use first-party Contentstack Marketplace apps. Cover the app catalog by category (DAM, video, commerce and PIM, search, translation, AI, analytics and experimentation, forms, editor and JSON RTE utilities, stack tools), stack apps vs organization apps, who can install and the Request Install flow, app configuration vs per-field Config Parameter, multiple configurations, UI locations, app webhooks and branch scope, updating, uninstalling, authorized apps, how app data is stored in entries and read on delivery, and when to build a custom app instead. Use when someone asks which Marketplace app fits a need, how to install or configure Bynder, Cloudinary, Shopify, commercetools, Algolia, Trados and similar apps, why an app field is empty or not syncing, or how to read app field data in a frontend. To build your own app, use developer-hub-app-architect; for the Assets DAM product, use asset-management."
allowed-tools: Read Grep Glob
---

# Contentstack Marketplace apps

Help teams pick the right first-party Marketplace app, install and configure it safely, and use the data it stores in entries.

## When to use

- Finding an app for a need: DAM, video, commerce, search, translation, AI, analytics, forms or editor tools.
- Installing an app, or getting it installed without admin rights.
- Configuring an app, including several configurations and per-field overrides.
- Apps whose field is empty, whose sync doesn't run, or whose UI location is missing.
- Reading app field data on the frontend.
- Updating, uninstalling or revoking an app.

Use another skill for:

- Building a custom or private app, UI locations in code, App SDK → `developer-hub-app-architect`
- The Contentstack Assets DAM product → `asset-management`
- The stack asset library → `cms-assets`
- Fetching entries and references → `cms-entries` or `dx-delivery-sdk`
- Rendering JSON RTE content that RTE plugins produce → `cms-json-rte`
- Locales and fallback (translation apps write localized entries) → `cms-localization`

## Before you answer

Find out the need and the third-party system the team already uses, whether the app is needed in one stack or the whole organization, and the user's role (organization or stack owner or admin, or not).

## Instructions

1. Match the need to an app, or recommend a custom app if none fits.
2. Check the install permissions.
3. Install it, configure it, and add its UI locations to content types.
4. Show how to read its data on delivery.

### Choose an app

Apps documented in the Marketplace docs, by category (check the Marketplace for the current list and for plan availability):

- **DAM:** Bynder, Cloudinary, Aprimo, Brandfolder, Frontify, Digizuite, Egnyte, Amazon S3.
- **Video:** Brightcove, JW Player, Mux, Vimeo, YouTube.
- **Commerce and PIM:** Shopify, commercetools, BigCommerce, Salesforce Commerce, SAP Commerce Cloud, Elastic Path, Akeneo, plus the Spartacus Contentstack Connector for SAP storefronts.
- **Search and merchandising:** Algolia, Constructor.
- **Translation:** Trados, Wordbee, XTM.
- **AI:** AI Assistant, AI Assistant with Brand Kit, MonkeyLearn.
- **Analytics and experimentation:** Google Analytics, Optimizely, Audience Insights (Lytics data), ClearWinner (A/B test cleanup), and the Audience and Variables plugins.
- **Forms:** Form.io, Marketo Forms.
- **Editor fields and JSON RTE plugins:** Ace Editor, JSON Editor, Color Picker, Star Ratings, Table, Fonts, Highlight, Info Panel, Word Count, Progress Bar, Interstack Reference, Image Preset Builder.
- **Stack tools and dashboards:** Bulk Operations, Calendar, Workflow Board, Content Type Visualizer, Developer Tools, Healthcheck.

The Marketplace also offers starters and importable content models. Recommend a custom app (`developer-hub-app-architect`) when no app covers the system, the data shape must differ from what the app stores, or the integration needs logic the app's configuration can't express. Extensions are no longer actively maintained; build new integrations as apps.

### Install

- **Stack apps** apply to one stack. Stack owners and admins can install them, and so can organization owners and admins who are members of that stack.
- **Organization apps** apply to the whole organization (SCIM provisioning, for example). Only organization owners and admins can install them, and they ask you to authorize module access (**Authorize & Install**).
- Developers and content managers see **Request Install** instead. Admins review requests under **Marketplace > Manage > App Requests**.

Install from **Marketplace > Discover > Explore > Apps**: open the app, click **Install App**, choose the stack, then fill in the configuration page and **Save**. Most third-party apps need credentials from the other system first (API keys, client ID and secret, store or index names), so collect those before installing.

### Configure

- **App configuration** is set once per installation, under **Manage > Installed Apps > [app] > Installed On > Configuration**.
- **Multiple configurations:** several apps (Bynder, Shopify and others) support more than one account or store. Add them with **+ New Configuration** and mark one **Set as Default**. A configuration migrated from an older version is named `legacy_config`; don't delete it, because entries that used it can lose access to their data.
- **Per-field override:** when you add the app's custom field to a content type, **Advanced > Config Parameter** takes a JSON object that overrides the app configuration for that field, for example choosing which store or configuration it uses. Some apps also accept per-locale overrides there.
- **What gets saved:** apps like Shopify and Bynder let you save **All Fields** from the source system, or only selected keys (**Custom Fields**). Saving fewer keys keeps entries small; saving all fields limits how many items an entry can hold.
- **UI locations:** the Installed Apps page lists the app's locations (custom field, sidebar, dashboard, full page, JSON RTE plugin and so on). Toggle optional ones off there; **Required** ones can't be disabled. A custom field or RTE plugin only appears in entries after you add it to the content type.
- **Webhooks:** apps that sync data (Algolia, translation apps) use app webhooks. When branches are enabled, set **Branch Scope** to all branches or specific ones on the app's **Webhook** tab, and check **Webhook Logs** when a sync doesn't run.

App-specific behaviour worth knowing:

- **Algolia** indexes on publish, only for the environments in its configuration, and maps each content type to an index. Without a mapping, entries of that content type aren't indexed. When the webhook fires from a branch, the branch UID is appended to the Algolia `objectID`.
- **Trados** can convert JSON RTE fields to HTML for translators, and can include referenced assets. It doesn't translate Select, Number, Date, File, URL, Link, Taxonomy, Boolean or Custom fields.

### Use app data on delivery

A custom field app stores its value in the entry as JSON (or another declared data type), and the CDA, the Delivery SDK and GraphQL return it as-is under the field UID. In GraphQL, query a JSON custom field by name with no sub-selection. The shape belongs to the app and its "save" settings, so fetch one published entry and inspect it before writing types. DAM and commerce apps usually store IDs, URLs and selected metadata, not the files or live prices. Fetch live data such as stock or price from the source system at request time.

### Update, uninstall and revoke

- Apps with an update show a red dot under **Manage > Installed Apps**; **Update** keeps the configuration and lets you review it.
- **Uninstall** (type the app name to confirm) permanently removes the app and all its associated data from that stack. Plan for the content types and entries that use its fields first.
- **Manage > Authorized Apps** lists apps holding OAuth access on users' behalf. Users can revoke their own grants; organization admins can revoke anyone's.

## MCP tools

When the Contentstack MCP server is connected, the `developerhub` group works through the Developer Hub API on apps your organization owns:

- Inspect: `get_all_apps`, `get_an_app`, `get_app_installations` (`developerhub`)
- Change: `install_an_app`, `update_an_app_installation` (`developerhub`)
- Delete: `uninstall_an_app` (`developerhub`)

`get_all_apps` lists your organization's apps, so third-party listings such as Bynder or Shopify may not appear there; install those from the Marketplace UI. There are no tools for app configuration screens, per-field Config Parameter, app requests or authorized apps. To check stored app data, read an entry with `get_single_entry` (`cma`) or `get_a_single_entry_cdn` (`cda`), and `get_a_single_content_type` (`cma`) shows which fields use the app.

## Output

Lead with the recommended app (or "build a custom app") and why, then install steps for the user's role, the configuration that matters, and a delivery snippet or sample field shape.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Prefer the least-privileged credentials the third-party system offers (read-only keys where the app only reads).
- Install on a development stack or branch first when the app writes to entries or external systems.

### Destructive Actions

Before uninstalling an app, deleting a configuration (especially `legacy_config`), or changing a configuration other fields depend on, name the stack, app and affected content types, explain that stored app data and dependent fields can stop working, and wait for confirmation.

### Secrets

App configurations hold third-party credentials, and `get_app_installations` can return them. Never print, echo or store API keys, client secrets or tokens; refer to them by name.

### Environment Variables

In frontend examples that read app data, use `CONTENTSTACK_API_KEY`, `CONTENTSTACK_DELIVERY_TOKEN` and `CONTENTSTACK_ENVIRONMENT`. Keep third-party secrets (for example a commerce admin key) server-side under their own variables.

## References

- https://www.contentstack.com/docs/marketplace
- https://www.contentstack.com/docs/marketplace/about-marketplace
- https://www.contentstack.com/docs/marketplace/installing-apps
- https://www.contentstack.com/docs/marketplace/installed-apps
- https://www.contentstack.com/docs/marketplace/updating-an-installed-app
- https://www.contentstack.com/docs/marketplace/uninstalling-an-app
- https://www.contentstack.com/docs/marketplace/authorized-apps
- https://www.contentstack.com/docs/marketplace/app-requests
- https://www.contentstack.com/docs/marketplace/difference-between-marketplace-apps-and-extensions
- https://www.contentstack.com/docs/marketplace/faqs
- Per-app guides follow the pattern https://www.contentstack.com/docs/marketplace/<app>, for example `bynder`, `shopify`, `algolia`, `trados`.
