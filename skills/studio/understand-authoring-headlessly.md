---
name: understand-authoring-headlessly
---

## When to use

Explain API-authoring a composition vs UI authoring: the entry's `ui` (zlib node tree) + `data_sources` shape, the six binding types, when this path fits. On-ramp before `author-composition-via-api`.

Use when the user asks "how do I create a composition via API", "can I bulk-import compositions", "what does Studio store in the entry", "what's the JSON shape of a composition", or before invoking `author-composition-via-api` without context. Concept only: for the actual API authoring run `author-composition-via-api`. Do NOT use for UI authoring (use `build-section` / `build-connected-template`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# What API-authoring a composition means

## Two ways to author a composition

Compositions live as **entries** in a Contentstack content type (the project's compositions CT, typically `<project>_compositions`). There are two paths to create those entries:

| Path | Tool | When to use |
|---|---|---|
| **UI authoring** (default) | Studio canvas: drag, drop, bind via Data Picker, Save, Deploy | Every author-driven workflow. Authors use it. Engineers use it for ad hoc composition. |
| **API authoring** (headless) | CMA `POST /v3/.../entries` with a hand-built `ui` payload | Seed pipelines, scripted provisioning, automated migration, debugging via diff, bulk import |

API authoring is NOT a replacement for the UI. The Data Picker handles every shape the API path describes. Reach for the API only when scripting at scale or seeding fixtures.

## What's in the composition entry

The compositions CT has 13 fields (full schema in [`provision-studio-project`](provision-studio-project.md)). The two that carry the composition itself:

- **`ui`**: `zlib:<base64>`-encoded composition node tree. The whole layout (page, sections, components, repeaters, condition blocks, section slots) lives here as one inflated JSON tree.
- **`data_sources`**: JSON object holding `resolvedReferences` (which fields to populate via CDA `?include[]=`), the static-value map, and other resolution metadata.

Other fields (`composable_uid`, `url`, `linked_schemas`, `linked_sections`, `url_metadata`, etc.) are CT-level routing/metadata. The actual composition is in `ui` + `data_sources`.

## The six binding types

Studio's Data Picker emits one of six binding shapes per bound prop, and these are the six an API author writes by hand:

| Type | Where the value comes from | Common use |
|---|---|---|
| `template` | The template's preview entry (the page-level CT) | `entry.title`, `entry.hero.headline` |
| `repeater` | The current Repeater iteration item | inside a Repeater iterating `entry.related_posts` |
| `contentstack` | A Pinned Entry on the template (Freeform must be on) | `dataSources.contentstack.<uid>.title` |
| `contentstack_queries` | A Pinned Query on the template (Freeform must be on) | a Repeater sourced from `dataSources.contentstack_queries.<uid>` |
| `static_value` | A literal value baked into the composition | Labels, button text the author types once |
| `component_props` | A Section's exposed prop (passed in from a Template) | Section's "Card Title" override |

API-authored bindings live at `props.<propName>.binding` on each node.

## The node anatomy

Each node in the `ui` tree has:

- `type`: registered component UID (`page`, `section`, `repeater`, `condition-block`, `section-slot`, or a custom registered component)
- `props`: bindings + static values + exposed-prop metadata
- `slots`: `{ <slot_uid>: [<child_node>, ...] }` for children. **Every slot must have a non-empty array**: empty slots crash the renderer (see [`troubleshoot-canvas`](troubleshoot-canvas.md)). Two exceptions: a `section-slot` node keeps `slots: { "<its-own-uid>": [] }` until a template fills it. The other is the page-side `section-composition` node, which keeps `slots: { "<section-slot-uid>": [] }` for each slot the template hasn't filled yet.
- `metadata`: `mode` (preview/design), `condition`, `sectionBindingOverride`, etc.

## When API-authoring is the right choice

| Task | Right path |
|---|---|
| Seed compositions for a test environment | API authoring (`author-composition-via-api`) |
| Migrate an existing hand-coded marketing site | UI authoring (Studio canvas + `build-section` / `build-connected-template`) |
| Bulk-import 200 product detail compositions from a CSV | API authoring |
| Author a Hero Strip section that authors will tweak | UI authoring |
| Diff "what Studio writes" against "what my SDK reads" | API authoring (decode + inspect) |
| Auto-provision a Studio project for a new test stack | API authoring + [`provision-studio-project`](provision-studio-project.md) |

The rule of thumb: API path for **machines doing it at scale or in pipelines**, UI path for **humans composing pages**.

## What you'll need to know before API authoring

1. The six binding types and their shapes (above).
2. The node anatomy: `props.<prop>.binding` for bindings, `slots: { <uid>: [...] }` for children, `metadata` for mode/condition.
3. `data_sources.resolvedReferences`: what to populate via CDA `?include[]=` so reference fields come back as full entries, not stubs.
4. The `zlib:<base64>` encoding: both for writing and for debugging (decode + walk to diagnose).
5. The `composable_uid` contract: unique across the compositions CT. Studio's UI fills it with a readable name from the title. It never places a section: a template's `section-composition` node references the section by its entry uid (`metadata.compositionUID: "blt…"`).
6. The pre-publish preflight: every slot's children array non-empty, no orphan descendant references, Repeater `metadata.mode: "preview"`, Condition Block sibling on reference/modular-block iteration.

## What this skill is NOT

- Not the recipe. For that, run [`author-composition-via-api`](author-composition-via-api.md).
- Not for UI authoring. Use [`build-section`](build-section.md), [`build-connected-template`](build-connected-template.md), [`build-repeating-section`](build-repeating-section.md).
- Not for provisioning the compositions CT itself. That's [`provision-studio-project`](provision-studio-project.md).
- Not for diagnosing a misbehaving composition. That's [`troubleshoot`](troubleshoot.md) router.
