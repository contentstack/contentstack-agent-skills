---
name: build-page-builder-template
---

## When to use

Assemble the pattern that lets an author **pick and order sections per page**, a page content type whose modular-block field lists the available section types, one Section per block type, and one template that renders whichever blocks the author added, in their order. Use Studio UI, driven through Playwright per [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md). Don't hand the clicks to the user or switch to the API unless they ask; that's [`author-composition-via-api`](author-composition-via-api.md).

Use when the ask is "authors should build their own pages", "a page builder", "let marketing add sections in any order", "drag sections onto a page", "one template for many different page layouts", or when a design set shows the same page shape recomposed differently per page (a marketing site, a landing-page system). Phrases: "page builder", "section picker", "modular page", "authors choose the sections", "reorder sections". Do NOT use for a page whose sections are fixed in a known order (that's `build-connected-template` dropping sections directly). Do NOT use to build the individual Sections (`build-section`) or decide the primitive library (`design-component-library`).

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Pattern preflight: mandatory.** Before the first write, run [`match-existing-pattern`](match-existing-pattern.md): read the Templates and Sections already in the project, **reuse what already covers this schema**, and build to the pattern they use. Skip it only when the project has no compositions at all. Authoring something structurally foreign to what is there is rework, and it is invisible until someone opens the Layers panel.

# Build a page-builder template

## Context

A Connected template normally places a fixed set of Sections. That is correct when every page of that type looks the same. It is wrong the moment marketing wants a hero on one page, a hero plus comparison table on another, and the same three sections in a different order on a third, because each variation then needs its own template.

The page-builder pattern moves that choice into content:

```
Page CT (alpha_page)
  page_sections : Modular Block
      ├── hero_centered      { heading, description, cta_1, media }
      ├── benefits_section   { heading, benefits[] }
      └── comparison_table   { … }

One Section per block type, each linked to alpha_page.page_sections.<block_uid>

Template (connected to alpha_page)
  repeater [items → page_sections]
    condition-block {modular_block = hero_centered}    → section-composition (Hero Centered)
    condition-block {modular_block = benefits_section} → section-composition (Benefits)
    condition-block {modular_block = comparison_table} → section-composition (Comparison)
```

The author adds blocks to `page_sections` in any order. The Repeater walks them. Each Condition Block matches one block type and renders the Section built for it. **One template renders every page of that type, whatever the author composed.**

Verified against a production Studio site: one template, 98 nodes, **30 Condition Blocks**, 30 section types an author can choose from, with no second template.

## Task

### Step 1: Model the page content type

One Modular Block field holds the page body. Each block type is one section's content shape.

- Field uid: something neutral (`page_sections`, `body`, `blocks`). It is the page's spine, not a section name.
- One block per section type. The block's sub-fields are exactly what that section binds: `heading`, `description`, `cta_1`, `media`.
- Do **not** add design fields (`gap`, `align`, `variant`). Those are static values on the canvas. See [`design-component-library`](design-component-library.md) § content binds, design stays static.

Schema work belongs to [`provision-studio-stack`](provision-studio-stack.md) (new CT) or [`migrate-ct-schema`](migrate-ct-schema.md) (existing CT).

### Step 2: Build one Section per block type

Each Section links to that **specific block**, not the Modular Block field:

```
linked schema: alpha_page . page_sections . hero_centered
                  CT           MB field        block uid
```

`build-section` calls this the **Block** linked-schema kind: the block shape is fixed, so the Section is single (no Repeater at this level). Its bindings then read the block's own fields directly, `text → heading`, `href → cta_1.url`.

Build each Section from the registered primitive library ([`compose-marketing-section`](compose-marketing-section.md)), not from bespoke components. That is what makes 30 sections share one palette.

### Step 3: Assemble the template

On a Connected template bound to the page CT:

1. Drop a **Repeater**, bind `items` to the Modular Block field (`page_sections`).
2. Binding `items` opens **Add Condition**: tick every block type and click **Add** (not Skip). Studio inserts **one Condition Block per block type**, siblings, not nested. Each carries `condition.type: "modular_block"` and the block uid as its value ([`use-condition-block`](use-condition-block.md)).
3. Drop each block type's **Section** into the Box inside its Condition Block. Dropping a Section never creates a condition.

The Condition Block is what makes a polymorphic list resolve: without it the iteration item has no known schema and every binding inside renders empty.

### Step 4: Verify with a real entry

Create one entry that uses **several different block types, out of order**, and confirm:

- Each block renders its own Section, in the author's order.
- A block type with no Condition Block renders **nothing, silently** (the most common defect here). Enumerate the CT's block types against the template's Condition Blocks and confirm the counts match.
- Adding a new block to the entry needs no developer.

## Acceptance

- [ ] Page CT has one Modular Block field holding the page body. No design props among its sub-fields.
- [ ] One Section per block type, each linked at `<ct>.<mb_field>.<block_uid>` (Block kind, not the MB field).
- [ ] Template has exactly one Repeater bound to the Modular Block field.
- [ ] One Condition Block per block type, as siblings under the Repeater: **count matches the CT's block count**.
- [ ] Each Condition Block contains the Section for its block type.
- [ ] An entry mixing several block types out of order renders each in the author's order.
- [ ] Adding a block type end-to-end touches three places: the CT (new block), then a new Section, then a new Condition Block. No template rewrite.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| One template per page layout | The variation is content, not structure: N templates all rendering the same components, each needing the same fix N times | One template, one Repeater, Condition Blocks per block type |
| Section linked to the Modular Block **field** instead of a **block** | The field is a list of mixed shapes, so bindings cannot resolve to one block's sub-fields | Link at `<ct>.<mb_field>.<block_uid>`, the Block kind in `build-section` |
| A block type with no Condition Block | That block renders **nothing**, with no error. Authors report "my section disappeared" | Enumerate CT block types vs template Condition Blocks. Counts must match |
| Authoring the iteration inside a Section instead of on the template | The Section then owns the whole page body and cannot be reused per block | Repeater lives on the template. Each Section handles exactly one block |
| Design fields (`gap`, `align`, `variant`) added to blocks so authors can "adjust" | Schema becomes unreadable and pages drift visually per entry | Design is a static value on the canvas |
| Bespoke components per block type | 30 blocks become 30 one-off components and the palette is unusable | Compose every Section from the shared primitive library |

## See also

- [`design-component-library`](design-component-library.md): decide the primitives before building 30 Sections from them.
- [`compose-marketing-section`](compose-marketing-section.md): build each Section from those primitives.
- [`build-section`](build-section.md) § linked-schema kinds: the **Block** kind this pattern depends on.
- [`use-condition-block`](use-condition-block.md): the discriminator metadata on each branch.
- [`use-repeater`](use-repeater.md): the iteration over the Modular Block field.
- [`build-connected-template`](build-connected-template.md): the template this pattern is assembled on.
- [`decompose-design`](decompose-design.md) / [`decompose-site`](decompose-site.md): deriving the block list from designs.
