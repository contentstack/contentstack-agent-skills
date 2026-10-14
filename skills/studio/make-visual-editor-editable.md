---
name: make-visual-editor-editable
---

## When to use

Make a Studio page fully editable in Contentstack's Visual Editor: every field clickable on the page, lists that can be added to, reordered and deleted from, an empty list that offers "+", and a brand-new entry that is editable before anyone types into the form. Each rule here fails silently: the page renders correctly and Visual Editor simply offers nothing.

Phrases: "nothing is clickable in Visual Editor", "Visual Builder opens but I can't edit", "can't add a block / reorder / delete in Visual Editor", "no + on an empty list", "new entry shows Your text here", "can't click an empty field", "image under an overlay can't be selected". Do NOT use for the per-component `$` props and `studioAttributes` contract (that's [`register-component-cslp`](register-component-cslp.md)), or for the stack-level Live Preview switch (that's [`enable-visual-experience`](enable-visual-experience.md)).

# Make every field and list editable in Visual Editor

Checked against `@contentstack/studio-react` 1.9.0 and `@contentstack/live-preview-utils` 4.5.3, in their code and on a rendered page (2026-10-07). Visual Editor works from the `data-cslp` edit tags in the page's HTML, so each check below is a count of tags, not a look at the page.

## 1. Live Preview must run in builder mode

`live-preview-utils` defaults to `mode: "preview"`, and its editing layer returns early unless the mode is `builder`. Visual Editor then loads the page, sits on "Initializing the editor…", and nothing can be clicked. The init options live in [`install-studio`](install-studio.md) § the `lib/contentstack` snippets: `mode: "builder"`, an explicit `ssr`, `editButton.exclude: ["outsideLivePreviewPortal"]` and `editInVisualBuilderButton: { enable: false }` (builder mode otherwise adds a floating "Start Editing" link to every page it runs on).

Check: open the page directly (not in Visual Editor) with a preview token set. With builder mode and the "Start Editing" button enabled, `[data-testid="vcms-start-editing-btn"]` appears, which proves the editing layer started. Then turn that button off again.

## 2. Lists need two kinds of tag

Visual Editor's list controls read two tags: the **list tag** `<…>.<field>` on an element around the whole list, and an **item tag** `<…>.<field>.<N>` on an element around each item. Move and delete need the item tags. Add needs both: it finds the list element from the item's tag.

| Trap | What happens | Fix |
|---|---|---|
| No wrapper marked as the list | No list tag at all, so no add buttons | The node holding the Repeater carries `metadata.repeaterWrapper: true`. Studio's UI sets it on the Repeater's parent; by API, set it yourself ([`author-composition-practice`](author-composition-practice.md)) |
| The Repeater's child is a Condition Block holding a Section, or a Section Slot | The item tag never reaches an element: a Section or Section Slot renders no element of its own, so every item tag is dropped | Make a **Box** the Repeater's only child and put the Condition Blocks inside it: Repeater → Box → Condition Blocks → Sections |
| A Section scoped to the list field (`selected_field: "blocks"`) with its Repeater bound to the Section root | The list renders, but the tags are looked up on the bare array, which has none: no list tag and no item tags | Scope the Section to the whole entry and bind the Repeater to `<field>` |

**Worked example (measured):** a page-builder template built in Studio's UI (Repeater over a modular-blocks field → Condition Block → Section per block type) rendered the list tag `page_sections` and the fields inside each block (`page_sections.0.cta_block.label`), but **no** `page_sections.0` / `.1` / `.2`. With a Box between the Repeater and the Condition Blocks, all three item tags appeared and nothing else changed.

Check, on the rendered HTML of an entry with at least one item:

```sh
curl -s "<page URL>" | grep -o 'data-cslp="[^"]*\.<field>\(\.[0-9]*\)\?"' | sort -u
```

Expect the `<field>` line and one `<field>.<N>` line per item.

## 3. An empty list should offer "+"

Visual Editor shows its "This page doesn't have any … added" panel, with a "+", inside an element that has the list tag **and** the class `visual-builder__empty-block-parent`, for a field that exists in the content type schema. It looks for that class only after a change to the page's children (a `childList` mutation), never at start-up, and never after a class change alone. So add the class in the browser after mount, inside the editor only, then append an empty comment node to trigger the scan:

```tsx
useEffect(() => {
  const el = ref.current;                                   // the list wrapper, carrying the list tag
  if (!el || window.self === window.top || el.children.length) return;
  el.classList.add("visual-builder__empty-block-parent");
  el.appendChild(document.createComment(""));               // a childList change, so Visual Editor rescans
}, [itemCount]);
```

Checked in the `live-preview-utils` code, not yet clicked through in Visual Editor.

## 4. A new entry must be editable before anyone types

A new entry holds only the fields someone has filled. A missing or `null` field gets no edit tag (tags are built from the entry's own keys) and its component shows the registered default ("Your text here"). An empty image is the worst case: a binding to `image.url` has nothing to tag. Two changes fix it, and both are needed:

1. **Complete the entry.** `studioSdk.init({ fetchTemplateEntry })` (studio-react 1.9.0) receives `defaultFetch()`. Give every missing or `null` field an empty value from the content type schema: `""` for text, `{ url: "" }` for a file, `[]` for anything multiple, recursing into groups and blocks. Never touch existing values. The SDK tags the entry after this hook, so every field gets a tag.
   ```ts
   fetchTemplateEntry: async (ctx) => {
     const entry = await ctx.defaultFetch();
     return entry ? completeEntry(entry, await ctSchema(ctx.connectedContentType)) : entry;
   },
   ```
   Fetch the schema with a plain Delivery API call (`GET /v3/content_types/<uid>?environment=…`, cached per uid). Don't use `stack.contentType(uid).fetch()`: with Live Preview configured, `delivery-sdk` calls `getData` without a params object and throws "Cannot set properties of undefined (setting 'live_preview')". A change to `studioSdk.init` options needs a dev-server restart; hot reload keeps the old config.
2. **Render the empty element.** A component that returns nothing for an empty value has no element to tag. Render the element whenever its `$` prop is present (`{(headline || $headline) && <h1 {...$headline}>{headline}</h1>}`), and give empty tagged elements a minimum size inside the editor so there is something to click.

**Measured:** with `hero` missing from Entry MB, the heading had no tag and showed "Your headline here". With the completer alone, the default text was gone but there was still no tagged element. With both changes, the page rendered `<h1 data-cslp="<ct_uid>.<uid>.en-us.hero.heading">`.

## 5. Decorative overlays block selection

Visual Editor selects the nearest tagged ancestor of the clicked element. A gradient or scrim laid over an image (an absolutely positioned sibling, or a `::after` on the wrapper) takes the click, so the image can never be selected. Give every decorative overlay `pointer-events: none`.

## Acceptance

- [ ] Live Preview runs with `mode: "builder"` and `editInVisualBuilderButton: { enable: false }`.
- [ ] Every list renders a `<field>` tag and one `<field>.<N>` tag per item.
- [ ] No Section or Section Slot is the Repeater's direct child: a Box is.
- [ ] An empty list's wrapper gets `visual-builder__empty-block-parent` after mount, inside the editor only.
- [ ] `fetchTemplateEntry` completes the entry, and a new entry's empty fields, the image included, render tagged elements.
- [ ] Decorative overlays have `pointer-events: none`.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Judging Visual Editor by an existing, fully filled entry | Every trap in § 4 (A new entry must be editable) shows only on a new entry | Test with a new entry whose fields are all empty |
| Rendering the empty-list class on the server | The class is present before Visual Editor starts watching, and nothing changes after | Add it after mount, then append the comment node |
| Completing the entry on the visitor side only | The editor fetch is the one that needs the tags | Pass `fetchTemplateEntry` to the `studioSdk.init` the editor's page uses (server and client) |
