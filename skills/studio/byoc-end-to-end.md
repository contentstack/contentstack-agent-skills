---
name: byoc-end-to-end
---

## When to use

End-to-end orchestrator for the BYOC arc, chaining register-component (lazy), import-design-tokens, build-section, use-section-slot, build-connected-template, configure-csr-vs-ssr, setup-template-preview-routes, then verify-setup.

Use when an engineer wants to bring their own component library into a Studio-backed app end-to-end. Walks the arc from registration to Section to Template to publish. Phrases: "BYOC", "use my components in Studio", "Studio with my design system". Do NOT use for one-off component registration (`register-component`) or once components already exist in Studio.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# BYOC end-to-end: from registered components to a rendered Template

BYOC ("Bring Your Own Components") chains the ~8 sub-skills that take registered React components and produce a rendered Template. This orchestrator only names + orders them. It doesn't replace any sub-skill.

## Prerequisite: concepts first

If the user can't crisply define Section, linked schema, Template, and `<StudioCanvas />` vs `<StudioComponent />` in one sentence each, run `start-here-zero-knowledge` first.

## Task

Print the plan for `projectShape` and `renderMode`, filling this in (Gate lines from the phases below, detours table as is). Name sub-skills, never run them:

```
BYOC plan: <existing | new> project, render mode <csr | ssr | rsc | unsure: decided by configure-csr-vs-ssr in Phase 5>
Phase 0a  plan-studio-architecture                       Gate: <Phase 0a gate>
Phase 0   analyze-project-fit, install-studio, enable-visual-experience,
          install-live-preview, setup-section-preview    Gate: <Phase 0 gate>
Phase 0b  (existing only) migrate-page-to-studio: one small page, not the homepage
Phase 1   register-component, import-design-tokens       Gate: <Phase 1 gate>
Phase 2-3 build-section, one at a time                   Gate: <Phase 2 gate>
Phase 4   build-connected-template                       Gate: <Phase 4 gate>
Phase 5   configure-csr-vs-ssr, setup-template-preview-routes  Gate: <Phase 5 gate>
Phase 6   complete-the-build, verify-setup, deploy-studio-site Gate: <Phase 6 gate>
If something breaks: <Common detours table>
```

### Phase 0a: Architecture planning (run BEFORE Preflight)

- **`plan-studio-architecture`**: turns requirements into a printed architecture plan (Sections, Connected pages, content model, build order). Skip only if the user already has a written plan.

Gate: printed plan with classified pages, content model, ordered Section + Template inventory, build order, sanity flags acknowledged.

### Phase 0: Preflight (run once)

- **`analyze-project-fit`**: confirm React 18 or 19, single React instance, no stale SDK pin. Catches the most common install foot-guns.
- **`install-studio`**: install SDK packages, confirm a single React, wire `ContentstackLivePreview.init`, set env Base URL pre-flight. Output: SDK installed + env Base URL for target locale is non-empty.
- **`enable-visual-experience`**: confirm stack-level Live Preview is on (commonly missed. Silently blocks the canvas) and that the delivery token carries a **preview token**.
- **`install-live-preview`**: the init must set `cslp: { appendTags: true }`. **Not optional, and not a "if they want Visual Editor" step**. Every Studio project is a Visual Editor project. With `appendTags` off or absent both tag bags arrive empty everywhere at once, and no per-component fix helps.
- **`setup-section-preview`**: create the `/canvas` route mounting `<StudioCanvas />`. Set the Canvas URL in Studio Project Settings.

Preflight owns items 1, 5 and 6 of [`complete-the-build`](complete-the-build.md). Phases 1 to 3 own the rest.

Gate: open Studio, open any composition (even an empty one). Canvas iframe loads cleanly (no blank frame, no Component Loading Error). If not, run `troubleshoot-canvas` before continuing.

### Phase 1: Register components (lazy by default)

- **`register-component`**: for each component the user wants Studio to surface in the palette. Default to the LAZY shape: `component: () => import("./Foo").then(m => ({ default: m.Foo }))`. Eager only when the component is tiny and on a hot path where Suspense fallback is unacceptable.
- **`register-breakpoints`** (optional): if the site needs custom responsive breakpoints registered for Studio's responsive editor.
- **`register-json-rte`** (optional): only if the site uses JSON-RTE-bound props.
- **`import-design-tokens`**: register the customer's design system. Do this BEFORE building any Section. Tokens here drive visual fidelity of every later canvas preview.

Detour: `component: Hero` where `Hero` is `function Hero() { ... }` (no `props` arg) produces "Invalid hook call". Back to `register-component`, read the arity rule. The lazy shape avoids the trap.

Gate: open the canvas. Switch the palette to **Registered Components**. Every component the user expects to see is present, with a non-blank preview (defaults populated).

### Phase 2: Build the first Section

- **`build-section`**: pick a linked schema (Content Type / Global Field / Group / Modular Block / Block / Reference). The picker only offers structural shapes. No scalar fields. **Default to Global Field as the section anchor** unless a different shape fits better.
- **Mid-step: scan for Slot candidates.** Inside `build-section` step 4, the user is told to inspect the linked CT for **Global Field / Modular Block / Group / Reference** fields. For each one, decide:
  - Expose as a Slot (the preferred default): run `use-section-slot` for that field.
  - Bind inline (rare): only when the shape is genuinely one-off.
  - Global Field is the strongest Slot candidate of all four: build a separate Section against the Global Field's schema and expose it as a Slot in the parent.
- **`expose-section-props`**: for any prop the user wants overridable per Section-drop (e.g. background color, layout variant). Do this WHILE building the Section, not later.
- **`wire-component-default-data`** (optional): for components whose defaults aren't representable as static `defaultValue:` literals.

Gate: the Section appears in the Studio Sections tab. Open it on the canvas, and bindings render real data from a sample entry. If not, run `troubleshoot-data-binding`.

### Phase 3: Repeat Phase 2 for every Section the site needs

- Most pages need 3 to 6 Sections (Header, Hero, Feature Grid, Testimonial, CTA, Footer, etc.).
- Build them ONE AT A TIME and verify each before moving on.
- Cross-references: if a Section iterates a list (Modular Block, multi-Reference, multi-Group), use **`build-repeating-section`**, the dedicated guide for the parent-with-Slot + child-Section pattern, which composes `use-repeater` + `use-section-slot` + `use-condition-block` into one flow. Don't drop raw cards into a repeating Slot. Build the card as its own Section and let the parent's Slot accept it.
- Discoverability: run `discover-sections` periodically to see what's already been built, avoids accidentally rebuilding a Section that already exists.

### Phase 4: Choose Template flavor + assemble

- **`build-connected-template`**: assemble the Sections from Phase 3 into the Template. Templates compose Sections. They don't model fields directly. If the user hasn't built any Sections yet, back to Phase 2.

Gate: the Template renders on the canvas with the expected Section stack. Switching the preview entry updates the rendered content. If not, run `troubleshoot-composition-resolution`.

### Phase 5: Visitor render path (CSR vs SSR vs RSC)

- **`configure-csr-vs-ssr`**: the canonical decision skill. For `renderMode = unsure`, this skill picks based on the host framework (Next App Router: main or RSC entry, Vite + React Router: CSR, Remix: SSR). Output: a clear recommendation and the per-route shape to use.
- **`setup-template-preview-routes`**: create the visitor route(s) mounting `<StudioComponent />`. Either a catch-all `[[...slug]]` (recommended for most projects) or per-template routes (more control, more boilerplate). The route(s) here serve BOTH real visitors AND Studio's template-preview iframe, same code path.

Gate: open `<env Base URL>` + `<Template URL>` directly in a browser (not through Studio). The Template renders with real data. Open the same Template in Studio's Templates tab, and the iframe shows the same render, with edit overlays.

### Phase 6: Verify + ship

- **`complete-the-build`**: the handover gate, run it first. Six deliverables, all of which fail silently: CSLP tags, `thumbnailUrl` per registration, `ui_preview` per Section, Live Preview + preview token, `appendTags`, `/canvas`. Run its verification block and **print the counts**. Anything outstanding is finished before shipping. A build that renders but that no marketer can edit is not shipped.
- **`verify-setup`**: 5-layer smoke test (Delivery SDK reachability, Live Preview channel, Visual Editor, Studio canvas, new-user trap smoke). ALL FIVE layers must pass before deploying.
- **`troubleshoot-ssr-rendering`** (if needed): for SSR-specific failures (RSC client-reference boundaries, hydration mismatches, lazy-not-loaded race when `fetchSpec` isn't awaited).
- **`deploy-studio-site`**: production checklist (env Base URL points at the deployed origin, Canvas URL still `/canvas`, prod build serves the right CSP headers for the iframe).

Gate: deployed site renders a real Template at a real URL. Studio's preview of the same Template (inside Studio) shows the same content, **and** clicking a text node in that preview selects it for inline editing. If it doesn't, the CSLP half of the build is missing, not the rendering half.

## Branch: brownfield (`projectShape = existing`)

Insert `migrate-page-to-studio` between Phase 0 and Phase 1: pick one small existing page (not the homepage). In Phase 5, mount the new visitor route side-by-side with the old one. Redirect after verification.

## Branch: greenfield (`projectShape = new`)

Phase 0 includes project bootstrap. Recommended: Next.js App Router (catch-all route) or Vite + React Router (CSR). React 18.3 or later, or React 19. Canvas-app and visitor-app are the SAME app: one `package.json`, two route trees.

## Common detours, and the step to back to

| Symptom | Detour | Back to |
|---|---|---|
| Component throws "Invalid hook call" the moment the canvas renders it | The component was registered eagerly with arity 0 (e.g. `function Header() {...}` with no `props` arg) | `register-component`: switch to the lazy shape, OR add a `props` arg |
| Studio canvas blank, no console error | env Base URL empty, or Canvas URL set to a full URL instead of a path | `setup-section-preview` + `understand-canvas-url` |
| Components don't show up in the palette | Registration file isn't imported at app startup | `register-component`: `import "./register-components"` from the app entry |
| Sections panel is empty even after Phase 2 finished | Wrong project selected in Studio top-bar | switch project, OR re-run `provision-studio-project` if it was provisioned against a different stack |
| "Internal components missing: page" on the visitor route | SDK predates the release that auto-registers built-ins on the visitor render path | `upgrade-studio-sdk`: bump to the patch that ships the visitor-path auto-register |
| Template renders in Studio but not on the live route | The visitor route isn't mounting `<StudioComponent />`, OR is mounting `<StudioCanvas />` by mistake | `understand-canvas-vs-component` + `setup-template-preview-routes` |
| "registered as lazy but hasn't been loaded yet" | `fetchSpec` / `fetchCompositionData` wasn't awaited before `<StudioComponent />` mounted | `configure-csr-vs-ssr`: the SSR / RSC patterns show the right await placement |
| `useData()` warning in dev console only | Benign. Basic component hit the SSR pass before `DataCtxProvider` attached. Disappears post-hydration. | `troubleshoot-ssr-rendering`: confirm it's a warning, not an error |

## Inputs needed from the user

1. `projectShape`: `existing` or `new`. Used to insert the `migrate-page-to-studio` branch at the right point.
2. `renderMode`: `csr` / `ssr` / `rsc` / `unsure`. Used by `configure-csr-vs-ssr` in Phase 5. `unsure` is acceptable, that skill picks based on the host framework.

## Acceptance

This orchestrator succeeds when:
- [ ] **[`complete-the-build`](complete-the-build.md) ran at handover and all six rows passed, with counts printed**: `registerComponent` count equals `thumbnailUrl` count, zero Sections with an empty `ui_preview` (audited over the CMA), `cslp.appendTags` on, Live Preview + preview token on the stack, `/canvas` mounted. Not adjectives, numbers.
- [ ] **Every atomic component carries its CSLP tags**: `studioAttributes` spread on the root element **and** `wrap: false` in its register entry and each bindable prop's `$`-twin spread on the element rendering it. Verified in the DOM, not assumed: the root and each bound text/image element must show `data-cslp`. Without this the atom renders correctly but is invisible to Visual Editor and Live Preview. See [`register-component` § The `studioAttributes` contract](register-component.md) and § The `$`-twin contract.

- [ ] The user sees the full BYOC path on one page, with every sub-skill named.
- [ ] Each phase has an explicit gate (the signal that says "ready for the next phase").
- [ ] The plan is customized to their `projectShape` (existing vs new) and `renderMode`.
- [ ] Common detours are flagged WITH the step to back to, not just "something went wrong."
- [ ] The plan ends at "deployed + verified," not at "Template renders."

## Common pitfalls

| Pitfall | Why it bites | Right move |
|---|---|---|
| Treating this orchestrator as a sub-skill replacement | The orchestrator doesn't author Sections or Templates. It points at the skills that do. Running it doesn't accomplish any phase. | Use this to see the whole path. Invoke the named sub-skill for each phase. |
| Skipping the concept gate at the top | User registers components, builds a "Section" that's actually unwrapped components on a route, ships a one-off page, loses all reuse benefit | If the user can't define Section + Template + linked schema crisply, RUN `start-here-zero-knowledge` first. Five minutes of concepts saves weeks of rework. |
| Running phases out of order | E.g. building a Section before importing design tokens: the Section's canvas preview looks wrong, the user thinks the Section is broken, rebuilds it, same problem because tokens are still missing | Tokens before Sections. Sections before Templates. Templates before visitor routes. Verify before deploy. The order is load-bearing. |
| Building all Sections in one big batch before verifying any of them | If something is wrong with the SDK / registry / Live Preview channel, the user discovers it after 4 hours of building, then has to debug across all Sections at once | Build ONE Section, verify it on the canvas, move to the next. Catch breakage when the surface area is small. |
| Forgetting Phase 6 ("verify + ship") | Template renders on the canvas, so the user assumes prod will be fine, and then CSP headers block the iframe in prod, or the env Base URL still points at localhost in prod. | `verify-setup` and `deploy-studio-site` are mandatory phases, not optional. The plan doesn't end at "renders on canvas." | <!-- style-lint: allow -->

## See also

- `start-here-zero-knowledge`: the conceptual prerequisite (run BEFORE this skill if the user is new)
- `plan-studio-architecture`: Phase 0a, the requirements-to-architecture planner that runs before this skill
- `analyze-project-fit`: Phase 0 gate
- `install-studio`, `setup-section-preview`, `setup-template-preview-routes`: wiring
- `register-component`, `import-design-tokens`, `register-breakpoints`, `register-json-rte`: registration
- `build-section`, `use-section-slot`, `expose-section-props`, `use-repeater`, `use-condition-block`: Section authoring
- `build-repeating-section`: the dedicated end-to-end recipe for parent-with-Slot + child Section iteration (composes the four skills above)
- `build-connected-template`: Template authoring
- `configure-csr-vs-ssr`, `troubleshoot-ssr-rendering`: render modes
- `verify-setup`, `deploy-studio-site`: ship
- `migrate-page-to-studio`: brownfield branch
