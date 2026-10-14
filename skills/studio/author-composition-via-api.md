---
name: author-composition-via-api
---

## When to use

Author Studio compositions by writing composition JSON via the CMA, the manual contract Studio's Data Picker hides. For headless / scripted / seed-pipeline projects, not interactive UI authors.

Use when authoring compositions programmatically via CMA: seed pipelines, scripted provisioning, migration scripts, debugging via diff. Phrases: "compositions from JSON", "API author composition", "seed compositions", "headless author", "bulk import". Do NOT use for UI authoring. The Data Picker handles every shape this skill describes. For UI use `build-section` / `build-connected-template`.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Author a composition by API (the manual contract)

> **Approved plan required: this path has no other gate.** This skill writes composition JSON. It does not decide what to build. If there is no plan the user has explicitly approved (Sections with their linked schemas, Section Slots, per-Section components, bindings, and the template kind), **stop and run [`plan-studio-architecture`](plan-studio-architecture.md) first**. The canvas build skills carry this guard. Scripted CMA authoring is the fastest way to reach a finished project without ever passing one, and [`decompose-design`](decompose-design.md) names this skill its default handoff. A template composition whose root slot holds a single component node is a monolith (no Sections, no slots, no reuse) and it renders perfectly, so nothing downstream will catch it. Exception: the user is iterating on a piece already in an approved plan.

> **Mandatory structural check before reporting success.** Read the saved template back and count `section-composition` nodes in `ui` and entries in `linked_sections`. Both zero means a monolith. The runnable check is [`build-connected-template`](build-connected-template.md) § Post-build structural check. It applies identically here, and it is the only acceptance check a monolith fails. When the page body is one modular-blocks field, [`decompose-blocks-page`](decompose-blocks-page.md) is the recipe for splitting it.

## When to use this: and when NOT to

Studio's Data Picker writes every binding shape this skill describes **automatically**. UI authors never need to know about `data_sources.resolvedReferences`, the `repeaterUID` discriminator, or any of the binding types. Studio's runtime resolves them under the hood.

**Use this skill ONLY** when bypassing the Data Picker:
- A seed pipeline that creates compositions programmatically (a docs / demo project's bootstrap, an automated stack provisioner)
- Migrating compositions between stacks
- Bulk-authoring compositions from another source (an existing CMS, a generator)
- Debugging: capture a working UI-authored composition, decode it, diff against your broken one

For interactive authoring, use Studio's UI. The Data Picker is the **source of truth** for these shapes. If your manually-written shape disagrees with what the Data Picker emits, the picker is right. Your manual shape is wrong.

## Prerequisite: the project, the compositions CT, the credentials

This skill assumes:
- A Studio project exists, bound to a stack
- That stack has a compositions CT (the CT the project's `contentTypeUid` points at) with the required field schema (see `provision-studio-project`)
- You have a CMA auth token + the stack API key with permission to create entries on that CT
- For headless verification later: a Delivery Token + paired Preview Token (`enable-visual-experience` Step 4)

If any of these is missing, this skill is the wrong starting point.

> **Auth: OAuth first.** Snippets here write `-H "$CS_AUTH"`, resolved once per run. **Assume there is no session `authtoken`**. The user authenticates with OAuth (MCP `--auth` / `csdx auth:login --oauth`) and never pastes one. Resolution order, scope headers (`organization_uid` vs `api_key`), the expiry/refresh rule and the 401/422 signature table: [`authenticate-cma`](authenticate-cma.md).

> **MCP-first execution.** Discover tools and verify the target with a read call per [`install-contentstack-mcp`](install-contentstack-mcp.md). When supported tools are callable, the entry write + publish run as MCP tool calls (`create_an_entry` / `update_an_entry` / `publish_an_entry`) with no pasted `authtoken`. The composition **shape** is unchanged: you still build the `ui` (`zlib:<base64>`), `data_sources`, `static_value`, and `composable_uid` (= entry uid) exactly as below. The MCP only replaces the raw CMA transport. **Shell-corruption caveat on the MCP path:** `create_an_entry` takes `entry_data` as an **inline JSON object: there is no file-path param**, so the temp-file / `curl -d @file` guard does NOT apply. Instead **build the entire `entry_data` object programmatically and hand it to the tool, never hand-transcribe the `ui` blob into the arguments**, and assert the `"children"` count in the tree before the call (see the shell-corruption pitfall). If hand-assembly is unavoidable, keep the raw `curl -d @file` path for the write. A missing readiness flag requires discovery; use HTTP only for unavailable operations or a recorded connection limitation.

## The API-authoring set: read the one you need

This skill is the entry point. It carries the decision to author by API at all, the
prerequisites, and the acceptance gate. Everything else lives in a focused sibling, so a
single task loads what it needs instead of the whole contract.

| Read this | For |
|---|---|
| [`author-composition-entry`](author-composition-entry.md) | The CMA body, `url` + `url_metadata`. **Read first.** |
| [`author-composition-static-values`](author-composition-static-values.md) | Where a `static_value` binding's literal lives |
| [`author-composition-bindings`](author-composition-bindings.md) | Every binding type, node anatomy, Repeater binding shapes. **Read second.** |
| [`author-composition-encoding`](author-composition-encoding.md) | Compressing the `ui` tree, and preflight-validating it before publish |
| [`author-composition-repeater-recipes`](author-composition-repeater-recipes.md) | Repeat a card over a multi-reference or GROUP-MULTIPLE field |
| [`author-composition-nested-repeaters`](author-composition-nested-repeaters.md) | A list inside each iterated item |
| [`author-composition-sections`](author-composition-sections.md) | Section scoping rules, `selectedField`, `section-slot` |
| [`author-composition-section-slot-fill`](author-composition-section-slot-fill.md) | Pattern B: fill a wrapper's slots with another Section |
| [`author-composition-exposed-props`](author-composition-exposed-props.md) | Per-instance overrides on a placed Section |
| [`author-composition-thumbnails`](author-composition-thumbnails.md) | Why the API never sets a Section thumbnail |
| [`author-composition-templates`](author-composition-templates.md) | `linked_sections` for API-placed sections, plus a complete Freeform body |
| [`author-composition-pitfalls`](author-composition-pitfalls.md) | Verifying the write, and the full pitfall table. **Read before reporting done.** |
| [`author-composition-practice`](author-composition-practice.md) | Skeleton-first authoring, reading component source, free-form primitives |
| [`author-composition-migration`](author-composition-migration.md) | Moving compositions between stacks |

Minimum path for any composition: `author-composition-entry`, then
`author-composition-bindings`, then `author-composition-pitfalls` before you report done.

## Acceptance

This skill succeeds only when ALL are true.

- [ ] The composition entry was created with a unique `composable_uid` (a readable name or the entry uid), published.
- [ ] For a cross-stack migration: the template's `ui` `compositionUID`s + `linked_sections` were remapped to the destination entry uids (not carried over from the source).
- [ ] **Every `place_composition_as: "page"` entry has BOTH `url` and `url_metadata`**, `url_source` matching how the pattern is derived (`content_type_url_pattern` for Connected, `default_url_pattern` / `user_specified_pattern` for Freeform), `url_queries` as a JSON string. **Read the entry back after the write** and confirm `url_metadata` is present: a compositions CT missing the group makes the CMA drop it silently, leaving the composition on `legacy_url`.
- [ ] `data_sources.resolvedReferences` is set per reference field the composition iterates.
- [ ] Every Repeater node has `metadata.mode: "preview"` (for canvas iteration).
- [ ] Every Repeater iterating a reference or modular block has a Condition Block as its immediate child.
- [ ] **Every Condition Block's `metadata.condition` has `operator` and `conditionBinding`**, and the composition was checked in **preview mode**. Without the binding the block renders nothing, but design mode still shows it.
- [ ] Card / iteration child bindings use `type: "repeater"` with `repeaterUID`, NOT `type: "template"` with `.0.<field>` fixed-index paths.
- [ ] **Every Section composition created in this run has `ui_preview` set, verified by re-reading each entry.** A section with a blank tile is an unfinished section. Do not report the work as done. Also true of sections created as a side effect (clones, rescopes, batch builds).
- [ ] **Every Section composition has `ui_preview` set**, an uploaded, **published** asset uid, verified by re-reading the entry (`.entry.ui_preview.url` resolves). Blank tiles in Studio's Sections accordion otherwise. Fastest fix is often opening each section in Studio and pressing Save. See § [Section thumbnails](author-composition-thumbnails.md#section-thumbnails-ui-preview)
- [ ] **Envelope complete**: every node in the written tree has all seven keys (`uid`, `type`, `props`, `metadata`, `slots`, `attrs`, `styles`), verified by re-reading the entry. A missing `slots` renders fine and white-screens the Data tab later.
- [ ] **Preflight passed**: every `slots[<uid>]` is a non-empty array (exception: `section-slot` nodes carry `slots: { "<own-uid>": [] }` by design). No orphan descendant references in the tree.
- [ ] **[Pattern B](author-composition-section-slot-fill.md) (if used)**: wrapper section has `section-slot` node with `slots:{"<own-uid>":[]}`. Fill section's leaf bindings use `type:"template"` (NOT `repeater`). Template's `section-composition` node has `slots.<slot-uid>: [<fill section-composition node>]`. Template's `linked_sections` includes BOTH wrapper and fill entries.
- [ ] **Every `section-composition` node's `metadata.compositionUID` is the placed section's entry uid** (`blt…`), never its `composable_uid`. A `composable_uid` there fails in the canvas with `Component with type '<it>' is not registered`.
- [ ] **A section whose `selected_field` is a multiple group / global field / file / link** has `cardinality` from the user's answer (asked, never assumed): `"collection"` with a root Repeater, or `"single"` without one. Reference and modular-block sections carry no `cardinality` ([`understand-linked-schemas`](understand-linked-schemas.md)).
- [ ] **Exposed section props (if used)**: `sectionExposedProps` array on section's `ui` ROOT `metadata`. Template's `section-composition.props` map keyed by each exposure's `uid`. Per-instance override values use distinct static_value keys.
- [ ] The composition resolves at runtime, verified by either curl against the CDA preview API (returns 200 + entries body, see `troubleshoot-canvas` § Symptom and cause matrix, row "CORS error on the CDA preview host") OR a SSR cold-load `await sdk.fetchCompositionData({ url })` returning `spec.data.section_scoped_data[<instance>]` with the expected `template` array (see [`author-composition-sections`](author-composition-sections.md) § Verifying a section's scope headlessly).

## Sanity-check the output

After authoring, verify by ONE of:

1. **CDA preview API curl**: confirm the composition is returned. See `troubleshoot-canvas` § Symptom and cause matrix, row "CORS error on the CDA preview host", for the curl shape. Status 200 + JSON entries body = the contract resolves.
2. **SSR cold-load**: `await sdk.fetchCompositionData({ url })` from a throwaway server route. It **rejects** if the URL resolves to nothing, so a thrown `NO_COMPOSITION_FOR_URL` / `URL_MATCHED_NO_ENTRY` here is itself the verification result: the composition isn't resolving. In a throwaway script that's fine. In app code wrap it ([`configure-csr-vs-ssr`](configure-csr-vs-ssr.md#resolve-composition-helper)). Dump `spec.data.section_scoped_data[<instance>]` to verify each section's `selectedField` + scoped `template` arrives correctly. The most reliable check.
3. **Decode the stored `ui`**: the read-only `zlib`-inflate snippet in `troubleshoot-canvas` § Diagnostic tooling. Diff your composition's node tree against a known-working UI-authored one to spot any shape mismatch. Useful for debugging.

## See also

- `troubleshoot-canvas` § Diagnostic tooling (inspecting a stored composition's ui) the zlib decoder
- `troubleshoot-canvas` § Symptom and cause matrix, row "CORS error on the CDA preview host": preview-token verification curl shape
- `use-repeater`: UI authoring side. The Preview Mode toggle the API directly sets via `metadata.mode`
- `use-condition-block`: the Condition Block schema requirement for reference / modular-block iteration
- `build-section`: section's `selectedField` scoping (the parent of most API-authored sections)
- `understand-auto-binding`: the UI mechanism that writes these shapes for UI authors
- `provision-studio-project` (planned): compositions CT field schema, including `linked_schemas` as group-multiple
- `troubleshoot-data-binding`: the "registered as lazy but not loaded yet" error class
