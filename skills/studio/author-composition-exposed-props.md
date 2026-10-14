---
name: author-composition-exposed-props
---

## When to use

Worked recipe for exposed section props: per-instance overrides a template author can set without forking the Section.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Recipe: Exposed section props (per-instance override)

Some sections need to expose a prop the **template** can override per drop instance, a Card Grid whose column count is set by the page, or a Hero whose tone changes per template. Verified end-to-end.

**Two-sided shape**: section declares the exposure. Template supplies the per-instance value.

### Section side: at the ui ROOT

The exposed-props declaration lives on the section's `ui.metadata` (NOT on the individual node). Each entry names one prop on one node, gives it a stable exposure `uid`, and captures the binding at expose time as a fallback:

```jsonc
{
  "type": "page",
  "uid": "<page-uid>",
  "metadata": {
    "sectionExposedProps": [
      {
        "nodeUid": "CARD1",                    // the node inside the section that owns the prop
        "propKey": "tone",                     // the prop being exposed
        "uid": "exp-tone-1",                   // stable identifier — templates reference this
        "displayName": "Card tone",            // label shown on the template's right panel
        "propType": "choice",                  // the widget kind — matches props.<key>.type
        "bindingAtExposeTime": {               // fallback binding if the template doesn't override
          "type": "static_value",
          "value": "CARD1-tone"
        }
      }
    ]
  },
  "slots": { /* … normal section ui … */ }
}
```

`sectionExposedProps` is on the section's `ui` **ROOT node's `metadata`**, not on the composition entry, and not on the individual node the prop lives on. Getting the placement wrong (on the node, or on the entry) means the template's right panel doesn't render the field.

### Template side: per instance

The template's `section-composition` node carries a `props` map keyed by the exposure `uid`:

```jsonc
{
  "type": "section-composition",
  "uid": "INST-1",
  "metadata": {
    "compositionUID": "<section's entry uid, blt…>",
    "sectionBindingOverride": { "selectedField": "…" }   // (selectedField priority — separate concern)
  },
  "props": {
    "exp-tone-1": {                            // keyed by section's exposure uid
      "type": "choice",                        // must match section's propType
      "binding": {
        "type": "static_value",
        "value": "INST-1-tone-override"        // static_value key on the TEMPLATE entry
      }
    }
  }
}
```

Two things to internalize:

1. **Per-instance uid**: the same section dropped twice on one template = two `section-composition` nodes with **different `uid`s**. Each carries its own `props.<exposed-uid>` map, so each drop can have a different override value.
2. **Static-value keys live on the template entry**, not the section entry. When the override is a static_value, the `binding.value` key is looked up in the **template**'s `static_value.<subtype>[]` bucket (per the two-level lookup rule earlier).

### Fallback resolution

For each exposed prop the SDK resolves in this order at render time:

1. Template's `section-composition.props.<exposure-uid>.binding`: if present, use it.
2. Section's `ui.metadata.sectionExposedProps[…].bindingAtExposeTime`: fallback.
3. Node's own `props.<propKey>.binding` in the section's `ui`: final fallback.

So a section can drop with no override (fallback to expose-time binding) OR with a per-instance override (template controls it). Leaving all three unset means the prop renders as the component's `defaultValue`.

### Verifying an exposed prop

Same as sections generally: SSR cold-load and dump `spec.data.section_scoped_data[<instance-uid>]`. The resolved override appears as the concrete `props.<propKey>` value on the section instance. If it's the fallback, either the template didn't provide an override or the `exposure-uid` doesn't match.
