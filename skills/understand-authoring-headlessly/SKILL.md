---
name: understand-authoring-headlessly
description: "Explain API-authoring a composition vs UI authoring — the entry's `ui` (zlib node tree) + `data_sources` shape, 7 binding types, when this path fits. On-ramp before `author-composition-via-api`."
allowed-tools: Read Grep Glob
---

## When to use

Explain API-authoring a composition vs UI authoring — the entry's `ui` (zlib node tree) + `data_sources` shape, 7 binding types, when this path fits. On-ramp before `author-composition-via-api`.

Use when the user asks "how do I create a composition via API", "can I bulk-import compositions", "what does Studio store in the entry", "what's the JSON shape of a composition", or before invoking `author-composition-via-api` without context. Concept only — for the actual API authoring run `author-composition-via-api`. Do NOT use for UI authoring (use `build-section` / `build-connected-template`).

# What API-authoring a composition means

## Two ways to author a composition

Compositions live as **entries** in a Contentstack content type (the project's compositions CT, typically `<project>_compositions`). There are two paths to create those entries:

| Path | Tool | When to use |
|---|---|---|
| **UI authoring** (default) | Studio canvas — drag, drop, bind via Data Picker, Save, Deploy | Every author-driven workflow. Authors use it; engineers use it for ad hoc composition. |
| **API authoring** (headless) | CMA `POST /v3/.../entries` with a hand-built `ui` payload | Seed pipelines, scripted provisioning, automated migration, debugging via diff, bulk import |

API authoring is NOT a replacement for the UI — the Data Picker handles every shape the API path describes. Reach for the API only when scripting at scale or seeding fixtures.

## What's in the composition entry

The compositions CT has 14 fields (full schema in [`provision-studio-project`](../provision-studio-project/SKILL.md)). The two that carry the composition itself:

- **`ui`** — `zlib:<base64>`-encoded composition node tree. The whole layout — page, sections, components, repeaters, condition blocks, section slots — lives here as one inflated JSON tree.
- **`data_sources`** — JSON object holding `resolvedReferences` (which fields to populate via CDA `?include[]=`), the static-value map, and other resolution metadata.

Other fields (`composable_uid`, `url`, `linked_schemas`, `linked_sections`, `url_metadata`, etc.) are CT-level routing/metadata; the actual composition is in `ui` + `data_sources`.

## The seven binding types

Studio's Data Picker emits one of seven binding shapes per bound prop. API authoring writes them by hand:

| Type | Where the value comes from | Common use |
|---|---|---|
| `template` | The template's preview entry (the page-level CT) | `entry.title`, `entry.hero.headline` |
| `repeater` | The current Repeater iteration item | inside a Repeater iterating `entry.related_posts` |
| `static_value` | A literal value baked into the composition | Labels, button text the author types once |
| `component_props` | A Section's exposed prop (passed in from a Template) | Section's "Card Title" override |
| `symbol_props` | (not in scope; intentionally not documented) | — |

API-authored bindings live at `props.<propName>.binding` on each node.

## The node anatomy

Each node in the `ui` tree has:

- `type` — registered component UID (`page`, `section`, `repeater`, `condition-block`, `section-slot`, or a custom registered component)
- `props` — bindings + static values + exposed-prop metadata
- `slots` — `{ <slot_uid>: [<child_node>, ...] }` for children. **Every slot must have a non-empty array** — empty slots crash the renderer (see [`troubleshoot-canvas`](../troubleshoot-canvas/SKILL.md)).
- `metadata` — `mode` (preview/design), `condition`, `sectionBindingOverride`, etc.

## When API-authoring is the right choice

| Task | Right path |
|---|---|
| Seed compositions for a test environment | API authoring (`author-composition-via-api`) |
| Migrate an existing hand-coded marketing site | UI authoring (Studio canvas + `build-section` / `build-connected-template`) |
| Bulk-import 200 product detail compositions from a CSV | API authoring |
| Author a Hero Strip section that authors will tweak | UI authoring |
| Diff "what Studio writes" against "what my SDK reads" | API authoring (decode + inspect) |
| Auto-provision a Studio project for a new test stack | API authoring + [`provision-studio-project`](../provision-studio-project/SKILL.md) |

The rule of thumb: API path for **machines doing it at scale or in pipelines**; UI path for **humans composing pages**.

## What you'll need to know before API authoring

1. The seven binding types and their shapes (above).
2. The node anatomy — `props.<prop>.binding` for bindings, `slots: { <uid>: [...] }` for children, `metadata` for mode/condition.
3. `data_sources.resolvedReferences` — what to populate via CDA `?include[]=` so reference fields come back as full entries, not stubs.
4. The `zlib:<base64>` encoding — both for writing and for debugging (decode + walk to diagnose).
5. The `composable_uid` contract — equals the CMA entry uid for runtime lookup.
6. The pre-publish preflight — every slot's children array non-empty; no orphan descendant references; Repeater `metadata.mode: "preview"`; Condition Block sibling on reference/modular-block iteration.

## What this skill is NOT

- Not the recipe — for that, run [`author-composition-via-api`](../author-composition-via-api/SKILL.md).
- Not for UI authoring — use [`build-section`](../build-section/SKILL.md), [`build-connected-template`](../build-connected-template/SKILL.md), [`build-repeating-section`](../build-repeating-section/SKILL.md).
- Not for provisioning the compositions CT itself — that's [`provision-studio-project`](../provision-studio-project/SKILL.md).
- Not for diagnosing a misbehaving composition — that's [`troubleshoot`](../troubleshoot/SKILL.md) router.
