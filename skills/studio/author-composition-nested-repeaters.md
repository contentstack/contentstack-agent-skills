---
name: author-composition-nested-repeaters
---

## When to use

Worked recipe for nested Repeaters: a list inside each iterated item, and the `repeaterUID` chain that makes the inner scope resolve.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Recipe: Nested Repeaters (a list inside each iterated item)

A Repeater inside another Repeater's iteration, e.g. a footer with multiple **columns**, each column having its own **links** list. The outer Repeater iterates columns. The inner Repeater iterates each column's links. The trick is the inner Repeater's `items` binding: it must reach into the **outer iteration's current item** to find that column's `links` array, which means `type: "repeater"` (with the outer's `repeaterUID`), not `type: "template"`.

### The two binding shifts

| Node | `items` binding `type` | `value` | What it resolves to at runtime |
|---|---|---|---|
| **Outer Repeater** (`R-outer`) | `template` | `{ path: { footer_columns: {} } }` | `dataSources.template.footer_columns` (the array on the parent entry) |
| **Inner Repeater** (`R-inner`) | **`repeater`** | `{ repeaterUID: "R-outer", path: { links: {} } }` | `dataSources.repeater.R-outer.context.links` (each outer iteration's `links` field) |
| **Inner card props** | `repeater` | `{ repeaterUID: "R-inner", path: { label: {} } }` | `dataSources.repeater.R-inner.context.label` (each link's `label`) |

Repeater-scoped bindings resolve as `dataSources.repeater.<repeaterUID>.context.<path>`. So the inner Repeater's items binding correctly reads the outer iteration's current `links`, and the inner card's bindings read each link inside that.

### Assembled

```jsonc
{ "type": "repeater", "uid": "R-outer",
  "metadata": { "mode": "preview" },
  "props": {
    "items": { "binding": {
      "type": "template",
      "value": { "path": { "footer_columns": {} } }
    } },
    "children": { "type": "slot", "slot": "<R-outer-slot>" }   // ← wires the slot below
  },
  "slots": { "<R-outer-slot>": [
    /* outer iteration body — one column */
    { "type": "site-column-header", "uid": "CH1",
      "props": { "title": { "binding": {
        "type": "repeater",
        "value": { "repeaterUID": "R-outer", "path": { "heading": {} } }
      } } } },
    { "type": "repeater", "uid": "R-inner",
      "metadata": { "mode": "preview" },
      "props": {
        "items": { "binding": {
          "type": "repeater",                                    // ← NOT template
          "value": { "repeaterUID": "R-outer",                   // ← outer's UID
                     "path": { "links": {} } }                   // ← path on outer's iteration item
        } },
        "children": { "type": "slot", "slot": "<R-inner-slot>" }
      },
      "slots": { "<R-inner-slot>": [
        { "type": "site-footer-link", "uid": "L1",
          "props": {
            "label": { "binding": { "type": "repeater",
                       "value": { "repeaterUID": "R-inner", "path": { "label": {} } } } },
            "href":  { "binding": { "type": "repeater",
                       "value": { "repeaterUID": "R-inner", "path": { "href": {} } } } }
          } }
      ] } }
  ] } }
```

Both Repeaters carry `props.children` pointing at their own slot. Without it the Repeater iterates but renders nothing ([`author-composition-repeater-recipes`](author-composition-repeater-recipes.md) step 2).

### Source-type combos

| Source-type combo | Extra prerequisites |
|---|---|
| group-multiple (e.g. `footer_columns`) containing group-multiple (`column.links`) | (nothing extra), inline values both ways |
| group-multiple containing multi-reference (e.g. column.related_entries) | Add `data_sources.resolvedReferences` for the nested reference path (e.g. `"root.footer_columns.0.related_entries": ["footer_columns.related_entries"]`). Add Condition Block as immediate child of `R-inner`. |
| multi-reference containing group-multiple (e.g. category.products[].images) | `resolvedReferences` for the outer reference (`root.products`). Condition Block as child of `R-outer`. Inner iteration is over the (inline) `images` group-multiple, no extra prerequisites for `R-inner`. |
| multi-reference containing multi-reference | `resolvedReferences` entries for BOTH the outer reference AND each inner reference path, inner path is `<outer_ref>.<inner_ref>`, with **no** content-type uid between them (§ [Where a reference path must terminate](author-composition-repeater-recipes.md#reference-path-termination)). Condition Block in both Repeaters. |
| **Modular Block with a reference inside a block** (e.g. `blocks[].feature_block.related_products`) | `resolvedReferences` path must include the **block uid** segment, `"blocks.feature_block.related_products"`, NOT `"blocks.related_products"`. Condition Block per block uid on the Repeater. See § Modular Block to reference: the block-uid segment below. |

The decision tree from the single-level recipes (group-multiple vs reference) applies per Repeater independently: outer's source determines what `R-outer` needs. Inner's source determines what `R-inner` needs.

### Modular Block to reference: the block-uid segment

**The trap:** a Modular Block field whose blocks each contain a reference (`MB → Ref` in every block). A Section linked to the MB renders its blocks, bindings look correct in the picker, and the referenced content inside each block renders nothing.

A modular-block item is shaped `{ <block_uid>: { …fields } }`. That block-uid level does **not** exist for a group-multiple, so the group shape (`footer_columns.related_entries`, one row up) generalizes wrong here: write `blocks.feature_block.related_products`, never `blocks.related_products`.

Omitting the block uid fails silently, for the reason given in § [Where a reference path must terminate](author-composition-repeater-recipes.md#reference-path-termination). Read that first if this is new to you. It is also where the numeric-prefix and CT-uid rules live.

**Where it goes:** on the **parent template** composition, keyed `"template"`, never on the Section composition, even though the reference is nested inside the Section's linked field. Same placement rule as every other reference iteration ([`author-composition-sections`](author-composition-sections.md) § Authoring a Section composition: scoping rules).

```jsonc
// Template composition — MB field `blocks`, block uid `feature_block`,
// reference field `related_products` inside that block.
"data_sources": "[{\"uid\":\"template\",\"data\":null,\"resolvedReferences\":{\"template\":[\"blocks.feature_block.related_products\"]}}]"
```

One entry **per block uid** that contains a reference. Blocks are independent shapes, so a second block with its own reference needs its own path.

### The key pitfall

Setting the inner Repeater's `items` binding to `type: "template"` with path `{ footer_columns: { 0: { links: {} } } }` is the **nested-`.0.` trap**, same family as the "all cards identical" fixed-index (`.0.`) trap, but one level up. A fixed index doesn't substitute. Inner repeater would always read column-0's links, so every outer iteration's links list is identical. Use `type: "repeater"` with the outer UID instead.
