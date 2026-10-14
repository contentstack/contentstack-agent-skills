---
name: configure-slot-defaults
---

## When to use

Set a Section Slot's Default section (render-time fallback when a placement leaves the slot empty) and Allowed sections (whitelist gating which sections a composer may drop). Use Studio UI, driven through Playwright per [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md). Don't hand the clicks to the user or switch to the API unless they ask; that's [`author-composition-via-api`](author-composition-via-api.md).

Use when a section exposes a Section Slot and the section author wants it to render something before anyone fills it, or wants to restrict what drops in. Phrases: "default section for the slot", "pre-fill empty slot", "only allow these sections", "restrict what drops into a slot". Do NOT use to create the slot: that's `use-section-slot`.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Configure Slot Defaults & Allowed Sections

## Context

> **Prerequisite: the slot must already exist.** Both settings are authored on an existing Section Slot. If the section has no slot yet, run [`use-section-slot`](use-section-slot.md) first. If the section canvas is blank, run [`setup-section-preview`](setup-section-preview.md).

A Section Slot is an empty opening the next composer fills. Two optional settings let the **section author** shape that opening without giving up "anything goes":

- **Default section**: one section that renders when a placement leaves the slot empty, so the section shows something useful before anyone touches it.
- **Allowed sections**: a whitelist of which sections a composer may drop into the slot.

Both are per slot, both optional, and a slot with neither behaves exactly as before: empty until filled, accepts anything.

Two properties that drive every judgment call below:

- **The default is a render-time fallback, never a copy.** It lives only as a setting on the slot: nothing is written into the placement. Editing the default section later updates every empty slot pointing at it, and clearing a filled slot brings the default back.
- **An empty allowed list means no restriction**, not "allow nothing". The whitelist gates **sections only**: a composer can always drop plain components into a restricted slot.

Stored on the slot node in the section's `ui` as `metadata.defaultSection` (a single `{ uid, _content_type_uid }` ref) and `metadata.allowedSections` (an array of the same). At save time the default is captured in the section's `linked_sections`. The allowed list deliberately is not, because it never renders.

## When the default renders

| Slot state | Section's own authoring canvas | Placement: Design mode | Preview mode | Deployed site |
| --- | --- | --- | --- | --- |
| Empty | Labeled placeholder (default **not** shown) | Drop zone + a hint naming the default | Renders the **default** | Renders the **default** |
| Empty, no default set | Labeled placeholder | Drop zone | Collapses to nothing | Collapses to nothing |
| Filled | - | Dropped content + drop affordances | Dropped content | Dropped content |

Design mode keeps the drop zone on purpose: design is for building, preview is for seeing the result. A composer who drops the section and flips to Preview immediately sees a meaningful result.

## Task

1. **Open the section in section authoring mode**: not a page. These settings live on the section that owns the slot. Selecting a placed section's slot on a page opens a different panel (it lists what the composer has put in the slot).

2. **Select the Section Slot node** on the canvas or in Layers. Open the right panel's **Settings** tab (gear icon; the **Data** tab is page data), then **Properties**. Two controls appear, in this order:

   | Control | Shape | Placeholder |
   | --- | --- | --- |
   | **Allowed sections** | multi-select | Select Sections |
   | **Default section** | single-select, clearable | Select a default section |

   Both pickers search by title and page through the project's sections from the server (30 per request), so they reach every section, not just recently loaded ones. Both exclude the section currently being edited.

3. **Set Allowed sections first when you want both.** Saving a non-empty allowed list clears a Default section that isn't in that list: pick the whitelist, then the default, and the default picker offers exactly the allowed set.

4. **Pick the allowed sections.** Choose the sections that genuinely fit the opening's role and size. Leave the field empty to keep the slot open to anything. That is the correct choice unless a wrong drop would break the design.

5. **Pick the Default section.** Choose one that reads as a sensible empty state (a placeholder media block, an empty-state card), not a section carrying real marketing copy: it renders on the live site until someone fills the slot. Clear the field to remove the default.

6. **Save the section.**

7. **Verify on a page.** Drop the section onto a page or template:
   - Design mode: the empty slot shows its drop copy plus the hint "(When this slot is empty, the default section (**Title**) added by the section author is shown in Preview and on the live page.)"
   - Flip to **Preview**, and the default renders.
   - Drop a real component or section into the slot, and it replaces the default.
   - Delete that content, and the default reappears.

8. **Verify the whitelist** (only if set). Drag a section that is not on the list into the slot. Studio rejects it with "This section isn't allowed in this slot. Choose one of the slot's allowed sections, or drop a different component." and nothing is placed. The in-canvas **Select section** button and the right-panel picker offer only the allowed sections. A plain component still drops in: the gate is sections-only.

## Nested defaults

Defaults chain: if A's slot defaults to B and B's slot defaults to C, placing A and previewing expands the chain, A first, then B, then C, each default filling the next empty slot. Depth is unlimited. Studio resolves the chain with batched fetches, one round per nesting level, not one per section.

Cycles are safe. The pickers list every section and do not gray out choices that would loop, but expansion **stops at render time** as soon as the chain would re-enter a section already in it: a chain of A, then B, then A again renders A, then B, then stops. Keep chains shallow anyway: every level is another fetch round.

## Inputs needed from the user

In this order. Stop and ask if the first two are missing, and require at least one of the last two.

1. `sectionUid`: the section that owns the slot.
2. `slotLabel`: which slot (its drop placeholder label), when the section has more than one.
3. `defaultSectionUid`: the section to render while the slot is empty.
4. `allowedSectionUids`: the sections a composer may drop.

If the user asks for a default that is not in a non-empty `allowedSectionUids`, say so and ask which one wins: writing it silently clears the default.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, surface the failure and stop.

- [ ] The settings are on the **section's** Section Slot node, not on a page-side placement.
- [ ] `defaultSectionUid` shows in the Default section field after save and reload.
- [ ] `allowedSectionUids` all show in the Allowed sections field after save and reload.
- [ ] When both are set, the default is one of the allowed sections.
- [ ] On a placement: the empty slot renders the default in **Preview** and shows the drop zone in **Design**, verified by a PNG screenshot of the canvas iframe, not by an a11y snapshot (iframe contents are opaque to it).
- [ ] Dropping content into the slot replaces the default. Deleting that content restores it.
- [ ] With a non-empty whitelist: a disallowed section is rejected with the warning and nothing is placed. A plain component still drops in.
- [ ] The default section renders correctly on the deployed/preview URL, not only inside Studio.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Setting the Default section before the Allowed list | A non-empty whitelist that excludes the current default clears it, silently | Set Allowed sections first, then the default |
| Expecting the default in Design mode | Design mode keeps the drop zone by design | Flip to Preview, or check the deployed page |
| Expecting the default inside the section's own canvas | The section being authored shows only the labeled placeholder | Verify on a placement, not in section authoring |
| Reading an empty Allowed list as "allow nothing" | Empty means no restriction | To restrict, list the sections explicitly |
| Expecting the whitelist to block components | It gates sections only | Component-level constraints don't exist. Use the slot label to signal intent |
| Expecting the default to be copied into the page | It is never persisted into the placement | Treat it as live config: editing it updates every empty slot pointing at it |
| Real marketing copy in the default section | It renders on the live site until a composer fills the slot | Use an empty-state / placeholder section |
| Looking for these controls on a placed section | The page-side slot panel lists slot contents, not the whitelist | Open the owning section and select its slot |
| Trying to default a slot to its own section | Both pickers exclude the section being edited | Point at a different section. Nested chains handle recursion |
| Deep default chains | One fetch round per nesting level | Keep chains one or two levels deep |
| A circular default that renders nothing | Expansion stops on re-entry: that level renders blank, not an error | Expected. Point the default elsewhere if you wanted content |
| Default's own Repeater renders wrong or throws `items.map is not a function` | The default's data is scoped through a virtual instance. A shape mismatch with the slot's surrounding scope surfaces here | Check the default section's linked schema against the scope the slot sits in: `understand-linked-schemas`, `troubleshoot-data-binding` |
| Selected sections show as raw uids | Title lookup is best-effort and falls back to the uid | Harmless. Reload the panel, or confirm the section still exists |
| Section titles missing from the design-mode hint | The hint resolves the title from the locally-known catalog and drops it when absent | Cosmetic: the default still renders in Preview |

## See also

- `use-section-slot`: carve the slot before configuring it
- `understand-section-slots`: what fills a slot, and the Section-in-Slot rule
- `expose-section-props`: the value-level sibling (override a prop, not the contents)
- `author-composition-via-api`: writing `metadata.defaultSection` / `metadata.allowedSections` programmatically
