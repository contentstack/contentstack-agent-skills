---
name: build-section
description: "Author a Section composition by linking it to a structural schema (CT / Global Field / Group / Modular Block / Block / Reference) and dropping registered components."
allowed-tools: Read Grep Glob
---

## When to use

Author a Section composition by linking it to a structural schema (CT / Global Field / Group / Modular Block / Block / Reference) and dropping registered components.

Use when a NEW reusable Section must exist for a Template to drop. Run AFTER components are registered; before Template work. Phrases — "build a hero section", "create card grid". Do NOT use to MODIFY an existing Section — use Studio UI. Do NOT use for one-off page composition — use `build-connected-template`.

# Build a Section

## Context

A Section is a reusable composition that template authors drop onto pages.

**⛔ Qualification gate — before authoring, confirm this Section qualifies.** A Section pays off when **the binding work amortizes** — i.e., when the same N bindings would otherwise be repeated by the author on every template drop. Qualifies if either:

1. **The component has ≥2 separate prop bindings** — Hero with `title` + `cover.url`; Card with `image` + `title` + `summary` + `link`; ProductHighlight composed of multiple sub-components each with their own bindings. Without a Section, the author re-wires every prop on every drop.
2. **The component takes one prop bound to a structural shape** — Modular Block list, Reference array, Group, Global Field. The outer bind is 1 click, but the internal rendering walks N sub-fields per iteration; that sub-field work amortizes.

A Section does **NOT** qualify for:

- **A single atomic component bound to a single primitive (scalar) field** — `Heading` bound to `entry.title`; `Image` bound to `entry.cover.url`; `Text` bound to `entry.tagline`. One bind, one drop, no repetition cost. Studio's Connect-a-Schema picker also rejects scalar fields. Use these components inline.

**Diagnostic question:** *"How many bindings will the author wire by hand on the next drop of this component?"* If ≥2 → make it a Section. If 1 → leave it as a registered component used inline.

If the candidate fails the qualification — STOP. It's not a Section. See [`understand-sections`](../understand-sections/SKILL.md) § *What qualifies as a Section*.

Its data contract is defined by a **linked schema** — and Studio only accepts **structural shapes** here, not single scalar fields. Allowed kinds:

| Kind | What it is | Single or multiple |
|---|---|---|
| **Content Type** | The whole entry of one CT | Single — one entry at a time |
| **Global Field** | A reusable named schema (the most common section anchor) | Single OR multiple (a list of group instances) |
| **Group** | A nested object on a CT | Single OR multiple (a list of group instances) |
| **Modular Block** | A field that holds a list of blocks; each block can be a different shape | Always multi — pair with Repeater + Condition Block |
| **Block** | A *specific* block type inside a Modular Block field | Single — the block shape is fixed |
| **Reference** | Points to one or more entries of one or more CTs | Single OR multi-entry — multi pairs with Repeater + Condition Block (always required, single-CT included) |

A section connecting to a *multiple* variant is meant to live **inside a Repeater** on the template — the Repeater iterates the list; each iteration places one instance of the section's shape.

Studio's picker omits scalar fields (`text`, `number`, `boolean`, `file`, `link`, `date`, etc.). A section composes UI against a *shape*; for a single value override at template level, use **Expose Section Prop** on a component inside the section.

Bindings on registered components come from the Data Picker. The picker shows the Section's linked-schema fields by default; inside a Repeater it switches root to the iteration item's fields. See `use-repeater` § *The scope rule, in user terms*. All References inside a Repeater — single-CT and multi-CT — require a Condition Block.

## Path A vs Path B — monolith Section or Section-with-Slot + child Section

When a Section iterates over a list of cards (a multi-reference field, a Modular Block list, a multi-Group, or a multi-entry pinned query), there's a recurring architectural choice:

- **Path A — one monolithic Section.** The Section owns the Repeater AND the card markup inside it. Card props bind from the Repeater Data root (the iterated item).
- **Path B — Section-with-Slot + separate child Section.** The parent Section owns the Repeater and exposes a Section Slot inside the iteration. A separate child Section (bound to the iterated item's CT) gets dropped into the Slot at template-authoring time. The child Section is pre-bound to its own linked schema; no per-prop binding needed.

**Deciding question:** *"Will this card visual ever appear outside this list?"* (Featured product hero, related-items strip, recommended carousel, search result row, etc.)

- **Yes / probably yes / unsure → Path B.** Sections exist so visuals can be reused. Splitting the card into its own Section costs one extra Section and unlocks reuse everywhere else. **Default to Path B.**
- **Genuinely no, single-use → Path A** is acceptable. Easier to collapse Path B into Path A later than to extract a Section out of a monolith — when in doubt, Path B.

In Path B, the parent's Repeater contains a Section Slot (see `use-section-slot`), filled at template time by the child Section — never a raw component (see `understand-section-slots`). Auto-binding wires it because the child Section's linked schema matches the iterated item.

## Layout lives in the Section

A Section that exposes a Slot must wrap it in a sized layout container. See `use-section-slot` § *Layout container* and `register-component` § *Layout contract*.

Reference: `docs/32-sections/overview.md`, `docs/32-sections/link-content-types-with-linked-schema.md`, `docs/20-bring-your-own-components/register-components.md`, `docs/34-smart-containers/create-repeatable-content-with-repeaters.md`.

## How a Section gets its data — the `selectedField` model

A Section has **no data of its own**. When it's dropped on a template, the SDK hands it a scoped slice of the page entry via `getScopedData(pageEntry, selectedField)`:

- **`selectedField` set** to a field uid → the section's `template` becomes that field's value (references and groups resolved along the path).
- **`selectedField` unset** → the section's `template` becomes the **whole page entry**.

The section's own canvas therefore always shows **one empty placeholder** (no page context exists standalone). That's not a bug — the section only fills out at template-render time. Verify via SSR cold-load: `await sdk.fetchCompositionData({ url })` on the parent template's URL and dump `spec.data.section_scoped_data[<instance-uid>]`.

### Decision rule — set `selectedField` or leave it unset

| Section shape | Rule | Where its bindings resolve against |
|---|---|---|
| **One Repeater over one field** (Card Grid over `related_posts`, feature list over `features[]`) | Set `selectedField=<that field>` + use scope-root repeater binding `{ path: {} }` inside | `template` becomes the field's array value directly |
| **Multiple fields on the page entry** (Header reading `brand` + `nav_links` + `signin_label`; Hero reading a `hero` group) | **Leave `selectedField` unset** — the section needs the whole entry | `template` is the full page entry; keep original `template.<field>` binding paths |

Setting `selectedField` on a multi-field section loses access to everything outside the scoped path — bindings to those fields resolve to `undefined`.

Full mechanism, wire shapes, and the reference-iteration `data_sources.resolvedReferences` handling: `author-composition-via-api` § *Authoring a Section composition — scoping rules* and § *Decision rule — single-field repeater section vs whole-entry section*.

## Basic field components vs custom registered components — the simple-vs-styled tradeoff

Studio palettes ship two kinds of nodes you can drop into a Section. **All editing happens in the right panel — neither kind supports inline-typing in the canvas.** The real tradeoff is shape and styling:

| | **Basic field components** (palette: Basic) — `Heading`, `Paragraph`, `Text`, `Image`, `Link`, `RichText`, etc. | **Custom registered components** (palette: Registered Components) — your `<Hero>`, `<ProductCard>`, etc. |
|---|---|---|
| Shape | Single value (a string for `Heading` / `Paragraph` / `Text`, a URL for `Image`, a JSON tree for `RichText`). The author sets it via the right panel: either as a **static value** typed inline, or as a **binding** to a CT field. | N props as declared in `registerComponent` schema. Each prop set via the right panel — static value or binding to a CT field. |
| Visual styling | Plain HTML by default — `<h1>`, `<p>`, `<img>`. Styling comes from node `styles.default.responsiveStyles.default` set via the Design panel, OR app-side CSS targeting the rendered DOM. RTE embeds use the default serializer unless you register a custom one (see `register-json-rte`). | Whatever your React + CSS produces. Pixel-perfect; uses your design system. |
| Layout authoring | Composable via Basic `Box` + node `responsiveStyles` (see pitfall row below). | Owned by the React component code. |
| Authoring UX | Quick — drop, type a value or bind a field in the right panel, done. Good for editorial copy that lives ONLY in the composition (not modelled in the CMS). | Higher-fidelity — drop a fully-styled block; bind props to CT fields. Right-panel surface is exactly the prop schema you registered. |
| Best for | Headlines, body copy, captions, CTA labels, RTE blocks — wherever literal copy can live in the composition itself OR map 1:1 to a CT field with no surrounding shell. | Marquee / styled / interactive sections — hero, carousel, 3D viewer, anything pixel-sensitive or with multi-field internal structure. |

**These are two render paths.** The local standalone page (custom `Hero`) and the Studio composition (Basic `Heading` + `Paragraph`) will NOT look identical by default. Treat the gap as design work, not a bug.

**Recommended pattern — hybrid.** Use both inside one Section:

- **Custom registered components** for the styled / interactive shells — the hero with its background, the carousel with its animations.
- **Basic field components** for editorial copy that doesn't need a custom shell — headline, intro paragraph, footnote — or for repeated content blocks where authors should be able to swap copy quickly via the right panel without engineering ever touching the codebase.
- **Match the Basic-component styling to your brand** by setting node `responsiveStyles` via the Design panel (typography, spacing, color) — or write CSS that targets the rendered semantic DOM. For RTE, register a custom renderer (`register-json-rte`).

Decision rule:

- Is THIS region a single string / scalar value that maps 1:1 to a CT field (or is composition-local copy)? → Basic field component.
- Is THIS region a multi-prop / styled / interactive piece? → Custom registered component.
- Both, in the same Section, is normal and good.

## Prerequisite — the canvas chain must be wired

Section authoring requires the full canvas chain: a route mounting `<StudioCanvas />`, the project's **Canvas URL** pointing at it, and — most often missing — a **non-empty per-locale Base URL on the environment the project targets**. Missing any link = blank or Playground canvas with no explanation. If you can't confirm all three, run [`setup-section-preview`](../setup-section-preview/SKILL.md) first.

## Task

1. **Open Studio → Sections tab → + New Section.** Confirm you are in section authoring mode (the palette shows the **Registered Components** category and **Smart Containers** category — both are section-mode signals).

2. **Name the section** using the supplied `sectionName`. The display name is what template authors see in the Sections palette.

3. **Connect A Schema.** The Schema panel offers structural shapes only — no scalar fields. Pick the kind matching `linkedSchemaKind`:
   - `content-type` → pick the connected CT
   - `global-field` → pick the Global Field UID
   - `group` → pick the group field on the parent CT
   - `modular-block` → pick the Modular Block field; the section sees the union of allowed block types
   - `block` → pick a specific block type inside a Modular Block; the section sees just that block's fields
   - `reference` → pick the Reference field; the section sees the union of `reference_to` CTs

   If the user asks to "link to the title field" or similar, redirect: that's not how sections work. Either pick the parent group / object / CT, or use **Expose Section Prop** at the component level later. If `linkedSchemaUid` is blank, warn explicitly: the section is static-only, no auto-binding, every value typed by hand at template-drop time.

   When the picked schema is a *multiple* variant (`isMultiple=y`), note it in the section's intent — this section is meant to be dropped *inside a Repeater* on a template. The Repeater iterates the list; each iteration places the section once.

4. **Scan the linked CT for Slot candidates BEFORE binding fields directly.** Inspect the CT for any **Global Field**, **Modular Block**, **Group**, or **Reference** fields. For each one, decide:
   - **Expose it as a Section Slot** (the preferred default) when the nested data is composable, shared across pages, or likely to have variants. Carve a Slot at that location via `use-section-slot` instead of binding the nested shape inline. Doing so keeps the nested shape replaceable with any compatible Section per template instance.
   - **Bind it inline** only when the shape is genuinely one-off, small, and unlikely to be reused. This is the rarer case.

   Default for Global Field / Modular Block / Group / Reference fields: **expose a Slot**. Inlining throws away the reusability of the nested structure. If unsure, expose a Slot — it can always be filled with a single fixed child Section.

   See `understand-section-slots` § *When to expose one — the Global Field / Modular Block / Group / Reference heuristic* for the full rationale (Global Fields are the strongest Slot candidate of the four).

5. **Drop registered components.** For each entry in `initialComponents`:
   a. Open the palette and switch to the **Registered Components** category. Do not drop Studio default components — they bypass the project's brand system.
   b. Drag the component onto the section canvas. Use the canvas drop indicators to confirm placement inside the intended container.
   c. Select the dropped node and bind each prop via the Data Picker. The picker shows the Section's linked-schema fields by default. If the dropped node sits inside a Repeater, the picker switches root to the **iteration item's** fields automatically (labelled "Repeater Data") — bind from whichever root the picker is showing. Add a Condition Block around any Reference or Modular Block iteration.

6. **Optional smart containers.**
   - For a section whose linked schema IS the *multiple* variant, you usually drop a Repeater bound to `template.items[]` (or whatever the array path is) and place sub-components inside it.
   - Carve a **Section Slot** (see `use-section-slot`) if you want template authors to drop arbitrary components into a named region.
   - **Expose Section Props** (see `expose-section-props`) for value-level overrides — toggling a flag or swapping a label per template instance.

7. **Save.** Studio surfaces the **Expose Props** modal on Save — toggle which component props template authors should be able to override per page. If you skip this step the section is locked: template authors can drop it but cannot change any value.

## Inputs needed from the user

In this order. Stop and ask if any is missing — DO NOT guess a `linkedSchemaUid` or invent component types.

1. `sectionName` — display name (reject empty or generic "Section 1"; ask again).
2. `linkedSchemaKind` — one of `content-type / global-field / group / modular-block / block / reference`. If the user says "field name X", redirect: ask for the enclosing structural shape.
3. `linkedSchemaUid` — UID of the structural shape; allow skip with an explicit static-only warning.
4. `isMultiple` — y/n; affects whether the section is intended to live inside a Repeater on the template.
5. `initialComponents` — comma-separated list of registered component types; reject any type not currently registered in the project.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, do not claim success — surface the failure and stop.

- [ ] The new Section appears in the Studio Sections tab with the supplied `sectionName`.
- [ ] If `linkedSchemaUid` was supplied, the section's Schema panel shows that UID under the correct structural kind (and **not** under any individual field).
- [ ] If the user asked to link to a scalar field, the request was redirected to the enclosing shape (or to Expose Section Prop) — single-field linking was NOT attempted.
- [ ] When `isMultiple=y`, the section's intent is documented for template authors: "drop inside a Repeater".
- [ ] Every component listed in `initialComponents` exists on the section canvas and was dropped from the **Registered Components** palette category (not the Studio defaults).
- [ ] Each bound prop on those components resolves under the right Data Picker root — the Section's linked-schema root for props outside any Repeater, and the **Repeater Data** root (iteration item) for props inside a Repeater. A Condition Block wraps any Reference or Modular Block iteration.
- [ ] On Save, the **Expose Props** modal was acknowledged — either props were exposed or the locked state was a deliberate choice.
- [ ] Dropping the saved section onto a template that has a field of the linked schema's shape auto-binds with no manual picker steps.
- [ ] **Migration builds only** — if this Section is replacing an existing production Section on a live route, run `verify-visual-parity` against the production URL at all target viewports before declaring success. Structural checkpoints (component present, prop bound) are necessary but not sufficient; pixel drift ships silently otherwise. Skip this line for greenfield Sections that have no production counterpart to compare.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Trying to link the section to a scalar field (`title`, `description`, `image`) | Studio's picker doesn't offer scalar fields — a section composes UI against a *shape*, not a value | Pick the parent Group / Global Field / CT / Block; expose individual props later via Expose Section Prop |
| Linking to a multi-variant schema without dropping a Repeater | Section composes against the whole list as one shape; renders only the first item or fails to bind | When `isMultiple=y`, drop a Repeater bound to the array path and place components inside it |
| Picking Modular Block instead of a specific Block type | Bindings are typed against the union of block shapes — most fields don't resolve | If the section is for one block type, pick `block` and select that specific block; if the section handles many, use Repeater + Condition Block per block type |
| Skipping Connect A Schema | Section is static-only; won't auto-bind on templates; authors wire every value by hand | Pick a structural schema; only skip when you know the section is purely presentational |
| Dropping Studio default components instead of Registered Components | No brand consistency; section ignores the project's component library | Switch palette category to **Registered Components** before dragging |
| Skipping the Expose Props step on Save | Template authors get a locked section — no value overrides possible | Toggle the props that should be overridable in the Expose Props modal |
| Assuming the Section is broken because the canvas shows defaults, not CMS values | Design Mode renders registration defaults; Preview Mode renders real bindings. See `use-repeater` for the two-mode model. | Toggle Preview Mode in Properties → Configuration. |
| Binding inside a Repeater without a Condition Block on references / modular blocks | Iteration items are polymorphic; bindings silently fail | Wrap with Condition Block (single-CT references included) |
| Picking from the Section's linked-schema root for a prop that sits inside a Repeater | Wrong scope — every iteration shows the same value (the parent's field), not the per-item value | Inside a Repeater, the Data Picker switches to the iteration item's fields automatically — bind from that root |
| Naming the section "Section 1" / "New Section" | Authors cannot tell sections apart in the palette | Use an intent-revealing name like `Hero Strip`, `Card Grid`, `Testimonial Card` |
| Dropping a **Rows / Box wrapper** before the first real component | Leaves a visible "Drop Here" placeholder zone in the canvas (and in every screenshot) that authors must clean up later. Rows is an e2e-test scaffolding habit, NOT a Studio authoring pattern. | Drop the first component directly onto the canvas root slot. Wrap in a container ONLY when you need explicit layout (e.g. an `hstack` to put two cards side-by-side). |
| Adding a **Repeater for a single, non-list use case** | Repeater iterates a multi-valued field; a static page with one Hero + one Product Card needs zero iteration. Adding one introduces a phantom iteration scope and shifts the Data Picker so the parent Section's fields aren't reachable from inside. | Use Repeater ONLY when the linked field is genuinely a list (Modular Block list, multi-Group, multi-Reference, multi-entry pinned query). For a single hero or single card: drop the component directly. |
| Path A when the card visual may be reused elsewhere | Locks the card into one parent; reuse contexts drift out of sync | Default to Path B — see § *Path A vs Path B*. |
| Slot inside Repeater without a sized layout container | Child stretches full canvas width | Wrap in grid/flex/`max-width` Box. See `use-section-slot` § *Layout container*. |
| Leaving empty "Drop Here" zones at the bottom of the canvas | Saved compositions render those zones as visible placeholders in screenshots and to authors browsing the section gallery. | Before Save, switch to Layers and delete any orphan empty Box / Slot rows. Acceptance: the Layers tree contains ONLY the components you intended; no orphan structural wrappers remain. |
| **Assigning a CSS class to a Basic `box` and expecting `display: flex/grid` to apply** — the box renders but the children stack vertically (no flex) or single-column (no grid). | The Basic `Box` component is just `<div {...rest} {...studioAttributes}>` — Studio renders box layout from the node's **`styles.default.responsiveStyles.default`** (set via the Design panel on the node) and surfaces it through the renderer's style pipeline. An external CSS class on the app side has no node-level styles to attach to and only applies whatever rules its stylesheet defines — it does NOT make Studio's renderer emit `display: flex`. | Author Basic-box layout via node `responsiveStyles` in the Design panel: select the Box → Design tab → set `display`, `gap`, `alignItems`, `flexDirection`, etc. The renderer writes these into the DOM. Reach for a CSS class only for tokens/colors/typography already wired through your design system — never for the load-bearing layout shape. (Custom registered components are different — they can apply layout via their own React/CSS.) |



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

- `docs/32-sections/link-content-types-with-linked-schema.md` — how schema connection drives auto-binding
- `docs/20-bring-your-own-components/register-components.md` — getting components into the Registered Components palette
- `docs/34-smart-containers/create-repeatable-content-with-repeaters.md` — Repeater + multi-variant sections
- `docs/34-smart-containers/condition-blocks.md` — required wrapping for Reference / Modular Block iteration
- `use-section-slot` — carve a drop region into the section
- `expose-section-props` — value-level overrides on Save
- `build-connected-template` — drop the saved section onto a template with a matching field
- `build-repeating-section` — the dedicated guide for the "parent Section with Repeater + Slot, child Section fills the Slot per iteration" pattern (Path B from this skill, walked end to end)
