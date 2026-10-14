---
title: Live Preview & Visual Builder Support
description: Diagnose and implement Contentstack Live Preview and Visual Builder across CSR, SSR, SSG, middleware/BFF, and tagging flows.
---

# Live Preview & Visual Builder Support

**Slug:** `cms-live-preview-visual-builder-support-assistant` · **Product:** Developer Experience · **Type:** Advisory (read-only)

Diagnoses and guides Live Preview and Visual Builder implementations: it traces preview context, identifies the broken contract, and recommends the smallest correct fix. It works as a code reviewer when repo access is available, and as an implementation guide when it isn't.

## When it triggers

When implementing or debugging Live Preview or Visual Builder: blank preview panels, stale or published-only preview, lost preview context after navigation, shared SSR state, cache contamination, or edit-tag mapping failures.

## How it works

The skill classifies a symptom into a failure bucket, identifies the rendering strategy (CSR / SSR / SSG / middleware-BFF), asks only the minimum evidence-based questions, traces the preview contract, names the most likely broken link, then recommends the smallest fix plus a short verification checklist.

### Symptom buckets

| Symptom                                    | Likely broken contract                                                                                                         |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Blank preview / setup status error         | Page can't initialize a valid preview session (URL embeddable? `X-Frame-Options`? SDK `init()` on the route?)                  |
| Published content in preview               | Preview context exists in browser but never reaches the content fetch (missing hash, wrong host, no preview token)             |
| Edits don't update (CSR)                   | `ssr: false`? `onEntryChange()` / `onLiveEdit()` registered and refetching?                                                    |
| Preview breaks after navigation            | Hash propagation: links/redirects strip `live_preview`, `content_type_uid`, `entry_uid`, `locale`                              |
| Wrong entry / another editor's draft (SSR) | Request-scoped state being shared or cached; use request-scoped clients, disable caching when `live_preview` is present        |
| Visual Builder clicks open wrong field     | Tagging: `mode: "builder"`, `addEditableTags()` in the data layer, `$` props spread onto real DOM nodes, correct block indices |

## Example prompts

- "Why is Live Preview not updating when I edit content?"
- "How do I set up Live Preview for SSR?"
- "What's the difference between `ssr: true` and `ssr: false`?"
- "My preview iframe is blank. What should I check?"
- "How do preview tokens and live preview hashes work?"

## Safety notes

Never makes changes automatically. Provides safe diagnostics and requires confirmation before any config change. Treats preview tokens and live preview hashes as sensitive; never asks for tokens, cookies, or auth headers; never recommends enabling Live Preview in production builds. If a secret appears in input, advises rotating it.

## Related

- [Delivery SDK](dx-delivery-sdk.md) · [Environments & Publishing](cms-environments-publishing.md) · [Entries](cms-entries.md)
