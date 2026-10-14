---
name: author-composition-repeater-recipes
---

## When to use

Worked recipes for repeating a card over a multi-reference field and over a GROUP-MULTIPLE field, with the full node trees.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Recipe: Repeat a card over a multi-reference field

The canonical pattern. Requires FIVE shapes in concert. Missing any one yields a silently-empty repeater or (worse) an all-items-identical render (the `template`-at-`.0.` trap below).

Scenario: a `category` template (Connected to the `category` CT). Each category entry has a `products` multi-reference field. We want to render one card per referenced product.

### 1. Composition-level: `data_sources.resolvedReferences`

The reference-resolution map. Tells the SDK "when bindings resolve through this reference path, materialize each stub into a real entry":

```jsonc
"data_sources": [
  {
    "uid": "template",
    "data": null,
    "resolvedReferences": {
      "template": ["products"]
    }
  }
]
```

Example: a section (Card Grid) that iterates `related_posts`:

```json
"data_sources": "[{\"uid\":\"template\",\"data\":null,\"resolvedReferences\":{\"template\":[\"related_posts\"]}}]"
```

**Wire format quirk:** on the CMA `data_sources` is stored as a **JSON-encoded string** (`"[]"`, `"[{…}]"`), not the parsed array. Serialize before write. Parse after read.

**Key semantics: depends on the data source, and getting it wrong fails silently:**

| Data source | Key | How the SDK reads it |
|---|---|---|
| `template` (the page entry) | Opaque label, Studio writes `"template"` | Flattens `Object.values(resolvedReferences)`, key content is ignored |
| `contentstack` (pinned entries) | **Must be the entry uid** | Direct lookup `resolvedReferences[entry.uid]`, a key that doesn't match the entry falls through to `[]` |

Values are the field paths on the parent entry in both cases.

So the "key doesn't matter" rule is **template-scope only**. For pinned entries the key is a lookup, not a label: mis-key it and the SDK finds no paths, adds no includes, and the references stay stubs, with no error, exactly as if you had never set `resolvedReferences` at all.

Without this, reference fields are just `[{uid, _content_type_uid}, …]` stubs at runtime. The iteration sees no items.

#### Where a reference path must terminate: the four shapes {#reference-path-termination}

**One rule, four instances.** A `resolvedReferences` value becomes a CDA `include[]` entry, so it must name a **real, fetchable field chain** ending at the reference (or at the nested field you need resolved). Include every intermediate level, and no segment that isn't a field.

| Source shape | Path to write | Not |
|---|---|---|
| Multi- or single reference on the parent | `products` | - |
| Reference inside a **Modular Block** | `blocks.<block_uid>.<ref_field>` | `blocks.<ref_field>`, block uid omitted |
| Reference inside a **reference** | `carousel.cards` | `carousel.products_carousel.cards`, CT uid leaked |
| **Nested asset** inside a reference | both `hero` **and** `hero.image_options.image` | `hero` alone, scalars resolve, the asset doesn't |
| Reference inside a **group-multiple** | `footer_columns.related_entries` | - (groups add no extra level) |

**Why this matters: every violation fails the same silent way.** A path that doesn't name a fetchable chain would 422 the CDA query, so Studio filters it out before the query is sent rather than letting it error. Nothing warns you. The reference stays a stub, the binding resolves against that stub, and the component renders empty. **A correct-looking binding with missing data is the signature of a bad path, not of a bad binding.**

Two segment types are not fields and must not appear:

- **Array indexes** (`0`, `2`) and the `entries` array-wrapper: the SDK strips both.
- **Reference-target CT uids.** A reference-inside-a-reference produces the inner reference's target CT uid directly after the reference field (`carousel`, then `products_carousel`, then `cards`). Studio drops it positionally: a segment is a discriminator **iff** it is a known CT uid **and** the preceding segment is a reference field whose `reference_to` includes it. That precision is deliberate: the same uid is often also a modular-block uid elsewhere in the path, and a block (having no preceding reference) is correctly preserved.

Numeric prefixes on block segments (`2_feature_block`) are stripped by both Studio and the SDK, so write the plain uid.

### 2. Repeater node's `items` binding: at `props.items.binding`, type `template`

The Repeater consumes its iteration source through its `items` prop:

```jsonc
{
  "type": "repeater",
  "uid": "R1",
  "props": {
    "items": {
      "binding": {
        "type": "template",
        "value": { "path": { "products": {} } }
      }
    },
    "children": { "type": "slot", "slot": "R1-slot" }
  },
  "metadata": { "mode": "preview" },
  "slots": { "R1-slot": [ /* see step 4 */ ] }
}
```

`props.children` is **required**: it wires the `R1-slot` slot to the Repeater's built-in `children` prop. Without it the Repeater iterates but renders nothing ([`author-composition-bindings`](author-composition-bindings.md) § Node anatomy, point 4). The `slots` key MUST match `props.children.slot`.

For a section whose `selectedField` is the reference itself (`build-section`'s scope-aware sections), the path collapses to scope-root `{ "path": {} }`, the section's `dataSources.template` is already the resolved array.

### 3. Repeater node's `metadata.mode: "preview"`

On the same Repeater node, in `metadata` (parallel to `props`). Per `use-repeater`'s two-mode model: Design Mode (default) renders one placeholder. Preview Mode renders N real iterations. UI authors toggle this in Properties, under Configuration. API authors set the metadata directly. See the Repeater node shape in step 2 above for placement.

### 4. Condition Block as the immediate child of the Repeater (under `slots`)

Required by Studio's composition schema for reference iteration (single-CT AND multi-CT, `use-condition-block`). Narrows the iteration item to a specific content type before child bindings resolve.

The Condition Block lives under a slot of the Repeater. Its discriminator is in `metadata.condition`:

```jsonc
{
  "type": "repeater",
  "uid": "R1",
  // …items binding / metadata.mode as in step 2…
  "props": {
    "items": { "binding": { /* …as step 2… */ } },
    "children": { "type": "slot", "slot": "<repeater-slot-uid>" }   // ← wire the Repeater's slot
  },
  "slots": {
    "<repeater-slot-uid>": [
      {
        "type": "condition-block",
        "uid": "CB1",
        "metadata": {
          "condition": {
            "type": "reference", "operator": "eq", "value": "product",
            "conditionBinding": { "type": "repeater",
              "value": { "repeaterUID": "R1", "path": { "_content_type_uid": {} } } }
          }
        },
        "props": {
          "children": { "type": "slot", "slot": "<cb-slot-uid>" }   // ← Condition Block needs it too
        },
        "slots": {
          "<cb-slot-uid>": [
            /* card subtree here — step 5 */
          ]
        }
      }
    ]
  }
}
```

Without `conditionBinding` the block silently renders nothing. Design mode hides this: verify in preview.

For modular-block iteration: `type: "modular_block"`, `value: "<block-uid>"`, `conditionBinding` and `dataBinding` on path `{ "<block-uid>": {} }`.

Both container nodes carry `props.children` pointing at their own slot ([`author-composition-bindings`](author-composition-bindings.md) § Node anatomy, point 4). The Condition Block also exposes a `children` slot prop. Skip its pointer and the card subtree never renders even though the Repeater iterates correctly.

### 5. Card prop bindings: type `repeater`, with `repeaterUID`

**The "all cards identical" trap:** Do NOT use `template` bindings indexed at `.0.<field>` (e.g. `products.0.title`). A fixed `.0.` index does NOT get substituted by the iteration: every iteration renders item 0.

Use repeater-scope bindings: `type: "repeater"`, with `repeaterUID` naming the parent Repeater node, and a path relative to the iteration item (NO index). The card node lives inside the Condition Block's slot:

```jsonc
{
  "type": "site-product-card",     // the registered component's type
  "uid": "CARD1",
  "props": {
    "title": {
      "binding": {
        "type": "repeater",
        "value": {
          "repeaterUID": "R1",
          "path": { "title": {} }
        }
      }
    },
    "image": {
      "binding": {
        "type": "repeater",
        "value": {
          "repeaterUID": "R1",
          "path": { "images": { "0": { "url": {} } } }
        }
      }
    },
    "price": {
      "binding": {
        "type": "repeater",
        "value": { "repeaterUID": "R1", "path": { "price": {} } }
      }
    }
  }
}
```

The `repeaterUID` ("R1" here) tells the SDK at render time which Repeater's current item this binding reads from. The path is on the iteration item itself.

### Assembled

```
Composition entry
├── composable_uid: "<15-char>" (= CMA entry uid)
├── data_sources: [{ uid:"template",
│                    resolvedReferences:{ "template":["products"] } }]
└── ui (zlib-inflated tree)
    └── Section "ProductGrid"
        └── Box  (grid layout — register-component-render-contracts § Layout contract)
            └── { type:"repeater", uid:"R1",
                  metadata:{ mode:"preview" },
                  props:{ items:{ binding:{ type:"template",
                                            value:{ path:{ products:{} } } } } },
                  slots:{ "<R1-slot>":[
                    { type:"condition-block", uid:"CB1",
                      metadata:{ condition:{ …step 4… } },
                      slots:{ "<CB1-slot>":[
                        { type:"site-product-card", uid:"CARD1",
                          props:{
                            title:{ binding:{ type:"repeater",
                                              value:{ repeaterUID:"R1", path:{ title:{} } } } },
                            image:{ binding:{ type:"repeater",
                                              value:{ repeaterUID:"R1", path:{ images:{ 0:{ url:{} } } } } } },
                            price:{ binding:{ type:"repeater",
                                              value:{ repeaterUID:"R1", path:{ price:{} } } } }
                          } }
                      ] } }
                  ] } }
```

Five shapes: composition `resolvedReferences` + Repeater `props.items.binding` + Repeater `metadata.mode` + Condition Block in slot with `metadata.condition` + repeater-scope card bindings. Any one missing produces an empty render or an all-identical render.

## Recipe: Repeat a card over a GROUP-MULTIPLE field

Sibling to the multi-reference recipe above, but **simpler**: group-multiple values are inline on the parent entry, so no reference resolution is needed.

Scenario: a `category` entry has a `features` field of type `group` + `multiple: true` (a list of inline objects, each with sub-fields like `headline`, `body`, `icon`). Render one card per feature.

### What's different vs the multi-reference case

| Shape | Multi-reference | **Group-multiple** |
|---|---|---|
| Composition `data_sources.resolvedReferences` | **Required**: reference stubs need resolving | **NOT needed**: values are inline on the parent entry |
| Condition Block as Repeater's immediate child | **Required**: references are polymorphic (any allowed CT). The block narrows | **NOT needed**: group-multiple has one shape, not polymorphic |
| Repeater `props.items.binding` | `type: "template"`, path at the multi-ref field | (same) `type: "template"`, path at the group-multiple field |
| Repeater `metadata.mode: "preview"` | Required for canvas iteration | (same) Required |
| Card prop bindings | `type: "repeater"`, `repeaterUID`, no index | (same) `type: "repeater"`, `repeaterUID`, no index |

So group-multiple drops to **THREE shapes** (Repeater items binding + Repeater metadata.mode + repeater-scope card bindings). No composition-level resolved-references map. No Condition Block.

### Group-multiple Repeater + card, assembled

```
Composition entry
├── composable_uid: "<15-char>" (= CMA entry uid)
├── data_sources: [/* no resolvedReferences entry needed */]
└── ui (zlib-inflated tree)
    └── Section "FeatureList"
        └── Box  (flex / grid layout — register-component-render-contracts § Layout contract)
            └── { type:"repeater", uid:"R2",
                  metadata:{ mode:"preview" },
                  props:{ items:{ binding:{ type:"template",
                                            value:{ path:{ features:{} } } } } },
                  slots:{ "<R2-slot>":[
                    /* card goes here directly — no Condition Block wrapper */
                    { type:"site-feature-card", uid:"FC1",
                      props:{
                        headline:{ binding:{ type:"repeater",
                                              value:{ repeaterUID:"R2", path:{ headline:{} } } } },
                        body:{     binding:{ type:"repeater",
                                              value:{ repeaterUID:"R2", path:{ body:{} } } } },
                        icon:{     binding:{ type:"repeater",
                                              value:{ repeaterUID:"R2", path:{ icon:{ url:{} } } } } }
                      } }
                  ] } }
```

The card sits **directly inside the Repeater's slot**, no Condition Block in between, because the iteration item has one shape (the group's sub-fields). Each card prop reads from the iteration item via `repeaterUID:"R2"` + the field path on the item.

### Decision rule: which recipe to use

Look at the field's `data_type` on the source CT:

| Field shape | Recipe to use |
|---|---|
| `data_type: "reference"`, `field_metadata.ref_multiple: true` (multi-reference) | Multi-reference recipe, needs `resolvedReferences` + Condition Block |
| `data_type: "reference"`, `field_metadata.ref_multiple: false` (single reference) | Multi-reference recipe minus the Repeater (a single Section drop, not iteration). The reference still needs `resolvedReferences`. |
| `data_type: "group"`, `multiple: true` (group-multiple) | Group-multiple recipe, no `resolvedReferences`, no Condition Block |
| `data_type: "blocks"` (Modular Block) | Multi-reference recipe shape, but Condition Block discriminator is `metadata.condition.type: "modular_block"`, value is the block UID. The MB field itself is inline: it needs **no** `resolvedReferences`. A reference **inside** a block does, and its path must carry the block uid: `blocks.<block_uid>.<ref_field>`. See [`author-composition-nested-repeaters`](author-composition-nested-repeaters.md) § Modular Block to reference: the block-uid segment |
| `data_type: "file"`, `multiple: true` (multi-file) | Multi-reference recipe minus `resolvedReferences` (files don't need resolution). Minus Condition Block (one shape). Like group-multiple. Path uses `.0.url` etc. inside each iteration. |
| `data_type: "<any scalar list>"` (array of strings, numbers, etc.) | Group-multiple recipe shape. Each iteration is one scalar. The card might be a single component reading the scalar via repeater scope |

This is exactly the group-multiple vs reference split: same iteration shape, different prerequisites (`resolvedReferences` + Condition Block) depending on the source.
