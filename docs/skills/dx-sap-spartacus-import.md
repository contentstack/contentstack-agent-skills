---
title: SAP Spartacus Content Import
description: Import an SAP Commerce Cloud storefront's CMS content over OCC into Contentstack, shaped for the Contentstack Spartacus connector.
---

# SAP Spartacus Content Import

**Slug:** `dx-sap-spartacus-import` · **Product:** Developer Experience · **Type:** Action (gated) · **Ships references & scripts**

Takes the content an SAP Commerce Cloud (Spartacus / composable storefront) site serves over OCC and recreates it in a Contentstack stack, in the model `@contentstack/contentstack-spartacus-connector` reads. Pages, slots, banners, paragraphs, carousels, links, navigation, logo, footer and images come across. Products, prices, search, cart and checkout stay with SAP, following the connector's hybrid model.

## When it triggers

When a developer has added the connector to a Spartacus app (`ng add @contentstack/contentstack-spartacus-connector`) and wants the existing SAP storefront content in Contentstack. Also for seeding a demo stack from an SAP electronics or powertools site, re-running an import to update entries, or adding locales such as de-de, ja-jp and zh-cn.

## What it covers

- **Dry run first**: extracts the site and prints what would be written, without touching the stack.
- **Two approval gates**: unknown component types need a mapping decision, and nothing is written until the user approves the summary.
- **Starter-pack check**: the run stops if the plan needs a content type or field the installed connector doesn't ship.
- **Idempotent seed and publish**: entries upsert by their SAP uid, so re-runs update in place.
- **Verification**: a round-trip comparison against SAP and a Delivery API read of the home page.
- **Localization**: localized content and images per language from SAP's own localized responses.
- **SAP product picker**: optionally installs and configures the SAP Commerce Cloud marketplace app, so editors pick carousel products from SAP instead of typing SKUs. It works for B2C and B2B sites (for example the electronics and powertools demos). Before installing, a preflight checks that the app's SAP server has a trusted certificate, the base site, a working product search and the carousel codes, and stops the run if not. After the run the agent checks the picker, repairs it at most twice, then lets the user fall back to the plain SKU list.
- **Your own login**: writes with a management token, or with the user's `csdx auth:login --oauth` session (required for the marketplace app).

## Example prompts

- "I just added the Spartacus connector. Import our SAP electronics storefront into my new stack."
- "Seed a demo stack from powertools-spa with German and Japanese."
- "Re-run the SAP import; we changed the homepage banners."
- "The import says a component type is unknown. What do I do?"
- "Let our editors pick the carousel products from SAP instead of typing SKUs."
- "Set up the SAP product picker on our powertools B2B demo stack too."

## References

Ships `references/pipeline.md` (stages, gates, flags, run directory, exit codes), `references/mapping-profile.md` (how SAP templates, slots and typeCodes map to connector content types) and `references/sap-commerce-app.md` (the marketplace app stage and its verify, repair and fallback steps). The Python scripts in `scripts/` use only the standard library; the csdx login and the marketplace app step use Node.js and the Contentstack CLI. Built by Vaishnavi Kedar as the Spartacus content-modelling agent.
