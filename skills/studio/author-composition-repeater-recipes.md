---
name: author-composition-repeater-recipes
---

## When to use

Worked recipes for repeating a card over a multi-reference field and over a GROUP-MULTIPLE field, with the full node trees.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

<a id="canonical-list-recipe"></a>

## The canonical list recipe {#canonical-list-recipe}

Every list Section uses this one shape. Other files link here instead of restating it.

1. **Scope the Section to the whole entry.** `linked_schemas: [{ "content_type_uid": "<page-ct>" }]`, no `selected_field`. A Section scoped to the list field renders, but Visual Editor finds no list or item tags ([`make-visual-editor-editable`](make-visual-editor-editable.md) § 2).
2. **A list Box holds the Repeater.** It carries `metadata.repeaterWrapper: true` (the list tag `<field>` lands on it) and the list layout: flex or grid with `gap` ([`build-repeating-section`](build-repeating-section.md) § The Repeater's wrapper element).
3. **The Repeater binds to the field**: `items` = `template` binding on `{ "<field>": {} }`, `metadata.mode: "preview"`, `metadata.repeaterBindingFieldType` per [`author-composition-bindings`](author-composition-bindings.md) § Binding a Repeater.
4. **An item Box is the Repeater's only child.** The item tag `<field>.<N>` lands on it. Without it, a Condition Block holding a Section or Section Slot drops every item tag.
5. **Condition Blocks go inside the item Box**, one per content type (references) or block uid (modular blocks), each with `operator` and `conditionBinding`. Group-multiple, multi-file and scalar lists skip this step: the card goes straight into the item Box.
6. **Card bindings** use `type: "repeater"` with the Repeater's `repeaterUID`, paths relative to the item.

The section's full `ui` tree for a multi-reference `products` field, every node with all seven keys:

```json
{
  "uid": "ROOT",
  "type": "page",
  "attrs": {},
  "metadata": { "title": "Product Grid", "sectionExposedProps": [] },
  "props": { "children": { "type": "slot", "slot": "ROOT-slot" } },
  "slots": {
    "ROOT-slot": [
      {
        "uid": "LIST",
        "type": "box",
        "attrs": {},
        "metadata": { "title": "Box — Product list", "repeaterWrapper": true },
        "props": { "children": { "type": "slot", "slot": "LIST-slot" } },
        "slots": {
          "LIST-slot": [
            {
              "uid": "R1",
              "type": "repeater",
              "attrs": {},
              "metadata": { "title": "Repeater — Products", "mode": "preview", "repeaterBindingFieldType": "reference" },
              "props": {
                "items": { "binding": { "type": "template", "value": { "path": { "products": {} } } } },
                "children": { "type": "slot", "slot": "R1-slot" }
              },
              "slots": {
                "R1-slot": [
                  {
                    "uid": "ITEM",
                    "type": "box",
                    "attrs": {},
                    "metadata": { "title": "Box — Product item" },
                    "props": { "children": { "type": "slot", "slot": "ITEM-slot" } },
                    "slots": {
                      "ITEM-slot": [
                        {
                          "uid": "CB1",
                          "type": "condition-block",
                          "attrs": {},
                          "metadata": {
                            "title": "Condition — product",
                            "condition": {
                              "type": "reference", "operator": "eq", "value": "product",
                              "conditionBinding": { "type": "repeater",
                                "value": { "repeaterUID": "R1", "path": { "_content_type_uid": {} } } }
                            }
                          },
                          "props": { "children": { "type": "slot", "slot": "CB1-slot" } },
                          "slots": {
                            "CB1-slot": [
                              {
                                "uid": "CARD1",
                                "type": "site-product-card",
                                "attrs": {},
                                "metadata": { "title": "Product card" },
                                "props": {
                                  "title": { "binding": { "type": "repeater", "value": { "repeaterUID": "R1", "path": { "title": {} } } } },
                                  "price": { "binding": { "type": "repeater", "value": { "repeaterUID": "R1", "path": { "price": {} } } } }
                                },
                                "slots": {},
                                "styles": {}
                              }
                            ]
                          },
                          "styles": {}
                        }
                      ]
                    },
                    "styles": {}
                  }
                ]
              },
              "styles": {}
            }
          ]
        },
        "styles": {
          "default": {
            "classes": [""],
            "responsiveStyles": { "default": { "display": "grid", "gridTemplateColumns": "repeat(3, minmax(0, 1fr))", "gap": "24px" } }
          }
        }
      }
    ]
  },
  "styles": {}
}
```

The composition also needs `data_sources` with `resolvedReferences` `{ "template": ["products"] }` (step 1 below). A modular-blocks list swaps the condition to `"type": "modular_block"` with the block uid ([step 4](#4-condition-block-inside-the-item-box)) and `repeaterBindingFieldType` to `"modular_block"`.

**Expected validator warning.** The Compositions API validator warns on the item Box that the Repeater's items won't render. On this shape the warning is expected and wrong: leave the Box in place. It is a warning, not a `422`, and the items render (see [`use-compositions-api`](use-compositions-api.md) § Expected validator warnings).

The recipes below explain each piece.

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

Shown parsed. On the raw CMA `data_sources` is a **JSON-encoded string**, on the Compositions API a plain array: [`author-composition-entry`](author-composition-entry.md#wire-shapes) § Wire shapes.

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

A Section scoped to the reference itself (`selectedField: "products"`) would need scope-root `{ "path": {} }`, because its `dataSources.template` is already the array. Don't author new Sections that way: it drops the Visual Editor list tags. Use the whole-entry scope of the [canonical list recipe](#canonical-list-recipe).

### 3. Repeater node's `metadata.mode: "preview"`

On the same Repeater node, in `metadata` (parallel to `props`). Per `use-repeater`'s two-mode model: Design Mode (default) renders one placeholder. Preview Mode renders N real iterations. UI authors toggle this in Properties, under Configuration. API authors set the metadata directly. See the Repeater node shape in step 2 above for placement.

### 4. Condition Block inside the item Box

Required for reference iteration (single-CT AND multi-CT, `use-condition-block`). Narrows the iteration item to a specific content type before child bindings resolve.

The Condition Block sits in the slot of the item Box that is the Repeater's only child ([canonical list recipe](#canonical-list-recipe), step 4). Its discriminator is in `metadata.condition`. The Repeater's `slots`, from the item Box down:

```jsonc
"slots": {
  "R1-slot": [
    {
      "type": "box", "uid": "ITEM", "attrs": {}, "metadata": {}, "styles": {},
      "props": { "children": { "type": "slot", "slot": "ITEM-slot" } },   // ← the item Box
      "slots": {
        "ITEM-slot": [
          {
            "type": "condition-block",
            "uid": "CB1", "attrs": {}, "styles": {},
            "metadata": {
              "condition": {
                "type": "reference", "operator": "eq", "value": "product",
                "conditionBinding": { "type": "repeater",
                  "value": { "repeaterUID": "R1", "path": { "_content_type_uid": {} } } }
              }
            },
            "props": { "children": { "type": "slot", "slot": "CB1-slot" } },   // ← Condition Block needs it too
            "slots": { "CB1-slot": [ /* card subtree here — step 5 */ ] }
          }
        ]
      }
    }
  ]
}
```

Without `conditionBinding` the block silently renders nothing. Design mode hides this: verify in preview.

For modular-block iteration the condition reads the block uid, and carries a `dataBinding` of the same shape:

```json
"condition": {
  "type": "modular_block", "operator": "eq", "value": "<block-uid>",
  "conditionBinding": { "type": "repeater", "value": { "repeaterUID": "R1", "path": { "<block-uid>": {} } } },
  "dataBinding":      { "type": "repeater", "value": { "repeaterUID": "R1", "path": { "<block-uid>": {} } } }
}
```

All three container nodes (Repeater, item Box, Condition Block) carry `props.children` pointing at their own slot ([`author-composition-bindings`](author-composition-bindings.md) § Node anatomy, point 4). The Condition Block also exposes a `children` slot prop. Skip its pointer and the card subtree never renders even though the Repeater iterates correctly.

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
    └── Section "ProductGrid"  (linked_schemas: [{ content_type_uid:"category" }], whole entry)
        └── Box "list"  (metadata.repeaterWrapper:true, grid + gap)
            └── Repeater R1  (items: template path {products:{}}, metadata.mode:"preview")
                └── Box "item"
                    └── Condition Block CB1  (type:"reference", operator:"eq", value:"product",
                        │                     conditionBinding: repeater R1 path {_content_type_uid:{}})
                        └── site-product-card CARD1
                              title: repeater R1 path {title:{}}
                              image: repeater R1 path {images:{0:{url:{}}}}
                              price: repeater R1 path {price:{}}
```

The node-for-node JSON is in [the canonical list recipe](#canonical-list-recipe). Five shapes: composition `resolvedReferences` + Repeater `props.items.binding` + Repeater `metadata.mode` + Condition Block with `metadata.condition` (`conditionBinding` included) + repeater-scope card bindings. Any one missing produces an empty render or an all-identical render.

## Recipe: Repeat a card over a GROUP-MULTIPLE field

Sibling to the multi-reference recipe above, but **simpler**: group-multiple values are inline on the parent entry, so no reference resolution is needed.

Scenario: a `category` entry has a `features` field of type `group` + `multiple: true` (a list of inline objects, each with sub-fields like `headline`, `body`, `icon`). Render one card per feature.

### What's different vs the multi-reference case

| Shape | Multi-reference | **Group-multiple** |
|---|---|---|
| Composition `data_sources.resolvedReferences` | **Required**: reference stubs need resolving | **NOT needed**: values are inline on the parent entry |
| Condition Block inside the item Box | **Required**: references are polymorphic (any allowed CT). The block narrows | **NOT needed**: group-multiple has one shape, not polymorphic |
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
    └── Section "FeatureList"  (whole-entry scope)
        └── Box "list"  (metadata.repeaterWrapper:true, flex / grid + gap)
            └── Repeater R2  (items: template path {features:{}}, metadata.mode:"preview")
                └── Box "item"
                    └── site-feature-card FC1   (no Condition Block)
                          headline: repeater R2 path {headline:{}}
                          body:     repeater R2 path {body:{}}
                          icon:     repeater R2 path {icon:{url:{}}}
```

The card sits **directly inside the item Box**, no Condition Block, because the iteration item has one shape (the group's sub-fields). Each card prop reads from the iteration item via `repeaterUID:"R2"` + the field path on the item.

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
