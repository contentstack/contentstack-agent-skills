---
name: discover-sections-from-ct
---

## When to use

Given an EXISTING Contentstack Content Type (already provisioned, entries populated), propose Studio Section boundaries by reading the CT's schema tree. Outputs a Section inventory: one Section per binding scope (root / Group / Reference / Modular Block) with the correct `linkedSchemaKind` per boundary.

Use when adopting Studio on top of a stack that already has real content (Profile D, the "existing CT" starting state). Phrases: "we have blog_post entries already, how do I map that to Sections", "I have a stack + populated content, what Sections should I build", "propose Sections from my existing CT schema". Complements [`discover-sections`](discover-sections.md), which scans route files. This skill scans a CT schema instead. Run once per CT you're adding Studio on top of. Do NOT use for greenfield installs (no existing CT), or when the CT is being redesigned (design-first flow via [`decompose-design`](decompose-design.md) instead).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Discover Sections from an existing Content Type

## Context

Studio's model is one Section per **scope**. A scope is a place in the CT schema tree where a Section binds: the CT root, a Group field, a Reference field, or a Modular Block. Each scope has its own `linkedSchemaKind` and its own set of visible fields. You can't cross scope boundaries in one Section.

If a customer already has a well-populated CT (e.g. `blog_post` with 400 published entries), they don't need `decompose-design`. The schema is settled. They need help mapping the existing schema shape onto Section boundaries. This skill produces that mapping.

The output is a **Section proposal**: a prioritized list of Section candidates, one per scope, with the fields visible in each scope + a proposed component structure per Section. You hand the top entry to [`build-section`](build-section.md), ship it, then hand the next entry to `build-section`. The proposal stays valid until the CT schema changes.

This skill is **discovery, not authoring**. It doesn't write any composition. It produces a markdown report.

## Task

1. **Fetch the target CT schema.** Given `ctUid` + a CMA credential resolved per [`authenticate-cma`](authenticate-cma.md) (OAuth first; a management token only if the user prefers one), GET `/v3/content_types/<ctUid>`. Extract `schema` (the field tree) and `options` (`is_page`, `url_pattern` if set).

2. **Walk the schema tree and enumerate scopes.** Every scope is a Section candidate. Categories:
   - **Root scope**: the top-level CT. Fields at the root that aren't nested in Group / Reference / Modular Block. Every CT has this.
   - **Group scopes**: each `data_type: "group"` field is a Section-authorable scope. Nested groups (group-of-group) are their own scopes.
   - **Reference scopes**: each `data_type: "reference"` field is a Section scope. Both single-reference (`ref_multiple: false`) and multi-reference (`ref_multiple: true`).
   - **Modular Block scopes**: each block type within a `data_type: "blocks"` field is its own Section scope. If the field has 3 block types, that's 3 scopes.

3. **For each scope, list visible fields.** Visible = fields declared at that scope + fields inherited via `_content_type_uid` on references. Do NOT include fields from parent or sibling scopes. Sections can't bind across scope boundaries.

4. **Propose a component structure per Section.** Best-effort inference from field names + types:
   - `title` / `headline` / `heading` maps to a Heading component with `text` bound to the field.
   - `image` / `cover_image` / `hero_image` maps to an Image component.
   - **Rich text: decide by `data_type`/`field_metadata`, never by field name.** These carry formatting, so `Text`/`Heading` would render markup as literal characters:

     | Schema shape | Component | Prop type |
     |---|---|---|
     | `data_type: "json_rte"` | **`RichText`** | `json_rte` |
     | `data_type: "text"` + `field_metadata.allow_rich_text` (HTML RTE) | **`RichText`** | `any` |
     | `data_type: "text"` + `field_metadata.markdown` | **`RichText`** | `any` |
     | `data_type: "text"` + `multiline`, no rich-text flags | `Text` | `plaintext` |

     Choose **`CollapsibleText`** instead wherever the design truncates the copy ("read more", accordion). If any such field permits **embedded entries or assets**, record it. The project needs one `registerRTERenderer` call, and unregistered embeds render as bare delivery-API spans. See [`register-json-rte`](register-json-rte.md#rte-field-to-component).
   - `body` / `content` / `description` that is plain long text maps to a Text component, **and record it as an upgrade candidate** (below).

   **Rich-text upgrade candidates: always surface these, never apply them silently.** An existing model often holds prose in a plain text field simply because that was the quickest thing to pick when it was created. Report them and let the user decide:

   | What you found | Suggest | Cost to accept |
   |---|---|---|
   | Field is **already** `json_rte` / rich text, but the current code renders it through a plain text component | Switch the component to `RichText` | **None**: no schema change, no migration. Free correctness win |
   | Plain **multiline `text`** field holding body copy, description or prose | Consider `json_rte` so authors can bold, link, list and embed | A schema change on a live CT. See [`migrate-ct-schema`](migrate-ct-schema.md). Existing entry values carry over as plain paragraphs |
   | Long prose the site truncates behind "read more" / an accordion | `CollapsibleText` over the same field | None if the field is already rich text |

   Phrase it as a recommendation with the cost attached ("`summary` is plain text today. Making it `json_rte` would let authors add links, but it's a schema change on N live entries. Want it?") and proceed with the existing type if they decline. Never migrate a field as a side effect of a discovery run.
   - `cta_label` + `cta_url` (or `link`) maps to a Button component.
   - `is_featured` / `is_premium` (boolean) maps to a Condition Block around premium-only children.
   - Multi-value fields inside a Repeater (already the scope's iteration boundary if Modular Block or multi-reference).
   - Flag unknown fields in "Unmapped fields" so the developer decides.

5. **Score + prioritize.** Sort scopes by rough authoring value:
   - Root scope + top-level fields: HIGHEST (every entry uses this Section).
   - Groups referenced from multiple contexts: HIGH.
   - Modular Blocks (composability wins): MEDIUM-HIGH.
   - References not yet used elsewhere: MEDIUM.
   - Rarely-populated fields (empty on >50% of entries. Check via a CDA sample of 10 entries): LOW.

6. **Emit the Section proposal** as a markdown document at `docs/_discovery/<ct_uid>-sections.md`:

   ```markdown
   # Section proposal — `<ct_uid>` CT

   ## Summary
   - CT UID: <ct_uid>
   - Total scopes: <N>
   - Recommended Sections to build: <top 3-5>

   ## Scope-by-scope Section candidates

   ### 1. `<ct_uid>` — root scope (linkedSchemaKind: entry)

   **Fields in scope:** `title`, `slug`, `hero_image`, `excerpt`, `published_date`, `is_featured`

   **Proposed Section: `<ct_uid>_hero`**
   - Layer 2 composition containing Heading + Image + Text + Condition Block
   - Bindings:
     - Heading.text ← `title`
     - Image.src ← `hero_image`
     - Text.value ← `excerpt`
   - Condition Block around a "Featured" badge, condition `is_featured == true`
   - Exposed props: `heading_level` (choice: h1/h2/h3), default h1
   - Priority: HIGH — used on every entry

   ### 2. `<ct_uid>.body_blocks` — Modular Block scope

   **Block types in this field:** `text_block`, `image_block`, `quote_block`

   Three Section candidates, one per block type:

   #### 2a. `<ct_uid>_body_text_block` (linkedSchemaKind: block, block_type: text_block)
   [...]

   #### 2b. `<ct_uid>_body_image_block` (linkedSchemaKind: block, block_type: image_block)
   [...]

   ### 3. `<ct_uid>.author` — Reference scope (linkedSchemaKind: reference)

   **Referenced CT:** `author`
   **Fields visible in this scope:** `author.name`, `author.avatar`, `author.bio`

   **Proposed Section: `<ct_uid>_author_card`**
   [...]

   ## Unmapped fields

   These fields exist in the CT but the skill couldn't confidently propose a Section shape. Decide per-field:

   - `<field_uid>` (data_type: <type>) — [suggestion, or "review manually"]

   ## Build order

   1. Build `<ct_uid>_hero` first (touches every entry).
   2. Then Modular Block Sections (2a, 2b, 2c) — enables authoring flexibility on body content.
   3. Then reference Sections (author_card, related_posts).
   4. Finally the Template composing all Sections in order.

   ## What this proposal is NOT

   - Not a schema migration — no CT fields change.
   - Not a design proposal — component names / layout are best-effort inference; feel free to override.
   - Not an author-experience proposal — governance choices (which props to expose per Template) are yours.
   ```

7. **Sanity-check the proposal.**
   - Every listed scope has at least one populated entry (spot-check via CDA `/v3/content_types/<ctUid>/entries?limit=1&only[BASE][]=<field>`).
   - No proposed Section spans two scopes.
   - Every scope has a valid `linkedSchemaKind` value.
   - Unmapped fields flagged: do NOT silently drop them.

## Inputs needed from the user

1. **Content Type UID**: the CT to discover Sections against.
2. **Stack API key + a CMA credential resolved per [`authenticate-cma`](authenticate-cma.md) (OAuth first); a management token only if the user prefers one**: for the CMA read.
3. **Optional: sample size for populated-check**: default 10 entries. Increase for larger stacks.
4. **Optional: output path**: default `docs/_discovery/<ct_uid>-sections.md`.

## Acceptance

- [ ] Every scope in the CT schema is enumerated.
- [ ] Each Section candidate has a valid `linkedSchemaKind` matching its scope.
- [ ] Fields are correctly attributed to scopes, no cross-scope leakage.
- [ ] Component-structure inference is documented as a proposal (not a decision).
- [ ] Unmapped fields are flagged with the field UID + data type.
- [ ] Build order is topologically sound: foundational Sections before dependents.
- [ ] Output file emitted at the requested path.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Proposing a Section that binds fields from two scopes | Studio rejects cross-scope bindings at author time | Every scope gets its own Section. If you want to combine, use a Template that composes both Sections. |
| Assuming Modular Block = one Section | Each block type is its own scope. A 3-block-type field is 3 Sections | Enumerate block types explicitly. |
| Skipping empty scopes | A rarely-populated field might still need a Section for the entries that DO have it | Include, mark LOW priority, let developer decide. |
| Over-inferring component structure | Component name doesn't have to match field name. Developer's design system may not have "Heading" | Propose, flag as suggestion, developer overrides. |
| Missing `_content_type_uid` resolution on references | Reference scopes need the referenced CT's schema fetched too, otherwise fields aren't visible | For each reference field, fetch the referenced CT's schema too. |
| Forgetting to check populated-ness | Skill proposes 15 Sections. 8 of them cover fields that no entry actually populates | Sample 10 entries. Downgrade scopes where >50% of samples don't populate. |

## Handoff to downstream skills

After the proposal is emitted, the customer walks the build order:

1. **Read the proposal**: the developer + design lead review + edit.
2. **Register any missing components** via [`register-component`](register-component.md).
3. **Build the top-priority Section** via [`build-section`](build-section.md). Hand it the scope + field list from the proposal.
4. **Verify it renders** against a real entry via [`verify-setup`](verify-setup.md) Layer 6-7.
5. **Repeat** for each Section in the build order.
6. **Assemble the Template** via [`build-connected-template`](build-connected-template.md).

## See also

- [`discover-sections`](discover-sections.md) (Section discovery from EXISTING ROUTE FILES (Profile C) hand-coded migration). Same output shape, different input.
- [`decompose-design`](decompose-design.md) (Section discovery from a DESIGN (Profile B) greenfield with a design).
- [`build-section`](build-section.md): authors each Section this proposal identifies.
- [`decompose-design`](decompose-design.md): the three-layer mental model + scope rules (one Section per scope).
- [`migrate-ct-schema`](migrate-ct-schema.md): evolves the CT AFTER this proposal, if scope boundaries need adjusting.
