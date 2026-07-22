---
name: gate-third-party-scripts
description: "Keep the host site's third-party scripts (cookie banners, chat widgets, GTM/analytics, ad pixels, feature-flag SDKs) out of the Studio canvas and preview sessions using the SDK's stable editor-mode contract — detect what the project loads, wrap each init in the right helper, verify."
allowed-tools: Read Grep Glob
---

## When to use

Keep the host site's third-party scripts (cookie banners, chat widgets, GTM/analytics, ad pixels, feature-flag SDKs) out of the Studio canvas and preview sessions using the SDK's stable editor-mode contract — detect what the project loads, wrap each init in the right helper, verify.

Use when the user reports a cookie banner / chat bubble inside the canvas, analytics counting author sessions, pixel conversions from editing, or asks to "hide X in Studio" / "gate scripts" / "detect canvas mode". Also run proactively at the end of a Studio install on any site that has GTM/OneTrust/chat scripts. Do NOT use for third-party scripts that *crash* the canvas with runtime-error overlays — that's `troubleshoot-canvas` § third-party overlays.

# Gate third-party scripts out of the Studio canvas

Reference: Detect the Studio canvas — the canonical recipe with all signals, semantics, and the decision table. This skill is the executable path.

## Step 1 — inventory what the project loads

Grep the app for third-party inits:

```bash
grep -rniE "onetrust|cookiebot|osano|intercom|drift|qualified|hubspot|posthog|mixpanel|amplitude|segment|gtag\(|googletagmanager|dataLayer|fbq\(|ttq\.|launchdarkly|splitio|split\.io" src app pages components --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.html" -l
```

Classify each hit with the recipe's rule: analytics / flags / banners / chat / pixels get gated; design-system CSS, font loaders, and SDKs the composed components need (maps, video players) do NOT.

## Step 2 — pick the gate per integration point

| Integration point | Gate |
|---|---|
| JS init in app code (banner, chat, flags) | `if (!isStudioCanvas()) { … }` |
| Analytics / pixels in app code | `if (!isStudioEditorMode()) { … }` — preview sessions aren't visitors either |
| GTM snippet in `<head>` (runs before SDK) | Inline `dataLayer.push({ cs_studio_canvas: new URLSearchParams(location.search).has("cs-composable-studio") })` BEFORE the GTM script, then tell the user to add the per-tag trigger condition `{{cs_studio_canvas}} equals false` in the GTM console — the SDK cannot do the GTM-console half |
| Declaratively injected widgets you can't reach in code | CSS: `html.cs-studio-canvas <widget-selector> { display: none !important; }` |
| Server-emitted script tags (SSR) | `isStudioCanvas(<request search params>)` — no-arg form is always `false` on the server |

Import from the package root: `import { isStudioCanvas, isStudioEditorMode } from "@contentstack/studio-react";`. Requires the SDK version shipping the editor-mode contract (PR #878+); on older versions, fall back to the query-param check only.

## Step 3 — apply

Wrap each inventoried init. Do not delete or re-order third-party code — only wrap. For GTM, add the inline push snippet immediately above the GTM `<script>` and report the GTM-console trigger instruction to the user as a required manual step.

| Pitfall | Why it bites | Fix |
|---|---|---|
| Gating with `window.self !== window.top` | Breaks when the site is legitimately embedded elsewhere; not part of the contract | Use the SDK helpers / documented signals only |
| Gating analytics with `isStudioCanvas` | Live-preview sessions still fire page views | Use `isStudioEditorMode` for analytics/pixels |
| Checking `location.search` in app code | Client-side navigation strips the param; the check flips mid-session | Use the helpers — the `window.__CS_STUDIO_MODE__` marker survives navigation |
| Gating the design system or component-required SDKs | Canvas renders unstyled/broken components | Only gate the recipe's "No" rows |

## Step 4 — verify (acceptance)

- [ ] Visitor route in a normal tab: banner + chat appear, analytics fires, `window.__CS_STUDIO_MODE__ === "visitor"`.
- [ ] Same route with `?cs-composable-studio=true`: nothing third-party fires, `<html>` has `cs-studio-canvas`, marker is `"canvas"`.
- [ ] Click an internal link inside the canvas (param disappears from URL): marker still `"canvas"`, gates still hold.
- [ ] If SSR: `curl` the page with and without the param — script tags present/absent accordingly.
