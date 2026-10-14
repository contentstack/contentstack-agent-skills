---
name: build-section
---

## When to use

Author a Section composition by linking it to a structural schema (CT / Global Field / Group / Modular Block / Block / Reference) and dropping registered components.

Use when a NEW reusable Section must exist for a Template to drop. Run AFTER components are registered, before Template work. Phrases: "build a hero section", "create card grid". Do NOT use to MODIFY an existing Section. Use Studio UI, driven through Playwright per [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md). Don't hand the clicks to the user or switch to the API unless they ask; that's `author-composition-via-api`. Do NOT use for one-off page composition. Use `build-connected-template`.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Pattern preflight: mandatory.** Before the first write, run [`match-existing-pattern`](match-existing-pattern.md): read the Templates and Sections already in the project, **reuse what already covers this schema**, and build to the pattern they use. Skip it only when the project has no compositions at all. Authoring something structurally foreign to what is there is rework, and it is invisible until someone opens the Layers panel.

# Build a Section

> **Approved plan required.** This skill builds. It does not decide. If there is no plan the user has explicitly approved (Sections with their linked schemas, Section Slots, per-Section components (registered vs built-in), bindings, and the template kind), **stop and run [`plan-studio-architecture`](plan-studio-architecture.md) first**, then come back with the approved block for this piece. Building without it is how a project ends up as one monolithic template with no Sections, no slots and no reuse. Exception: the user is explicitly iterating on a piece already in an approved plan.

## Context

A Section is a reusable composition that template authors drop onto pages.

**Qualification gate: before authoring, confirm this Section qualifies.** A Section pays off when **the binding work amortizes**, i.e., when the same N bindings would otherwise be repeated by the author on every template drop. Qualifies if either:

1. **The component has ≥2 separate prop bindings**: Hero with `title` + `cover.url`, Card with `image` + `title` + `summary` + `link`, ProductHighlight composed of multiple sub-components each with their own bindings. Without a Section, the author re-wires every prop on every drop.
2. **The component takes one prop bound to a structural shape**: Modular Block list, Reference array, Group, Global Field. The outer bind is 1 click, but the internal rendering walks N sub-fields per iteration. That sub-field work amortizes.

A Section does **NOT** qualify for:

- **A single atomic component bound to a single primitive (scalar) field**: `Heading` bound to `entry.title`, `Image` bound to `entry.cover.url`, `Text` bound to `entry.tagline`. One bind, one drop, no repetition cost. Studio's Connect-a-Schema picker also rejects scalar fields. Use these components inline.

**Diagnostic question:** "How many bindings will the author wire by hand on the next drop of this component?" If ≥2, make it a Section. If 1, leave it as a registered component used inline.

If the candidate fails the qualification, STOP. It's not a Section. See [`understand-sections`](understand-sections.md) § What qualifies as a Section.

Its data contract is defined by a **linked schema**, and Studio only accepts **structural shapes** here, not single scalar fields. Allowed kinds:

| Kind | What it is | Single or multiple |
|---|---|---|
| **Content Type** | The whole entry of one CT | Single: one entry at a time |
| **Global Field** | A reusable named schema (the most common section anchor) | Single OR multiple (a list of group instances) |
| **Group** | A nested object on a CT | Single OR multiple (a list of group instances) |
| **Modular Block** | A field that holds a list of blocks. Each block can be a different shape | Always multi: pair with Repeater + Condition Block |
| **Block** | A specific block type inside a Modular Block field | Single: the block shape is fixed |
| **Reference** | Points to one or more entries of one or more CTs | Single OR multi-entry: multi pairs with Repeater + Condition Block (always required, single-CT included) |

A section connecting to a multiple variant is meant to live **inside a Repeater** on the template. The Repeater iterates the list. Each iteration places one instance of the section's shape.

Studio's picker omits scalar fields (`text`, `number`, `boolean`, `file`, `link`, `date`, etc.). A section composes UI against a shape. For a single value override at template level, use **Expose Section Prop** on a component inside the section.

Bindings on registered components come from the Data Picker. The picker shows the Section's linked-schema fields by default. Inside a Repeater it switches root to the iteration item's fields. See `use-repeater` § The scope rule, in user terms. All References inside a Repeater (single-CT and multi-CT) require a Condition Block.

## Path A vs Path B: monolith Section or Section-with-Slot + child Section

When a Section iterates over a list of cards (a multi-reference field, a Modular Block list, a multi-Group, or a multi-entry pinned query), there's a recurring architectural choice:

- **Path A: one monolithic Section.** The Section owns the Repeater AND the card markup inside it. Card props bind from the Repeater Data root (the iterated item).
- **Path B: Section-with-Slot + separate child Section.** The parent Section owns the Repeater and exposes a Section Slot inside the iteration. A separate child Section (bound to the iterated item's CT) gets dropped into the Slot at template-authoring time. The child Section is pre-bound to its own linked schema, no per-prop binding needed.

**Deciding question:** "Will this card visual ever appear outside this list?" (Featured product hero, related-items strip, recommended carousel, search result row, etc.)

- **Yes, probably yes, or unsure: take Path B.** Sections exist so visuals can be reused. Splitting the card into its own Section costs one extra Section and unlocks reuse everywhere else. **Default to Path B.**
- **Genuinely no, single-use: Path A** is acceptable. Easier to collapse Path B into Path A later than to extract a Section out of a monolith. When in doubt, Path B.

In Path B, the parent's Repeater contains a Section Slot (see `use-section-slot`), filled at template time by the child Section, never a raw component (see `understand-section-slots`). Auto-binding wires it because the child Section's linked schema matches the iterated item.

## Layout lives in the Section

A Section that exposes a Slot must wrap it in a sized layout container. See `use-section-slot` § Layout container and `register-component` § Layout contract.

## How a Section gets its data: the `selectedField` model

A Section has **no data of its own**. When it's dropped on a template, the SDK hands it a scoped slice of the page entry via `getScopedData(pageEntry, selectedField)`:

- **`selectedField` set** to a field uid: the section's `template` becomes that field's value (references and groups resolved along the path).
- **`selectedField` unset**: the section's `template` becomes the **whole page entry**.

The section's own canvas therefore always shows **one empty placeholder** (no page context exists standalone). That's not a bug: the section only fills out at template-render time. Verify via SSR cold-load: `await sdk.fetchCompositionData({ url })` on the parent template's URL and dump `spec.data.section_scoped_data[<instance-uid>]`.

### Decision rule: set `selectedField` or leave it unset

| Section shape | Rule | Where its bindings resolve against |
|---|---|---|
| **One Repeater over one field** (Card Grid over `related_posts`, feature list over `features[]`) | Set `selectedField=<that field>` + use scope-root repeater binding `{ path: {} }` inside | `template` becomes the field's array value directly |
| **Multiple fields on the page entry** (Header reading `brand` + `nav_links` + `signin_label`, Hero reading a `hero` group) | **Leave `selectedField` unset**: the section needs the whole entry | `template` is the full page entry. Keep original `template.<field>` binding paths |

Setting `selectedField` on a multi-field section loses access to everything outside the scoped path. Bindings to those fields resolve to `undefined`.

Background only (this skill builds in the UI): full mechanism, wire shapes, and the reference-iteration `data_sources.resolvedReferences` handling: `author-composition-via-api` § Authoring a Section composition (scoping rules and § Decision rule) single-field repeater section vs whole-entry section.

## Prerequisite: the canvas chain must be wired

Section authoring requires the full canvas chain: a route mounting `<StudioCanvas />`, the project's **Canvas URL** pointing at it, and (most often missing) a **non-empty per-locale Base URL on the environment the project targets**. Missing any link = blank or Playground canvas with no explanation. If you can't confirm all three, run [`setup-section-preview`](setup-section-preview.md) first.

## Task

1. **Open Studio, then the Sections tab, then + New Section.** Confirm you are in section authoring mode (the palette shows the **Registered Components** category and **Smart Containers** category, both are section-mode signals).

2. **Name the section** using the supplied `sectionName`. The display name is what template authors see in the Sections palette.

3. **Connect A Schema.** The Schema panel offers structural shapes only, no scalar fields. Pick the kind matching `linkedSchemaKind`:
   - `content-type`: pick the connected CT
   - `global-field`: pick the Global Field UID
   - `group`: pick the group field on the parent CT
   - `modular-block`: pick the Modular Block field. The section sees the union of allowed block types
   - `block`: pick a specific block type inside a Modular Block. The section sees just that block's fields
   - `reference`: pick the Reference field. The section sees the union of `reference_to` CTs

   If the user asks to "link to the title field" or similar, redirect: that's not how sections work. Either pick the parent group / object / CT, or use **Expose Section Prop** at the component level later. If `linkedSchemaUid` is blank, warn explicitly: the section is static-only, no auto-binding, every value typed by hand at template-drop time.

   When the picked schema is a multiple group / global field / file / link, Studio opens the **Add Repeater** prompt. **Do not click Add or Skip yourself:** ask the user "every item, or one item?" and click their answer ([`understand-linked-schemas`](understand-linked-schemas.md)). Add: root Repeater, `cardinality: "collection"`. Skip: `"single"`, meant to be dropped inside a Repeater on a template, which iterates the list and places the section once per item.

4. **Scan the linked CT for Slot candidates BEFORE binding fields directly.** Inspect the CT for any **Global Field**, **Modular Block**, **Group**, or **Reference** fields. For each one, decide:
   - **Expose it as a Section Slot** (the preferred default) when the nested data is composable, shared across pages, or likely to have variants. Carve a Slot at that location via `use-section-slot` instead of binding the nested shape inline. Doing so keeps the nested shape replaceable with any compatible Section per template instance.
   - **Bind it inline** only when the shape is genuinely one-off, small, and unlikely to be reused. This is the rarer case.

   Default for Global Field / Modular Block / Group / Reference fields: **expose a Slot**. Inlining throws away the reusability of the nested structure. If unsure, expose a Slot. It can always be filled with a single fixed child Section.

   See `understand-section-slots` § When to expose one: the Global Field / Modular Block / Group / Reference heuristic for the full rationale (Global Fields are the strongest Slot candidate of the four).

5. **Drop registered components.** For each entry in `initialComponents`:
   a. Open the palette and switch to the **Registered Components** category. Do not drop Studio default components: they bypass the project's brand system.
   b. Drag the component onto the section canvas. Use the canvas drop indicators to confirm placement inside the intended container.
   c. Select the dropped node and bind each prop via the Data Picker. The picker shows the Section's linked-schema fields by default. If the dropped node sits inside a Repeater, the picker switches root to the **iteration item's** fields automatically (labeled "Repeater Data"). Bind from whichever root the picker is showing. Add a Condition Block around any Reference or Modular Block iteration.

   d. **Field-existence gate: before binding ANY prop, confirm the target field is actually in the Data Picker.** The picker lists exactly the fields the linked schema (or iteration-item scope) exposes. If the field you intend to bind is **not in the list, STOP**: do not force a bind, do not invent a path, do not accept a stale binding that shows a field name the picker no longer offers. A bind that references a non-existent field resolves to `undefined` at runtime, and the component silently falls back to its registration `defaultValue`, which reads on the canvas as "real data that's actually placeholder." When the field is missing, the linked schema is wrong (see the collection-source gate below) or the CT needs a schema change first via [`migrate-ct-schema`](migrate-ct-schema.md). Report the mismatch and stop. Never paper over it with a bind that can't resolve.

   e. **Collection-source gate: a component prop that takes a whole array/object needs a matching multi-valued SOURCE on the linked schema.** If a registered component exposes ONE prop shaped as an array or object (a `Card Grid` / `Article Grid` / list wrapper that `.map()`s internally, the native array-prop pattern, see [`build-repeating-section`](build-repeating-section.md)), the linked schema **must** have a multi-valued field to feed it: a **multi-Reference**, **Modular Block list**, **Group with `multiple:true`**, or a **Pinned Query** (Freeform). Verify that field is in the Data Picker **before** binding. If the linked schema has **no such field** (e.g. an `Article List` CT with only `Title`/`URL`/`Description`/`SEO` and no `articles` reference), then there is nothing to bind the collection prop to, and the component renders its default array forever. **STOP and pick a fix, do not bind:**
      - Add the missing multi-valued field to the CT ([`migrate-ct-schema`](migrate-ct-schema.md)), the usual fix when the list lives in a separate CT (articles, products) that the page CT should reference, **or**
      - Source it dynamically via a Pinned Query on a Freeform template ([`pin-query-to-freeform`](pin-query-to-freeform.md)), **or**
      - **Decompose to atomic** instead of one whole-array component. Use a Repeater over the multi-valued field + a child Section bound to the iterated item's CT, with atomic components (Heading / Image / Text) each bound per-item. This surfaces per-field binding in Studio rather than hiding it inside the component. See [`build-repeating-section`](build-repeating-section.md) and [`use-repeater`](use-repeater.md).

   f. **Verify the bind resolved to REAL data, not the component's default.** After binding, toggle **Preview Mode** (select the node or Repeater, then Configuration, then Preview Mode) and confirm the canvas shows values from the **preview entry**, not the registration `defaultValue`. Tell them apart: default data is the generic placeholder baked into `registerComponent` (`"ARTICLE ONE"`, `"A short teaser…"`, a gray image icon). Real data is the seeded entry's actual field values. If Preview Mode still shows the defaults, the bind did **not** resolve. Re-run gates (d) and (e). Design Mode showing defaults is expected. **Preview Mode** showing defaults means the binding is broken.

6. **Optional smart containers.**
   - For a section whose linked schema IS the multiple variant, you usually drop a Repeater bound to `template.items[]` (or whatever the array path is) and place sub-components inside it.
   - Carve a **Section Slot** (see `use-section-slot`) if you want template authors to drop arbitrary components into a named region.
   - **Expose Section Props** (see `expose-section-props`) for value-level overrides, toggling a flag or swapping a label per template instance.

7. **Save.** Studio surfaces the **Expose Props** modal on Save. Toggle which component props template authors should be able to override per page. If you skip this step the section is locked: template authors can drop it but cannot change any value.

## Inputs needed from the user

In this order. Stop and ask if any is missing. DO NOT guess a `linkedSchemaUid` or invent component types.

1. `sectionName`: display name (reject empty or generic "Section 1", ask again).
2. `linkedSchemaKind`: one of `content-type / global-field / group / modular-block / block / reference`. If the user says "field name X", redirect: ask for the enclosing structural shape.
3. `linkedSchemaUid`: UID of the structural shape. Allow skip with an explicit static-only warning.
4. `isMultiple`: y/n. Affects whether the section is intended to live inside a Repeater on the template.
5. `initialComponents`: comma-separated list of registered component types. Reject any type not currently registered in the project.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, do not claim success. Surface the failure and stop.

- [ ] The new Section appears in the Studio Sections tab with the supplied `sectionName`.
- [ ] **The Section is published to the environment the Studio project targets**, and re-published after every later edit to its tree. An edit creates an unpublished version on a published composition, so delivery keeps serving the old shape while the CMA and the canvas both look correct. Row 7 of [`complete-the-build`](complete-the-build.md).
- [ ] **The section's atoms are inline-editable in the DOM**: the component root carries `data-cslp` (`studioAttributes` spread, with `wrap: false` in its register entry) and each bound text/image element carries its own `$`-twin tag. Verified by inspecting the rendered DOM, not assumed. Without it the section renders correctly and is invisible to Visual Editor. See [`complete-the-build`](complete-the-build.md).
- [ ] **The Sections accordion shows a thumbnail for it, not a blank tile. Mandatory, not cosmetic.** A section with an empty `ui_preview` is an unfinished section. Do not report it as created. If the thumbnail can't be set yet, say "created, thumbnail pending" and then finish it. Studio screenshots the canvas and uploads it to the composition's `ui_preview` field **on save**, so pressing Save in the editor is what produces the thumbnail. A blank tile means the section was created by API (that chain is editor-only) or the save's fire-and-forget upload failed. Fix: re-open the section and Save, or set `ui_preview` explicitly ([`author-composition-via-api` § Section thumbnails](author-composition-thumbnails.md#section-thumbnails-ui-preview)).
- [ ] If `linkedSchemaUid` was supplied, the section's Schema panel shows that UID under the correct structural kind (and **not** under any individual field).
- [ ] If the user asked to link to a scalar field, the request was redirected to the enclosing shape (or to Expose Section Prop). Single-field linking was NOT attempted.
- [ ] When `isMultiple=y`, the section's intent is documented for template authors: "drop inside a Repeater".
- [ ] Every component listed in `initialComponents` exists on the section canvas and was dropped from the **Registered Components** palette category (not the Studio defaults).
- [ ] Each bound prop on those components resolves under the right Data Picker root: the Section's linked-schema root for props outside any Repeater, and the **Repeater Data** root (iteration item) for props inside a Repeater. A Condition Block wraps any Reference or Modular Block iteration.
- [ ] **Every bound field exists in the Data Picker** (Step 5d). No prop is bound to a field the picker doesn't offer. No stale binding to a removed field was left in place.
- [ ] **Every collection-shaped prop (array/object) is backed by a real multi-valued source** on the linked schema: a multi-Reference, Modular Block list, `multiple:true` Group, or Pinned Query (Step 5e). If no such source exists, the Section was NOT saved with a dangling collection bind. The schema was fixed, a query pinned, or the component decomposed to atomic + Repeater.
- [ ] **Preview Mode shows real entry data, not registration defaults** (Step 5f). Placeholder text baked into `registerComponent` (`"ARTICLE ONE"`, generic teaser copy, gray image icons) is NOT being mistaken for a working bind.
- [ ] On Save, the **Expose Props** modal was acknowledged: either props were exposed or the locked state was a deliberate choice.
- [ ] Dropping the saved section onto a template that has a field of the linked schema's shape auto-binds with no manual picker steps.
- [ ] **Migration builds only**: if this Section is replacing an existing production Section on a live route, run `verify-visual-parity` against the production URL at all target viewports before declaring success. Structural checkpoints (component present, prop bound) are necessary but not sufficient. Pixel drift ships silently otherwise. Skip this line for greenfield Sections that have no production counterpart to compare.

## Driving the canvas

Moving a component on the Studio canvas through browser automation has a required event sequence, and the high-level drag helpers do not satisfy it. See [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md) before attempting a drop.

## Reference for this skill

| Read this | For |
|---|---|
| [`build-section-component-choice`](build-section-component-choice.md) | Basic field components vs your own registered components |
| [`build-section-pitfalls`](build-section-pitfalls.md) | What fails silently on the canvas. **Read before reporting done.** |

## See also

- `use-section-slot`: carve a drop region into the section
- `expose-section-props`: value-level overrides on Save
- `build-connected-template`: drop the saved section onto a template with a matching field
- `build-repeating-section`: the dedicated guide for the "parent Section with Repeater + Slot, child Section fills the Slot per iteration" pattern (Path B from this skill, walked end to end)
