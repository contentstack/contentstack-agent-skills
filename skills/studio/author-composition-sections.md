---
name: author-composition-sections
---

## When to use

Author a Section composition by API: the scoping rules, `selectedField` priority, the `section-slot` node shape, and the wrapper + section-slot pattern.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Authoring a Section composition: scoping rules

So far the recipes have been about page-level compositions (Templates). Authoring **Section** compositions via API has its own contract: sections have **no data of their own**, so how they get the right scope at runtime is non-obvious.

> **STOP before writing the section: ask the Repeater question.** If its `selected_field` is a `multiple: true` group, global field, file or link, ask the user *"This field holds multiple items. Should the section show every item (adds a Repeater) or one item?"* and wait. Ask even when the request seems to imply an answer: Studio asks every time. The answer sets `cardinality` and the root Repeater ([`understand-linked-schemas`](understand-linked-schemas.md)). Never ask for a reference, modular-block, single-value or whole-entry section.

### How a Section gets data when placed on a Template

A Section composition is data-less when authored standalone (its own canvas has nothing to bind against). It only gets data when **placed inside a Template**. The Template hands it a scoped slice of the page entry.

The SDK's scoping pipeline:

```
Section's dataSources.template = <scoped slice of pageEntry at selectedField, with references resolved>
```

- **`selectedField` empty/absent** makes the section's `template` the **whole page entry** (with any reference following). Use this when a section reads multiple fields off the page.
- **`selectedField` = "products"** makes the section's `template` the **`products` field's value** (an array, with references resolved). Use this when a section iterates one field.
- **`selectedField` = "hero.cta"** (dotted path) traverses. Each segment can drill into nested groups or follow references.
- **`selectedField` does NOT traverse array indices.** The dotted path drills nested Groups and single references, but a **numeric** segment into a multi-value field (`modular_blocks.1.…`, `products.0.…`) resolves the section's `template` to `null` (verified: `section_scoped_data[uid].template` came back `null`, whole section blank). To iterate an array nested inside a Modular Block or at a fixed index, leave `selectedField` **empty** (whole-entry scope) and put the full indexed path on the Repeater's `items` binding instead: `value.path = { "modular_blocks": { "1": { "image_grid": { "image": {} } } } }`. The binding-path flattener keeps numeric keys even though the scoping walk does not. Reserve `selectedField` for top-level Group / reference fields.

This means the section's own canvas always shows **one empty placeholder** (no data exists standalone). That's not a bug. The section only fills out at template-rendering time. (See `build-section` for the UI-side framing.)

### Where `selectedField` is read from: three sources, in priority order

The runtime (SSR) and the editor BOTH read in this order:

1. **`node.metadata.sectionBindingOverride.selectedField`**: set on the template's `section-composition` node when API-placing the section
2. **`node.metadata.selectedField`**: legacy fallback on the same node
3. **The section's `linked_schemas` default**: declared on the section composition itself: `[{ content_type_uid: "<page-ct>", selected_field: "<field>" }]`

The Studio web UI sets all three correctly when you drag a section onto a template. API authors set them explicitly.

### The `linked_schemas`-as-reference trap

The compositions CT's `linked_schemas` MUST be a **group-multiple** field, NOT a reference field. If it's a reference field, the CMA **silently drops** any `{content_type_uid, selected_field}` object you `PUT` to it, every read comes back `linked_schemas: []`. The editor reads `linked_schemas` to derive the `UPDATE_SECTION_CONTEXTS` push that scopes each placed section instance. An empty `linked_schemas` means an empty scope push, meaning the editor canvas shows blank repeaters even though `fetchCompositionData` (runtime) renders correctly via the override.

Two outcomes from this:

- **Proper fix:** model `linked_schemas` as a group-multiple on the compositions CT. See `provision-studio-project` for the CT field schema. This makes every UI-driven path work without manual overrides.
- **Runtime escape hatch (if you can't change the CT shape right now):** set `metadata.sectionBindingOverride` on each template's `section-composition` node:
  ```jsonc
  {
    "type": "section-composition",
    "uid": "INST-1",
    "metadata": {
      "compositionUID": "<the-section's-entry-uid-blt…>",
      "sectionBindingOverride": { "selectedField": "products" }
    }
  }
  ```
  This makes the runtime/SSR path correct (the SDK honors it). The editor canvas will still show blank repeaters until `linked_schemas` is also populated. So this escape hatch covers production rendering but doesn't unblock editor authoring: both must agree.

### The editor vs runtime asymmetry (in detail)

| Path | What it reads | Where it happens |
|---|---|---|
| **Runtime / SSR** (`sdk.fetchCompositionData`) | `sectionBindingOverride.selectedField` first, then `metadata.selectedField`, then the `linked_schemas` default | SDK data collection |
| **Editor canvas** (live editing in Studio web app) | `UPDATE_SECTION_CONTEXTS` push from the Studio web app, derived from the section's `linked_schemas` field. `sectionBindingOverride` is also honored as an override on top. | Studio web app messaging |

So you can have a section that renders perfectly on the deployed site (runtime path uses the override) yet shows empty repeaters in the editor (editor path's `linked_schemas` is empty). Both metadata paths must point to the same `selectedField` for editor + runtime to agree.

### Recipe: section iterates one field on the page

When a section's `selectedField` is set to the iterated field (e.g. `selectedField: "products"` and the section's job is to render one card per product), the section's `dataSources.template` IS the products array. **A top-level Repeater inside the section must bind to scope-root, NOT to `{ path: { products: {} } }`**:

```jsonc
{
  "type": "repeater",
  "uid": "R-section-products",
  "metadata": { "mode": "preview" },
  "props": {
    "items": {
      "binding": {
        "type": "template",
        "value": { "path": {} }      // ← scope-root, NOT { products: {} }
      }
    },
    "children": { "type": "slot", "slot": "<R-slot>" }   // ← required, wires the slot below
  },
  "slots": {
    "<R-slot>": [
      // ConditionBlock + card here, per the multi-reference recipe;
      // card bindings still use type:"repeater" with repeaterUID
    ]
  }
}
```

`getBindingStringForCS` flattens `{path: {}}` to `""`, so the binding resolves to `dataSources.template` directly. With `selectedField: "products"`, that IS the products array. A path of `{products: {}}` would resolve to `dataSources.template.products`, undefined when the section's template IS the array, not an object containing one.

Reference iterations still need `data_sources.resolvedReferences` on the composition: key `"template"`, value is the array of field paths on the parent entry (e.g. `"template": ["products"]`). The runtime resolves these along the `selectedField` path. You set them on the parent (template) composition, not the section composition.

### Decision rule: single-field repeater section vs whole-entry section

| Section's job | `selectedField` | Repeater binding (if any) | When to use |
|---|---|---|---|
| One repeater over one field of the page (a card grid, a feature list) | Set to that field (`"products"`) | Scope-root `{ path: {} }` | Most reusable sections: Editions list, Features grid, Card grid |
| A custom component reading several fields off the page entry (header reading brand + nav_links + signin_label. Hero reading the `hero` group) | **Leave unset**: section's `template` is the whole page entry | Original `template.<field>` paths work verbatim | Single-purpose sections with no iteration: Header, Hero, static 3D block |

The choice is data-shape-driven: one field iterated calls for `selectedField` plus a scope-root. Many fields read calls for whole-entry scope and the original paths.

### Verifying a section's scope headlessly

The section's own canvas can't confirm binding correctness (no data exists standalone). Use the SSR cold-load instead:

```js
const spec = await sdk.fetchCompositionData({ url: "/<some-page-using-the-section>" });
console.log(JSON.stringify(spec.data.section_scoped_data["<instance-uid>"], null, 2));
//   → { selectedField: "products", parentRepeaterUID: null,
//       template: [<resolved entry 1>, <resolved entry 2>, ...] }
```

`spec.data.section_scoped_data[<instance-uid>]` is the runtime resolution: `selectedField` + the actual scoped `template` array. If `template` shows the right array length and right entry sample, the section's scope is correct. If it's `undefined` or wrong-shaped, the bindings won't work.

## `section-slot` node shape: the one legitimate empty-slots node

The built-in `section-slot` type declares a **placeholder** inside a section's `ui`. The template that embeds this section then fills the slot via a `section-composition` node (see next recipe: Pattern B). Non-obvious shape:

```jsonc
{
  "type": "section-slot",
  "uid": "SS1",
  "props": {},
  "slots": { "SS1": [] }        // ← key is the node's OWN uid; value is [] until filled
}
```

Two things that trip API authors:

1. **`slots.<own-uid>: []` is required**: the section-slot's own uid appears as the slot key, with an empty array. This is one of only two legitimate exceptions to the preflight rule "no empty slot arrays". The other is the page-side `section-composition` node, where Studio writes `slots.<section-slot-uid>: []` for each slot the template hasn't filled yet. Omitting the entry (no `slots` at all, or `slots: {}`) leaves the template unable to target the slot when composing.
2. **The slot is filled by the TEMPLATE, not the section.** In the section's authored tree the slot stays empty. The template's `section-composition` node holds the fill in its own `slots`, keyed by the section-slot uid ([Pattern B](author-composition-section-slot-fill.md)).

Section slots typically sit inside a Repeater + Condition Block on the wrapper section (Pattern B for reference / MB iteration) or directly under the section root (Pattern B for a simpler single-slot section).

## Pattern B: wrapper + `section-slot`, filled by another Section

When the leaf content belongs in its own Section (reused across wrappers, different per content type, or swapped per template), a wrapper List Section exposes a `section-slot` per item and the template fills it. Recipe and node trees: [`author-composition-section-slot-fill`](author-composition-section-slot-fill.md).
