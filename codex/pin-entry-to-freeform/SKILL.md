# pin-entry-to-freeform


## When to use

Pin a Contentstack entry to a Freeform template via the Additional Entry Data section so components on that template can bind to the entry's fields.

Use only on Freeform templates needing to bind components to a specific entry — "pin this entry", "I can't find my entry on this template", "Pinned Entry missing from Data Picker". Connected templates auto-bind via their content type so they don't expose Additional Entry Data. Do NOT use on Connected templates; for dynamic lists use `pin-query-to-freeform`.

# Pin Entry to Freeform Template

> **Prerequisite:** this skill assumes you've already chosen Freeform via `choose-connected-vs-freeform`. If you haven't, run that first — Connected is the recommended default in Studio and most pages should use it (including one-off pages, via a single-entry CT). Freeform is the documented exception, not a parallel option. This skill remains valid for the legitimate Freeform cases; it just shouldn't be your starting point.

## Context

Freeform templates have no inherent connection to a content type, so by default their components have nothing to bind to beyond `template.*` exposed props and static values. The **Additional Entry Data** section on the template's Data tab lets an author "pin" one or more Contentstack entries to the template; once pinned, every component on the template can bind props to that entry's fields through the Data Picker under the **`Additional Entry Data` → &lt;title&gt;** root.

This is a Freeform-only flow. Connected templates auto-bind to a single entry via their connected content type, and the right panel does not render the Additional Entry Data section at all on a Connected template — you bind through `Linked Template Entry` instead.

Reference: `docs/33-freeform/pinned-entries.md`.

Mental model:

- Pinned entries are a **template-level** resource. They live on the template, not on any single component.
- They show up in the Data Picker as a binding root, **alongside** (not replacing) `template.*` exposed props, `Component Default Data`, and any `Pinned Queries`.
- The Data tab is **context-sensitive**: with nothing selected it shows template-level config (Additional Entry Data, Pinned Queries); with a component selected it shows that component's bindings. You must deselect to reach the pin UI.

## Task

1. **Confirm the template is Freeform.** Open `templateName` in Studio and look for the **FREEFORM MODE** badge on the canvas. If you see a Connected template indicator instead, stop — pinning does not apply; bind via `Linked Template Entry`.

2. **Verify Freeform is enabled at the project level.** In project settings, confirm **Enable Freeform Feature** is on. Without it, the Data tab does not render at all and you'll incorrectly conclude pinning is broken.

3. **Deselect any component on the canvas.** Click an empty area of the canvas so no component is selected. If a component is selected, the Data tab swaps to component-level bindings and Additional Entry Data is not visible.

4. **Open the Data tab and expand Additional Entry Data.** Right panel → **Data** tab → expand the **Additional Entry Data** accordion → click **Link Entry**.

5. **Pick the entry.** In the entry picker modal:
   - Filter by content type using `entryContentTypeUid`.
   - Search by title using `entrySearchTerm`.
   - Select the matching entry.
   - Confirm.

6. **Verify the pin landed.** The Additional Entry Data section should now list the pinned entry with its title and content type label. It will remain visible whenever the template is loaded with no component selected.

7. **Bind a component prop to a pinned-entry field.** Select any component on the canvas, click the binding chip next to a prop in the right panel, and in the Data Picker navigate **`Additional Entry Data` → &lt;entry title&gt; → &lt;field&gt;**. Confirm. The canvas should re-render with the live field value.

8. **(Optional) Bindings inside a Repeater.** If you bind a Repeater's source to a reference field on the pinned entry, every reference inside that Repeater — single-CT or multi-CT — needs a **Condition Block** before its fields are reachable. Iteration-scoped bindings use `repeater.<field>`; template-level bindings continue to use `template.<field>`. Pinned-entry bindings appear as their own root and are neither.

## Inputs needed from the user

Collect in this order. If any is missing, ask before clicking anything in Studio.

1. `templateName` — the Freeform template to pin onto.
2. `entryContentTypeUid` — the content type UID to filter by in the picker.
3. `entrySearchTerm` — title or UID to locate the specific entry.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, surface the failure and stop.

- [ ] The template displays the **FREEFORM MODE** badge.
- [ ] **Enable Freeform Feature** is on at the project level.
- [ ] With nothing selected on the canvas, the right panel's **Data** tab shows **Additional Entry Data** with the pinned entry listed (title + content type).
- [ ] With a component selected, the Data Picker shows **`Additional Entry Data` → &lt;title&gt;** as a binding root.
- [ ] A prop bound via `Additional Entry Data → <entry title> → <field>` renders the entry's live value on the canvas — verified by inspecting a PNG screenshot of the canvas iframe (a11y snapshots are opaque to iframe contents).
- [ ] Unpinning the entry removes the **Pinned Entry** root from every component's Data Picker on that template.

## Verifying the runtime render

If you want to confirm the pinned entry flows through at runtime (not just in Studio), the canvas-app side uses:

```tsx
// SSR — sdk.fetchCompositionData returns StudioComponentSpecOptions directly
const specOptions = await sdk.fetchCompositionData({ compositionUid: "<your-freeform-uid>" });
if (!specOptions.hasSpec) return notFound();
return <StudioComponent specOptions={specOptions} />;
```

The pinned entry data is embedded inside `specOptions.spec` — you do NOT pass it via the `data` prop. `data` is a separate `Record<string, any>` for runtime Component Default Data (external data outside Contentstack — live pricing, geo, etc.).

The Freeform composition URL only carries `{{composition_uid}}` plus `{{environment}}` and `{{branch}}` — it does **not** carry `{{entry.*}}` or `{{content_type_uid}}`. The pin is resolved server-side from the composition itself. (`{{locale}}` is accepted by the pattern engine but not recommended in URL patterns; carry locale via your routing layer + the SDK `locale` query option.)

## Common pitfalls

| Pitfall | Symptom | Fix |
| --- | --- | --- |
| Pinning attempted on a Connected template | No Additional Entry Data section in the Data tab | Use the Connected template's `Linked Template Entry` binding root instead; this skill does not apply. |
| A component is selected while opening the Data tab | Data tab shows component bindings; no Additional Entry Data section | Click empty canvas to deselect, then reopen the Data tab. |
| Enable Freeform Feature is off at the project level | Data tab does not render at all on Freeform templates | Toggle Enable Freeform Feature on in project settings. |
| Picker filter not set to `entryContentTypeUid` | Wrong / too many entries in the search list | Apply the content-type filter before searching by title. |
| Reference field inside a Repeater bound without a Condition Block | Reference fields don't appear in the Data Picker under the repeater iteration | Wrap the reference in a Condition Block (required for single-CT and multi-CT alike). |
| Mixing iteration vs template scope | `repeater.<field>` used outside a Repeater, or `template.<field>` used for per-iteration data | Use `repeater.<field>` only inside a Repeater iteration; `template.<field>` only for template-level exposed props; `Additional Entry Data` → …` is its own root. |

## See also

- `docs/33-freeform/pinned-entries.md` — full reference.
- Pair with `build-freeform-template` when introducing the template for the first time.
- Pair with `expose-section-props` when the same template also needs author-editable `template.*` props alongside pinned-entry bindings.
