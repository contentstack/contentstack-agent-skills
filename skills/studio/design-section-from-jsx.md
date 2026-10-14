---
name: design-section-from-jsx
---

## When to use

From a component used across routes, propose the Section's linked-schema shape and create the Global Field / Group / Modular Block so `build-section` can run.

Use BEFORE `build-section` when migrating a hand-coded route into Studio AND the section's linked schema does not exist yet. Phrases: "design schema for my Hero", "what fields does this section need", "migrate this component to a section". Pairs with `discover-sections`. Skip if the schema already exists. Do NOT use to redesign live schemas.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Design a section's linked schema from existing JSX

## Context

Studio sections **link to a structural schema**: Content Type / Global Field / Group / Modular Block / Block / Reference (never a scalar). For a migration, the natural section schema is whatever shape the existing JSX has been binding against. If `<Hero>` is currently rendered as `<Hero headline={entry.title} subhead={entry.tagline} cover={entry.cover.url} />` across four routes, the section's linked Global Field needs `headline / subhead / cover` fields with types that match.

`build-section` assumes the schema already exists. For greenfield Studio installs that's fine: model the schema first in Contentstack, then build the section. For a **migration**, this skill reverses the order: read what the existing JSX is binding to and propose the schema.

This skill **does not write to Contentstack**: it has no auth token, no Management Token, no CMA access (Studio's public skills never ask for those credentials). It emits the schema spec + step-by-step UI instructions. The user creates the Global Field manually in Contentstack's web app, then runs `build-section` to author the section against it.

## Task

1. **Read `componentPath`.** Extract the component's prop names and types. Use the TypeScript interface (best), `propTypes` (second), or destructured args (fallback).

2. **For each route in `usingRoutes`, read the file and find the JSX element matching the component.** For each prop assignment, capture the expression on the right, so `headline={entry.title}` becomes `{ prop: "headline", binding: "entry.title", routeFile: "..." }`.

3. **Build a binding union across routes.** For each prop:
   - If all routes bind to the same field (`headline ← entry.title` everywhere), that is a strong signal, and the schema gets a `title` field, exposed as `headline`.
   - If routes bind to different field names (`headline ← entry.title` on /blog vs. `entry.headline` on /products), flag the prop as ambiguous. Ask the user which canonical name to use OR propose making the binding configurable via `exposed-props`.
   - If a prop is sometimes set and sometimes not, mark it optional in the schema.
   - If a prop is a literal (`layout="centered"` on every route), it is not a CMS field. Keep it as a registered component prop's `defaultValue`, NOT in the section's linked schema.

4. **Map prop types to Contentstack field types.** Use the table:

   | Component prop type | Contentstack field type | Notes |
   |---|---|---|
   | `string` | `text` (single-line) | Multiline becomes `text` with `multiline:true` |
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

6. **Pause for user review.** Print exactly: `Review the schema above. To proceed, confirm: (y) the schema is correct — give me the UI steps to create it, (e) edit the proposed schema first.` Wait. **The skill never writes to Contentstack**: the user creates the Global Field in the web UI.

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

   For users who prefer a programmatic path, also emit the equivalent Global Field JSON (the body the Content Management API accepts at `POST /v3/global_fields`, and the shape the web app's Global Field **Import** takes):

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

   The user can import this JSON in the web app (Global Fields > Import), or, after confirming, send it as `POST /v3/global_fields` with a credential resolved per [`authenticate-cma`](authenticate-cma.md) (OAuth first) and the stack `api_key` header.

8. **Print the hand-off:** `Once you've created the Global Field manually in the Contentstack web UI (or via the API), run: build-section with sectionName="<name>" linkedSchemaKind="global-field" linkedSchemaUid="<uid>". build-section will then create the Studio section and bind <component> against the schema you just created.`

## Inputs needed from the user

1. `componentPath`: required, exact file path.
2. `usingRoutes` (required. If empty, the skill can't extract bindings) refuse and ask the user to run `discover-sections` first to identify routes.
3. `sectionName`: required.
4. `proposedSchemaUid`: required (default lower-snake from sectionName).

If the user hasn't run `discover-sections`, recommend that first. The skill works without it but the user-supplied `usingRoutes` becomes a guess.

## Acceptance

- [ ] Every route in `usingRoutes` was read and its JSX scanned for the component.
- [ ] Per-prop binding union table is produced: covers every prop on the component.
- [ ] Ambiguous-binding rows surface for the user to disambiguate. The skill does NOT pick a canonical name silently.
- [ ] Singleton (literal) props are listed separately and explicitly NOT in the proposed schema: they stay as component-registration defaults.
- [ ] Proposed schema field types map cleanly to Contentstack field types per the table above. No invented types.
- [ ] Step-by-step Contentstack web-UI instructions are printed for the user to create the Global Field. Optionally, the contentstack-cli JSON spec is also printed.
- [ ] The skill did NOT attempt to call CMA, did NOT ask for an auth token or Management Token, and did NOT write to the stack. The user creates the schema themselves in the UI (or via their own CLI session).
- [ ] The hand-off line names the next skill (`build-section`) and its three required inputs.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Picking a canonical UID for an ambiguous binding without asking | Routes start failing because the new field name doesn't match what the entry has | Always ask for ambiguous-row decisions explicitly |
| Folding literal props into the linked schema | The schema gets a `layout: text` field nobody writes to. Defaults are lost | Keep literal-only props as `defaultValue` on the registered component, NOT in the schema |
| Choosing `text` for a string that's actually a rich-text body | Authors get a single-line input for a long-form field | If the JSX renders the prop via `dangerouslySetInnerHTML` or a markdown renderer, propose `json_rte` instead |
| Creating a Global Field when the data clearly belongs on one CT | Authors can't edit it from the entry's natural form | If `usingRoutes` is just one CT's pages, propose a `group` field on that CT, not a Global Field |
| Inferring `reference` cardinality from prop name | "relatedPosts" plural may still be one entry. "relatedPost" singular may be multiple | Look at how the prop is rendered (`.map(...)` means multiple, a direct render means single) |

## See also

- [`design-component-library`](design-component-library.md): the pattern this schema-design applies. This skill runs **Q3 + Q4 of the [four-question framework](design-component-library.md)**: for each JSX prop, decide whether it earns a place in the linked schema (Q3: varies + functional intent) and whether it's an Exposed Prop candidate (Q4: author-understandable + DS-portable). Refuse polish props at schema-design time.
- `discover-sections`: run BEFORE this skill to identify which components become sections. This skill designs the schema for each
- `build-section`: run AFTER this skill creates the schema, binds the component against it
