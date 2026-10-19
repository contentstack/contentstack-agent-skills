---
name: author-composition-static-values
---

## When to use

Write `static_value` bindings by API: the binding stores a key, and the literal lives in the composition entry's `static_value.<subtype>[]` bucket. Phrases: "static_value binding", "static value renders the default", "where does the literal go".

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md). The entry fields are in [`author-composition-entry`](author-composition-entry.md).

# How `static_value` binding resolves: two-level lookup

**Not obvious from the binding shape**: the literal ISN'T on the node. The `binding.value` on a `static_value` binding is a lookup key into the composition entry's `static_value.<subtype>[]` bucket:

1. The node's prop binding stores a **key string** in `binding.value` (e.g. `"mHjnXsgKbBlj_PZ-headline"`), NOT the literal.
2. The literal lives in the composition entry's top-level `static_value.<subtype>[]` array under that key: `{ "key": "mHjnXsgKbBlj_PZ-headline", "value": "Welcome to Studio" }`.
3. The SDK resolves by keying into `entry.static_value` with that key at render time.

Consequences for API authoring:

- **You must write to TWO places** for every static-value prop: `props.<name>.binding.value = "<key>"` on the node AND `entry.static_value.<subtype>` (the bucket for the prop's declared `type`, with `string` → `text`: `text` / `textarea` / `href` / `imageurl` / `number` / `choice` / `boolean` / `json_rte` / `array` / `object` / `any` / `datestring` / `html_rte`) with an entry `{ key, value }` pair.
- **Key uniqueness matters**: the resolver looks up the key against the whole `static_value.<subtype>` bucket. Reuse the same key across multiple nodes to share a literal. Use unique keys to keep them independent.
- **Widget-to-subtype pairing.** The node's `props.<name>.type` (`"string"` / `"number"` / `"href"` / `"imageurl"` / `"choice"` / …) determines which sub-bucket the SDK looks in. `string` is the exception: its literal never goes in `static_value.string`. A single-line string goes in **`text`**, a multiline string (textarea widget) in **`textarea`**, as in the template recipe's `headline` and `subhead`. Verify the bucket against the registered schema or a working composition before writing. Other types use the bucket of the same name. If you write the key to the wrong subtype array, the resolver misses and the prop renders as the schema default.
- **`type` also decides whether the binder FLATTENS the value: never write `"any"` for structured data.** The binder runs a recursive single-key unwrap on every type except `object` and `array` (`retrieve-data.ts`: `if (type !== "object" && type !== "array" …) resolvedData = getFlattenedData(resolvedData)`), descending while an object has exactly one key (`$` and `_metadata` don't count). So a node prop typed `"any"` and bound to a single-field block (`image_grid → { image: [...] }`) receives the **inner array**, not the block: lookups return `undefined`, indices surface as `{0,1,2,3}`, and it renders blank with no error. Write `"object"` for a group / Global Field / block object and `"array"` for a list. Those two skip the unwrap. Full mechanism: [`register-component` § The `any` flatten trap](register-component.md).
- **Convention Studio uses:** keys are `<node-uid>-<propName>` (e.g. `mHjnXsgKbBlj_PZ-headline`). Not required but stable and readable.
