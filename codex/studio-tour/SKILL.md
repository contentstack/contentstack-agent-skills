# studio-tour


## When to use

Intent-driven end-to-end walkthrough that meets the user wherever they are and routes them through setup → register → sections → templates → ship via specialist skills.

Use when the user wants Studio working end-to-end but has not picked a starting point ("just walk me through", "I want to ship a page", "I have components, what next"). This skill orchestrates — it delegates to specialists at each step. Do NOT use when the user has a specific named task — invoke that skill directly.

# Studio Tour — start here

## Context

Studio sits between three things a user already has (a React component library, a Contentstack, an app routing layer) and one thing they want (visually composed pages with real CMS data, editable post-publish without code changes). The "I want to use Studio" → "page rendering" journey is six stages — many users don't realise some are optional.

This skill identifies the user's current stage, names what they're really trying to do, and routes to the right specialist.

Studio is three things in one (surface this early if the user hasn't seen it):

1. **A visual page builder** — drag-drop composition for content authors
2. **A real-data preview surface for composed components** — the missing rung between Storybook (isolated, fake data) and the live URL (composed, real data, post-deploy)
3. **An on-the-fly editor for layouts / components / look-and-feel** — when pages are built through templates, swap sections / reorder / re-bind without a redeploy

Reference: `docs/00-overview/contentstack-studio-overview.md`, `docs/00-overview/the-development-flow-with-and-without-studio.md`.

## The six stages

```
1. Stack          → API key, Delivery Token, Preview Token, Environment, Language (Contentstack)
2. App SDKs       → install-studio + install-live-preview into the user's React app
3. Studio project → Playground Canvas (no app) OR Website Canvas (with canvas route)
                    + Environment + Language
4. Registered     → register-component for each custom component the user already has
   components       (skip on Playground; required for Website Canvas to use brand components)
5. Sections       → build-section: connect a structural schema (CT / GF / Group / MB / Block /
                    Reference; never a scalar field) + drop registered components + bind props
6. Templates      → build-connected-template (CT-bound; covers both repeatable pages AND
                    one-off pages backed by a single-entry CT). Drops sections; saves.
                  → Deploy when ready (deploy-studio-site)
```

Stages 3-6 happen inside Studio's web UI (no API tokens needed — the user's browser session is the auth). Stages 1-2 + 4 touch the user's app code or Contentstack and may need credentials.

## Task

This skill is a **discovery + routing flow**, not a doing-flow. Walk it through 4 phases.

### Phase 1 — Discover the user's intent

Map the supplied `userGoal` to one of these named intents. If unclear, ask one clarifying question — never guess.

| If the user said something like… | Intent |
|---|---|
| "try it without installing anything", "explore", "see what it looks like" | **try** |
| "understand what Studio does", "decide if it fits my project", "evaluate" | **understand** |
| "build my first page", "ship a real page" | **build** |
| "bring my React components into Studio" | **byoc** (bring your own components) |
| "I have a page idea but don't know how to model it" | **model** |
| "swap a section / move things around / change the layout" | **edit** (existing Studio user) |
| "troubleshoot a broken canvas" | redirect → `troubleshoot-canvas` (NOT this skill) |
| "verify my setup" | redirect → `verify-setup` |

State the named intent back before proceeding ("Sounds like you're trying to **build** a real page — let me walk you through the path.").

### Phase 2 — Map their current state to the six stages

Take `existingState` and translate it onto the stage list. Identify the lowest unfinished stage — that's the current step.

| `existingState` value | Stages completed | Lowest unfinished |
|---|---|---|
| `none` | (none) | Stage 1 / 2 |
| `studio-project-only` | 1, 3 (partial — Playground) | Stage 2 if they want Website Canvas, else go to 5 |
| `sdks-installed` | 1, 2 | Stage 3 |
| `canvas-route-mounted` | 1, 2, 3 (Website Canvas) | Stage 4 |
| `components-registered` | 1-4 | Stage 5 |
| `sections-exist` | 1-5 | Stage 6 |
| `templates-exist` | 1-6 | Done — go to deploy / edit |

If the user picked combinations that don't make sense (e.g. `templates-exist` without `sections-exist`) — ask one clarifying question. Don't assume.

### Phase 3 — Route based on intent + state

Pick the next specialist skill (or doc page) from this matrix.

| Intent | Current stage | Next concrete step |
|---|---|---|
| **try** | none | Run `install-studio` only IF user wants real components. Otherwise: read `docs/10-setup/studio-project/try-studio-in-the-playground-canvas-without-an-app.md` → create project in Studio → start authoring directly in Playground (no app setup needed). |
| **try** | studio-project-only | Author a small section in Playground using Studio's defaults. Skip steps 2 + 4. Use `build-section` with `linkedSchemaUid` blank (static-only). |
| **understand** | any | Reading path — `docs/00-overview/contentstack-studio-overview.md` → `docs/00-overview/the-development-flow-with-and-without-studio.md` → `docs/00-overview/choosing-between-templates-and-sections.md` → `docs/40-recipes/marketing-site-walkthrough-with-four-end-to-end-scenarios.md`. No skill needed. |
| **build** | none | Sequence: `install-studio` → `setup-section-preview` (or stay on Playground if exploring) → `register-component` (one per component) → `build-section` → `build-connected-template` → `setup-template-preview-routes` → `verify-setup` → optionally `deploy-studio-site`. |
| **build** | sdks-installed | Resume at `setup-section-preview` → continue the build sequence. |
| **build** | components-registered | Resume at `build-section` → `build-connected-template`. |
| **byoc** | any | `register-component` per component, then `wire-component-default-data` for sensible defaults. Optionally `figma-generate-components` if Figma is the source of truth, or `import-design-tokens` to pull tokens. |
| **model** | any | Walk content modelling first (CT / Global Field / Modular Block / Reference); then `build-section`. If sections need iteration over a list, `use-repeater` + `use-condition-block`. If a single value should be overridable per template, `expose-section-props`. If a region should be template-author-defined, `use-section-slot`. |
| **edit** | templates-exist | Direct to the relevant in-Studio action — re-bind a prop, swap a section, re-order. No skill needed; this is what Studio's runtime editor is for. If an entire layout change is needed, route to `build-connected-template` or rebuild a section with `build-section`. |

### Phase 4 — Map the path end-to-end

Before they start the next skill, **describe the full path** so they know what they're getting into. Example for `build` intent from `none`:

```
Path: from zero → a Blog Post page rendering at /blog/<slug>

1. install-studio          → SDKs in your app, 3 packages, env vars
2. setup-section-preview   → canvas route mounted, Canvas URL set on the project
3. register-component (×N) → your Hero, Card, Button etc. appear in Studio's palette
4. build-section           → Hero Strip section linked to a gf_hero Global Field
5. build-connected-template → Blog Post template, drops Hero Strip, connected to blog_post CT
6. setup-template-preview-routes → /blog/:slug route in your app mounting <StudioComponent />
7. verify-setup            → smoke test: open the URL, see a real entry render

Estimated wall-clock for a fresh setup: 30–60 min the first time, 10 min for the second blog-post template.

Skills you can skip:
- setup-section-preview → if you're fine on Playground Canvas (no deploy though)
- register-component → if you only want Studio's defaults (less interesting for production)
```

Then ask: "Ready to start with step 1?" — and on confirmation, invoke the first specialist skill.

## Inputs needed from the user

In this order:

1. `userGoal` — free-form sentence describing what they want. Don't accept anything generic like "use Studio"; ask for specifics until one of the named intents lands.
2. `existingState` — comma-separated state markers. If user doesn't know, ask one clarifying yes/no per item: "Do you have an app with @contentstack/delivery-sdk installed already? Do you have a Studio project in your Contentstack account?"
3. `frameworkOrTarget` — required for `install-studio` / `setup-section-preview` / `configure-csr-vs-ssr` downstream; ask now to avoid asking later.

## Acceptance

- [ ] User's intent named explicitly (one of: try / understand / build / byoc / model / edit), confirmed back to them
- [ ] Current state mapped to the six stages, with the lowest-unfinished stage identified
- [ ] Next specialist skill (or doc page for understand intent) named and the reason for picking it stated
- [ ] Full path through remaining stages described before the user starts work
- [ ] On confirmation, the next specialist skill is invoked OR the doc page is opened
- [ ] User does NOT leave the tour without a clear next action

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Guessing the intent from vague input | Wrong path; user wastes time on the wrong skill | Ask one clarifying question; never assume between try / build / model |
| Skipping the Playground vs Website Canvas distinction | User installs SDKs they didn't need (try intent) OR is stuck without deploy (build intent) | Surface Playground Canvas early for try intent; surface Canvas URL setup for build intent |
| Inviting the user to "build a section" without first checking they have registered components | Section composes only Studio defaults; brand wrong | Confirm step 4 (registered-components) before step 5 (build-section) for Website Canvas users |
| Treating troubleshoot / verify intents as "tour" cases | The user wanted a focused diagnostic, got a journey overview | Recognize troubleshoot-canvas / verify-setup keywords and redirect immediately |
| Forgetting the 3-in-1 framing for understand intent | User leaves still thinking Studio is "just a page builder" | Open with the three-things-in-one explanation from `what-is-studio.md` |



## LLM execution caveat — drag-drop works, but only with the right sequence

Studio's canvas is a React-DnD iframe. Palette tiles listen on `mousedown` / `mousemove` / `mouseup` (NOT HTML5 native drag), and the drop COMMITS only when mousemove fires intermediate events between mousedown and mouseup. The high-level `dragTo()` helper fires HTML5 `dragstart`/`drop` which Studio does not honor — you must use `page.mouse.down()` / `page.mouse.move({steps})` / `page.mouse.up()` directly.

**Stable selectors (verified by execution):**

- Palette tile: `[data-builder-component="true"][data-node-type="<type>"]` where `<type>` is e.g. `doc-hero`, `doc-card`, `repeater`, `header`, `box`. (Section tiles use the section's composition UID as the type.)
- Canvas iframe: `[data-testid="canvas-iframe"]`
- Drop slot inside the iframe: `[data-composable-studio-slot="true"]` (the `="true"` filter is required; without it you can match elements that have the attribute but aren't active drop targets)
- Layers row title (to select a node for deletion or inspection): `[data-testid="layer-editable-title-container"]`
- Node IDs (to verify a drop committed): `[data-composable-studio-id]` inside the FrameLocator

**The drop sequence — proven working pattern:**

```ts
const item = page.locator('[data-builder-component="true"][data-node-type="doc-hero"]');
const frame = page.frameLocator('[data-testid="canvas-iframe"]');
const slot = frame.locator('[data-composable-studio-slot="true"]').first();

await item.hover();                                      // 1. position cursor over palette tile
await page.mouse.down();                                 // 2. mousedown → posts PARENT_DRAG_START to iframe
const sb = await slot.boundingBox();
await page.mouse.move(sb.x + sb.width / 2,               // 3. move cursor in STEPS — required for mousemove events to fire
                      sb.y + sb.height / 2,
                      { steps: 10 });
await slot.hover();                                      // 4. final settle on the slot (FrameLocator handles cross-frame)
await page.mouse.up();                                   // 5. mouseup → commits the drop
```

The `page.mouse.move({steps: 10})` between mousedown and mouseup is the critical detail. Without intermediate mousemove events, the iframe's drag-tracking code never registers the path and the drop is silently swallowed.

**Anti-phantom guardrail.** Always verify a NEW `data-composable-studio-id` appeared inside the FrameLocator after each drop:

```ts
const idsBefore = await frame.locator('[data-composable-studio-id]')
  .evaluateAll(els => els.map(e => e.getAttribute('data-composable-studio-id')));
// ... drop sequence ...
await page.waitForTimeout(800);
const idsAfter = await frame.locator('[data-composable-studio-id]')
  .evaluateAll(els => els.map(e => e.getAttribute('data-composable-studio-id')));
const newIds = idsAfter.filter(id => !idsBefore.includes(id));
if (newIds.length === 0) {
  throw new Error('Drop did not commit; do not continue.');
}
```

If `newIds.length === 0`: stop and surface the failure — do not fabricate completion.

**Sibling drops after the root slot is consumed.** Once a component is dropped at the canvas root, `[data-composable-studio-slot="true"]` may return zero matches because the root slot is now occupied. To add siblings, hover the **edge** of an existing node — Studio reveals a drop indicator there. Alternatively wrap children in a container (`box`, `vstack`, `hstack`) and drop subsequent siblings into the container's slot.

**Execution-path matrix:**

| Path | Drag-drop status |
|---|---|
| Human in their own Studio browser | ✅ Native — this is how authors use Studio every day |
| Playwright with direct `page.mouse.down/move/up` access | ✅ Use the proven sequence above |
| Playwright `dragTo()` only | ❌ Fires HTML5 drag events Studio does not honor |
| Synthetic `DragEvent` dispatched from page-context JS | ❌ Same reason |

**What ALSO works programmatically (verified):**

- Click a Layers row + press `Delete` → removes the node and persists
- Click the Save button → persists the composition; the button greys out post-save
- Switch right-panel tabs (Settings / Design / Data) via direct DOM clicks
- Open Configuration / URL Pattern / Schema Picker modals via their action buttons
- Read iframe canvas state via `frameLocator` (read-only operations)
- Switch palette accordion sections (Basic / Media / Container / Smart Containers / Registered Components / HTML Elements) via direct DOM clicks

## See also

- `docs/00-overview/contentstack-studio-overview.md` — the 3-in-1 framing
- `docs/00-overview/the-development-flow-with-and-without-studio.md` — without/with Studio comparison
- `docs/00-overview/choosing-between-templates-and-sections.md` — Templates vs Sections
- `docs/00-overview/choosing-your-studio-setup-path.md` — onboarding paths
- `docs/10-setup/studio-project/try-studio-in-the-playground-canvas-without-an-app.md` — try-without-installing path
- `docs/00-getting-started/quickstart-with-skills.md` — evaluator quickstart
- `docs/40-recipes/marketing-site-walkthrough-with-four-end-to-end-scenarios.md` — full real-world example
- Every specialist skill referenced in the Phase 3 routing matrix
