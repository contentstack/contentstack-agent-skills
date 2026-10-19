---
name: build-freeform-template
---

## When to use

Author a Freeform (Static) template with Pinned Entries and Pinned Queries. Connected is the default. Freeform is the last resort. Use Studio UI, driven through Playwright per [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md). Don't hand the clicks to the user or switch to the API unless they ask; that's [`author-composition-via-api`](author-composition-via-api.md).

Use ONLY when the page genuinely cannot be modelled by any content type (not even a single-entry CT). First run `choose-connected-vs-freeform`. If its recommendation is Connected, stop and use `build-connected-template` instead. Reach for this when the page composes from multiple unrelated sources with no anchor CT. Three-AND Freeform rule applies.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Pattern preflight: mandatory.** Before the first write, run [`match-existing-pattern`](match-existing-pattern.md): read the Templates and Sections already in the project, **reuse what already covers this schema**, and build to the pattern they use. Skip it only when the project has no compositions at all. Authoring something structurally foreign to what is there is rework, and it is invisible until someone opens the Layers panel.

# Build a Freeform template

> **Approved plan required.** This skill builds. It does not decide. If there is no plan the user has explicitly approved (Sections with their linked schemas, Section Slots, per-Section components (registered vs built-in), bindings, and the template kind), **stop and run [`plan-studio-architecture`](plan-studio-architecture.md) first**, then come back with the approved block for this piece. Building without it is how a project ends up as one monolithic template with no Sections, no slots and no reuse. Exception: the user is explicitly iterating on a piece already in an approved plan.

## STOP: Freeform is the very very very last resort

**Reach for Freeform only after confirming ALL THREE of these are true:**

1. **Short-lived**: the page has an expected end date (campaign, splash, takeover, time-boxed promo).
2. **Owns ZERO content of its own**: no hero copy, no page-specific title, no subheading, no CTA text, no callouts. Literally nothing the page itself authors. Hero copy IS content. "Throwaway HTML" is owned content in disguise.
3. **Visible content is 100% assembled from existing entries**: pinned entries, pinned queries, references into existing CTs. The page is a pure vitrine.

If ANY of those is missing (even a hero title specific to this page) the page has owned content. Owned content belongs in a CT, which means **Connected** (single-entry CT for one-offs, multi-entry / `campaign` CT for recurring shapes). Most pages users initially tag as Freeform DO own copy and should be Connected.

**If you arrived here without running `choose-connected-vs-freeform` or `plan-studio-architecture`, stop and run one of those.** This skill exists for genuine vitrine cases. They are rare.

## Before you start: confirm Freeform is the right choice

If you haven't already run `choose-connected-vs-freeform`, do that first. Only proceed when every Connected option (existing CT, extended CT, single-entry CT) has been ruled out. The Project-level **Enable Freeform Feature** toggle is often deliberately OFF. If off, usually leave it off and create a CT.

**Section-qualification rule still applies.** Before dropping components + bindings directly on this Freeform template, apply the golden rule from [`plan-studio-architecture`](plan-studio-architecture.md) § Step 2: **Reused across Templates?** Build a Section first. **Schema iteration (MB / multi-ref / group-multiple)?** Build a List Section first. Freeform doesn't exempt you from this. A shared Header pinned to two Freeform pages must be a Section, and a Pinned-Query Repeater rendering N items belongs in a List Section, not authored inline.

## Context

**Freeform** (labeled **Static Template** in the create modal, **FREEFORM MODE** on canvas, same thing) is not tied to a content type. Bring data in by pinning entries and queries directly on the template. Use only as the documented exception.

The right panel (nothing selected) surfaces three sections:

- **Pinned Entries**: explicitly chosen single entries. Bindable roots in the Data Picker.
- **Pinned Queries**: saved CDA queries. Repeater item sources.
- **External Data**: non-Contentstack sources via Component Default Data at runtime.

## Prerequisite

In Project Configuration, **Enable Freeform Feature** must be ON. Without it, the right panel collapses to **Settings only**, no Design tab, no Data tab, no way to pin. If the user sees only Settings, stop and direct them to flip the feature flag at the project level before continuing.

## Task

1. **Confirm Freeform is enabled** on the Studio project. If not, instruct the user to open Project Configuration and toggle **Enable Freeform Feature** on, then resume.

2. **Create the template.**
   - From the Studio templates list, click **New Template**.
   - In the Create New Template chooser modal, pick **Freeform** (the chooser's two options are Connected Template and Freeform). The follow-up dialog is titled "Create Static Template". Static is Studio's internal name for Freeform. Same thing.
   - Enter the `templateName` from inputs and confirm.

   On the canvas verify:
   - A **FREEFORM MODE** badge in the top bar (replaces the content-type chip used by Connected templates).
   - A **PREVIEW COMPOSITION:** label (not **PREVIEW ENTRY:**), preview drives off the composition itself.

3. **Edit the URL pattern.**
   - Click the **pencil icon** next to the URL in the canvas navbar to open **Edit URL**.
   - Replace the auto-generated default with `urlPattern` from inputs.
   - The Insert chip row exposes exactly one entry-style variable: `{{composition_uid}}`. There is intentionally no `{{entry.*}}` and no `{{content_type_uid}}`. Freeform has no connected entry/content-type. You may type context vars (`{{environment}}`, `{{branch}}`) by hand. `{{locale}}` is also accepted by the pattern engine but **avoid using it**. The recommended way to carry locale is via your routing layer + the SDK's `locale` query option.
   - Save.

4. **Open the template-level Data tab.**
   - Click empty canvas space to ensure no component is selected (otherwise the right panel switches to component-prop bindings).
   - In the right panel, open the **Data** tab and confirm three accordion sections appear: **Pinned Entries**, **Pinned Queries**, **External Data**. Empty state reads "No Data Connected Yet".

5. **Pin an entry (Pinned Entries).** If `pinnedEntryContentTypeUid` was provided:
   - In the **Pinned Entries** section click the empty-state prompt / **Link Entry** button.
   - In the entry-picker modal, set the content-type filter to `pinnedEntryContentTypeUid`.
   - Use search/sort/checkbox selection in the entries table, then click **Add Selected Entries**.
   - The pinned entry now appears with its title + content type and is bindable from any component's Data Picker.
   - Re-pinning (swap to a different entry of the same shape) preserves existing bindings.

6. **Pin a query (Pinned Queries).** If `pinnedQueryContentTypeUid` was provided:
   - In the **Pinned Queries** section click **+ New Query**.
   - In the **New Query** modal fill **Name** and set **Content Type** = `pinnedQueryContentTypeUid`.
   - Either configure filters/order/limit directly, or type a free-text prompt in **"Tell me what data you need"**. Quick-prompt seeds include "Show the last 5 recent entries", "List all entries from the past week", "Filter the entries by specific tags", "Fetch the entries containing taxonomy". The prompt is converted to a stored CDA query at save time. It is not re-translated per render.
   - Save. The query appears under **Pinned Queries** with its Name + Content Type.

7. **Bind components on the canvas.**
   - Drop a card, hero, or other component, then in the right panel open the **Data** tab and click a prop. The **Data Picker** opens. Pinned entries appear as bindable roots alongside their fields.
   - For lists: drop a **Repeater**, bind **Items** to a Pinned Query, then drop the iteration component inside the Repeater body. Bindings inside resolve against the current iteration (`repeater.<field>`).
   - Static prop values and Component Default Data remain available for purely presentational content.

8. **Verify the rendered route.** The host app's catch-all route (default + recommended: `app/[[...slug]]/page.tsx` for Next.js, `<Route path="*">` for React Router) mounts `<StudioComponent />` and handles every URL, including the freeform template's resolved `urlPattern`. No per-template route is needed. Studio's CDA query inside `sdk.fetchCompositionData` resolves the composition.

   Open the resolved URL in the browser to confirm the pinned content appears. If it 404s, the catch-all isn't wired. Run [`setup-template-preview-routes`](setup-template-preview-routes.md) first.

## Inputs needed from the user

In order. Two are optional. Skip the corresponding step if blank.

1. `templateName`: template display name (required)
2. `urlPattern`: URL pattern. Defaults to `/compositions/{{composition_uid}}` (required). Avoid encoding `{{locale}}`. Carry locale via routing + the SDK `locale` query option.
3. `pinnedEntryContentTypeUid`: optional. Skip step 5 if blank
4. `pinnedQueryContentTypeUid`: optional. Skip step 6 if blank

If the user is unsure which content types to pin, ask what data the page needs to show (single entry vs. list) and map accordingly.

## Acceptance

This skill succeeds only when ALL applicable items below are true. If any fails, do not claim success. Surface the failure and stop.

- [ ] **FREEFORM MODE** badge visible in the canvas top bar.
- [ ] **PREVIEW COMPOSITION:** label (not PREVIEW ENTRY) shown in the preview row.
- [ ] Edit URL modal shows the `{{composition_uid}}` chip and no `{{entry.*}}` chips. The saved pattern uses only allowed tokens.
- [ ] With nothing selected on canvas, the right panel's Data tab lists all three sections: Pinned Entries, Pinned Queries, External Data.
- [ ] If a pinned entry was requested, it appears under Pinned Entries with its title + content type and is reachable from a component's Data Picker.
- [ ] If a pinned query was requested, it appears under Pinned Queries with its Name + Content Type and is bindable as a Repeater **Items** source.
- [ ] The app route at the resolved URL mounts `<StudioComponent />` and renders the freeform layout with pinned content. (For lists, the Repeater shows real iterations after toggling **Preview Mode** in Properties, the canvas previews one iteration by default.)

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Right panel shows only Settings | Freeform feature is OFF at project level | Enable it before continuing |
| A component is selected when you wanted template-level pins | Data tab swaps to component-prop bindings | Click empty canvas to deselect |
| Trying to use `{{entry.title}}` or `{{content_type_uid}}` in the URL pattern | Freeform has no entry / no connected content type | Only `{{composition_uid}}` + context vars work |
| "Static Template" (create modal) vs "Freeform Mode" (canvas badge) | Same thing, different label | Treat as one |
| Pinned Entry vs Pinned Query mix-up | A single entry goes in Pinned Entries. A list goes in Pinned Queries (Repeater source). A pinned query re-runs every render. A pinned entry does not refresh as content changes. | Pick by cardinality |
| Pinned query prompt isn't live | Natural-language prompt is converted once at save time | Re-open the query to tune later |
| Repeater renders one row on the canvas | Design Mode preview shows one iteration | Select Repeater in Layers and toggle **Preview Mode** in Properties |
| Template doesn't render at the resolved URL | Catch-all missing, or not mounting `<StudioComponent />`, or pattern doesn't resolve inside `sdk.fetchCompositionData` | Verify all three. The catch-all covers every URL. Per-template routes are NOT needed. |
| Dropping a Rows / Box wrapper before the first real component | Leaves visible "Drop Here" placeholder zones. Rows is an e2e-test scaffolding habit, NOT a Studio authoring pattern. | Drop the first component directly onto the canvas root slot. Wrap in a container ONLY for explicit layout. |
| Adding a Repeater for a non-list use case | Repeater iterates a multi-valued field. One hero + one promo card needs zero iteration | Use Repeater ONLY when the data source is genuinely a list (Pinned Query, multi-entry Pinned Reference) |
| Leaving empty "Drop Here" zones at the bottom | Saved compositions render those zones as visible placeholders | Before Save, switch to Layers and delete any orphan empty Box / Slot rows |

## Driving the canvas

Moving a component on the Studio canvas through browser automation has a required event sequence, and the high-level drag helpers do not satisfy it. See [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md) before attempting a drop.

## See also

- `install-studio`: install SDKs and wire `studioSdk.init` at the app shell.
- `setup-section-preview`: add the `<StudioCanvas />` route for previewing Sections in Studio.
