---
name: verify-visual-parity
description: "Drive a browser to compare a Studio-composed page against its production hand-coded counterpart, Section-by-Section at matched viewports, and classify every drift by root cause: unbound prop rendering a default, boolean flag the live call site set, prop-routing mismatch, or layout-wrapper drift. Loop until dry — no new drift class two rounds running."
allowed-tools: Read Grep Glob
---

## When to use

Drive a browser to compare a Studio-composed page against its production hand-coded counterpart, Section-by-Section at matched viewports, and classify every drift by root cause: unbound prop rendering a default, boolean flag the live call site set, prop-routing mismatch, or layout-wrapper drift. Loop until dry — no new drift class two rounds running.

Use during a brownfield migration once the Studio composition renders end-to-end and the production URL is still shipping. Phrases — visual parity, compare with live URL, drift between composed and hand-coded, screenshot diff, migration QA. Do NOT use for greenfield pages (no production counterpart to compare), for pure design-system audits (that's a code-review, not a Studio task), or as a substitute for `verify-setup` (which checks the plumbing, not the pixels).

# Verify visual parity — composed vs production, Section by Section

## Context

Every brownfield migration ships a Studio composition alongside an existing production URL rendering the same content. The composition **will drift** from the production page in ways nobody decided on purpose — heading typography, item basis, gap, boolean flag defaults, per-CT image fallbacks. Manual screenshot ping-pong ("does this look right?") converges slowly and hides root causes.

This skill drives a browser, captures the two side by side at matched viewports, and classifies each visible difference into one of four root-cause buckets. The bucket names the fix; the fix goes into the adapter or the registration.

The four root-cause buckets and their fixes:

| Cause class | What it looks like | Fix |
|---|---|---|
| **A. Unbound prop rendering a default** | A prop was registered with `defaultValue: 'Resources related title'` (meant as palette preview) but the composition never bound it — the literal ships to the live page | Bind the prop, OR change the registration to have no default (blank in palette is worse UX but honest), OR exclude registration defaults from published output (product gap) |
| **B. Boolean flag the live call site set** | Production JSX says `<Card isInteractive={false} />` — the Studio adapter registered `isInteractive` with `defaultValue: true` (framework default), so composed cards animate on hover while live ones don't | Set the adapter's `defaultValue` to the call-site literal. Better: preset per known call site |
| **C. Prop-routing mismatch** | Production reroutes fields (`copy = short_description ?? description`) before passing; Studio binds a bare path (`copy → description`) and gets the wrong field | Route inside the adapter — accept both fields, choose per-branch. Or expose the raw fields as separate props and let a preset choose |
| **D. Layout-wrapper drift** | Heading class differs (`cs-h2` vs `h1-display-compact`), item `basis` off by one breakpoint, `gap` mismatched, subtitle not composed | Transcribe production wrapper CSS line-by-line into the Studio adapter wrapper. Add `KEEP-IN-SYNC` comment naming both files |

Every drift falls into exactly one bucket. If a drift resists classification, it's usually two stacked — split it.

## Task

1. **List the Sections.** From the composition (via the canvas or `docs/prompts/build-connected-template`'s output), enumerate the composed Sections in DOM order. Number them 1..N.

2. **Match viewports.** Pick three: mobile (390 wide), tablet (768), desktop (1280). If the production site has a hard breakpoint the migration must match, add that one too. Every capture happens at every viewport.

3. **Capture per Section.** For each Section × viewport:
   - Navigate the browser to the production URL, scroll the Section into view, screenshot the Section's bounding rect.
   - Navigate to the composed URL, scroll the same Section into view, screenshot the same rect.
   - Save the pair with a name like `Section-3-tablet-{prod,composed}.png`.
   - Use `mcp__playwright__browser_take_screenshot` with `element` targeting the Section's outer container.

4. **Classify each visible drift.** Open both screenshots side by side (`browser_evaluate` to render an HTML page with both images), and for every difference name the cause class (A/B/C/D) and the fix. Record as `{ Section, viewport, cause: A|B|C|D, symptom, fix }`.

5. **Apply fixes at the source.** Never patch the composed page directly.
   - **Class A** — edit the composition (bind the prop) or the registration file (drop the default).
   - **Class B** — edit the adapter's registration (set `defaultValue` to the call-site literal) or add a preset.
   - **Class C** — edit the adapter body (reroute inside).
   - **Class D** — edit the adapter wrapper CSS to match production line-by-line.

6. **Re-capture the affected Section and re-classify.** Do not move to the next Section until this one is drift-free at all viewports. Localized drift is 10× cheaper to fix than compounded drift.

7. **Loop until dry.** When a full Section pass at all viewports finds no new drift for two consecutive Sections, you're done. If ANY class-A/B drift keeps appearing (registration defaults leaking, call-site literals missed), stop and run the call-site-sweep step from `register-component` § *Acceptance* — you're missing a pattern, not fixing individual defects.

## Inputs needed from the user

1. Production URL (`https://…/glossary/a-b-testing`).
2. Composed URL (`http://localhost:PORT/glossary/a-b-testing` after `setup-template-preview-routes`).
3. Which viewports matter (default: 390/768/1280 unless the user's design system defines others).
4. Any Sections to skip (e.g. header/footer are usually app-shell, not composed).

## Acceptance

- [ ] Every Section screenshotted at every viewport, prod + composed, saved with predictable names.
- [ ] Every visible drift labeled with a cause class (A/B/C/D) and a source-file fix — no "adjust CSS on the composed page" fixes.
- [ ] Every class-A/B fix lands in the adapter or registration, not the composition.
- [ ] Every class-D fix carries a `KEEP-IN-SYNC` comment on both the Studio adapter wrapper and the production wrapper.
- [ ] Two consecutive Sections drift-free at all viewports → stop.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Patching the composition (moving/resetting values) to hide drift | Loses the root-cause signal; next brownfield project re-lives the same fix cycle | Fix at the source (adapter, registration, wrapper CSS). The composition is the *outcome* of the fix, not the fix. |
| Comparing the whole page instead of Section-by-Section | Drift compounds; the second Section's failure is polluted by the first | Screenshot Sections with a bounding-rect element target; classify per-Section. |
| Skipping mobile viewport | Peek percentages, breakpoint splits, and container queries only misbehave on narrow viewports | 390-wide capture is mandatory even if desktop looks fine. |
| Comparing at wrong scroll position (auto-loaded content) | Lazy-loaded sections render skeleton in one capture, real content in another | Scroll into view + `wait_for(networkidle)` + a short pause before each capture. |
| Chasing individual drift instead of classifying | Endless individual fixes; same bug re-appears three Sections later | Every drift gets a cause class. Two class-B drifts in a row = you missed a call-site sweep pattern; stop and address the pattern. |

## See also

- `adapt-collection-component` — the decomposition this skill verifies; the four cause classes above map to steps 4/6/7 in that skill.
- `register-component` § *Acceptance* — the call-site sweep step; class B drift means it wasn't run.
- `use-repeater` — Repeater's `display:contents` wrapper is a common source of layout drift at the leaf level.
- `troubleshoot-canvas` — separate skill; that's for "canvas won't load," this one is for "canvas loads but pixels are wrong."
- `docs/for-developers/migration/` playbook — the codified migration flow this skill's per-Section verification loop plugs into.
