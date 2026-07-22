# use-repeater


## When to use

Drop a Repeater on a section or template canvas and bind it to a multi-valued field so the same shape renders once per item. Two-mode mental model: bind-then-iterate.

Use when rendering the same component once per item from a multi-valued source — Modular Block lists, multi-Reference fields, Group with multiple:true, or any array field. Phrases — "repeat per item", "list of blocks", "iterate references". Pair with `use-condition-block` for heterogeneous iteration items (Modular Blocks, References). Do NOT use for single-value fields.

# Use a Repeater

## Context

> **Prerequisite — the canvas must render.** This is a canvas operation; if the section/template canvas is blank, the canvas chain isn't wired (route + Canvas URL path + the targeted environment's per-locale Base URL). Run [`setup-section-preview`](../setup-section-preview/SKILL.md) first — it walks the whole chain, including the env Base URL.

A Repeater is a Smart Container that renders its child subtree once per item of a multi-valued source — Modular Block lists, Reference fields with multiple entries, Group with `multiple: true`, or any array field.

**The scope rule, in user terms:** clicking inside a Repeater switches the Data Picker roots. Outside the Repeater = the Section's linked-schema fields. **Inside the Repeater = the iteration item's fields, labelled "Repeater Data".** Bind from whichever root the picker shows; the location determines the shape, not your choice.

When the iteration items are heterogeneous — Modular Block lists, or References (single-CT *and* multi-CT) — the immediate child of the Repeater must be a Condition Block; Studio surfaces an inline hint when you bind a child directly and offers to wrap it for you.

## What goes into a repeating Slot — a Section, not a raw component

When the Repeater contains a Section Slot (the common "list of cards" pattern), what fills the slot is **another Section**, not a raw registered component — the Section's pre-bound linked schema auto-binds to each iterated item, so no per-prop hand-binding is needed. See `understand-section-slots` § *What fills a Slot — a Section, not a raw component*.

Reference: `docs/34-smart-containers/create-repeatable-content-with-repeaters.md`.

## Task

1. **Confirm the source field is multi-valued.** Inspect `sourceFieldPath` on the connected content type or Pinned Query. If it is single-valued (single reference, group with `multiple: false`, scalar), stop — redirect the user to bind the component directly without a Repeater.

2. **Drag the Repeater tile from the palette.** Palette → **Smart Containers** → drag **Repeater** onto the canvas region of `compositionName` where iterations should appear.

3. **Select the Repeater node from the Layers panel.** Clicking the Repeater on the canvas is unreliable because nested children intercept the click — always select it from **Layers**.

4. **Bind the Repeater to the source.** In the right panel **Properties** section, click **Bind items** to open the Data Picker. Navigate to `sourceFieldPath`:
   - For a template field: pick under the connected content type root.
   - For a Pinned Query: pick under **Pinned Queries**.
   - The picked node must be a list/array; the picker disables scalar leaves for this slot.

5. **Wrap iteration in a Condition Block when required.** If `itemKind` is `modular-block` or `reference` (single-CT or multi-CT), the immediate child of the Repeater must be a Condition Block. The cleanest path: drop the `iterationComponent` directly inside the Repeater first — when you bind any prop on it, Studio shows an inline hint that this source needs a Condition Block; accept the wrap prompt and Studio inserts the Condition Block around the component, scoping it to the active item type. For `group` and `array` of scalars, skip this step.

6. **Drop the iteration content inside the Repeater.**
   - **Preferred — drop a Section.** If the iteration content is non-trivial (a card with title + image + price + rating, etc.), build it as its own Section bound to the iterated item's CT and drop *that Section* into the Repeater (or into the Condition Block if step 5 applied, or into a Section Slot inside the Repeater — see the "What goes into a repeating Slot" pattern in Context above). The Section is pre-bound; nothing to wire per drop.
   - **Fallback — drop raw components.** For trivial single-prop iterations only, you can drop a raw registered component directly inside the Repeater and bind its props via the Data Picker. The picker is already showing the **Repeater Data** root (iteration item fields) because you're inside the Repeater — pick from there, not from the parent Section's linked-schema fields. This works but doesn't scale beyond simple cases; reach for the Section route the moment you have more than one or two props.

7. **Toggle Preview Mode on the Repeater to verify with real data.**

   Studio's canvas has two render modes for Smart Containers (Repeater, Condition Block, and similar):

   - **Design Mode (default).** Renders with **placeholder defaults** — Repeaters iterate once, Conditions show the un-checked branch, bindings on registered components resolve to their `defaultValue` from registration (not to real CMS data). Purpose: lay out structure without depending on live data. You can position, size, style, and arrange Sections without waiting for fetches or worrying about empty arrays.
   - **Preview Mode (toggle).** Renders with **real data** — Repeaters iterate over real items, Conditions apply real checks, bindings resolve to actual CMS values. Purpose: verify the bound result looks right against live content.

   You **design** in Design Mode and **verify** in Preview Mode — both modes are correct for their phase of authoring. Don't treat Design Mode's single-iteration placeholder as a bug; it's by design, so you can edit the iteration shape without fetching N items every time you nudge a margin.

   Select the Repeater in Layers → right-panel **Configuration** → toggle **Preview Mode** to confirm N iterations render with the expected per-item values.

8. **Save the composition.** Verify in Layers that the tree is `Repeater → (Condition Block →) iterationComponent`, and on the canvas (with Preview Mode on) that each iteration renders the expected per-item values.

## Inputs needed from the user

Collect these in order; stop and ask if any is missing — do not guess `sourceFieldPath` or `itemKind`.

1. `compositionName` — section or template hosting the Repeater
2. `sourceFieldPath` — a list field on the Section's linked schema, or a Pinned Query name
3. `itemKind` — one of `modular-block`, `reference`, `group`, `array` (drives whether a Condition Block is required)
4. `iterationComponent` — optional; if blank, prompt the user to drop one manually after step 5

## Acceptance

Succeeds only when ALL are true. If any fails, surface it and stop.

- [ ] A Repeater node exists in `compositionName`'s tree, selected and visible in Layers.
- [ ] The Repeater's **Bind items** property points at `sourceFieldPath` via the Data Picker.
- [ ] If `itemKind` is `modular-block` or `reference`: a Condition Block is the immediate (or sole) child of the Repeater, wrapping the iteration component.
- [ ] If a raw iteration component was dropped: its bound props all resolve under the **Repeater Data** root in the Data Picker (iteration-item fields), not the parent Section's linked-schema root. Confirm by inspecting any bound prop in the picker breadcrumb.
- [ ] If a child Section was dropped (preferred path): the Section appears inside the Repeater (or its Condition Block / Slot), with no hand-binding needed — the Section's own bindings flow through automatically.
- [ ] Preview Mode on the Repeater renders more than one iteration on the canvas, each showing distinct per-item values.
- [ ] The composition is saved.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Selecting the Repeater by clicking the canvas | Nested children intercept the click; you end up selecting the wrong node and binding the wrong slot | Always select the Repeater from the **Layers** panel |
| Binding iteration props from the parent Section's linked-schema root instead of the iteration item's root | Resolves at parent scope — every iteration shows the same value | Inside the Repeater, the Data Picker shows the **Repeater Data** root automatically. Bind from there — those are the iteration item's fields. |
| Dropping a raw multi-prop card into a repeating Slot and hand-binding each prop | Doesn't scale beyond one or two props; easy to miss a prop or pick the wrong path | Build the card as its own Section bound to the iterated item's CT, then drop that Section into the Slot. Section-level auto-binding handles the wiring. |
| Skipping the Condition Block for References | References (single-CT and multi-CT) are heterogeneous per Studio schema; bindings silently fail to resolve | Accept Studio's inline wrap prompt, or insert a Condition Block manually as the Repeater's direct child |
| Expecting all iterations to render in Design Mode (Preview Mode off) | Design Mode renders one placeholder iteration on purpose so you can lay out the structure without depending on live data. It's not a bug; it's the design phase. | Toggle **Preview Mode** in Properties → Configuration when you're ready to verify with real data |
| Repeater still renders 0 items AFTER toggling Preview Mode on | Preview Mode controls *whether* bindings resolve, not *whether they resolve correctly*. If Preview Mode is on and the Repeater is still empty, the toggle isn't the issue — the binding shape is. Flipping Preview Mode again does nothing once it's already on. | Stop flipping the toggle. Diagnose the binding: re-check the Bind items source field, confirm the source has items in real data (DevTools Network → composition / entry payload), verify scope (is the binding picked from the right Data Picker root?), confirm the Condition Block is in place for Reference / Modular Block iteration. See `troubleshoot-data-binding` and `build-repeating-section`. |
| Dropping the Repeater on a single-value field | Repeater requires an iterable source; binding rejects scalars | Bind the component directly without a Repeater |
| Dropping multiple iteration components as siblings inside the Repeater | All siblings render once per item, multiplying output unintentionally | Wrap intended iteration shape in a single container (Box/Row) inside the Repeater |
| Reaching for a Repeater on a static, single-instance page | Repeater exists to iterate a list. A page with one hero + one promo card has nothing to iterate — adding a Repeater introduces a phantom iteration scope, shifts the Data Picker to "Repeater Data" so the parent's fields aren't reachable, and leaves an empty iteration placeholder in the canvas | Confirm the data source is genuinely multi-valued BEFORE dropping a Repeater. Static single-instance content → drop the component directly on the canvas; no Repeater |

## See also

- `build-repeating-section` — the end-to-end "parent Section with Repeater + Slot, child Section drops in" recipe; use that when the iteration content is a non-trivial card that should be reusable elsewhere
- `adapt-collection-component` — reach for this when the iteration wraps a **production component whose interface takes an array/object prop** (`<Carousel items={[…]} />`). Native `array`/`object` prop types don't bind to CMS fields, so the wrapper needs a `slot` prop + leaf adapter to become a List Section. Migration flavor of List Section authoring.
- `verify-visual-parity` — Repeater's per-iteration `display:contents` wrapper is a common source of layout drift and breaks JS libraries that measure children (Embla, Swiper). If a slider/carousel misbehaves at runtime, run visual parity per Section against the production URL and classify the drift.
- `author-composition-via-api` § *Recipe — Nested Repeaters* — nested-repeater shapes (inner `items` binding uses the OUTER repeater's `repeaterUID`; inner card props bind to the inner repeater scope). Studio's UI doesn't have a direct authoring path for nested repeaters yet; the API recipe is the reference
- `docs/34-smart-containers/create-repeatable-content-with-repeaters.md` — full reference
- `docs/34-smart-containers/condition-blocks.md` — when and how to wrap heterogeneous iteration
- `skills/src/use-condition-block.md` — sibling skill, always invoked for Modular Block and Reference iteration
