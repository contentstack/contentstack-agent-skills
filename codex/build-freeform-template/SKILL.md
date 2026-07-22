# build-freeform-template


## When to use

Author a Freeform (Static) template with Additional Entry Data pins and Pinned Queries. Connected is the default; Freeform is the last resort.

Use ONLY when the page genuinely cannot be modelled by any content type (not even a single-entry CT). First run `choose-connected-vs-freeform` — if its recommendation is Connected, stop and use `build-connected-template` instead. Reach for this when the page composes from multiple unrelated sources with no anchor CT. Three-AND Freeform rule applies.

# Build a Freeform template

## STOP — Freeform is the very very very last resort

**Reach for Freeform only after confirming ALL THREE of these are true:**

1. **Short-lived** — the page has an expected end date (campaign, splash, takeover, time-boxed promo).
2. **Owns ZERO content of its own** — no hero copy, no page-specific title, no subheading, no CTA text, no callouts. Literally nothing the page itself authors. Hero copy IS content; "throwaway HTML" is owned content in disguise.
3. **Visible content is 100% assembled from existing entries** — pinned entries, pinned queries, references into existing CTs. The page is a pure vitrine.

If ANY of those is missing — even a hero title specific to this page — the page has owned content. Owned content belongs in a CT → **Connected** (single-entry CT for one-offs; multi-entry / `campaign` CT for recurring shapes). Most pages users initially tag as Freeform DO own copy and should be Connected.

**If you arrived here without running `choose-connected-vs-freeform` or `plan-studio-architecture`, stop and run one of those.** This skill exists for genuine vitrine cases — they are rare.

## Before you start: confirm Freeform is the right choice

If you haven't already run `choose-connected-vs-freeform`, do that first. Only proceed when every Connected option (existing CT, extended CT, single-entry CT) has been ruled out. The Project-level **Enable Freeform Feature** toggle is often deliberately OFF — if off, usually leave it off and create a CT.

**Section-qualification rule still applies.** Before dropping components + bindings directly on this Freeform template, apply the golden rule from [`plan-studio-architecture`](../plan-studio-architecture/SKILL.md) § *Step 2*: **reused across Templates?** → Section first. **Schema iteration (MB / multi-ref / group-multiple)?** → List Section first. Freeform doesn't exempt you from this — a shared Header pinned to two Freeform pages must be a Section, and a Pinned-Query Repeater rendering N items belongs in a List Section, not authored inline.

## Context

**Freeform** (labeled **Static Template** in the create modal, **FREEFORM MODE** on canvas — same thing) is not tied to a content type. Bring data in by *pinning* entries and queries directly on the template. Use only as the documented exception.

The right panel (nothing selected) surfaces three sections:

- **Additional Entry Data** — explicitly chosen single entries; bindable roots in the Data Picker.
- **Pinned Queries** — saved CDA queries; Repeater item sources.
- **External Data** — non-Contentstack sources via Component Default Data at runtime.

Reference docs: `docs/33-freeform/`.

## Prerequisite

Project Configuration → **Enable Freeform Feature** must be ON. Without it, the right panel collapses to **Settings only** — no Design tab, no Data tab, no way to pin. If the user sees only Settings, stop and direct them to flip the feature flag at the project level before continuing.

## Task

1. **Confirm Freeform is enabled** on the Studio project. If not, instruct the user to open Project Configuration and toggle **Enable Freeform Feature** on, then resume.

2. **Create the template.**
   - From the Studio templates list, click **New Template**.
   - In the *Create New Template* chooser modal, pick **Freeform** (the chooser's two options are Connected Template and Freeform). The follow-up dialog is titled "Create Static Template" — *Static* is Studio's internal name for Freeform; same thing.
   - Enter the `templateName` from inputs and confirm.

   On the canvas verify:
   - A **FREEFORM MODE** badge in the top bar (replaces the content-type chip used by Connected templates).
   - A **PREVIEW COMPOSITION:** label (not **PREVIEW ENTRY:**) — preview drives off the composition itself.

3. **Edit the URL pattern.**
   - Click the **pencil icon** next to the URL in the canvas navbar to open **Edit URL**.
   - Replace the auto-generated default with `urlPattern` from inputs.
   - The Insert chip row exposes exactly one entry-style variable: `{{composition_uid}}`. There is intentionally no `{{entry.*}}` and no `{{content_type_uid}}` — Freeform has no connected entry/content-type. You may type context vars (`{{environment}}`, `{{branch}}`) by hand. `{{locale}}` is also accepted by the pattern engine but **avoid using it** — the recommended way to carry locale is via your routing layer + the SDK's `locale` query option (see [multi-locale-at-scale](docs/50-advanced/managing-multiple-locales-at-scale.md)).
   - Save.

4. **Open the template-level Data tab.**
   - Click empty canvas space to ensure no component is selected (otherwise the right panel switches to component-prop bindings).
   - Right panel → **Data** tab → confirm three accordion sections appear: **Additional Entry Data**, **Pinned Queries**, **External Data**. Empty state reads "No Data Connected Yet".

5. **Pin an entry (Additional Entry Data).** If `pinnedEntryContentTypeUid` was provided:
   - In the **Additional Entry Data** section click the empty-state prompt / **Link Entry** button.
   - In the entry-picker modal, set the content-type filter to `pinnedEntryContentTypeUid`.
   - Use search/sort/checkbox selection in the entries table, then click **Add Selected Entries**.
   - The pinned entry now appears with its title + content type and is bindable from any component's Data Picker.
   - Re-pinning (swap to a different entry of the same shape) preserves existing bindings.

6. **Pin a query (Pinned Queries).** If `pinnedQueryContentTypeUid` was provided:
   - In the **Pinned Queries** section click **+ New Query**.
   - In the **New Query** modal fill **Name** and set **Content Type** = `pinnedQueryContentTypeUid`.
   - Either configure filters/order/limit directly, or type a free-text prompt in **"Tell me what data you need"**. Quick-prompt seeds include *"Show the last 5 recent entries"*, *"List all entries from the past week"*, *"Filter the entries by specific tags"*, *"Fetch the entries containing taxonomy"*. The prompt is converted to a stored CDA query at save time — it is not re-translated per render.
   - Save. The query appears under **Pinned Queries** with its Name + Content Type.

7. **Bind components on the canvas.**
   - Drop a card, hero, or other component → right panel → **Data** tab → click a prop → the **Data Picker** opens. Pinned entries appear as bindable roots alongside their fields.
   - For lists: drop a **Repeater**, bind **Items** to a Pinned Query, then drop the iteration component inside the Repeater body. Bindings inside resolve against the current iteration (`repeater.<field>`).
   - Static prop values and Component Default Data remain available for purely presentational content.

8. **Verify the rendered route.** The host app's catch-all route (default + recommended: `app/[[...slug]]/page.tsx` for Next.js, `<Route path="*">` for React Router) mounts `<StudioComponent />` and handles every URL — including the freeform template's resolved `urlPattern`. No per-template route is needed; Studio's CDA query inside `sdk.fetchCompositionData` resolves the composition.

   Open the resolved URL in the browser to confirm the pinned content appears. If it 404s, the catch-all isn't wired — run [`setup-template-preview-routes`](../setup-template-preview-routes/SKILL.md) first.

## Inputs needed from the user

In order. Two are optional — skip the corresponding step if blank.

1. `templateName` — template display name (required)
2. `urlPattern` — URL pattern; defaults to `/compositions/{{composition_uid}}` (required). Avoid encoding `{{locale}}` — carry locale via routing + the SDK `locale` query option.
3. `pinnedEntryContentTypeUid` — optional; skip step 5 if blank
4. `pinnedQueryContentTypeUid` — optional; skip step 6 if blank

If the user is unsure which content types to pin, ask what data the page needs to show (single entry vs. list) and map accordingly.

## Acceptance

This skill succeeds only when ALL applicable items below are true. If any fails, do not claim success — surface the failure and stop.

- [ ] **FREEFORM MODE** badge visible in the canvas top bar.
- [ ] **PREVIEW COMPOSITION:** label (not PREVIEW ENTRY) shown in the preview row.
- [ ] Edit URL modal shows the `{{composition_uid}}` chip and no `{{entry.*}}` chips; the saved pattern uses only allowed tokens.
- [ ] With nothing selected on canvas, right panel → Data tab lists all three sections: Additional Entry Data, Pinned Queries, External Data.
- [ ] If a pinned entry was requested, it appears under Additional Entry Data with its title + content type and is reachable from a component's Data Picker.
- [ ] If a pinned query was requested, it appears under Pinned Queries with its Name + Content Type and is bindable as a Repeater **Items** source.
- [ ] The app route at the resolved URL mounts `<StudioComponent />` and renders the freeform layout with pinned content. (For lists, the Repeater shows real iterations after toggling **Preview Mode** in Properties — the canvas previews one iteration by default.)

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Right panel shows only Settings | Freeform feature is OFF at project level | Enable it before continuing |
| A component is selected when you wanted template-level pins | Data tab swaps to component-prop bindings | Click empty canvas to deselect |
| Trying to use `{{entry.title}}` or `{{content_type_uid}}` in the URL pattern | Freeform has no entry / no connected content type | Only `{{composition_uid}}` + context vars work |
| "Static Template" (create modal) vs "Freeform Mode" (canvas badge) | Same thing, different label | Treat as one |
| Pinned Entry vs Pinned Query mix-up | Single entry → Additional Entry Data; list → Pinned Queries (Repeater source). A pinned query re-runs every render; a pinned entry does not refresh as content changes. | Pick by cardinality |
| Pinned query prompt isn't live | Natural-language prompt is converted once at save time | Re-open the query to tune later |
| Repeater renders one row on the canvas | Design Mode preview shows one iteration | Select Repeater in Layers and toggle **Preview Mode** in Properties |
| Template doesn't render at the resolved URL | Catch-all missing, or not mounting `<StudioComponent />`, or pattern doesn't resolve inside `sdk.fetchCompositionData` | Verify all three. The catch-all covers every URL; per-template routes are NOT needed. |
| Dropping a Rows / Box wrapper before the first real component | Leaves visible "Drop Here" placeholder zones. Rows is an e2e-test scaffolding habit, NOT a Studio authoring pattern. | Drop the first component directly onto the canvas root slot. Wrap in a container ONLY for explicit layout. |
| Adding a Repeater for a non-list use case | Repeater iterates a multi-valued field; one hero + one promo card needs zero iteration | Use Repeater ONLY when the data source is genuinely a list (Pinned Query, multi-entry Pinned Reference) |
| Leaving empty "Drop Here" zones at the bottom | Saved compositions render those zones as visible placeholders | Before Save, switch to Layers and delete any orphan empty Box / Slot rows |



## LLM execution caveat — drag-drop works, but only with the right sequence

Studio's canvas is a React-DnD iframe listening on `mousedown`/`mousemove`/`mouseup` (NOT HTML5 native drag). Use `page.mouse.down/move/up` directly — `dragTo()` doesn't work.

**Stable selectors:**

- Palette tile: `[data-builder-component="true"][data-node-type="<type>"]`
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

**Sibling drops.** Once root is occupied, hover the **edge** of an existing node for a drop indicator, or wrap children in a `box`/`vstack`/`hstack`.

**Also works programmatically:** Layers row + `Delete`; Save button; right-panel tab switches; opening Configuration / URL Pattern modals; reading iframe state via `frameLocator`; switching palette accordion sections.

## See also

- `install-studio` — install SDKs and wire `studioSdk.init` at the app shell.
- `setup-section-preview` — add the `<StudioCanvas />` route for previewing Sections in Studio.
- `docs/33-freeform/freeform-templates.md`, `page-data-tab.md`, `pinned-entries.md`, `pinned-queries.md` — reference documentation.
