---
name: troubleshoot-data-binding
description: "Symptom-mapped diagnostic for bound fields rendering incorrectly — covers binding paths, type mismatches, repeater item context, and condition-block parent dependency."
allowed-tools: Read Grep Glob
---

## When to use

Symptom-mapped diagnostic for bound fields rendering incorrectly — covers binding paths, type mismatches, repeater item context, and condition-block parent dependency.

Use when a binding is wired but renders the wrong value, an empty value, the literal path, or breaks at runtime. Phrases — "binding shows nothing", "wrong value rendering", "literal {{...}}". If the symptom is ambiguous, route via `troubleshoot` first. Do NOT use for canvas iframe failures (use `troubleshoot-canvas`), SSR errors (`troubleshoot-ssr-rendering`), or URL resolution (`troubleshoot-composition-resolution`).

# Troubleshoot Studio data binding

## Context

Data binding in Studio flows through three layers, each with distinct failure modes:

1. **Authoring (Studio editor)** — the user picks a field via the Data Picker. The picker enforces type / shape rules at selection time; violations surface as inline modal errors.
2. **Spec validation (registry)** — when a component is registered, the SDK checks each prop's declared type against incoming bindings. Mismatches log in editor mode.
3. **Runtime resolution (SDK data-binder)** — at render time, the SDK walks the binding path against actual data, falls back to static value or type-default if missing, and `console.warn`s on type mismatches **in production only** (editor mode suppresses them).

Almost every "field renders wrong" report maps to one of these three layers. This skill walks symptom → failing layer → UI control.

## Diagnostic tooling — inspecting a stored composition's `ui`

Binding-shape debugging often needs the *actual* stored shape — what the Data Picker emitted into the composition. Fetch via the Studio API; the **`ui`** field comes back as **`zlib:<base64>`** — a literal `zlib:` prefix + base64-encoded zlib-deflated JSON. Decode for read-only inspection:

```js
// Node 18+. Save as inspect-ui.js
import zlib from "node:zlib";

function decodeUi(ui) {
  if (!ui.startsWith("zlib:")) return JSON.parse(ui);  // legacy plain-JSON fallback
  const bytes = Buffer.from(ui.slice("zlib:".length), "base64");
  return JSON.parse(zlib.inflateSync(bytes).toString("utf8"));
}

const composition = JSON.parse(await new Response(process.stdin).text());
console.log(JSON.stringify(decodeUi(composition.ui), null, 2));
```

The reliable debugging move when bindings misbehave is: capture a *working* composition that was hand-authored through the UI, decode its `ui`, and diff your broken composition's tree against it. Bindings, data-source resolution, repeater metadata — they're all visible in the decoded tree.

**Read-only — for debugging.** Don't modify bindings by writing back to the API; use the Data Picker. Hand-edited bindings drift from the shape Studio expects and reproduce exactly the failure mode you're trying to debug.

## Task

1. **Note the surface** the user is on. Some symptoms only appear in production (the type-mismatch console warning is silenced in editor mode). Live Preview also has different fallback behavior than a raw production page.
2. **Match the symptom** to the table below — exact wording matters less than category.
3. **Run the "Check first" step.** If it confirms the cause, propose the fix. If not, run the secondary check.
4. **Report:** symptom → cause → check → fix. Cap at two checks; escalate to engineering if both come back negative, sharing the page URL, the binding path from Properties, and the data payload (DevTools Network tab → composition / entry fetch responses).

### Symptom → cause matrix

| Symptom (verbatim or paraphrased) | Likely cause | Check first | Fix |
|---|---|---|---|
| **"Invalid binding"** marker in the Layers panel | Condition Block's condition binding is null/undefined, or the binding resolves to no data. | Properties → Conditions → is the picker actually populated? | Re-select the field via the picker. If parent (section/repeater/template) is itself unbound, bind it FIRST (Condition Block depends on parent context). |
| **"No source configured"** in Layers | Binding was set, then the source field was deleted from the schema or the data source was disconnected; static value is still rendering as fallback. | Open Properties → Data — does the binding chip look empty or stale? | Click the picker, re-bind the field. Static value persists as a fallback when the binding goes stale; both can coexist. |
| **"Direct binding isn't supported because this field has no data—use a repeater to bind it to the schema"** | The chosen data path resolved to an empty array. The picker blocks expanding empty arrays at selection time. | Confirm the upstream data has items (Live Preview / production payload). | If iterating, wrap with a Repeater bound to the array field, then bind nested props inside the iteration context. |
| **"Primitive fields cannot be selected when binding nested repeaters. Only array fields are allowed."** | Tried to bind a nested Repeater's `items` to a primitive (string / number / boolean) field. | Check the picked field's type in the schema. | The field must be `type: "array"`. Pick a different field, or restructure upstream data so the iteration source is an array. |
| **"Non-array object fields (like JSON editor) cannot be selected when binding nested repeaters."** | Same picker, tried to bind a nested Repeater's `items` to an object/JSON-editor field. | Check the picked field's type. | The binding must point to an array. Transform object → array of entries upstream if you genuinely need to iterate object keys. |
| **Browser console warning:** `Data binding type mismatch in component "...": Expected prop "..." to be ... but received ...` | At runtime, the SDK saw a type that doesn't match the registered prop's declared `type`. **Only logged in production-style render**; editor mode suppresses it. | Open DevTools console on the published page; filter `Data binding type mismatch`. | Reconcile the schema. Either change the prop's declared type, or change the bound field, or insert a transformation in code. Don't silence the warning — it always indicates a real type drift. |
| **Field renders a hardcoded default (or empty string / 0 / false) instead of CMS data** | Binding path didn't resolve in the actual data, so the SDK used the static value / default value (then a type-default if both are absent). | DevTools Network → composition fetch → find the binding's path in the response. Does the path exist? | (a) If path is wrong: re-bind via picker. (b) If path is correct but value is `null`/missing: fix upstream content. (c) Set a non-empty static value as visible fallback if the field is legitimately optional. |
| **Console:** `[Composable Studio SDK] useData() was called outside a DataCtxProvider` (dev only, client only) | A basic component (Repeater / ConditionBlock / SectionComposition) rendered without its parent `DataCtxProvider`. Hook returns empty data and warns. | Confirm the component tree wraps the basic component with `<StudioComponent>`. | Always render compositions inside `<StudioComponent>` (it provides `DataCtxProvider` with the spec). If you're using a basic component directly outside that wrapper, wrap it explicitly. This is a render-tree shape issue, not a binding-path issue. |
| **Repeater renders one iteration on the Studio canvas; production renders the correct N** | Repeater's authoring default is to render a single iteration with placeholder/default values so authors can lay out the structure without depending on bound data. Production iterates the real array. | Repeater Preview Mode toggle in Properties. | Select the Repeater node in Layers, toggle **Preview Mode** in Properties — canvas re-renders with real iteration data. (If production *also* renders one or zero iterations, the binding itself is wrong — re-check the bound array field in the data payload.) |
| **Repeater renders no iterations in production / SSR** | During SSR, `useData()` returns empty data (no items), so the Repeater iterates 0× until hydration attaches real context. | View page source (no JS): Repeater HTML is minimal. | This is expected for SSR. If the items don't appear AFTER hydration either, the issue is upstream: `specOptions.data.dataSources` doesn't contain the items, or the binding path is wrong. Check the Network payload. See `troubleshoot-ssr-rendering` for further SSR-specific failure modes. |
| **Condition Block's field picker shows no options** | Parent node (section / repeater / template) has no binding set, or its binding hasn't resolved. Condition is a child of the parent's data context. | Select the parent in Layers; check its binding in Properties → Data. | Select the parent in Layers FIRST. In Properties → Data, verify a binding is set. Then return to the Condition Block — its picker now lists fields from the parent context. |
| **Component prop's declared type doesn't match what the binding supplies (editor-side warning)** | Component registry validates declared types against incoming bindings. Mismatch surfaces in the editor (not as a thrown error, as a warning). | Look for the warning in the editor's console alongside the component name. | Open the component's registration (where `registerComponent` was called). Reconcile the `type` declaration with what the binding actually returns. If the mismatch is intentional (e.g. number → string), clear the binding and use a static value, or transform upstream. |
| **Empty render that worked seconds ago, no code changes** (grid suddenly empty, list blank, etc.) | A **transient 5xx from the Studio API** — `/composable-studio-api/v1/projects/...` returns 503 / 502 / 504 intermittently and Studio renders nothing. Not your binding. | DevTools Network → filter `composable-studio-api` → 503 / 502 / 504 around the time it went empty? If yes, that's the cause. | **Reload.** Don't chase a transient 5xx through the binding-debug path above — empty renders from upstream blips look identical to real binding failures and will cost an hour. Only if the 5xx reproduces consistently is it no longer transient; escalate with the API path + project ID + timestamp. See `troubleshoot-canvas` for the canonical row on this symptom. |
| **Section renders blank in production AND in the editor canvas** — the section is dropped on a template but shows no content / repeats nothing / shows one empty placeholder | The section's scope (`selectedField`) didn't resolve. Sections are data-less standalone (`author-composition-via-api` § *How a Section gets data*); they only fill out when placed on a template. If the resolved `selectedField` is wrong / missing, the section's `dataSources.template` is undefined or empty → repeaters render nothing → blank section. Common causes: `linked_schemas` dropped by the compositions CT (P23 trap — modeled as reference instead of group-multiple), `selectedField` points at a field that doesn't exist on the page CT, the page entry's field is genuinely empty, missing `data_sources.resolvedReferences` for a reference path. | Dump `section_scoped_data` via the SSR cold-load — see [`verify-setup`](../verify-setup/SKILL.md) § *Layer 7*. For every section instance, that map shows the resolved `selectedField` + the actual scoped `template`. If `template` is undefined / empty / wrong-shape, the section's scope is broken. | Fix per the failure class: `linked_schemas` trap → re-model the compositions CT field as group-multiple AND populate `sectionBindingOverride` on each `section-composition` node (see `author-composition-via-api` § *The linked_schemas-as-reference trap*). Wrong `selectedField` → fix the section's `linked_schemas` to point at a field that exists on the page CT. Missing `resolvedReferences` → see `author-composition-via-api` § *Repeat a card over a multi-reference field*. |

### When the symptom maps to none of the above

These failure modes have **no diagnostic surface** in the codebase as of the current SDK alpha:

- **Manually typed binding path with a typo** — silently falls through to fallback. Picker-only authoring avoids this; if you find a hand-edited binding string, re-set it through the picker.
- **Repeater item context lost inside a deeply nested Section Slot** — propagation is implicit via `DataCtxProvider`; no warning if the context doesn't reach the slot's subtree.
- **Schema mismatch between Studio's composition and runtime `ComponentData` you pass in code** — the SDK uses fallback values, no validation error.
- **CSLP-append behavior when `appendTags: false`** — content renders un-tagged with no UI indication.
- **Data source fetch timeout / network failure** — picker may stall without a banner unless the adapter explicitly surfaces it.

If the symptom fits none of the rows above and is not in this silent-failure list, escalate to engineering with: the page URL, the bound field's path from Properties, the actual data payload from DevTools Network, and the SDK version (`grep '"@contentstack/studio-client"' package.json`).

## What this skill is NOT

- Not a guide to authoring bindings from scratch — use `build-connected-template` / `build-section`.
- Not a guide to wiring external data — use `wire-external-data` / `wire-component-default-data`.
- Not for live-site URL resolution (use `troubleshoot-composition-resolution`).
- Not for canvas iframe / Studio editor failures (use `troubleshoot-canvas`).
- Not for SSR / RSC boundary errors (use `troubleshoot-ssr-rendering`).
