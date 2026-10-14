---
name: author-composition-bindings
---

## When to use

The binding contract: all binding types, where bindings and children live in the `ui` node tree, and the Repeater binding shapes that actually resolve.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Binding types: the full set

The SDK defines **6 binding `type` values** that Studio's Data Picker emits. Each type is available in a specific composition context. Picking one that doesn't fit the context is the most common trap.

| `type` | Available in | Configured in Studio via | Shape |
|---|---|---|---|
| `static_value` | Connected + Freeform + Sections (always) | Right panel: in Settings, type the literal into the prop input | `{ type: "static_value", value: "<key>" }`, where `<key>` looks up `entry.static_value.<subtype>[]`. See [`author-composition-static-values`](author-composition-static-values.md) |
| `template` | Connected templates + Sections placed on Connected templates | Right panel: in the Data Picker, pick a field on the connected entry | `{ type: "template", value: { path: {…} } }` |
| `repeater` | Anywhere inside a Repeater | Right panel: Data Picker under the Repeater's scope, auto-picked | `{ type: "repeater", value: { repeaterUID: "<uid>", path: {…} } }` |
| `contentstack` | Requires **Freeform enabled** on the project; then available on freeform templates AND Connected Templates. Data tab, under **Pinned Entries** | In the Data tab, pin an entry, then the Data Picker binds to its fields | `{ type: "contentstack", value: { uid, _content_type_uid, path: {…} } }` |
| `contentstack_queries` | Requires **Freeform enabled** on the project; then available on freeform templates AND Connected Templates. Data tab, under **Queries** (Pinned Queries) | In the Data tab, save a query, then Repeater `items` picks it | `{ type: "contentstack_queries", value: { queryUID: "<uid>", path: {…} } }` |
| `component_props` | Anywhere: component's registered `defaultValue` OR the Data tab's **External Data** | Registration path (`registerComponent`) or Data tab External Data | `{ type: "component_props", value: "<propName>" }` |

`path` is a nested-object leaf structure: `{ products: { 0: { url: {} } } }` reads `products.0.url`. The path is flattened at resolution. `{ products: {} }` and `{ products: { "": {} } }` are equivalent.

### Authoring UX: the same for every binding kind

**No inline click-to-edit exists on the canvas for any binding kind.** Every value edit happens in the right panel:

- **Static bindings**: edited in the **Settings** tab. Type into the prop input. The literal writes to `binding.value`.
- **Template bindings**: edited via the **Data Picker** in Settings (pick a different field on the connected entry). The rendered value itself is read-only: to change the underlying content, edit the connected entry in the CMS.
- **Pinned bindings** (`contentstack`, `contentstack_queries`): the pin itself is set up in the **Data** tab, which requires Freeform enabled on the project. With it on, Connected Templates can pin too. Once pinned, bindings reference it through the Data Picker in Settings. Rendered values are read-only from Studio's perspective. Edit the source entry in the CMS to change them.

### Context mismatches: the real trap

Picking a binding type that doesn't fit the composition's context is silent. The shape is valid, but resolution returns `undefined` at render:

| Mismatch | Symptom | Fix |
|---|---|---|
| `template` binding in a **Freeform** template | Binding never resolves. Freeform has no page-level entry to source from | Use `contentstack` (pinned entry) or `contentstack_queries` (pinned query) via the Data tab, or `static_value` for a literal |
| `contentstack` / `contentstack_queries` binding in a **Connected** template | The binding works, but it bypasses the connected entry. You've hard-pinned data that should come from the page. Usually a mistake | Use `template` with a path into the connected entry's schema |
| `repeater` binding used on a node NOT inside a Repeater | `repeaterUID` refers to a scope that doesn't exist above the node, resolves to `undefined` | Place the node inside the referenced Repeater's `slots`, or switch to a `template`/`contentstack` binding matching the current scope |

## Node anatomy: where bindings and children actually live in the `ui` tree

Node shape (canonical Repeater example, binding wrapper included):

```jsonc
{
  "type": "<node-type>",          // "repeater" / "condition-block" / a registered component type
  "uid": "<unique-id>",
  "metadata": {                   // node-level metadata
    "mode": "preview"             //   - Repeater: "preview" vs implicit Design Mode
    // "condition": { ... }       //   - Condition Block: discriminator (see below)
  },
  "props": {                      // bindings live HERE — one per prop
    "<propName>": {
      "binding": { "type": "<one of the 6 binding types>", "value": { /*…*/ } },
      "value": "<static fallback if any>"
    },
    // CONTAINER nodes ONLY — wire the child slot to the built-in's slot-typed
    // `children` prop, or children never render (see point 4):
    "children": { "type": "slot", "slot": "<slot-uid>" }
  },
  "slots": {                      // children go HERE, grouped by slot uid (NOT a flat `children` array)
    "<slot-uid>": [               // …this uid MUST equal props.children.slot above
      { /* child node */ }
    ]
  }
}
```

Eight things to internalize:

0. **Every node carries the full envelope (`uid`, `type`, `props`, `metadata`, `slots`, `attrs`, `styles`) even when empty.** `metadata` is not only for Repeater `mode` and Condition `condition`: the renderer reads `metadata.visible` on **every** node, so a leaf authored without the key throws `Cannot read properties of undefined (reading 'visible')` and the whole canvas renders `Component Loading Error`, no partial paint, no indication of which node. **A missing `slots` fails differently and worse, because the canvas still looks fine.** `Node.isNode` requires a truthy `slots`, so a slots-less node is not recognized as a node at all: tree walkers skip it silently (its props never appear in the Data tab), and any walker handed it as its ROOT crashes on `Object.entries(undefined)`. Measured: `Pricing Systems Cards` carried 4 slots-less atoms. Clicking one white-screened Studio's Data tab through `collectComponentProps`, with no error boundary to catch it. The section rendered perfectly on canvas and on the site the whole time. Leaves need `"metadata": {}` and `"slots": {}` exactly as containers do. The minimum leaf, copied from a production section:

```jsonc
{
  "uid": "1v7tfQQBhdETYAN",
  "type": "alpha-atom-heading",
  "attrs": {},
  "metadata": {},                 // ⛔ required even when empty
  "slots": {},                    // ⛔ required even when empty
  "props": { /* … */ },
  "styles": { "default": { "classes": [""], "responsiveStyles": { "default": {} } } }
}
```

0a. **A `choice` value is stored as a LIST, every other type as a scalar.** `"value": ["h1"]`, not `"value": "h1"`. Measured across production `static_value` buckets: `choice` is a list in **938** entries against 18 stray strings, while `boolean` is a bare bool (180), `text` a bare string (582) and `number` a bare int (39).

**This fails in the worst possible way: it renders correctly and configures wrongly.** The renderer accepts the bare string, so the canvas shows the right 72px heading and every visual check passes. Studio's Settings panel matches the stored value against the registered `options`, finds no match for a string, and displays **`Select…`**, so the author sees Tag, Size Variant and Color as unset on a node that looks finished, and re-picks them by hand. Neither a screenshot nor a computed-style assertion catches it. Only reading the entry back does.

```jsonc
"choice":  [ { "key": "<uid>-tag", "value": ["h1"] } ],   // ✅ list
"boolean": [ { "key": "<uid>-wrap", "value": true } ],    // ✅ scalar
"text":    [ { "key": "<uid>-text", "value": "80%" } ]    // ✅ scalar
```

0b. **Write EVERY registered prop, not only the ones the design dictates.** An unwritten prop still renders (it falls back to the registration default) but Studio's Settings panel shows it **blank**, so the author sees a half-configured node and fills the dropdowns by hand. That is the API author's omission surfacing as manual work downstream. For each registered prop: use the comp's value if the design determines one, otherwise write the registration's own `defaultValue` explicitly. Only a prop the registration declares with **no** `defaultValue` may stay unset. Measured on one section, this took the node count from 64 written props to 135. The other 71 were defaults the panel had been showing as empty.

0c. **Name the layer and mark it visible.** Studio reads `metadata.title` as the layer name in the Layers tree. With no title the tree reads as repeated type names (`Stack / Box`, `Stack / Box`, `Stack / Box`) and is unnavigable. Give each node a purpose-name: `Stack — Card content`, `CTA — Read the full story`. Production nodes also carry `visible: true` and `locked: false`, and the root `page` node carries `metadata.sectionExposedProps: []`.

```jsonc
"metadata": {
  "title": "Card Shell — Stat card",   // layer name in the Layers panel
  "visible": true,
  "locked": false
}
```

**`attrs` is where the panel's Attributes section keeps the ID and custom attributes** (`"attrs": { "id": "car-stat-card" }`). Across 650 production nodes it is empty on every one, and the components verified here do not spread it to the DOM, so set it when you want the ID field pre-filled in the panel, and don't rely on it reaching the rendered markup.

1. **Bindings are at `props.<propName>.binding`.** Not directly on the node, not in a flat `bindings` map.
2. **Children are in `slots.<slot-uid>: [...]`.** Not a `children` array. Each slot has a uid. Child nodes live inside the array under that uid.
3. **Discriminators live in `metadata`.** Condition Block's `condition` and Repeater's `mode` are both `metadata.<key>`, not top-level node fields.
4. **Container nodes must ALSO wire `props.children` to their slot: putting children in `slots` alone is not enough.** Every built-in container exposes a **slot-typed prop** in its definition: `page`, `section`, `box`, `columns`, `rows`, `repeater`, and `condition-block` all declare `children: { type: "slot" }`. The SDK fills that prop only when the node points at the slot: `props.children = { "type": "slot", "slot": "<uid>" }`, with `<uid>` matching a key in `slots`. Omit the pointer and the prop resolves to `undefined`: the container renders empty even though the child nodes sit in `slots`. A Repeater is the sharpest trap: it still iterates (N `<div data-composable-studio-wrapper="repeater">` wrappers appear in the DOM), but clones **zero** children into each, so it renders blank with no error. (The `page` node in every working composition carries `props.children`. Mirror it on every container you author.) A registered component with a `slot`-typed prop is wired the same way, under whatever name the registration gave the slot prop.

### Built-in node `type` values

These are the built-in `type` strings the SDK ships with. Anything else must be a component you registered via `registerComponent`.

| Group | `type` values (the palette label and its `type` string) |
|---|---|
| System | `page` |
| Basic: text | `header` · `plain-text` · `collapsible-text` · `rich-text` · `text` · `number` · `json-rte` |
| Basic: button/link | `button` · `link` · `link-container` |
| Media | `image` · `video` · `embed` |
| Container / layout | `section` · `box` · **`hstack`** (palette: Columns) · **`vstack`** (palette: Rows) · `fragment` |
| Composition primitives | `condition-block` · `section-slot` |
| Iteration | `repeater` |
| HTML | `html-element` · `style-sheet` |

Palette labels are author-facing. `type` strings are what appear in the `ui` tree. **Non-obvious pairings:** palette Columns becomes `hstack`, palette Rows becomes `vstack`. Inspect a UI-authored composition (decode `ui`, see [`troubleshoot-canvas`](troubleshoot-canvas.md) § Diagnostic tooling) to confirm the exact `type` string before hand-authoring a node of that kind.

None of these support inline click-to-edit on the canvas. All value edits go through the right panel (both built-ins and BYOC, see [`build-section-component-choice`](build-section-component-choice.md) § Basic field components vs custom registered components).

## Binding a Repeater: the shapes that actually work

Copy these from a working composition in the target project rather than inferring them. The path shape differs per field kind and a wrong one yields **zero iterations** with no error.

| Iterating | `items` binding path | `metadata.repeaterBindingFieldType` |
|---|---|---|
| A modular-block field | `{"page_sections": {}}`, plain | `"modular_block"` |
| A multi-reference field | `{"edge_card": {"": {}}}`, note the `{"": {}}` leaf | `"reference"` |

Also required on the Repeater: `metadata.mode: "preview"`, or the canvas shows one placeholder while production renders N.

**Worked failure.** A carousel repeater bound with the reference shape (`{"case_study_cards": {"": {}}}`) over a modular-block field rendered **0** cards. The same tree with the plain path and `repeaterBindingFieldType: "modular_block"` rendered all **6**, with each Condition Block routing to its branch. Nothing in the entry data or the panel indicated which shape was wrong. The Layers panel read "Iterates Case Study Cards" in both cases.

**Scope the section at the content type root when the repeated field is top-level.** A `linked_schemas` entry of `{content_type_uid}` alone makes root fields addressable. Adding `selected_field` narrows the scope to that field, after which a path naming the same field no longer resolves.

**Verify a `resolvedReferences` path against the API before assuming it is wrong.** The paths feed `include[]`, so they are directly testable:

```bash
curl ".../entries/<uid>?include[]=<mb_field>.<block_uid>.<ref_field>"
```

A resolved object back means the path is right and the gap is elsewhere. Measured on one project: `case_study_cards.case_study_card_with_image_statistics.card` resolved fully, while `case_study_cards.card` and `card` returned null, confirming the `<mb_field>.<block_uid>.<ref_field>` form. **A reference nested inside a repeated modular block resolved through the API but did not resolve in the canvas**, so every prop behind it fell back to its registration default. When a block's only field is a reference, that blocks all of its content, worth checking early, because no amount of path fixing helps.
