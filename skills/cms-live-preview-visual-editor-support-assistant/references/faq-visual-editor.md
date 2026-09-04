# Visual Editor FAQ

In-canvas behaviour once Live Preview itself is confirmed working: edit-tag resolution, the empty-block
affordance, and what the canvas does with the site's own clicks. Live Preview refreshing correctly while
the canvas misbehaves points here.

If nothing on the canvas is editable at all, start with `edit-tags-not-generated-or-not-spread` in
`faq-setup.md` — that is setup contract 2, and everything here assumes it is met.

### cslp-not-rebased-to-referenced-entry
- **bucket**: visual-editor
- **symptom**: Edit tags on fields that come from a **referenced** entry do nothing when clicked. Tags on the page's own fields work. Console may show `{code: 'NO_REQUEST_LISTENER_FOUND', message: 'contentstack-adv-post-message: No request listener found for event "scroll"'}`, but that message is routine and appears on healthy setups too — treat it as incidental, not as the identifying evidence. Diagnose from the tags themselves.
- **frameworks**: React, Next.js, framework-agnostic
- **rendering_modes**: CSR, SSR
- **root_cause**: `addEditableTags()` rebases a tag onto the referenced entry only when the resolved reference object carries both `uid` and `_content_type_uid`. Without them the tag stays anchored to the parent entry (`product.<parent_entry_uid>.<locale>.<reference_field>.<index>.<field>`), so there is no entry to navigate to. Common causes: references fetched separately and merged by hand (which drops those keys), or a GraphQL query that omits `system`. Hardcoding `data-cslp` by hand is a related failure — the referenced entry's uid and content type uid are not the ones being edited.
- **fix**:
  1. Inspect the referenced field in DevTools. Working shape is `<referenced_ct_uid>.<referenced_entry_uid>.<locale>.<field>`. If you see the parent entry's uid, this is the bug.
  2. REST / Delivery SDK: resolve references with `includeReference()` / `include[]` so resolved objects keep `uid` and `_content_type_uid`.
  3. GraphQL: request `system { uid, content_type_uid, locale }` on every reference.
  4. If references are fetched separately, either preserve those two keys when merging, or call `addEditableTags()` on each referenced entry with its own content type uid.
  5. Never hardcode `data-cslp` — always read the value the SDK put on the entry object.
- **verification**: Click the edit tag on a referenced field; the CMS should open the referenced entry's editor and scroll to that field.

---

### locale-case-mismatch-lowercased-cslp
- **bucket**: visual-editor
- **symptom**: Visual Editor will not initialize for any non-fallback locale on an older stack, while Live Preview works. Locales defined with mixed case (for example `en-GB`) never match; only the fallback locale partially works, and updates still fail.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: `addEditableTags()` lowercases the locale segment when it builds `data-cslp`, and it does so **by default** — `useLowerCaseLocale` defaults to `true`. The generated tags therefore never match a stack whose locale codes were created with uppercase characters. Newer stacks create locales lowercase by default, which is why this is specific to older stacks. The fix is an opt-out flag, not a change in default behaviour.
- **fix**:
  1. Pass the opt-out as the fifth argument:
     `addEditableTags(entry, "<content_type_uid>", true, locale, { useLowerCaseLocale: false });`
     `addEditableTags` is an alias of `addTags` in `@contentstack/utils`; the option is typed as `options?: { useLowerCaseLocale?: boolean }`.
  2. Confirm your `@contentstack/utils` version accepts a fifth argument. If your installed `addEditableTags` signature stops at `locale`, upgrade — 1.9.1 has it. Do not rely on the flag silently working on an older version; an extra argument is ignored without error.
  3. Alternatively, normalise the stack's locale codes to lowercase — but only if nothing else depends on the existing casing.
- **verification**: `data-cslp` values carry the locale in the stack's own casing (for example `...en-GB...`, not `...en-gb...`), and the editor opens for a non-fallback locale.

---

### empty-fields-are-not-clickable-on-the-canvas
- **bucket**: visual-editor
- **symptom**: An empty rich text field renders with zero height in preview mode, so there is nothing to click and the author cannot start editing it from the canvas. Same class of problem for any field that renders nothing when empty.
- **frameworks**: React (reported); applies to any frontend
- **rendering_modes**: any
- **root_cause**: The canvas can only target what the page renders. A field whose empty state produces no DOM box has no hit area for the click-to-edit overlay.
- **fix**:
  1. Render a placeholder element for empty fields when the page is in preview or builder mode, so the field has a clickable box.
  2. Detect preview/builder mode through the SDK rather than threading a prop through every nested component.
  3. Give the placeholder a minimum height and keep the `data-cslp` attributes on it so the overlay targets it correctly.
  4. This is about a **scalar field whose empty state renders no box**. An empty modular-block or multiple field is handled differently — the SDK draws its own "+ Add Component" affordance if the wrapper is marked correctly; see `empty-block-add-button-not-appearing-or-failing`.
- **verification**: Clear a rich text field, reload the canvas, and confirm the empty field is still clickable and opens the correct field in the form.

---

---

### empty-block-add-button-not-appearing-or-failing
- **bucket**: visual-editor
- **symptom**: A page or component with an empty modular-block / multiple field shows no "+ Add Component" affordance, so authors have to go to the form panel to add the first block.
- **frameworks**: React, Next.js
- **rendering_modes**: CSR, SSR
- **root_cause**: The empty-block placeholder only renders when the wrapper carries **both** the `VB_EmptyBlockParentClass` class (exported by the SDK; its literal value is `visual-builder__empty-block-parent`) and a `data-cslp` pointing at the block field itself. Miss either and there is nothing for the canvas to attach the affordance to.
- **fix**:
  1. Confirm the wrapper renders both the class and a `data-cslp` pointing at the block field (for example `<page_ct>.<entry_uid>.<locale>.components`), and that it is rendered conditionally when the array is empty.
  2. Confirm the wrapper is visible and has height. A zero-height container gives nothing to hover.
  3. For nested blocks, put the same class and `data-cslp` on the inner block container, not only at page level.
  4. This is specifically about a **block or multiple field with zero items**, where the SDK draws the affordance for you. A scalar field that renders nothing when empty is a different problem — see `empty-fields-are-not-clickable-on-the-canvas`.
- **verification**: Open a page whose block field is empty. The "+ Add Component" placeholder appears on hover, and adding a block inserts it into both the canvas and the form.

---

### graphql-connection-wrappers-break-cslp
- **bucket**: visual-editor
- **symptom**: With GraphQL, edit tags are generated but Visual Editor cannot resolve them. The `data-cslp` values contain connection plumbing — for example `...edges.0.node.hero.heading` — and clicking a tagged element does nothing, or edit buttons on referenced fields are inert. The same integration over REST works.
- **frameworks**: Next.js, React, any GraphQL client
- **rendering_modes**: any
- **root_cause**: `addEditableTags()` walks the response object and bakes every traversed layer into the `data-cslp` path. A GraphQL response nests values under `Connection -> edges -> node`, so those wrapper layers end up in the path and no field path resolves against the entry. This is by design — the SDK has no knowledge of GraphQL response shapes — so it needs a normalizer on the application side.
- **fix**:
  1. Request `system { uid, content_type_uid }` on every node the page renders, including referenced entries. Without those the tags cannot be attributed to an entry at all.
  2. Flatten the response before tagging: collapse each `Connection -> edges -> node` into the plain object or array the REST shape would have produced, so a reference is an array of entries and a field is a direct property.
  3. Call `addEditableTags()` on the flattened object, never on the raw GraphQL response.
  4. Confirm the resulting `data-cslp` values contain no `edges` or `node` segments.
- **verification**: Inspect a tagged element. Its `data-cslp` reads `<content_type_uid>.<entry_uid>.<locale>.<field_path>` with no connection segments, and clicking it focuses the field in the form panel.

---

### highlight-variant-or-audience-mode-does-nothing
- **bucket**: visual-editor
- **symptom**: Variant content renders correctly on the canvas, but Highlight Variant outlines nothing and audience mode shows no variant-specific fields. No error anywhere. Every `data-cslp` on the page is v1 (`<ct>.<uid>.<locale>.<field>`); none starts with `v2:`.
- **frameworks**: any
- **rendering_modes**: any
- **root_cause**: `addEditableTags()` emits a `v2:<ct>.<entry_uid>_<variant_uid>.<locale>.<field>` tag only for fields listed in the entry's `_applied_variants`. That map is in the response only when the content request carries `include_applied_variants=true`. Without it every tag is v1, the SDK parses no variant, and both features have nothing to key on. Content still renders correctly because the Preview Service already applied the variant, which is why this looks like a highlighting bug rather than a fetch problem. Two places look like they set the flag and do not: `livePreviewQuery({ include_applied_variants: true })` and `include_applied_variants` on the Stack's `live_preview` config are accepted by the delivery-sdk types and stored, but `@contentstack/core` never reads them off that config, so the flag never reaches the request (checked against delivery-sdk 5.6.0, core 1.5.2).
- **fix**:
  1. Pass it as a query parameter on the content request itself. Delivery SDK: `.addParams({ include_applied_variants: "true" })` on the query chain (`.entry().query().addParams(...)`) or on a single-entry fetch (`.entry(uid).addParams(...)`). REST: append `include_applied_variants=true` to the URL.
  2. Do not route it through `livePreviewQuery()` or the Stack `live_preview` config. Both drop it silently.
  3. Leave it on for delivery traffic too. When no variant applies the response carries no `_applied_variants` and is otherwise unchanged, so a preview-only branch buys nothing.
  4. One flag on the page query covers referenced entries that `includeReference()` resolved; `addEditableTags()` reads `_applied_variants` per reference.
  5. Never pass the variant uid yourself. The Preview Service applies it from the UI selection; `Entries.variants()` and `x-cs-variant-uid` are for regular delivery.
- **verification**: With a variant selected, inspect a variantised field in DevTools. Its `data-cslp` starts with `v2:` and the entry segment reads `<entry_uid>_<variant_uid>`. Highlight Variant now outlines it.

---

### canvas-swallows-site-click-events
- **bucket**: visual-editor
- **symptom**: Interactive components stop working inside the editor canvas: carousel arrows, tab strips, accordions, dropdowns and links do nothing when clicked, while the same page works normally outside the editor. Often noticed as soon as a parent container gets a `data-cslp`.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: By design. In builder mode the SDK intercepts clicks so the canvas can capture them for editing: a click on any anchor, or on any element that is or sits inside a `data-cslp` element, gets `preventDefault()` and `stopPropagation()` before the site's own handler sees it. Anything interactive inside a tagged container is therefore inert in the canvas. This is what makes click-to-edit possible, so it cannot be switched off per element.
- **fix**:
  1. Recognise it as expected editor behaviour and say so. Authors are editing content, not exercising the site; interactivity is suspended in the canvas the same way it is in most visual editors.
  2. Alt+click a link to follow it. The SDK navigates explicitly on alt+click, which is the supported way to move through the site inside the canvas.
  3. Where a control must stay usable while editing, keep it outside any `data-cslp` container. Tag the content that is editable, not the interactive chrome around it.
  4. Do not try to re-enable the site's handlers by stopping the SDK's interception. That breaks click-to-edit for every field under that element.
- **verification**: The same control works on the public site and via alt+click in the canvas; tagged content around it still opens the field on click.
