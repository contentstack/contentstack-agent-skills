---
name: match-existing-pattern
---

## When to use

Read the Templates and Sections already in a Studio project, work out **how they are built** (repeater-driven, block-wise, flat section list, single component) and build anything new the same way. When the project holds more than one pattern, show the user each one as a layer tree and let them pick before building.

**Mandatory before authoring any Template or Section in a project that already has compositions.** Run it from `plan-studio-architecture` § Step 0a, and from `build-section`, `build-connected-template`, `build-freeform-template`, `build-page-builder-template` and `compose-marketing-section` before their first write. Phrases: "match the existing design", "build it like the other templates", "follow the existing pattern", "same as the current sections". An empty project needs nothing from this skill: report "no existing compositions, building fresh" and continue.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Match the pattern the project already uses

## Why this matters

A composition's `ui` is zlib-compressed, so a project's build conventions are invisible to every other inspection skill. `discover-sections` reads route files, `discover-sections-from-ct` reads a schema, `verify-visual-parity` compares screenshots. None of them can see that the existing Templates iterate their blocks through a Repeater with one Condition Block per type, or that Sections declare `linked_schemas` so a dropped Section binds itself.

Build without looking and the new work is structurally foreign to what is there: it may render correctly and still be wrong, because authors get no Repeater, no Condition Blocks and nowhere to drop anything. That is rework, and it is only visible once someone opens the Layers panel.

## Task

### Step 1: Inventory, then read the trees

`place_composition_as` splits Templates from Sections. The listing endpoint does **not** return `ui`. Fetch each composition individually, then inflate.

```bash
# requires:
#   STUDIO_API  Studio API base URL for your region
#   PROJECT     Studio project uid
#   CS_AUTH     one auth header resolved per authenticate-cma, e.g. "authorization: Bearer $CS_OAUTH_ACCESS_TOKEN"
#   CS_SCOPE    the scope header, e.g. "organization_uid: <org-uid>"
# List (paginate: the endpoint caps at 100; repeat with skip=100, 200, … until a page returns fewer than 100)
curl -s "$STUDIO_API/projects/$PROJECT/compositions?limit=100&skip=0" -H "$CS_AUTH" -H "$CS_SCOPE"
# Then per composition (UID from the listing)
curl -s "$STUDIO_API/projects/$PROJECT/compositions/$UID" -H "$CS_AUTH" -H "$CS_SCOPE"
```

`ui` usually arrives as `zlib:<base64>`. Inflate it before walking:

```python
import zlib, base64, json
raw = composition["ui"]  # composition = the parsed "composition" object from the per-uid fetch
if isinstance(raw, dict):
    ui = raw
elif raw.startswith("zlib:"):
    ui = json.loads(zlib.decompress(base64.b64decode(raw[5:])))
else:
    ui = json.loads(raw)
```

Fetch concurrently. A few hundred compositions at ~1.5s each is ten minutes sequentially, which is long enough that the run gets abandoned half-read.

### Step 1b. Reuse inventory: what already exists

Shape is only half the answer. The same scan also answers "what can I drop instead of building?", and skipping it is how a project ends up with two Sections doing one job.

Three lists come out of the trees you already inflated:

**Sections keyed by the schema they bind to.** Group every Section by its `linked_schemas` entry (`<content_type>.<block_type>`). Before building for a target CT, look it up:

```
== TARGET: platform_details ==
  platform_details_section.banner_section  (1)
      Alpha platform_details — Banner Section   [single component]  preview:n  blt21e341ba…
  platform_details_section.benefits_section  (1)
      …
```

Six Sections already cover this CT. The build is reuse or extend, not create. Say which, and name the uid.

**The component palette, ranked by real usage.** Count each `type` across all trees, split atoms + layout primitives from composites:

| Component type | Compositions using it |
|---|---|
| `alpha-atom-heading` | 88 |
| `alpha-atom-body-string` | 82 |
| `alpha-atom-cta-button` | 41 |

Usage count is what makes this trustworthy. A registered component nothing uses is not a convention, and building on it means inventing one alone.

**Unlinked Sections.** A Section with no `linked_schemas` cannot auto-bind when dropped. The author wires every prop by hand. Report the count. It is the project's largest hidden authoring cost.

Report reuse before the pattern trees. A user who learns the Section already exists does not need the pattern at all.

### Step 2: Derive each composition's shape

Walk the tree and count what decides how you build one:

| Signal | What it tells you |
|---|---|
| `repeater` nodes | blocks are iterated in the tree, not inside React |
| `condition-block` nodes | one branch per block type, `metadata.condition.value` names it |
| `section-composition` nodes | Sections are referenced, not inlined |
| `alpha-atom-*` nodes | content is built from atoms rather than a section component |
| tree depth | flat list vs nested composition |
| binding `type` mix | `template` / `repeater` / `static_value` / literal |

Classify each into a shape:

- **`repeater + condition + sections`**: the fully composable pattern
- **`repeater + condition + atoms`**: composable, content built from atoms
- **`section list`**: flat list of Section references, no iteration
- **`single component`**: one registered component holds the whole page
- **`flat` / `atoms`**: everything else

### Step 3: Report the patterns as layer trees, not prose

The user recognizes a pattern by its **Layers panel**, so print the chain:

```
Box
  Slot
    Repeater            iterates <blocks field>
      Contents
        Condition Block   when <block type>
          Contents
            Box
              Slot
                Section   <name>
```

State the count behind each: "14 of 18 Templates are built this way."

### Step 4: One pattern, or a choice

**Exactly one pattern**: say so, name a representative composition, and build the new work that way without asking.

> Found 18 existing Templates, all built as Repeater + Condition Block + Section
> (e.g. `Latest - Homepage`). Building the new Template the same way.

**More than one**: do not guess, and do not pick the most common by default. Show each with its layer tree and its count, then ask which to follow. Use `AskUserQuestion` so the trees render side by side as previews.

Only offer patterns that actually fit the target. A Repeater pattern needs the page's body in **one** modular-blocks field. A page whose content is split across named fields and two blocks fields cannot use it, and offering it wastes a build.

### Step 5: Copy the wiring, not just the silhouette

Matching the shape is not enough. The bindings have to match too. Read them off a working composition rather than inferring:

- **Repeater**: `props.items` bound to the blocks field, `metadata.repeaterBindingFieldType: "modular_block"`, `metadata.mode: "preview"`
- **Condition Block**: `metadata.condition` with `operator: "eq"`, `value: "<block type>"`, and both `conditionBinding` and `dataBinding` pointing at `{ repeaterUID, path: { <block type>: {} } }`
- **Section auto-bind**: `linked_schemas: [{ content_type_uid, selected_field: "<field>.<block type>" }]`. This is what makes a dropped Section bind itself
- **Scope-relative paths**: see the pitfall table

### Step 6: Record the choice, then enforce it

Re-asking on every build is noise, and it lets two answers coexist in one project. Write the decision to
`.studio/pattern.json` in the consuming repo the first time it is made, and read it before Step 1:

```json
{
  "project": "<studio project uid>",
  "template_pattern": "repeater + condition + sections",
  "section_pattern": "shell + stack + inner repeater",
  "chosen_by": "user",
  "example_template": "Latest - Glossary Pages",
  "example_section": "Benefits"
}
```

With a record present, skip the prompt and say which pattern is being followed and where it came from. Re-prompt only
when the user asks to change it, or when the scan finds a pattern the record does not mention.

**Enforce it.** The pattern is not a suggestion: build to it, and if the target genuinely cannot take it (a page whose
body is split across named fields and two blocks fields cannot take the Repeater pattern), say so plainly, name the
constraint, and build the nearest fit. Do not silently pick a different shape and leave the user to find it in the
Layers panel.

## Pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Binding a Section inside a Condition Block with an entry-root path | The Section is scoped to **the block**, so `template.<blocks_field>` resolves to nothing and it silently renders its unbound placeholder, a page that returns 200 with no content | Bind relative to the block: `path: { heading: {} }`, never `path: { hero: { heading: {} } }` |
| Reading the shape from the listing endpoint | `ui` is not returned there. Every composition looks empty | Fetch each composition individually, then inflate |
| Trusting `static_value` bindings | They do not resolve on this render path. The component receives the **key**, not the value | Write literals as `{ type, value }` |
| Offering the Repeater pattern for every page | Needs the body in one modular-blocks field. A page mixing named fields with two blocks fields renders nothing | Check the schema shape first. Leave those flat and say why |
| Judging "it renders" as "it matches" | A 404 page inside the canvas still has headings and characters | Compare the layer tree, and check the first heading is real content |
| Building a Section that already exists | The scan classified shape but never grouped Sections by `linked_schemas`, so a duplicate ships and two Sections drift apart | Run the reuse inventory (Step 1b) before any write. A hit means reuse or extend |
| A newly registered component type in the canvas | The canvas serves a stale client bundle and reports the type unregistered even though the page route renders it | Restart the dev server after registering a new type |

## Acceptance

- Every existing composition read and classified, count reported, none skipped
- Reuse checked before shape: existing Sections for the target schema named with uids, or "none, new build" stated explicitly
- Atoms and composites reported with usage counts, so the new work is built from what the project actually uses
- Patterns reported as layer trees with counts
- With one pattern, it was matched without asking. With several, the user chose from previews
- New composition's tree matches the chosen pattern node for node
- Bindings copied from a working example, and the new page renders real content, not just a 200
- Choice recorded in `.studio/pattern.json`, so the next build does not re-ask
- New composition re-scanned after building: it classifies into the chosen pattern, not a neighbouring one
