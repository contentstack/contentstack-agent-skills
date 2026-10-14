---
name: verify-visual-parity
---

## When to use

Drive a browser to compare a Studio-composed page against its production hand-coded counterpart, Section-by-Section at matched viewports, and classify every drift by root cause: unbound prop rendering a default, boolean flag the live call site set, prop-routing mismatch, or layout-wrapper drift. Loop until dry, no new drift class two rounds running.

Use during a brownfield migration once the Studio composition renders end-to-end and the production URL is still shipping. Phrases: visual parity, compare with live URL, drift between composed and hand-coded, screenshot diff, migration QA. Do NOT use for greenfield pages (no production counterpart to compare), for pure design-system audits (that's a code-review, not a Studio task), or as a substitute for `verify-setup` (which checks the plumbing, not the pixels).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Verify visual parity: composed vs production, Section by Section

## Context

Every brownfield migration ships a Studio composition alongside an existing production URL rendering the same content. The composition **will drift** from the production page in ways nobody decided on purpose: heading typography, item basis, gap, boolean flag defaults, per-CT image fallbacks. Manual screenshot ping-pong ("does this look right?") converges slowly and hides root causes.

This skill drives a browser, captures the two side by side at matched viewports, and classifies each visible difference into one of four root-cause buckets. The bucket names the fix. The fix goes into the adapter or the registration.

The four root-cause buckets and their fixes:

| Cause class | What it looks like | Fix |
|---|---|---|
| **A. Unbound prop rendering a default** | A prop was registered with `defaultValue: 'Resources related title'` (meant as palette preview) but the composition never bound it: the literal ships to the live page | Bind the prop, OR change the registration to have no default (blank in palette is worse UX but honest), OR exclude registration defaults from published output (product gap) |
| **B. Boolean flag the live call site set** | Production JSX says `<Card isInteractive={false} />`: the Studio adapter registered `isInteractive` with `defaultValue: true` (framework default), so composed cards animate on hover while live ones don't | Set the adapter's `defaultValue` to the call-site literal. Better: preset per known call site |
| **C. Prop-routing mismatch** | Production reroutes fields (`copy = short_description ?? description`) before passing. Studio binds a bare path (`copy → description`) and gets the wrong field | Route inside the adapter: accept both fields, choose per-branch. Or expose the raw fields as separate props and let a preset choose |
| **D. Layout-wrapper drift** | Heading class differs (`cs-h2` vs `h1-display-compact`), item `basis` off by one breakpoint, `gap` mismatched, subtitle not composed | Transcribe production wrapper CSS line-by-line into the Studio adapter wrapper. Add `KEEP-IN-SYNC` comment naming both files |

Every drift falls into exactly one bucket. If a drift resists classification, it's usually two stacked. Split it.

## Task

1. **List the Sections.** From the composition (via the canvas or `build-connected-template`'s output), enumerate the composed Sections in DOM order. Number them 1..N.

2. **Match viewports.** Pick three: mobile (390 wide), tablet (768), desktop (1280). If the production site has a hard breakpoint the migration must match, add that one too. Every capture happens at every viewport.

3. **Capture per Section.** For each Section × viewport:
   - Navigate the browser to the production URL, scroll the Section into view, screenshot the Section's bounding rect.
   - Navigate to the composed URL, scroll the same Section into view, screenshot the same rect.
   - Save the pair with a name like `Section-3-tablet-{prod,composed}.png`.
   - A composed Section renders no element of its own (Repeater and Slot wrappers are `display: contents`), so crop by band: from the Section's first text to the next Section's. Run this as is (Playwright `browser_run_code`), filling in the URLs and each Section's first text **as the production page shows it**, in order (a text the composed page lacks is then a finding):
     ```js
     async (page) => {
       const sections = ["<Section 1 first text>", "<Section 2 first text>"], missing = [];
       const urls = {prod: "<production URL>", composed: "<composed URL>"};
       for (const w of [390, 768, 1280]) for (const [side, url] of Object.entries(urls)) {
         await page.setViewportSize({width: w, height: 900}); await page.goto(url, {waitUntil: "networkidle"});
         const tops = await page.evaluate(fs => { let prev = -1; return fs.map(t => {
           const ys = [...document.querySelectorAll("body *")].filter(e => !e.children.length && e.textContent.trim() === t)
             .map(e => e.getBoundingClientRect().top + scrollY).filter(y => y > prev);
           return ys.length ? (prev = Math.min(...ys)) : null; }); }, sections);
         const end = await page.evaluate(() => document.documentElement.scrollHeight);
         for (const [i, y] of tops.entries()) { const name = `Section-${i+1}-${w}-${side}`;
           if (y == null) { missing.push(name); continue; }
           const next = tops.slice(i+1).find(t => t != null) ?? end;
           await page.screenshot({path: `parity/${name}.png`, fullPage: true, clip: {x: 0, y, width: w, height: next - y}}); }
       }
       return missing; // a missing first text is a finding, never a reason to take a full-page shot
     }
     ```

4. **Classify each visible drift.** Open both screenshots side by side (`browser_evaluate` to render an HTML page with both images), and for every difference name the cause class (A/B/C/D) and the fix. Record as `{ Section, viewport, cause: A|B|C|D, symptom, fix }`.

5. **Apply fixes at the source.** Never patch the composed page directly.
   - **Class A**: edit the composition (bind the prop) or the registration file (drop the default).
   - **Class B**: edit the adapter's registration (set `defaultValue` to the call-site literal) or add a preset.
   - **Class C**: edit the adapter body (reroute inside).
   - **Class D**: edit the adapter wrapper CSS to match production line-by-line.

6. **Re-capture the affected Section and re-classify.** Do not move to the next Section until this one is drift-free at all viewports. Localized drift is 10× cheaper to fix than compounded drift.

7. **Loop until dry.** When a full Section pass at all viewports finds no new drift for two consecutive Sections, you're done. If ANY class-A/B drift keeps appearing (registration defaults leaking, call-site literals missed), stop and run the call-site-sweep step from `register-component` § Acceptance: you're missing a pattern, not fixing individual defects.

## Inputs needed from the user

1. Production URL (`https://…/glossary/a-b-testing`).
2. Composed URL (`http://localhost:PORT/glossary/a-b-testing` after `setup-template-preview-routes`).
3. Which viewports matter (default: 390/768/1280 unless the user's design system defines others).
4. Any Sections to skip (e.g. header/footer are usually app-shell, not composed).

## Acceptance

- [ ] **Pixel parity is not structural parity.** This skill compares rendered output, and a monolithic template (one component bound to the whole page body, no Sections) matches production exactly and passes every line below. Before reporting a migration done, count `section-composition` nodes per [`build-connected-template`](build-connected-template.md) § Post-build structural check. A request phrased as "make it look exactly like the existing design" routes here, which is why the structural check has to be claimed here too.
- [ ] Every Section screenshotted at every viewport, prod + composed, saved with predictable names.
- [ ] Every visible drift labeled with a cause class (A/B/C/D) and a source-file fix, no "adjust CSS on the composed page" fixes.
- [ ] Every class-A/B fix lands in the adapter or registration, not the composition.
- [ ] Every class-D fix carries a `KEEP-IN-SYNC` comment on both the Studio adapter wrapper and the production wrapper.
- [ ] Two consecutive Sections drift-free at all viewports, which is the signal to stop.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Patching the composition (moving/resetting values) to hide drift | Loses the root-cause signal. Next brownfield project re-lives the same fix cycle | Fix at the source (adapter, registration, wrapper CSS). The composition is the outcome of the fix, not the fix. |
| Comparing the whole page instead of Section-by-Section | Drift compounds. The second Section's failure is polluted by the first | Screenshot Sections with a bounding-rect element target. Classify per-Section. |
| Skipping mobile viewport | Peek percentages, breakpoint splits, and container queries only misbehave on narrow viewports | 390-wide capture is mandatory even if desktop looks fine. |
| Measuring inside the canvas iframe at its default width | The preview frame is far narrower than the desktop breakpoint, so a 3-column grid measures as **1 column** and reads as a broken build. The composition is correct. The viewport is not | Set the viewport wide enough to cross the desktop breakpoint before measuring, and compare a comp's desktop numbers only against a desktop-width render. |
| Measuring `querySelector('h4')` instead of the element you authored | The first match is often app chrome or a wrapper, not your node. Two "mismatches" (a 14px heading and a transparent button) were both the wrong element. The authored nodes were correct | Select by the text you wrote (`textContent` match, `children.length === 0`), then read `tagName` + `className` to confirm identity before trusting the numbers |
| Assuming the canvas iframe is as wide as the browser window | It is not: the editor chrome and its own scaling mean browser widths of 1282 / 1600 / 1920 produced frames of 591 / 909 / 1229. A width measured against the browser size is wrong by hundreds of pixels | Measure `document.documentElement.clientWidth` **inside the frame**, and compare content width to that, not to the window. |
| Reporting a width mismatch without checking the gutters | Fluid content differs from the comp at every width except the comp's own. Reading `content 1085 vs comp 1138` as a defect leads to adding a `max_width` that then breaks at real viewports | Verify `content = frame − 2×gutter` holds at two or more widths. If it does, the layout is fluid and correct. See [`decompose-design`](decompose-design.md) § Step 4b. |
| Comparing at wrong scroll position (auto-loaded content) | Lazy-loaded sections render skeleton in one capture, real content in another | Scroll into view + `wait_for(networkidle)` + a short pause before each capture. |
| **Excluding "site chrome" by tag hides your own content** | A parity probe that skips `nav` / `header` to drop site chrome also drops component chrome. A tab bar authored as `<nav>` reported 0 links. An article's `<header>` made its `<h1>` invisible to the probe. Both produced "missing h1 / missing CTAs" reports against pages that were correct | Exclude by position, not tag: `body > header`, `body > footer`, or a known site-shell class. Then confirm the element you think is missing really is absent (`document.querySelector('h1')` with no filter) before reporting it |
| **Counting broken images without `complete`** | `naturalWidth === 0` is also true for an image still in flight, so a lazy-loaded page reports phantom "broken images" that vanish on the next run | Test `img.complete && img.naturalWidth === 0`. Scroll the full page first so lazy images actually load |
| **Hunting horizontal overflow with bounding rects** | An element can push `documentElement.scrollWidth` past the viewport without its own box exceeding it, so a "which element sticks out?" scan returns nothing while the page still scrolls sideways. Three fixes aimed at text wrapping changed nothing before the real cause showed up | Walk every element comparing `scrollWidth > clientWidth` with `overflow-x: visible`. Measured causes, in order of frequency: an embed carrying a fixed authoring width (an `<iframe>` in rich-text body), a list element falling back to the browser's default marker padding because only its sibling type was styled, and a long unbroken token such as a URL. Fix respectively with `max-w-full` on embeds, explicit list styling, and `overflow-wrap: anywhere` |
| **Comparing raw image / section counts against the live site** | A production marketing site's mega-menu and footer contribute dozens of images and `<section>`s. Counted as page content they invent a gap that isn't there: a page can read as a 3x image deficit when the real content gap is a fraction of that | Compare **body text length** inside content elements, which is far less contaminated, and compare asset identity (filenames) rather than counts. Treat count-based ratios as a smell, not a verdict |
| **Trusting a measurement when the dev server is serving a stale build** | A dev server can silently stop recompiling. The edit sits on disk while the page serves the old bundle, so a correct fix measures as "still broken" and invites a second, wrong fix on top of it | Before concluding a fix failed, dump what the browser actually received, e.g. read the rendered element's `className` and look for the class you just added. If it is absent, restart the dev server rather than re-editing the code |
| Chasing individual drift instead of classifying | Endless individual fixes, same bug re-appears three Sections later | Every drift gets a cause class. Two class-B drifts in a row = you missed a call-site sweep pattern. Stop and address the pattern. |

## See also

- `adapt-collection-component`: the decomposition this skill verifies. The four cause classes above map to steps 4/6/7 in that skill.
- `register-component` § Acceptance: the call-site sweep step. Class B drift means it wasn't run.
- `use-repeater`: Repeater's `display:contents` wrapper is a common source of layout drift at the leaf level.
- `troubleshoot-canvas`: separate skill. That's for "canvas won't load," this one is for "canvas loads but pixels are wrong."
