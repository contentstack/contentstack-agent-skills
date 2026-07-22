---
name: design-section-from-jsx
description: "From a component used across routes, propose the Section's linked-schema shape and create the Global Field / Group / Modular Block so `build-section` can run."
allowed-tools: Read Grep Glob
---

## When to use

From a component used across routes, propose the Section's linked-schema shape and create the Global Field / Group / Modular Block so `build-section` can run.

Use BEFORE `build-section` when migrating a hand-coded route into Studio AND the section's linked schema does not exist yet. Phrases — "design schema for my Hero", "what fields does this section need", "migrate this component to a section". Pairs with `discover-sections`. Skip if the schema already exists. Do NOT use to redesign live schemas.

# Design a section's linked schema from existing JSX

## Context

Studio sections **link to a structural schema** — Content Type / Global Field / Group / Modular Block / Block / Reference (never a scalar). For a migration, the natural section schema is whatever shape the existing JSX has been binding against. If `<Hero>` is currently rendered as `<Hero headline={entry.title} subhead={entry.tagline} cover={entry.cover.url} />` across four routes, the section's linked Global Field needs `headline / subhead / cover` fields with types that match.

`build-section` assumes the schema already exists. For greenfield Studio installs that's fine — model the schema first in Contentstack, then build the section. For a **migration**, this skill reverses the order: read what the existing JSX is binding to and propose the schema.

This skill **does not write to Contentstack** — it has no auth token, no Management Token, no CMA access (Studio's public skills never ask for those credentials). It emits the schema spec + step-by-step UI instructions; the user creates the Global Field manually in Contentstack's web app, then runs `build-section` to author the section against it.

Reference: `docs/32-sections/link-content-types-with-linked-schema.md` (rules for linked-schema shapes), `docs/40-recipes/migrating-hand-coded-pages-to-studio.md` (section-first migration flow).

## Task

1. **Read `componentPath`.** Extract the component's prop names and types. Use the TypeScript interface (best), `propTypes` (second), or destructured args (fallback).

2. **For each route in `usingRoutes`, read the file and find the JSX element matching the component.** For each prop assignment, capture the expression on the right (`headline={entry.title}` → `{ prop: "headline", binding: "entry.title", routeFile: "..." }`).

3. **Build a binding union across routes.** For each prop:
   - If all routes bind to the same field (`headline ← entry.title` everywhere) → strong signal, schema gets a `title` field, exposed as `headline`.
   - If routes bind to different field names (`headline ← entry.title` on /blog vs. `entry.headline` on /products) → flag as ambiguous; ask the user which canonical name to use OR propose making the binding configurable via `exposed-props`.
   - If a prop is sometimes set, sometimes not → mark optional in the schema.
   - If a prop is a literal (`layout="centered"` on every route) → not a CMS field; keep as a registered component prop's `defaultValue`, NOT in the section's linked schema.

4. **Map prop types to Contentstack field types.** Use the table:

   | Component prop type | Contentstack field type | Notes |
   |---|---|---|
   | `string` | `text` (single-line) | Multiline → `text` with `multiline:true` |
   | `string` (long-form / RTE) | `json_rte` or `markdown` | Default to `json_rte` unless prop was rendered as `<div dangerouslySetInnerHTML>` |
   | `number` | `number` | |
   | `boolean` | `boolean` | |
   | URL string passed as `href` | `link` | Contentstack `link` has `title` + `href` |
   | URL string passed as `src` (image) | `file` | Contentstack `file` is an asset reference |
   | ISO date | `isodate` | |
   | `string` constrained to literals (union) | `text` with `choices` validation | Section's `choice` prop has its own `options:` |
   | Array of objects | `modular_block` (mixed) or `reference` (entries) or `group` with `multiple:true` | Pick based on what each item is |
   | Reference to another CT entry | `reference` | Single vs multi controlled by `reference_to` cardinality |

5. **Emit the schema spec** in markdown for the user to review:

   ```
   ## Proposed Global Field: <proposedSchemaUid>
   Display name: <sectionName> data

   | Field UID | Type | Required | Multiline | Default | Bound prop |
   |---|---|---|---|---|---|
   | headline | text | yes | no | — | Hero.headline |
   | subhead | text | yes | yes | — | Hero.subhead |
   | cover | file | yes | — | — | Hero.cover |
   | cta_label | text | no | — | "Get started" | Hero.ctaLabel |
   | cta_href | link | no | — | — | Hero.ctaHref |

   Ambiguous bindings — pick canonical name per row:
   | Prop | /blog binding | /products binding | Canonical UID? |
   |---|---|---|---|
   | headline | entry.title | entry.headline | ?

   Singleton (literal) props — leave as registered-component defaults, NOT in this schema:
   - Hero.layout = "centered"
   - Hero.theme = "light"
   ```

6. **Pause for user review.** Print exactly: `Review the schema above. To proceed, confirm: (y) the schema is correct — give me the UI steps to create it, (e) edit the proposed schema first.` Wait. **The skill never writes to Contentstack** — the user creates the Global Field in the web UI.

7. **On confirm, print step-by-step UI instructions** for the user to create the Global Field manually:

   ```
   Open https://app.contentstack.com → your stack → Content Models → Global Fields → "+ New Global Field".

   1. Display Name:  <sectionName> data
   2. UID:           <proposedSchemaUid>
   3. Description:   "Used by Studio's <sectionName> section. Schema derived from existing JSX bindings on: <usingRoutes>."

   Add these fields in order:

   | Field Name  | UID       | Field Type  | Multi-line | Required | Notes                  |
   |-------------|-----------|-------------|------------|----------|------------------------|
   | Headline    | headline  | Single Line | no         | yes      | —                      |
   | Subhead     | subhead   | Multi Line  | yes        | yes      | —                      |
   | Cover Image | cover     | File        | —          | yes      | —                      |
   | CTA Label   | cta_label | Single Line | no         | no       | Default: "Get started" |
   | CTA Link    | cta_href  | Link        | —          | no       | —                      |

   Click Save. Note the UID — it's already <proposedSchemaUid> if you followed step 2.
   ```

   For users who prefer a programmatic path, also emit the equivalent JSON spec the [contentstack CLI](https://www.contentstack.com/docs/developers/cli) accepts (`csdx cm:stacks:import` or `csdx cm:global-fields:create`):

   ```json
   {
     "global_field": {
       "title": "<sectionName> data",
       "uid": "<proposedSchemaUid>",
       "schema": [
         { "data_type": "text",  "display_name": "Headline",     "uid": "headline",  "field_metadata": { "_default": true, "version": 3 }, "mandatory": true,  "multiple": false },
         { "data_type": "text",  "display_name": "Subhead",      "uid": "subhead",   "field_metadata": { "_default": true, "multiline": true, "version": 3 }, "mandatory": true, "multiple": false },
         { "data_type": "file",  "display_name": "Cover Image",  "uid": "cover",     "field_metadata": { "description": "" }, "mandatory": true, "multiple": false },
         { "data_type": "text",  "display_name": "CTA Label",    "uid": "cta_label", "field_metadata": { "_default": true, "version": 3, "default_value": "Get started" }, "mandatory": false },
         { "data_type": "link",  "display_name": "CTA Link",     "uid": "cta_href",  "field_metadata": { "description": "" }, "mandatory": false }
       ]
     }
   }
   ```

   The user can save this JSON and run `csdx cm:global-fields:create --stack-api-key <key> --filename <path-to-json>` with their own CLI session (the CLI has its own auth flow Studio doesn't touch).

8. **Print the hand-off:** `Once you've created the Global Field manually in the Contentstack web UI (or via csdx CLI), run: build-section with sectionName="<name>" linkedSchemaKind="global-field" linkedSchemaUid="<uid>". build-section will then create the Studio section and bind <component> against the schema you just created.`

## Inputs needed from the user

1. `componentPath` — required, exact file path.
2. `usingRoutes` — required. If empty, the skill can't extract bindings — refuse and ask the user to run `discover-sections` first to identify routes.
3. `sectionName` — required.
4. `proposedSchemaUid` — required (default lower-snake from sectionName).

If the user hasn't run `discover-sections`, recommend that first. The skill works without it but the user-supplied `usingRoutes` becomes a guess.

## Acceptance

- [ ] Every route in `usingRoutes` was read and its JSX scanned for the component.
- [ ] Per-prop binding union table is produced — covers every prop on the component.
- [ ] Ambiguous-binding rows surface for the user to disambiguate; the skill does NOT pick a canonical name silently.
- [ ] Singleton (literal) props are listed separately and explicitly NOT in the proposed schema — they stay as component-registration defaults.
- [ ] Proposed schema field types map cleanly to Contentstack field types per the table above; no invented types.
- [ ] Step-by-step Contentstack web-UI instructions are printed for the user to create the Global Field. Optionally, the contentstack-cli JSON spec is also printed.
- [ ] The skill did NOT attempt to call CMA, did NOT ask for an auth token or Management Token, and did NOT write to the stack. The user creates the schema themselves in the UI (or via their own CLI session).
- [ ] The hand-off line names the next skill (`build-section`) and its three required inputs.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Picking a canonical UID for an ambiguous binding without asking | Routes start failing because the new field name doesn't match what the entry has | Always ask for ambiguous-row decisions explicitly |
| Folding literal props into the linked schema | The schema gets a `layout: text` field nobody writes to; defaults are lost | Keep literal-only props as `defaultValue` on the registered component, NOT in the schema |
| Choosing `text` for a string that's actually a rich-text body | Authors get a single-line input for a long-form field | If the JSX renders the prop via `dangerouslySetInnerHTML` or a markdown renderer, propose `json_rte` instead |
| Creating a Global Field when the data clearly belongs on one CT | Authors can't edit it from the entry's natural form | If `usingRoutes` is just one CT's pages → propose a `group` field on that CT, not a Global Field |
| Inferring `reference` cardinality from prop name | "relatedPosts" plural may still be one entry; "relatedPost" singular may be multiple | Look at how the prop is rendered (`.map(...)` → multi; direct render → single) |

## See also

- `discover-sections` — run BEFORE this skill to identify which components become sections; this skill designs the schema for each
- `build-section` — run AFTER this skill creates the schema; binds the component against it
- `docs/32-sections/link-content-types-with-linked-schema.md` — the full rules for linked-schema kinds
- `docs/20-bring-your-own-components/component-schema-prop-types.md` — registered-component prop type reference (for distinguishing CMS-field props from defaults-only props)
- `docs/40-recipes/migrating-hand-coded-pages-to-studio.md` — the section-first migration recipe; this skill automates the "design the schema" sub-step
