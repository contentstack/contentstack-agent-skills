---
name: build-repeating-section
description: "Build a Section that renders a list of cards/tiles — parent Section with Repeater + Section Slot, plus child Section bound to the iterated item."
allowed-tools: Read Grep Glob
---

## When to use

Build a Section that renders a list of cards/tiles — parent Section with Repeater + Section Slot, plus child Section bound to the iterated item.

Use when a Section renders N cards/tiles from a multi-valued field (Reference, Modular Block, Group multi, multi-Reference). Phrases — "card grid", "list of N items", "iterate related posts". Do NOT use for single-instance compositions (use `build-section`). For nested repeaters, see `author-composition-via-api` § *Recipe — Nested Repeaters* (hand-author via API; Studio's UI can't author that shape).

# Build a repeating Section — parent + child pattern

## Context

The canonical "repeat the same card per item" pattern (product grids, blog lists, related items) — **two Sections working together**:

- A **parent Section** owning the layout container, Repeater, and one Section Slot inside the iteration.
- A **child Section** bound to the iterated item's CT, dropped into the parent's Slot at template-authoring time. Bindings come along; no per-prop clicks.

This is **Path B** from `build-section`. See `build-section` § *Path A vs Path B*.

Composes: `build-section` (child + parent frame), `use-repeater`, `use-section-slot`, `understand-section-slots`.

## When to skip the Repeater entirely — the array-prop alternative

Before reaching for the parent+child+Repeater pattern, check whether a **single registered component with an array prop** would work. If the list rendering is straightforward (no per-iteration variant authoring, no template-author swap) and the items come from a single **Reference field**, this path is simpler AND avoids the Repeater + Condition Block schema-disambiguation dance entirely.

The pattern:

1. **Register a component** with an `array`-typed prop (e.g. `cards: { type: "array" }`).
2. **Bind that prop to a Reference field** on the section's linked schema.
3. **Populate `data_sources.resolvedReferences`** in the composition — this tells the SDK to include the referenced entries via CDA `?include[]=<ref_field>`, so the bound array arrives at the component as **full resolved entry objects**, not `{uid}` stubs.
4. **The component does its own `.map()`** to render each item — no Studio Repeater, no Condition Block, no iteration scope inside Studio.

```tsx
// Registered component
registerComponent({
  type: "doc-card-list",
  component: CardList,
  schema: {
    cards: { type: "array" }, // <-- bound to a multi-Reference field on the section's linked schema
  },
});

function CardList({ cards }: { cards: Array<{ title: string; url: string }> }) {
  return (
    <ul>
      {cards.map((c) => <li key={c.url}><a href={c.url}>{c.title}</a></li>)}
    </ul>
  );
}
```

**Why this works:** the SDK's data-binder handles `type: "array"` bindings by reading the bound array directly. When `resolvedReferences` includes the field, the array arrives populated with full entries — the component renders them with its own JSX. No iteration scope means no need for a Condition Block to disambiguate per-iteration item schemas.

**When the Repeater pattern is still right:**

- Author needs to **swap a different child Section per template instance** via the Section Slot (the whole reason the Repeater + Section Slot pattern exists).
- The list iterates a **Modular Block** (polymorphic — different block types need different rendering; the Repeater + Condition Block sibling chain is built for this).
- The Studio canvas should show **real iteration preview** of N rendered child Sections (Preview Mode).
- The same iteration shape is reused across multiple Sections.

**When the array-prop pattern wins:**

- The list is a **single Reference field** (or single multi-entry pinned query) with one rendering shape.
- The component is owned by engineering and won't change per template instance.
- You want to skip the Repeater UI overhead and the schema-disambiguation requirement.

If unsure, default to the Repeater pattern documented below — it's the canonical Studio path and surfaces variability to authors. The array-prop alternative is a known-good shortcut for reference-list cases where author variability isn't needed.

## Prerequisite — the canvas chain must be wired

This is a canvas operation. If the Section canvas is blank, run `setup-section-preview` first.

## Task

### Step 1 — Build the child Section first

If `childSectionName` doesn't exist yet, build it now via `build-section`:

- Linked schema: `childLinkedSchema`
- Drop registered components for the card visual; bind their props via Data Picker against the child's linked schema
- Slot-candidate scan: expose Slots for any Global Field / Modular Block / Group / Reference fields (see `understand-section-slots`)
- Components stay **layout-agnostic** — see `register-component` § *Layout contract*

Gate: open the child standalone; it must adapt at any canvas width. If it renders full-bleed or collapses, fix the child's layout before continuing.

### Step 2 — Create the parent Section frame

Open Studio → Sections tab → + New Section. Name it `parentSectionName`.

Link the parent to `parentLinkedSchema` (the CT / Global Field that holds `iterationSourceField`). Use the same Connect-A-Schema flow `build-section` describes.

### Step 3 — Drop a layout container Box first

**Don't drop the Repeater bare onto the Section root** — without a layout container the Slot gets a full-canvas-width cell (see `use-section-slot` § *Layout container*). Drop a **Box** onto the Section root, configure per `layoutShape`:

| `layoutShape` | Box CSS |
|---|---|
| `grid` | `display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px;` |
| `flex-row` | `display: flex; flex-wrap: wrap; gap: 16px;` with `flex-basis: calc(33% - 16px)` on the child cell |
| `vertical-list` | `display: flex; flex-direction: column; gap: 16px;` |
| `horizontal-scroll` | `display: flex; gap: 16px; overflow-x: auto; scroll-snap-type: x mandatory;` with `flex: 0 0 280px` on the cell |

The Box defines the cell size. The Slot will sit inside the Repeater inside this Box, so each iteration fills one grid track / flex item / list row.

### Step 4 — Drop a Repeater inside the Box

Drag **Repeater** from the palette's Smart Containers category into the Box.

Bind the Repeater's **Bind items** property to `iterationSourceField` via the Data Picker. The picker shows the parent Section's linked-schema fields; pick the multi-valued field (the picker disables scalars for this slot).

For multi-reference / Modular Block iteration, see Step 5 (Condition Block). For `group` / `array` / `pinned-query`, skip to Step 6.

### Step 5 — Wrap in a Condition Block (when required)

If `iterationItemKind` is `reference` (single-CT *or* multi-CT) or `modular-block`, the Repeater's immediate child must be a **Condition Block** (Studio schema requirement). Two ways:

- **Preferred** — drop a Section Slot inside the Repeater (Step 6), then when you later drop the child Section into the Slot at template time, Studio surfaces an inline hint that this iteration source needs a Condition Block; accept the wrap and Studio inserts it for you.
- **Manual** — drop a Condition Block inside the Repeater first; then drop the Section Slot inside the Condition Block.

For `group` / `array` / `pinned-query`, no Condition Block is needed.

### Step 6 — Drop exactly ONE Section Slot inside the Repeater (or its Condition Block)

Drag a **Section Slot** from the palette into the Repeater (or the Condition Block from Step 5). One Slot, not multiple.

Set the Slot's **Drop placeholder label** to something intent-revealing — `Drop ${childSectionName} here` (e.g. `Drop ProductCard here`). The label is the only contract template authors have with this Section.

**Do not** drop the child Section directly into the Slot at this point. The Slot is filled at template-authoring time (Step 8). In the parent Section's own canvas, the Slot is an inert labelled placeholder.

### Step 7 — Save the parent Section + verify on its own

Save. In Layers, the tree should read:

```
Section "<parentSectionName>"
└── Box  (layoutShape container)
    └── Repeater  (bound to <iterationSourceField>)
        └── (Condition Block, if reference/modular-block)
            └── Section Slot  (label: Drop <childSectionName> here)
```

In the parent Section's own canvas (with no template open), the Repeater shows one placeholder iteration containing the empty Slot. This is normal — fills happen at template / parent-of-parent time.

### Step 8 — Drop the child Section into the Slot at usage time

When the parent Section is dropped on a Template (or in another Section's Slot), each iteration shows the empty Slot. Drag `childSectionName` from the Sections palette into the Slot.

What happens:
- Studio drops the child Section into the Slot
- Section-level auto-binding kicks in: the child's linked schema (`childLinkedSchema`) is matched to the Repeater's iteration scope. The child Section's bindings resolve against each iterated item.
- Zero manual binding clicks. The child Section is pre-bound by virtue of being a Section.

If the iteration source is a single-CT / multi-CT Reference (or Modular Block) and you didn't add a Condition Block manually in Step 5, Studio prompts you to wrap; accept.

### Step 9 — Toggle Preview Mode to verify

Select Repeater → right-panel **Configuration** → toggle **Preview Mode** on. See `use-repeater` step 7. The canvas should render N iterations with real per-item data.

Troubleshooting:
- Wrong iteration count → re-check Step 4 Repeater binding.
- Same value across iterations → child's linked schema doesn't match iterated item's CT.
- Card full-bleed → parent Box (Step 3) doesn't define cell size.

## Inputs needed from the user

Collect in order; don't guess `iterationSourceField` or `iterationItemKind`.

1. `parentSectionName` — the grid / list container name
2. `parentLinkedSchema` — the CT / Global Field the parent binds to
3. `iterationSourceField` — the multi-valued field on that schema
4. `iterationItemKind` — reference / modular-block / group / array / pinned-query
5. `childSectionName` — the card / tile Section (built in Step 1 if missing)
6. `childLinkedSchema` — what the child binds to (should match the iterated item's CT)
7. `layoutShape` — grid / flex-row / vertical-list / horizontal-scroll

## Acceptance

This skill succeeds only when ALL are true:

- [ ] The child Section exists, is layout-agnostic, and renders correctly standalone at any width.
- [ ] The parent Section exists with the tree: Section → Box → Repeater → (Condition Block, if needed) → Section Slot.
- [ ] The parent Section's Box has explicit layout CSS for `layoutShape` (grid tracks, flex with basis, etc.) defining each cell's size.
- [ ] The Repeater is bound to `iterationSourceField` via the Data Picker (confirmed by inspecting the Bind items breadcrumb).
- [ ] Exactly ONE Section Slot sits inside the Repeater (or its Condition Block).
- [ ] When the parent Section is dropped on a template and the child Section is dropped into the Slot, **no manual prop binding** is needed — the child binds automatically at Section level.
- [ ] Preview Mode on the Repeater renders N iterations of the child Section, each iteration's bindings showing the corresponding item's data.
- [ ] No iteration renders full-bleed (parent Box defines the cell size correctly).

## Common pitfalls

| Pitfall | Fix |
| --- | --- |
| Dropping a raw registered card into the Slot | Build it as a Section first; drop the Section. See `understand-section-slots`. |
| Skipping the Box (Step 3) — Repeater bare on Section root | Wrap Repeater in a sized Box. See `use-section-slot` § *Layout container*. |
| Multiple Section Slots inside the Repeater | Exactly ONE Slot per Repeater; put multi-region content inside the child. |
| Skipping Condition Block for Reference / Modular Block iteration | Accept Studio's inline wrap prompt, or insert Condition Block manually (Step 5). |
| Binding from parent's linked-schema root inside the Repeater | Inside Repeater, picker shows "Repeater Data" — bind from that root. See `use-repeater` § *The scope rule*. |
| Child depends on layout ancestor (`.fs-grid > .fs-card`) | Keep child layout-agnostic. See `register-component` § *Layout contract*. |
| Empty Slot in Design Mode mistaken for binding error | Toggle Preview Mode. See `use-repeater` step 7. |
| Preview Mode on but Repeater still empty | Toggle isn't the issue — diagnose binding (Step 4), source field has items, Condition Block in place (Step 5), child schema matches. See `troubleshoot-data-binding`. |
| Monolithic Section (Path A) when card is reusable | Use Path B — see `build-section` § *Path A vs Path B*. |

## See also

- `build-section` — for both the parent and child Sections; covers Path A vs Path B
- `use-repeater` — for the Repeater step
- `use-section-slot` — for the Slot step
- `use-condition-block` — for Reference / Modular Block iteration
- `understand-section-slots` — what fills a Slot (a Section, not a raw component)
- `register-component` — the layout-agnostic contract for components inside the child Section
- `byoc-end-to-end` — the broader BYOC arc this skill fits into
