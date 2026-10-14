---
title: Live Preview & Visual Editor Support
description: Diagnose and set up Contentstack Live Preview, Visual Editor (Visual Builder) and Timeline with a fixed, evidence-first protocol.
---

# Live Preview & Visual Editor Support

**Slug:** `cms-live-preview-visual-editor-support-assistant` · **Product:** Developer Experience · **Type:** Advisory (read-only)

Diagnoses and guides Contentstack Visual Experience: Live Preview, Visual Editor (also called Visual Builder) and Timeline. It follows a fixed protocol, localises the failure to one setup contract, and gives the smallest fix or a ready-to-send Support handover. It works as a code reviewer when repo access is available, and as an implementation guide when it isn't.

## When it triggers

When setting up, configuring or debugging Live Preview, Visual Editor or Timeline in any framework: blank or unreachable preview panes, edits that never appear, stale or published-only preview, a stuck Onboarding Check, nothing editable on the canvas, edit-tag mapping failures, lost preview context after navigation, shared SSR state, wrong locale or variant, or Timeline showing the wrong version.

## How it works

1. **Which product?** Live Preview, Visual Editor or Timeline.
2. **Question, new setup, never worked, or regression?** Questions get answered; new setups get the right setup guide.
3. **Read the Onboarding Check** from a screenshot. Each step name maps to one gate.
4. **Detect framework, rendering mode and fetch layer** from the code.
5. **Collect what is still open:** console output (checked against known harmless noise), server logs, and one redacted content request.
6. **Localise to one contract:**

| # | Contract | One-look check |
|---|---|---|
| 1 | `init()` runs on the client in the deployed build | Onboarding Check gets past "Live Preview SDK Not Initialized" |
| 2 | Edit tags are generated and land on DOM elements | Rendered elements carry `data-cslp` |
| 3 | The hash reaches the fetch, which switches host and headers | Content requests hit the region's `*-preview` host |
| 4 | The site is reachable in an iframe | The pane renders at all |

7. **Fix and verify, or hand over** to Contentstack Support with the evidence already collected.

The skill stops once one contract is localised and adds no fallbacks while diagnosing. Detailed fixes live in its `references/` folder: FAQs for integration, preview runtime, Visual Editor and Timeline, plus a symptom index, framework notes, edit-tag conventions and console noise.

## Example prompts

- "Why is Live Preview not updating when I edit content?"
- "How do I set up Live Preview for SSR?"
- "What's the difference between `ssr: true` and `ssr: false`?"
- "My preview iframe is blank. What should I check?"
- "How do preview tokens and live preview hashes work?"

## Safety notes

Never makes changes automatically. Provides safe diagnostics and requires confirmation before any config change. Never asks for, echoes or reconstructs preview tokens or live preview hashes, and never asks for cookies or auth headers. Delivery tokens are safe in the browser; preview tokens read unpublished content, so they are exposed client-side only on preview deployments (CSR preview needs them), never in production builds; management tokens never reach the browser. Never recommends enabling Live Preview in production builds. If a secret appears in input, advises rotating it.

## Related

- [Delivery SDK](dx-delivery-sdk.md) · [Environments & Publishing](cms-environments-publishing.md) · [Entries](cms-entries.md)
