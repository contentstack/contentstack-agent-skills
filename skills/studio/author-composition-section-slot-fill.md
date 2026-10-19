---
name: author-composition-section-slot-fill
---

## When to use

Pattern B by API: a wrapper Section iterates a reference or modular-block field and exposes a `section-slot` per item, and the template fills each slot with a separate Simple Section. Phrases: "Pattern B", "fill a section slot by API", "wrapper section with a slot".

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md). Read [`author-composition-sections`](author-composition-sections.md) first: its Repeater question and `section-slot` node shape apply here.

# Pattern B by API: wrapper + `section-slot`, filled by a Simple Section

Sibling to the multi-reference recipe in [`author-composition-repeater-recipes`](author-composition-repeater-recipes.md). Same iteration outcome (one card per reference / MB item), but the leaf content lives in a **separate section composition** rather than in the wrapper's own `ui`. Verified end-to-end for references and modular blocks.

**When to prefer Pattern B over Pattern A (self-contained):**
- Leaf content is reused across multiple wrappers (e.g. an author card shown in blog lists AND author-page hero).
- Leaf content varies per CT and you want each CT's binding tree in its own composition entry.
- You want to swap the fill section per template instance without editing the wrapper.

**Shape overview:**

| Composition | Kind | Role |
|---|---|---|
| Wrapper section | **List Section**: Repeater at root + CB per CT/block, CB slot holds a `section-slot` node | Iterates the reference/MB, emits one slot per item |
| Fill section (one per branch) | **Simple Section**: no root Repeater, `linked_schemas.selected_field` scoped to the reference target CT (or block) | Binds leaf fields |
| Template | Has a `section-composition` node embedding the wrapper. Its `slots.<section-slot-uid>` holds a `section-composition` node for each fill section | Wires the slot to the fill |

## Wrapper section: Repeater + CB + section-slot

```jsonc
// ui tree of the wrapper section
{
  "type": "repeater", "uid": "R1",
  "metadata": { "mode": "preview" },
  "props": {
    "items": { "binding": { "type": "template", "value": { "path": {} } } },
    "children": { "type": "slot", "slot": "<R1-slot>" }      // required, see repeater-recipes step 2
  },
  "slots": { "<R1-slot>": [
    { "type": "condition-block", "uid": "CB1",
      "metadata": { "condition": { "type": "reference", "operator": "eq", "value": "author",
        "conditionBinding": {…} } },   // required, see repeater-recipes step 4
      "props": { "children": { "type": "slot", "slot": "<CB1-slot>" } },
      "slots": { "<CB1-slot>": [
        { "type": "section-slot", "uid": "SS1",
          "slots": { "SS1": [] } }
      ] } }
  ] } }
```

Wrapper section entry also declares `linked_schemas: [{ content_type_uid: "<parent-CT>", selected_field: "<ref-or-mb-field>" }]` (group-multiple field, see [`author-composition-sections`](author-composition-sections.md) § The `linked_schemas`-as-reference trap).

## Fill section: Simple Section per branch

One fill section per allowed CT (references) or block (MB). No root Repeater. Its top-level node is the leaf component. `linked_schemas.selected_field` names the reference target CT (or block schema path) so the SDK scopes each iteration's item into the section's `dataSources.template`.

```jsonc
// ui tree of the fill section (e.g. author-card)
{
  "type": "author-card", "uid": "AC1",
  "props": {
    "name":  { "binding": { "type": "template", "value": { "path": { "name": {} } } } },
    "photo": { "binding": { "type": "template", "value": { "path": { "photo": { "url": {} } } } } }
  }
}
```

Note the fill section's bindings use `type: "template"` (NOT `type: "repeater"`). The wrapper's SDK scoping already unwraps the iteration item into the fill section's `template` scope.

## Template: fill nodes in the placed wrapper's `slots`

The template's `section-composition` node embedding the wrapper holds each fill as a real `section-composition` node in its `slots`, keyed by the section-slot uid. Studio writes this shape when an author fills a slot:

```jsonc
{
  "type": "section-composition",
  "uid": "INST-1",
  "metadata": { "compositionUID": "<wrapper section's entry uid, blt…>" },
  "slots": {
    "SS1": [
      { "type": "section-composition", "uid": "FILL-1",
        "metadata": { "compositionUID": "<author-fill section's entry uid, blt…>" },
        "props": {}, "slots": {}, "attrs": {}, "styles": {} }
    ]
    // one key per CB branch's section-slot uid, each holding its own fill
  }
}
```

Also populate the template's `linked_sections` with references to BOTH the wrapper section entry AND every distinct fill section entry.

## Assembled: reference-iterating wrapper filled by an author fill

```
Wrapper section  linked_schemas: [{ ct: "blog_post", selected_field: "primary_author" }]
  ui: Repeater(items:{path:{}}, mode:"preview")
        └── ConditionBlock(condition:{type:"reference", value:"author", conditionBinding})
              └── section-slot uid:"SS1" slots:{"SS1":[]}

Author fill section  linked_schemas: [{ ct: "blog_post", selected_field: "primary_author" }]
  ui: author-card
        ├── name:  binding template path:{name:{}}
        └── photo: binding template path:{photo:{url:{}}}

Template (blog_post)
  data_sources: [{ uid:"template", resolvedReferences:{ "template":["primary_author"] } }]
  linked_sections: [wrapper-entry-ref, author-fill-entry-ref]
  ui: page → … → section-composition uid:"INST-1"
                    metadata.compositionUID: "<wrapper entry uid>"
                    slots.SS1: [section-composition compositionUID:"<author-fill entry uid>"]
```

MB variant: swap the CB condition to the modular-block form ([`author-composition-repeater-recipes`](author-composition-repeater-recipes.md) step 4). Wrapper's `selected_field` names the MB field. Fill section's `selected_field` names the same MB path plus the block key. Leaf bindings inside the fill section still use `type: "template"`.
