---
name: author-composition-practice
---

## When to use

How to approach API authoring: skeleton first then bind, read the component source not just the registration, and look for a free-form primitive before declaring a value inexpressible.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Skeleton first, bind later: authoring structure before the content model exists {#skeleton-first}

Translating a design set into Sections does not require the content model to be finished. **Author the structure with static values only, bind fields in a later pass.** This is the cheaper order when a Figma board defines 30 section shapes and the CT blocks for them do not exist yet.

A skeleton composition is an ordinary composition with one difference: **no `template` bindings**. It is not a composition with fewer props.

**Skeleton means unbound, NOT unset. Design props must still be authored to match the comp.**

| | Skeleton pass | Binding pass |
|---|---|---|
| **Content** props (`text`, `href`, `src`) | `static_value` carrying the comp's real copy | `template` binding to a CT field |
| **Design** props (`direction`, `variant`, `size`, `color`, `gap`, `align`) | **set explicitly, same as the final section** | unchanged |
| Needs a linked schema? | **no** | yes |
| Needs a preview entry / block instance? | **no** | yes |
| Renders on canvas? | **yes**: comp copy, final layout | yes, real content |

**Omitting a design prop does not leave it blank. It silently selects the library's `defaultValue`, which is rarely the comp.** Worked failure, from authoring a Figma hero against a production library: the comp showed two CTAs side by side, and the authored section rendered them stacked. Cause:

```js
// registration
direction: { type: 'choice', options: stackDirectionOptions, defaultValue: 'column' }
```

The `direction` prop was never written, so the stack defaulted to `column`. Nothing errored. The canvas simply disagreed with the design. The same pass omitted both buttons' `variant` and `text`, so a brand CTA and a secondary CTA both rendered as the identical default button. **Every visual difference between the comp and the canvas was a prop left unwritten.**

The rule that follows: **a design prop is skeleton-time work, because it is static in the final section too** (see [`design-component-library`](design-component-library.md): design props stay static, only content binds). Leaving it for the binding pass means it never gets written at all.

For content props, prefer the comp's own copy as the `static_value` over relying on a default. Two buttons that both read "Get started" hide the fact that they are different CTAs. `"Explore our platform"` and `"Try for free"` make the structure legible and make the later binding pass obvious.

**A Repeater is authored in the skeleton too: it does not wait for data.** A repeating region is one child inside a `repeater`, never N copies of the same subtree. Leave `items` unbound and the canvas renders a single placeholder iteration, which is exactly what the skeleton needs:

```jsonc
// repeater node
"props": {
  "children": { "type": "slot", "slot": "<slot-uid>" },   // ONE child: the repeated shape
  "items":    { "type": "array",
                "binding": { "type": "static_value", "value": "<uid>-items" } }
}
// entry.static_value.array — key present, NO value
[ { "key": "<uid>-items" } ]
```

The wrapper holding the repeater carries `metadata.repeaterWrapper: true`, and its `direction` / `gap` / `wrap` props produce the row or grid the iterations flow into. Verified against a production section authored this way with `linked_schemas: []` and no data sources at all.

**A list whose items have different shapes needs one Condition Block per shape, all of them, in the skeleton.** A carousel showing stat / image / quote cards is not three lists and not one card repeated. It is one Repeater with three branches. Build every branch. Stopping after the first leaves two thirds of the design unbuilt while the canvas looks plausible, and the omission is invisible once the sheet is written.

```jsonc
// repeater.slots.<contents> holds ONE condition-block per item type
{
  "type": "condition-block",
  "metadata": {
    "slotNames": { "<slot-uid>": "Contents" },
    "condition": {
      "type": "modular_block", "operator": "eq", "value": "<block_uid>",
      "conditionBinding": { "type": "repeater",
        "value": { "repeaterUID": "<repeater-uid>", "path": { "<block_uid>": {} } } },
      "dataBinding": { /* same shape */ }
    }
  },
  "props": { "children": { "type": "slot", "slot": "<slot-uid>" } }
}
```

The branches can be authored **before the Modular Block exists**. Name the block uids the schema uses (`stat_card`, `image_card`, `quote_card`) and the binding pass creates them. Verified on an unbound Repeater: all three branches render their placeholder side by side, so the skeleton shows the whole design rather than one card.

**Building N copies instead is the defect this prevents.** Five hand-placed cards look identical on the canvas, but the shape is fixed at five, editing one leaves four stale, and the binding pass has nothing to point at a collection. One card in a Repeater binds later by setting `items`. The subtree never changes.

Two consequences worth stating:

- **The canvas looking right proves structure, not data.** A skeleton and a correctly-bound section are visually similar. Both show plausible copy. `build-section` (step d, the field-existence gate) covers the inverse hazard: a **bound** prop falling back to `defaultValue` reads as real data when the binding is actually broken. Skeleton-first is safe precisely because nothing is claimed to be bound yet.
- **Bind by rewriting the same nodes.** The binding pass replaces `props.<name>.binding` from `static_value` to `template` on the existing tree. Node uids, slots and layout stay untouched. Keep the skeleton's `static_value` entries or drop them: an unreferenced key in `entry.static_value` is inert.

## Read the component source before authoring, not just the registration

The registration gives prop **names, types, options and defaults**. It does not say how the component **consumes** them, and that is where authored values silently stop working. Open the component file (`components/…/<Name>.tsx` in the host project) for every component you author, and look for four things.

**1. Props that override other props.** A component may ignore one prop when another is set:

```tsx
// AlphaRow.tsx — position overrides align/justify when set
position && position !== 'auto'
  ? ROW_POSITION_CLASS[position]
  : cn(ALIGN_CLASS[align], JUSTIFY_CLASS[justify])
```

**2. Equality comparisons: the trap that follows from list-wrapped `choice` values ([`author-composition-bindings`](author-composition-bindings.md) § Node anatomy, point 0a).** A list works for an object-key lookup and fails a strict comparison:

```js
['auto'] !== 'auto'            // true  → takes the override branch
ROW_POSITION_CLASS[['auto']]   // ""    → align AND justify are dropped
JUSTIFY_CLASS[['end']]         // 'justify-end'  → key lookup still works
```

Worked failure: a pagination row authored with `justify: end` rendered **left**-aligned. Every value was correct and the panel showed them correctly. `position: ["auto"]` (written only because the rule says fill every registered prop) sent the component down the override branch and discarded `justify`. **Where a component compares a prop by equality, leave that prop unwritten** and let its own string default apply. This is a component-side bug (it should normalize the array), so record it for the library owner rather than working around it silently everywhere.

**3. Values the component derives from another prop.** A component often computes a child's value from its own color scheme rather than taking it verbatim:

```tsx
// AlphaFeatureGrid.tsx
const bodyColor = isDark ? 'medium' : 'light';
const iconColor = isDark ? 'inverse' : 'strong';
```

Authoring the same tree atomically means supplying those values yourself, and the correct one depends on context. A dark feature grid authored with `color: light` on the body and `default` on the icon looked reasonable and was wrong on both. The shipped component uses `medium` and `inverse` for dark. **When you compose from atoms what a composite renders internally, its derivation logic is the specification for the values you write.**

**4. Which prop the component actually reads.** A registration often exposes several props for the same thing, and the component uses one of them. Worked failure: a media atom's registration offers `url` (string) **and** `media` (object). The component's first line is `if (!media?.url) return null`. A node authored with `url` rendered **nothing**: no error, no placeholder, just an absent image that read as a missing design element. The registration is a menu, not a contract. The component decides.

**5. Whether a layout prop needs a width or a height to act on.** `justify` distributes free space. A shrink-wrapped row has none. The same pagination row, with `justify: flex-end` correctly applied, still sat left until its parent stack moved from `align: start` (which shrink-wraps children) to `align: stretch`. **Alignment is a two-node problem**: the prop on the child, the width it is given by the parent. Verify by measuring the rendered box, not by reading the prop back.

## Before declaring a value inexpressible, look for a free-form primitive

A constrained prop is not the whole library. Most palettes ship an escape hatch: a shape / box / spacer primitive whose `color`, `width` and `height` are **raw CSS strings** rather than token choices. It renders exactly what the comp asks for.

**Check WHERE it renders, not just that it renders.** A shape/box primitive is often decorative background art, not an in-flow element:

```js
// outer wrapper of a typical shape primitive
{ position: 'absolute', inset: 0, pointerEvents: 'none' }
```

With that wrapper the node occupies **zero layout space** and pins to the nearest positioned ancestor, usually the section, not the card you nested it in. Worked failure: three accent rules and four slide indicators were authored as shapes. Every one measured at the exact width, height and color asked for, and every one rendered at the **section origin**, stacked on top of each other over the heading. Size and color were verified. Position was not. Read the component before using a shape as a rule, and confirm the rendered box sits inside its intended parent.

Worked failure: three accent rules were reported as impossible because `card-shell.border` is uniform and its width is a two-value choice. A card needing `border-top: 6px solid #899CFA` seemed unreachable. The same library had a `shape` primitive taking `color: "#899CFA"`, `width: "421px"`, `height: "6px"`, which reproduced all three rules exactly, including a `1px rgba(255,255,255,0.19)` hairline. **Grep the registry for a primitive with free-form size/color props before writing a row in Deviations.**

The trade-off is real, so state it: a shape used as a rule is a positioned box, not a border. It does not follow the element on resize the way a real border does, and it adds a node. When a token-level fix exists (a per-side border prop on the container), the shape is the interim answer and the registration change is the durable one.
