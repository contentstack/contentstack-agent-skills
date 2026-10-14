---
name: author-composition-migration
---

## When to use

Move compositions between stacks: uid, index and schema remaps, and what breaks if you skip them.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Migrating compositions between stacks: uid, index, and schema remaps

Copying compositions from a source stack (a dev/staging stack, another project) to a destination is NOT a byte copy. The entry JSON carries three classes of stack-bound values that MUST be rewritten, or the composition writes cleanly, resolves in the SSR fetch, and still renders blank or errors in the canvas. All three apply to any cross-stack copy, including across data centers.

### 1. Template references to sections must be REMAPPED to each destination entry's NEW uid

A template places each section by the section's **entry uid** (`metadata.compositionUID`), and both the canvas and the runtime fetch sections by entry uid. On the destination, `POST` gives each section a **new** entry uid, so every template reference to the old one is dead: **`Component with type '<uid>' is not registered`**, once per section.

`composable_uid` is different: it only has to be unique across the compositions CT, and Studio's UI fills it with a readable name. Carrying it over is fine, as long as no destination composition already uses it.

The fix (do both, in order):
1. Create each section on the destination. Capture its new entry uid.
2. In the template: rewrite every `ui` `section-composition` node's `metadata.compositionUID` from the source uid to the destination uid, and set `linked_sections` to the destination uids (`{uid, _content_type_uid}`, the compositions CT). Publish.

`linked_sections` is a **reference field storing entry uids**: those are always stack-specific and always need remapping (see [`author-composition-templates`](author-composition-templates.md) § Authoring a Template: populate `linked_sections`). `metadata.compositionUID` inside the `ui` is what the client resolves by, so it must match the new uid too.

### 2. Block-index paths must be remapped when the destination CT's field ORDER differs

Bindings into an ordered multi-value field bake the index into the path: `{ modular_blocks: { "2": { image_grid: {} } } }`. If the destination entry orders those blocks differently (an extra block inserted, a different author order), every baked index points at the wrong block, which produces wrong data or a blank. Block order is stored **per entry**, so build the `old→new` index map **per migrated entry**: match each source block to its destination block by block type and identity (not position), then rewrite the indices in the `ui` binding paths that point at that entry. The path flattener keeps numeric keys, so the rewrite itself is a straight substitution over `modular_blocks.<N>`. Never reuse one entry's map for another.

### 3. Binding paths + `selected_field` must match the DESTINATION CT's schema, not the source's

The same logical field can sit at a different path across stacks (schema drift): a hero image at `image` in one stack, `image_options.image` in another. A migrated binding of `hero.0.image.url` silently resolves to nothing on a stack whose `hero_banner` nests the file under `image_options`. Symptom: text/scalar props render (their paths matched) but one field is blank. Verify each bound path against the destination CT schema (`GET /v3/content_types/<ct>`), and fix the drifted ones. Same for `linked_schemas.selected_field`.

### 4. Assets are stack-scoped

File/image fields reference asset uids that don't exist on the destination. Either re-upload the assets to the destination (raw multipart `POST /v3/assets`, then publish) and re-point the fields, or bind to existing destination assets. A migrated composition whose entry data still points at source-stack asset uids renders with broken/blank media.

### Pre-flight for a cross-stack migration

Verify BOTH paths, exactly as [`author-composition-templates`](author-composition-templates.md) § Authoring a Template prescribes: SSR resolves (fetch returns the sections) **and** the canvas opens without `not registered` errors. The uid remap (#1) is the one that passes SSR and fails the canvas, so an SSR-only check is not enough.
