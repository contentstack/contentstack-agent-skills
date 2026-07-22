# build-connected-template


## When to use

Scaffold a Connected (content-type-bound) Studio template by dropping sections, wiring linked-schema bindings, and saving — every entry of that CT renders at a derived URL.

Use for a Connected template — a page bound 1:1 to a content type (blog post, product) where every entry renders at a derived URL. Phrases — "build a blog template", "PDP template", "connected to a content type". Assumes `install-studio` is done.

# Build a Connected Template in Studio

## STOP — apply the Section-qualification rule before dropping anything

Before dropping components or bindings directly on this Template, check the **golden rule** from [`plan-studio-architecture`](../plan-studio-architecture/SKILL.md) § *Step 2*:

- **Reused across Templates?** Any bound compound component that appears on more than one Template MUST be built as a Section first (`build-section` or `build-repeating-section`), then dropped here.
- **Schema iteration (Modular Block / multi-Reference / group-multiple)?** MUST become a **List Section** (Repeater + CBs). Never author the iteration directly on the Template.

Only when BOTH answers are no is it correct to drop registered components straight onto this Template. When in doubt, build the Section first — Sections are cheap to add, direct-drop is expensive to unwind.

## Context

Templates compose Sections — build Sections first via `build-section`. See `understand-templates` § *Templates compose Sections*.

**Connected is the default flavor** — including one-off pages backed by a single-entry CT.

A **Connected template** is bound to one content type. Every entry renders through it at a URL derived from the CT's `url` field (or VX preview URL, or per-template override). What makes it Connected:

1. **Content-type binding** (chip in canvas chrome).
2. **Linked-schema auto-binding** — Studio reads each section's `linked_schemas` and wires it to a matching field on the CT.

Studio uses one preview entry at a time (auto-picked, most recently updated matching the URL pattern); bindings record field paths, not entry UIDs.

Two render surfaces:
- **Studio canvas iframe** — `<StudioCanvas />` on the canvas route, for authoring.
- **Live site** — `<StudioComponent />` on ONE catch-all (`app/[[...slug]]/page.tsx` / `<Route path="*">`). Studio resolves every URL via `sdk.fetchCompositionData(...)`; per-template routes are NOT needed. Without the catch-all, the derived URL 404s even after Deploy.

This skill creates the template, drops sections, confirms bindings, saves. It does NOT publish/deploy.

## Task

1. **Confirm prerequisites.** Before touching the UI, verify (ask the user to confirm if you can't check):
   - Studio project exists and is linked to the stack.
   - Content type `contentTypeUid` exists and has at least one entry.
   - **A URL pattern is available.** Studio resolves which entry to preview by matching the request path against a URL pattern. **One of these five sources must be in play**: `custom_preview_url` (Stack → Visual Experience), `content_type_url_pattern` (page CT with `url_pattern`), `default_url_pattern` (Studio-generated default — applied automatically for connected templates when nothing else is configured), `user_specified_pattern` (authored via the canvas's Edit URL flow), or `legacy_url` (binding against a CT `url` field on every entry). You do NOT need a CT `url` field — Studio's `default_url_pattern` covers the no-config case. Only verify upfront if the project uses the `legacy_url` path: in that case every entry must have `url` populated AND starting with `/` (no leading-slash → invisible to the matcher; canvas opens blank with "No composition for /…").
   - At least one **published** entry exists for the connected CT. Connected canvas fetches via the CDA; unpublished entries return 404 — canvas appears blank.
   - At least one Section composition exists whose `linked_schemas` references a field on `contentTypeUid` — otherwise auto-binding will silently leave every section unbound. If unsure, list sections via the Studio Sections tab and check each one's `linked_schemas`.
   - For a custom URL pattern: prefer configuring **Stack → Settings → Visual Experience → Preview URL** rather than per-template overrides. If the CT already has a `url` field with a pattern, Studio will derive from it automatically.

2. **Open the Templates tab** in the target Studio project. Empty state shows an illustration with a **+ New Template** button; populated state shows a list with columns *Title · Connected Content Type · Publish Status · Modified At · Actions*.

3. **Click `+ New Template`** (top right). The *Create New Template* chooser modal opens with the Connected Template option ready to create.

4. **Fill in the modal:**
   - Title: `templateName`
   - Connected Content Type: pick `contentTypeUid` from the dropdown (lists every CT in the stack)
   - Click **Create Connected Template**

5. **Verify the canvas chrome** once Studio opens the new template:
   - Composition title matches `templateName` (top bar)
   - Content-type chip matches `contentTypeUid`
   - `PREVIEW ENTRY :` *(entry name)* with a `⇄` swap icon — Studio auto-picks the most recently updated entry that satisfies the URL pattern
   - URL line directly below evaluates against that entry (no `{{...}}` leftovers)

   **⛔ Symptom — "No entry has a URL field populated yet" (canvas shows the message, no preview entry is auto-selected):** the connected CT either isn't a page type, OR no entry of that CT has its `url` field set. Fix: ensure the CT is `is_page: true` with a `url` field + `url_pattern` (see [URL pattern rule below](#single-entry-vs-multi-entry-url-pattern-rule)); for every entry, set the `url` field; then click `⇄` and pick a preview entry. After a CT `url_pattern` change, re-save + republish entries so `entry.url` recomputes — otherwise old entries still carry stale URLs.

6. **(Optional) Edit the URL pattern.** Only if `urlPattern` is provided OR the derived URL is wrong. Pencil icon → *Edit URL*. Use Insert chips for `{{entry.<field>}}`, `{{environment}}`, `{{taxonomy:<uid>}}`. **Save** validates + refetches. **Avoid `{{locale}}`** — carry locale via routing + SDK `locale` query option.

   <a id="single-entry-vs-multi-entry-url-pattern-rule"></a>**⛔ Single-entry vs multi-entry URL pattern rule.** Connected templates split into two cases that need different URL shapes:

   - **Single-entry template** (homepage, about, pricing — one entry, one URL): a literal URL like `/home` works. The matcher only needs to resolve one path.
   - **Multi-entry template** (blog posts, products, recipes — many entries through one template): the literal pattern `/blog/:slug` does NOT work. The `:slug` placeholder comes back **literal** — Contentstack's **CMS-side** CT URL-pattern compiler (separate from the Studio SDK pattern compiler) doesn't substitute `:slug`, the entry's `url` field saves as `/:slug` instead of a real slug, and the SDK has no per-entry URL to match against. **The proven shape:** CT `url_pattern: "/:title"` — Contentstack's CMS slugifies the title field into `entry.url` (`:title` is the working CMS substitution token; `:slug` is treated literal) + CT `url_prefix: "/<route>/"` (e.g. `/blog/`); composition `url: "/<route>/{{entry.title}}"` with `url_metadata.url_source: "content_type_url_pattern"` and `url_queries: ""`. The SDK then queries entries by `entry.url`. CT pattern and composition URL must be **consistent by construction**. After changing the CT pattern, re-save + republish every entry so `entry.url` recomputes.

   **⛔ URL traps — same symptom ("No composition for /…"), different fixes:**

   - **(a) Literal URL on a multi-entry template.** A composition `url` like `/home` works for single-entry, but a multi-entry template needs a placeholder. **Fix:** use `{{entry.url}}` or `{{entry.title}}` (NOT `:slug` — see rule above).
   - **(b) Entry `url` field missing leading slash.** SDK matches the full request path; `url: "home"` never matches `/home`. **Fix:** every entry's `url` starts with `/`.
   - **(c) API-set `user_specified_pattern` reverts.** `url_metadata.url_queries` is only generated by the UI Edit-URL → Save flow. **Zero-UI workaround:** make the CT a page type (`is_page: true` + CT-level `url_pattern`), set composition `url_metadata.url_source: content_type_url_pattern`, put `{{entry.x}}` in composition `url`.
   - **(d) `:slug` placeholder comes back literal.** Contentstack's CT URL pattern recognises `:title` but treats `:slug` as a literal string — `url_pattern: "/:slug"` saves and stays `/:slug`, never substituting. **Fix:** use `:title` in the CT pattern (Contentstack slugifies it); use `{{entry.title}}` in the composition URL.

7. **Drop the primary section.** If `primarySectionUid` was provided, drag it from the left palette (Sections category) or the Sections sidebar onto the empty canvas. Drop targets highlight as you drag.

8. **Confirm auto-binding.** When the section drops, Studio reads its `linked_schemas` and tries to bind to a matching field on the connected CT:
   - **One match** → bound silently. Verify by selecting the section → right panel → **Settings** tab.
   - **Multiple matches** → bound to one; switch via the dropdown in the section's right-panel **Settings** tab.
   - **No match** → drops unbound. Either (a) add a matching field to the CT, (b) edit the section's `linked_schemas`, or (c) manually pick a compatible field from the section's Settings if one exists.
   For sections that render lists, the section internally uses a Repeater bound to the matched field; per-item field bindings inside the section read from `repeater.<field>` and resolve automatically — no per-template wiring needed.

9. **Fill any Section Slots.** If the section exposes a Section Slot (e.g. `Hero Strip` slot for a CTA), drag a component (Button, Link, registered component) into the slot's outlined region on the canvas. Slots are carved out of the section's structure — drop into the outlined region, not the surrounding section frame.

10. **Override exposed props per template instance.** Select the section → right panel → **Settings** tab. Each exposed prop (e.g. *Card Title*) shows an input; type the per-template override (e.g. `"Related Blogs"`). This stores on the template instance, not on the section composition itself.

11. **(Optional) Drop individual components and bind them.** From the left palette (Basic / Media / Container / Smart Containers / Registered Components / HTML Elements). Select on canvas → right panel → **Data** tab → click the binding chip on a prop → Data Picker opens → pick `entry.<field>`, a reference field, or a context value (including `repeater.<field>` when inside a Repeater).

12. **Sanity-check with a swap.** Click `⇄` next to PREVIEW ENTRY and pick an entry with different content shapes (long titles, missing images, empty references). Canvas re-renders instantly. Empty fields mean the *entry* lacks the value — not that the binding is wrong. Don't re-edit the binding to "fix" an empty render; swap back and confirm.

13. **Save.** Top bar **Save** persists the template to Contentstack. This does NOT publish — Deploy is a separate step that moves the template through the publishing workflow to an environment.

14. **Smoke-test on the live site.** Hit the derived URL on the host app. The catch-all route should match it and mount `<StudioComponent />`. If the canvas iframe renders but the live URL doesn't, the catch-all route is missing — add it via [`setup-template-preview-routes`](../setup-template-preview-routes/SKILL.md) (default = ONE catch-all that handles every URL; no per-template route needed) before claiming success. The live page fetches its data via `sdk.fetchCompositionData(...)` under the hood.

15. **⛔ Connected templates preview at the ENVIRONMENT base URL — NOT the Canvas URL.**
    - **Sections** preview at the **Canvas URL** (Studio → Project → Settings → Configuration).
    - **Connected templates** preview at the **environment base URL** + resolved path (`Stack → Settings → Environments → <env> → Base URL`).

    If sections render but a connected template shows *"localhost didn't send any data"* / *"SDK Not Initialized"*, env base URL is wrong (common cause: scheme mismatch — env says `http://localhost:5173` but dev server is HTTPS-only via mkcert).

    **Fix:** `PUT /v3/environments/<env>` so `urls[...]` scheme matches the served canvas-app.

16. **⛔ Multiple-file fields bind to `.0.url`, not the field name.** When a CT has a `file` field of type *multiple* (an asset array), and you bind it to a scalar prop like `imageurl`:

    - Wrong: `entryBind("imageurl", "images")` — binds the array → renders "No image" (or the array's `.toString()`).
    - Right: `entryBind("imageurl", "images.0.url")` — picks the first asset's URL.

    If the prop should iterate (multiple images), use a **Repeater** bound to the array and bind `imageurl` to `repeater.url` inside the repeater item. The `.0.url` shortcut is for single-image props only.

## Inputs needed from the user

Ask in this order. Stop if any required input is missing.

1. `contentTypeUid` — content type uid (required)
2. `templateName` — human title (required)
3. `urlPattern` — optional override; leave blank to use CT-derived URL
4. `primarySectionUid` — optional; leave blank to skip auto-drop and let the user choose interactively

If the user doesn't know the content-type UID, point them at: `app.contentstack.com` → stack → **Content Models** → click a model → the UID is on the right-rail.

## Acceptance

Succeed only when ALL of the following are true. If any fails, surface exactly which step broke and stop.

- [ ] A new row appears in the Studio Templates list with `templateName` as title and `contentTypeUid` populated in the *Connected Content Type* column
- [ ] The canvas opens cleanly on reload — preview-entry URL line evaluates without `{{...}}` leftovers
- [ ] Every section dropped is either bound (linked-schema match shown in right panel) or explicitly flagged unbound with the reason
- [ ] Bound props render real values from the auto-picked preview entry; swapping the preview entry re-renders without errors
- [ ] Save completed without error (top bar reverts from dirty to clean state)
- [ ] Hitting the derived URL on the host app's catch-all route renders the page (404 → the catch-all is missing or the URL pattern doesn't match what Studio expects; do not claim success)

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| "Template did not load." | URL pattern doesn't match anything the host app's catch-all routes through Studio | Fix the pattern or wire the catch-all — see template preview routes. Per-template routes are NOT the fix; the catch-all covers every URL. |
| Bound value renders empty | Current preview entry lacks that field | Swap via `⇄`, don't re-edit the binding |
| Registered component drops blank | Missing default data on the component | Developer needs to add Component Default Data; not a Studio-side fix |
| Section drops unbound | No `linked_schemas` match on the CT | Add a matching field, edit the section's `linked_schemas`, or bind manually from Settings |
| "No element is currently selected" in the right panel | Nothing on canvas is selected | Click the component on canvas first |
| Editing URL from the composition list | That view is read-only for URLs | Edit from the canvas navbar pencil icon |
| Assuming Save with preview entry = X pins the template to X | Bindings record field paths; preview entry is authoring-only | Treat preview-entry swaps as visual diagnostics, not state |
| Dropping a Rows / Box wrapper before the first real component | Leaves visible "Drop Here" placeholder zones in canvas + screenshots. Rows is an e2e-test scaffolding habit, NOT a Studio authoring pattern. | Drop the first section directly onto the canvas root slot. Wrap in a container ONLY for explicit layout (e.g. `hstack` for two cards side-by-side). |
| Adding a Repeater for a non-list use case | Repeater iterates a multi-valued field; single-hero + single-body needs zero iteration | Use Repeater ONLY when the field is genuinely a list (Modular Block list, multi-Group, multi-Reference). For one-of-each: drop directly. |
| Leaving empty "Drop Here" zones at the bottom | Saved compositions render those zones as visible placeholders in screenshots and at runtime in builder mode | Before Save, switch to Layers and delete any orphan empty Box / Slot rows |



## LLM execution caveat — drag-drop works, but only with the right sequence

Studio's canvas is a React-DnD iframe listening on `mousedown` / `mousemove` / `mouseup` (NOT HTML5 native drag). Use `page.mouse.down/move/up` directly — `dragTo()` fires HTML5 events Studio doesn't honor.

**Stable selectors:**

- Palette tile: `[data-builder-component="true"][data-node-type="<type>"]` (Section tiles use the section's composition UID)
- Canvas iframe: `[data-testid="canvas-iframe"]`
- Drop slot: `[data-composable-studio-slot="true"]` (the `="true"` filter is required)
- Layers row: `[data-testid="layer-editable-title-container"]`
- Node IDs: `[data-composable-studio-id]`

**The drop sequence:**

```ts
const item = page.locator('[data-builder-component="true"][data-node-type="doc-hero"]');
const frame = page.frameLocator('[data-testid="canvas-iframe"]');
const slot = frame.locator('[data-composable-studio-slot="true"]').first();

await item.hover();                                      // 1. position cursor over palette tile
await page.mouse.down();                                 // 2. mousedown → posts PARENT_DRAG_START to iframe
const sb = await slot.boundingBox();
await page.mouse.move(sb.x + sb.width / 2,               // 3. move cursor in STEPS — required for mousemove events to fire
                      sb.y + sb.height / 2,
                      { steps: 10 });
await slot.hover();                                      // 4. final settle on the slot (FrameLocator handles cross-frame)
await page.mouse.up();                                   // 5. mouseup → commits the drop
```

The `move({steps: 10})` is critical — without intermediate mousemove events the drop is silently swallowed.

**Anti-phantom guardrail.** Verify a NEW `data-composable-studio-id` appeared after each drop:

```ts
const idsBefore = await frame.locator('[data-composable-studio-id]')
  .evaluateAll(els => els.map(e => e.getAttribute('data-composable-studio-id')));
// ... drop sequence ...
await page.waitForTimeout(800);
const idsAfter = await frame.locator('[data-composable-studio-id]')
  .evaluateAll(els => els.map(e => e.getAttribute('data-composable-studio-id')));
const newIds = idsAfter.filter(id => !idsBefore.includes(id));
if (newIds.length === 0) {
  throw new Error('Drop did not commit; do not continue.');
}
```

If `newIds.length === 0`: stop and surface the failure.

**Sibling drops.** Once root is occupied, hover the **edge** of an existing node for a drop indicator, or wrap children in a `box`/`vstack`/`hstack` container.

**Also works programmatically:** Layers row + `Delete`; Save button; right-panel tab switches; opening Configuration / URL Pattern modals; reading iframe state via `frameLocator`; switching palette accordion sections.

## See also

- `docs/31-templates/overview.md` — Templates tab, list columns, create modal
- `docs/31-templates/connected-content-type.md` — URL derivation, preview entry, edit URL modal
- `docs/31-templates/using-sections-and-components-in-a-template.md` — palette categories, auto-binding flow, Save vs Deploy
- `docs/32-sections/auto-binding-by-drop-location.md` — linked-schema matching rules
- `docs/34-smart-containers/section-slots.md` — filling carved-out slots
- `docs/32-sections/expose-section-props.md` — what becomes overridable per template instance
- `docs/90-reference/url-variables-reference.md` — full URL variable list
- Pair with `install-studio` (SDKs) and `setup-template-preview-routes` (host-app **catch-all route** mounting `<StudioComponent />` — one route handles every URL).
