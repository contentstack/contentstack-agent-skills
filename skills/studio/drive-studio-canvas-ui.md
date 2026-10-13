---
name: drive-studio-canvas-ui
---

## When to use

Driving the Studio canvas through browser automation: the drag-and-drop sequence that actually commits, and why the high-level helpers silently do nothing. Read before any skill that moves a component on the canvas via Playwright MCP.

Referenced by `build-section`, `build-connected-template`, `build-freeform-template` and `studio-tour`, which all drive the same canvas.

## LLM execution caveat: drag-drop works, but only with the right sequence

Studio's canvas is a React-DnD iframe. Palette tiles listen on `mousedown` / `mousemove` / `mouseup` (NOT HTML5 native drag), and the drop COMMITS only when mousemove fires intermediate events between mousedown and mouseup. The high-level `dragTo()` helper fires HTML5 `dragstart`/`drop` which Studio does not honor. You must use `page.mouse.down()` / `page.mouse.move({steps})` / `page.mouse.up()` directly.

**Stable selectors (verified by execution):**

- Palette tile: `[data-builder-component="true"][data-node-type="<type>"]` where `<type>` is e.g. `doc-hero`, `doc-card`, `repeater`, `header`, `box`. (Section tiles use the section's composition UID as the type.)
- Canvas iframe: `[data-testid="canvas-iframe"]`
- Drop slot inside the iframe: `[data-composable-studio-slot="true"]` (the `="true"` filter is required. Without it you can match elements that have the attribute but aren't active drop targets)
- Layers row title (to select a node for deletion or inspection): `[data-testid="layer-editable-title-container"]`
- Node IDs (to verify a drop committed): `[data-composable-studio-id]` inside the FrameLocator

**The drop sequence (proven working pattern):**

```ts
const item = page.locator('[data-builder-component="true"][data-node-type="doc-hero"]');
const frame = page.frameLocator('[data-testid="canvas-iframe"]');
const slot = frame.locator('[data-composable-studio-slot="true"]').first();

await page.bringToFront();                               // 0. Chrome holds mouse input to a background tab: calls hang
await item.hover();                                      // 1. position cursor over palette tile
await page.mouse.down();                                 // 2. mousedown → posts PARENT_DRAG_START to iframe
const sb = await slot.boundingBox();
await page.mouse.move(sb.x + sb.width / 2,               // 3. move cursor in STEPS — required for mousemove events to fire
                      sb.y + sb.height / 2,
                      { steps: 10 });
await slot.hover();                                      // 4. final settle on the slot (FrameLocator handles cross-frame)
await page.mouse.up();                                   // 5. mouseup → commits the drop
```

The `page.mouse.move({steps: 10})` between mousedown and mouseup is the critical detail. Without intermediate mousemove events, the iframe's drag-tracking code never registers the path and the drop is silently swallowed.

**Anti-phantom guardrail.** Always verify a NEW `data-composable-studio-id` appeared inside the FrameLocator after each drop:

```ts
const idsBefore = await frame.locator('[data-composable-studio-id]')
  .evaluateAll(els => els.map(e => e.getAttribute('data-composable-studio-id')));
// ... drop sequence ...
let newIds = [];
for (let i = 0; i < 15 && newIds.length === 0; i++) {   // poll up to ~3 s: a commit can land after 800 ms
  await page.waitForTimeout(200);
  const idsAfter = await frame.locator('[data-composable-studio-id]')
    .evaluateAll(els => els.map(e => e.getAttribute('data-composable-studio-id')));
  newIds = idsAfter.filter(id => !idsBefore.includes(id));
}
if (newIds.length === 0) {
  throw new Error('Drop did not commit; do not continue.');
}
```

If `newIds.length === 0`: stop and surface the failure. Do not fabricate completion.

**Sibling drops after the root slot is consumed.** `[data-composable-studio-slot="true"]` exists only while a slot is empty, and the page root has no box (`display: contents`), so releasing in empty space below a node drops nothing. Release **on an existing node**: bottom half inserts below it, top half above, its left/right 10px beside it. The canvas is scaled to fit (1440px frame drawn 1066px wide): page point = iframe rect origin + frame point × (rect width / frame `innerWidth`). Check the frame's `elementFromPoint` there is that node, not an inner child. After `mouse.down()` wait ~150 ms, move with `{steps: 15}` plus two 1–2px nudges, confirm the parent shows `[data-direction="horizontal"]`, then `mouse.up()`.

**Binding through the data picker.** Click the row's title text (`[data-outlinename="<path>"] > span[tabindex="0"]`), not its chevron or toggle. The bind writes to the selected node, so reselect the node if the canvas reloaded. It stuck when the prop shows a binding chip instead of its input.

**Execution-path matrix:**

| Path | Drag-drop status |
|---|---|
| Human in their own Studio browser | **Yes**. Native: this is how authors use Studio every day |
| Playwright with direct `page.mouse.down/move/up` access | **Yes**. Use the proven sequence above |
| Playwright `dragTo()` only | **No**. Fires HTML5 drag events Studio does not honor |
| Synthetic `DragEvent` dispatched from page-context JS | **No**. Same reason |

**What ALSO works programmatically (verified):**

- Click a Layers row and press `Delete`, which removes the node and persists
- Click the Save button, which persists the composition. The button grays out post-save
- Switch right-panel tabs (Settings / Design / Data) via direct DOM clicks
- Open Configuration / URL Pattern / Schema Picker modals via their action buttons
- Read iframe canvas state via `frameLocator` (read-only operations)
- Switch palette accordion sections (Basic / Media / Container / Smart Containers / Registered Components / HTML Elements) via direct DOM clicks
