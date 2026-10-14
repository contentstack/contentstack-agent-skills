---
name: pin-entry-to-freeform
---

## When to use

Pin a Contentstack entry to a Freeform template, or to any template or Section, via the Pinned Entries section so components there can bind to the entry's fields. Use Studio UI, driven through Playwright per [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md). Don't hand the clicks to the user or switch to the API unless they ask; that's [`author-composition-via-api`](author-composition-via-api.md).

Use on Freeform templates needing to bind components to a specific entry — "pin this entry", "I can't find my entry on this template", "Pinned Entry missing from Data Picker" — and on a Connected template or Section that needs one fixed entry beside the page's own, such as a header or footer reading a shared site-settings entry. A Connected template's own entry binds through its content type, not a pin; for dynamic lists use `pin-query-to-freeform`.

> **⛔ Auth preflight — settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` — it needs a TTY and a browser, so it cannot be run for them — and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Pin Entry to Freeform Template

> **Prerequisite:** this skill assumes you've already chosen Freeform via `choose-connected-vs-freeform`. If you haven't, run that first — Connected is the recommended default in Studio and most pages should use it (including one-off pages, via a single-entry CT). Freeform is the documented exception, not a parallel option. This skill remains valid for the legitimate Freeform cases; it just shouldn't be your starting point.

## Context

Freeform templates have no inherent connection to a content type, so by default their components have nothing to bind to beyond `template.*` exposed props and static values. The **Pinned Entries** section on the template's Data tab lets an author "pin" one or more Contentstack entries to the template; once pinned, every component on the template can bind props to that entry's fields through the Data Picker under the **`Pinned Entries` → &lt;title&gt;** root.

Pinned Entries is on every composition type: Freeform and Connected templates and Sections (checked 2026-10-07 in a project with Enable Freeform Feature on). A Connected template binds **its own** entry through `Linked Template Entry`; pin an entry only for data that is not the page's own, such as a shared site-settings entry. **For a header or footer**, pin the settings entry on the header or footer **Section itself** (open the Section, Data tab), not on each template: every placement is then filled with no per-placement setup ([`plan-studio-architecture`](plan-studio-architecture.md) § 0c).

**A placed section is rooted, not bound field by field.** The pinned-entry root above is for components authored directly on the template. A *section* dropped on the template resolves through its own per-placement **Section Data** row (right panel → **Properties**): root the placement at the pinned entry via the **Entire Entry** row, or at a field inside it, and the section's internal bindings resolve against that document. The Section Data picker offers only targets whose structure matches what the section declared, so an incompatible entry simply doesn't appear.

Mental model:

- Pinned entries are a **template-level** resource. They live on the template, not on any single component.
- They show up in the Data Picker as a binding root, **alongside** (not replacing) `template.*` exposed props, `Component Default Data`, and any `Pinned Queries`.
- The Data tab is **context-sensitive**: with nothing selected it shows template-level config (Pinned Entries, Pinned Queries); with a component selected it shows that component's bindings. You must deselect to reach the pin UI.

## Task

1. **Confirm the template is Freeform.** Open `templateName` in Studio and look for the **FREEFORM MODE** badge on the canvas. If you see a Connected template indicator instead, stop — pinning does not apply; bind via `Linked Template Entry`.

2. **Verify Freeform is enabled at the project level.** In project settings, confirm **Enable Freeform Feature** is on. Without it, the Data tab does not render at all and you'll incorrectly conclude pinning is broken.

3. **Deselect any component on the canvas.** Click an empty area of the canvas so no component is selected. If a component is selected, the Data tab swaps to component-level bindings and Pinned Entries is not visible.

4. **Open the Data tab and expand Pinned Entries.** Right panel → **Data** tab → expand the **Pinned Entries** accordion → click **Link Entry**.

5. **Pick the entry.** In the entry picker modal:
   - Filter by content type using `entryContentTypeUid`.
   - Search by title using `entrySearchTerm`.
   - Select the matching entry.
   - Confirm.

6. **Verify the pin landed.** The Pinned Entries section should now list the pinned entry with its title and content type label. It will remain visible whenever the template is loaded with no component selected.

7. **Bind a component prop to a pinned-entry field.** Select any component on the canvas, click the binding chip next to a prop in the right panel, and in the Data Picker navigate **`Pinned Entries` → &lt;entry title&gt; → &lt;field&gt;**. Confirm. The canvas should re-render with the live field value.

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
- [ ] With nothing selected on the canvas, the right panel's **Data** tab shows **Pinned Entries** with the pinned entry listed (title + content type).
- [ ] With a component selected, the Data Picker shows **`Pinned Entries` → &lt;title&gt;** as a binding root.
- [ ] A prop bound via `Pinned Entries → <entry title> → <field>` renders the entry's live value on the canvas — verified by inspecting a PNG screenshot of the canvas iframe (a11y snapshots are opaque to iframe contents).
- [ ] Unpinning the entry removes the **Pinned Entry** root from every component's Data Picker on that template.

## Verifying the runtime render

If you want to confirm the pinned entry flows through at runtime (not just in Studio), the canvas-app side uses:

```tsx
// SSR — fetchCompositionData THROWS on a miss (it does not resolve with
// hasSpec:false), so an unwrapped call 500s instead of 404ing. A compositionUid
// lookup throws COMPOSITION_UID_NOT_FOUND (not NO_COMPOSITION_FOR_URL). Wrap it:
// configure-csr-vs-ssr § "fetchCompositionData does not return not-found".
const { specOptions, notFound: miss } = await resolveComposition(sdk, {
  compositionUid: "<your-freeform-uid>",
});
if (miss) return notFound();
return <StudioComponent specOptions={specOptions} />;
```

The pinned entry data is embedded inside `specOptions.spec` — you do NOT pass it via the `data` prop. `data` is a separate `Record<string, any>` for [runtime Component Default Data](wire-external-data.md) (external data outside Contentstack — live pricing, geo, etc.).

The Freeform composition URL only carries `{{composition_uid}}` plus `{{environment}}` and `{{branch}}` — it does **not** carry `{{entry.*}}` or `{{content_type_uid}}`. The pin is resolved server-side from the composition itself. (`{{locale}}` is accepted by the pattern engine but not recommended in URL patterns; carry locale via your routing layer + the SDK `locale` query option.)

## Common pitfalls

| Pitfall | Symptom | Fix |
| --- | --- | --- |
| Pinning the page's own entry on a Connected template | It already binds through `Linked Template Entry`; a pin duplicates it | Pin only other, fixed entries (shared site settings); bind the page's own fields through `Linked Template Entry` |
| A component is selected while opening the Data tab | Data tab shows component bindings; no Pinned Entries section | Click empty canvas to deselect, then reopen the Data tab. |
| Enable Freeform Feature is off at the project level | Data tab does not render at all on Freeform templates | Toggle Enable Freeform Feature on in project settings. |
| Picker filter not set to `entryContentTypeUid` | Wrong / too many entries in the search list | Apply the content-type filter before searching by title. |
| Reference field inside a Repeater bound without a Condition Block | Reference fields don't appear in the Data Picker under the repeater iteration | Wrap the reference in a Condition Block (required for single-CT and multi-CT alike). |
| Section dropped on the template renders component defaults | Pinning an entry does not bind a placed section — a section resolves through its own root, not the template's binding roots | Select the placement → **Properties → Section Data** → pick the pinned entry (**Entire Entry**) or a matching field inside it |
| Mixing iteration vs template scope | `repeater.<field>` used outside a Repeater, or `template.<field>` used for per-iteration data | Use `repeater.<field>` only inside a Repeater iteration; `template.<field>` only for template-level exposed props; `Pinned Entries` → …` is its own root. |

## See also

- Pair with [`build-freeform-template`](build-freeform-template.md) when introducing the template for the first time.
- Pair with [`expose-section-props`](expose-section-props.md) when the same template also needs author-editable `template.*` props alongside pinned-entry bindings.
- [`understand-linked-schemas`](understand-linked-schemas.md) § *Part 3 — Section Data* — rooting a placed section at a pinned entry, a field inside it, or a query.
