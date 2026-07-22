---
name: decompose-design
description: "Take a **design artefact** (a Figma frame or URL, a screenshot, a PDF mock, a wireframe, a whiteboard photo, a hand-drawn sketch, or a natural-language description of a page) and emit a full three-layer decomposition ready to feed the downstream Studio skills. Output is a machine-readable inventory of Layer-1 atomics, Layer-2 containers, Layer-2 layout components, Layer-3 Sections, and a proposed Content Type shape."
allowed-tools: Read Grep Glob
---

## When to use

Take a **design artefact** (a Figma frame or URL, a screenshot, a PDF mock, a wireframe, a whiteboard photo, a hand-drawn sketch, or a natural-language description of a page) and emit a full three-layer decomposition ready to feed the downstream Studio skills. Output is a machine-readable inventory of Layer-1 atomics, Layer-2 containers, Layer-2 layout components, Layer-3 Sections, and a proposed Content Type shape.

Use as the FIRST skill on any greenfield Studio build starting from a design (no code yet), or before running `plan-studio-architecture` when the input is visual rather than a requirements doc. Phrases — "here's the design", "here's a Figma link", "here's a screenshot of the page", "map this design to Studio", "how would I build this in Studio", "how do I decompose this page", "decompose this design", "what components do I need for this design". Do NOT use when the customer already has a React codebase — reach for `discover-sections` and `design-section-from-jsx` instead. Do NOT use for backend/data-model-only questions (no visual design).

# Decompose a design into Studio's three layers

## Context

Studio composes pages from three layers: **Layer-1 atomic components** (one CMS field each), **Layer-2 containers with slots** (holding atomics or nested containers, encoding design-system layout in code), and **Layer-3 Sections** (canvas compositions rooted at a schema scope). See `from-designs-to-sections` for the taxonomy — this skill assumes you've read it (or you're an agent applying its rules).

This skill runs the taxonomy over a specific design artefact. Every downstream skill in the Studio flow — `register-component`, `build-section`, `build-connected-template`, `plan-studio-architecture` — assumes this decomposition is already done. When it's not, developers guess piece-by-piece and produce inconsistent registrations (over-exposed slots, under-exposed slots, missed layout components, wrong Section boundaries).

Ship this decomposition BEFORE registering anything. Registrations are expensive to redo; the plan you emit here is what makes them right the first time.

## Audience — who consumes the sheet, and how it gets executed

**The developer** is the sole audience. The sheet is *not* for content managers — it's a machine-readable build plan. It gets executed one of three ways, in priority order:

### Execution path 1 — API authoring (fastest, most reliable, no canvas clicks)

For every Section + the Template on the sheet, chain to [`author-composition-via-api`](../author-composition-via-api/SKILL.md). It writes the composition JSON directly through the CMA — no Studio UI, no drag-drop, no iframe timing issues. Every drop-tree in the sheet maps 1:1 onto the composition's node tree; every bind row maps 1:1 onto a `bindings` entry. Deterministic, idempotent, replayable.

**Prerequisites:** stack credentials in the customer's env (management token). This skill's Step 1 already reads `.env` when fetching the CT — the same creds serve API authoring.

This is the **default handoff** for `decompose-design`. Ship the sheet, then loop over Sections calling `author-composition-via-api` per Section, then post the Template.

### Execution path 2 — Playwright MCP driving the Studio canvas

For customers who want the canvas trail (for review, screenshotting, or matching what a human author would do), chain to [`build-section`](../build-section/SKILL.md) per Section, then [`build-connected-template`](../build-connected-template/SKILL.md). These skills drive the Studio canvas via [Playwright MCP](../install-playwright-mcp/SKILL.md) using the proven `mouse.down/move/up` sequence documented in `build-section` § *LLM execution caveat*. Slower than API path, but produces a real Studio canvas trail you can screenshot.

**Prerequisites:** Playwright MCP installed (`install-playwright-mcp`) + a running Studio session in a browser the MCP can drive.

### Execution path 3 — Developer follows the sheet in Studio's UI manually

Only when neither API creds nor Playwright MCP is available. The sheet's drop-trees and bind tables are formatted to be read top-to-bottom in Studio's canvas: every node is a drop-target instruction, every table is a prop-to-field binding. Slowest path; last resort.

### Which path does `decompose-design` recommend?

Determined by what the environment provides:

| Environment signal | Handoff |
|---|---|
| Management token available (env vars / Contentstack profile) | **Path 1 — API authoring.** Chain to `author-composition-via-api` per Section + Template. |
| No management token but Playwright MCP installed | **Path 2 — canvas automation.** Chain to `build-section` + `build-connected-template`. |
| Neither | **Path 3 — manual.** Print the sheet; instruct the developer to follow it in Studio's UI. |

Content managers benefit *from* what the sheet produces (exposed props, slots, modular-block areas) but they don't consume the sheet. If a content manager is doing this without a developer, run [`author-without-code`](../author-without-code/SKILL.md) instead — that's their skill.

## Task

### Step 1 — Ingest the design

Accept the artefact in whatever form the customer supplies:

- **Figma URL or frame node ID** — request read access; use the Figma MCP or a screenshot dump. Identify every frame that maps to one page + its child components.
- **Screenshot / image / PDF page** — inspect visually (Read tool + image viewing). Identify sections stacked top-to-bottom.
- **Wireframe / sketch** — same as image; less fidelity but same decomposition rules apply.
- **Natural-language description** — "the page has a hero with a title on the left and an image on the right, then a three-across card grid…". Enumerate the sections + their contents mechanically.
- **HTML/CSS mock** — parse the markup; each block-level region is a candidate Section, each leaf element is a candidate atomic.

Output of this step: a numbered list of visual regions (Sections) top-to-bottom, each with a short description.

### Step 2 — Identify Layer-1 atomics

For every design region, list every **leaf visual element** that renders one piece of content:

- Any heading / title / label → likely a `string` atomic (`<Heading>`, `<Text>`).
- Any paragraph / body copy → `string` atomic (`<Text>`, `<Paragraph>`).
- Any image → `imageurl` atomic (`<Image>`).
- Any button or link → `href` atomic (`<Button>`, `<Link>`).
- Any date / time-ago / "N min read" → `datestring` or `number` atomic.
- Any badge / status pill / tag → `choice` or `string` atomic.
- Any rich-text block (mixed formatting, embedded assets, lists) → `json_rte` atomic (`<RichText>`).

For each atomic, record:
- Proposed component name (`<Heading>`, `<Image>`, etc. — reuse across the design, don't invent new atomics per Section unless the visual really differs).
- Proposed prop schema (one scalar prop, plus its Studio prop type).
- Proposed CMS field the prop binds to (naming pattern: `entry.<field>` or `item.<field>` if inside a Repeater).

Never propose a Layer-1 atomic with an `array`, `object`, or `React.ReactNode` prop — that's not atomic (atomic = one scalar → one visual). Those props are valid Studio prop types, but the component that owns them is a **Layer-2 self-composing shape** — see Step 3.

### Step 3 — Identify Layer-2 components

Layer 2 = any registered component that's not a pure Layer-1 atomic. Three concrete shapes to look for:

**3a. Container with slots** — wrappers holding other components in fixed shape regions:

- Card frames (border, radius, padding around a title + body).
- Modal / panel chrome (header + body + footer).
- Split / two-up shapes (`left` + `right`).
- Callout boxes (icon + message + action).
- Author cards (avatar + text block).

For each, record:
- Proposed component name (`<Card>`, `<AuthorCard>`, `<Callout>`).
- Slot props (`body`, `left`, `right`, `header`, `content`).
- **Whether the container also binds to CMS scalars.** If some regions of the container are same-content-every-usage (e.g. `authorName` always binds to `author.name`), those become scalar bindable props on the container itself, not slots. See `from-designs-to-sections` § *When to expose a slot vs bind a scalar*.
- Proposed scope (does this container bind to the CT root, a Group, a Reference — or is it purely structural).

**3b. Self-iterating component (`type: "array"` prop)** — a component that receives a bound multi-value field and renders `.map()` internally, without a Studio Repeater. Use when the list rendering is straightforward (single-shape items, no per-iteration variant authoring, no template-author child-swap):

- Bullet list of feature items (`<FeatureList>` bound to a **multi-value Group** — the values are already on the entry, no extra resolution needed).
- Compact tag strip (`<TagList>` bound to a **multi-Reference** of tag entries).
- Logo bar (`<LogoBar>` bound to a **multi-Reference** of brand entries).

For each, record:
- Proposed component name.
- One `array` prop (e.g. `items`, `tags`, `logos`) with `items: { type: <inner shape> }`.
- Proposed CMS field binding: multi-value Group, multi-value scalar, Modular Block, or multi-Reference.
- **Reference-only requirement** — if the source is a Reference (single or multi), populate `data_sources.resolvedReferences` on the composition so CDA includes the referenced entries. Without it, References arrive as `{ uid }` stubs. Groups, Modular Blocks, and scalar multi-values live on the entry itself and need no resolution — the array arrives populated as-is.

Do NOT use this shape when the design needs per-iteration variant authoring, Modular-Block polymorphism, template-author child-swap, or Studio's canvas Preview Mode showing N rendered children — those cases want a **List Section with a Repeater** (Step 5). The full decision framework — array-prop vs Repeater-in-Simple-Section vs List Section — is documented at `from-designs-to-sections` § *Deciding how to iterate*. Walk it every time a list appears in the design; don't guess.

**3c. Self-composing component (`type: "object"` prop)** — a component that receives a bound object shape and renders its subfields internally. Use when a nested Group has a fixed structure that always renders the same way:

- Address block bound to a `location` Group with `street / city / zip` subfields.
- Contact card bound to a `contact` Group with `email / phone / role`.
- Nested stat block bound to a `stats` Group.

For each, record:
- Proposed component name.
- One `object` prop with `properties: { … }` matching the Group's subfields.
- Proposed Group binding.

**3d. Layout container** — covered in Step 4.

For every Layer-2 component (any shape above), pick one of two design intents:

- **Content shape** (3a / 3b / 3c) — the component knows a specific content pattern; the fill is either slot-driven (3a) or data-driven (3b / 3c).
- **Layout shape** (Step 4) — the component encodes a design-system layout rule (columns, gaps, breakpoints).

A component can be BOTH — a hybrid layout+content component that renders a design-system 3-column grid AND binds to a multi-Reference through an internal `.map()`. Record it under the layout list with its array binding noted.

### Step 4 — Identify Layer-2 layout components

Every layout decision — grid tracks, gaps, breakpoints, spacing rhythm — that recurs across the design gets its own registered layout component:

- 2-column split (hero image + text) → `<TwoColumn>`.
- 3-across card grid → `<ThreeColumn>` (or `<Grid columns={choice}>`).
- Vertical spacing between Sections on the Template → `<Stack>`.
- Constrained content width → `<Container>` or `<PageWrapper>`.

For each layout component, record:
- Proposed name.
- Slot props per region (`col1`, `col2` / `left`, `right` / `items` for repeating).
- Design-system values encoded in the component's CSS (columns, gap at each breakpoint).

Do NOT propose registering `<Grid>` with a free-integer `columns` prop that lets authors invent unauthorized column counts. Constrain to design-system-approved values via a `choice` prop, or register named variants (`<TwoColumn>`, `<ThreeColumn>`, `<FourColumn>`).

Do NOT propose registering `<Box>` — a generic wrapper is either an unnecessary registration (skip it) or actually a specific layout component (name it accordingly).

### Step 5 — Draw Section boundaries (Layer 3)

Apply the **schema-shape rule** from `from-designs-to-sections` § *Where Section boundaries fall*: each Section is rooted at exactly one schema scope. New scope → new Section.

For each Section candidate:

- Identify the schema scope it binds against — CT root / Global Field / Group / Modular Block / Reference (single) / Reference (multi).
- Classify as **Simple Section** (no root Repeater) or **List Section** (root Repeater over a multi-value field).
- List the Layer-2 containers + Layer-1 atomics dropped inside it.
- For List Sections iterating a polymorphic scope (multi-CT Reference, Modular Block), note the **Condition Blocks needed per allowed type**.

### Step 6 — Propose the Content Type shape

Given the Sections and their scope requirements, propose the underlying Content Type shape:

- Root fields directly on the CT (used by Sections rooted at the CT root).
- Groups for structured subfields.
- References (single) for "belongs to one entry" relationships.
- References (multi) for "belongs to N entries" relationships.
- Modular Blocks for "polymorphic list of typed blocks".
- Global Fields for schemas reused across CTs.

For each field, propose:
- Field type (single-line, multi-line, number, boolean, isodate, link, file/asset, json_rte, reference, group, modular_block).
- `multiple` flag where applicable.
- Field UID (kebab-case).
- Which Section(s) bind to it.

### Step 7 — Apply the governance dial

Before writing the sheet, classify each field / prop on the target Content Type into one of three governance states. This is a design-system decision: how much of the page is a marketer allowed to change?

- **Content — bound and sealed.** Headlines, copy, images, links, prices. The CMS entry drives the value; the component reads it; the marketer cannot override on this page. Default for anything semantic.
- **Layout/style — exposed props with token-constrained values.** Columns, media side, gap, background, variant, alignment. Marketers pick from design-system-approved options via a `choice` prop; they don't invent new values.
- **Variable areas — marketer-open.** Story flows, campaign bodies, promoted-content strips. Modular Blocks or a Section Slot lets the marketer add / reorder / choose per-page without code.

**Target: five marketer decisions per page, not fifty.** Fully data-driven Sections expose nothing (all-bound). A Section that exposes every prop is a design failure: authors either drift the design system or ignore Studio entirely. The governance dial output for each Section: "content bound + these three exposed props + this one slot for variable content."

### Step 8 — Every CT field ends in exactly one state (unmapped-fields discipline)

Walk every field on the target Content Type. Each must end this run in one of four states:

- **Bound** — used by an atomic or Layer-2 scalar prop inside a Section.
- **Exposed** — used by an exposed section prop (per Step 7's governance dial).
- **Handled outside Studio** — SEO metadata read by the framework's `<Head>`, route-level fields consumed by the app, etc. Note explicitly.
- **Unmapped** — not used by this design. Listed on the sheet's `Unmapped fields:` one-liner with a reason (deprecated, planned-but-not-yet, held-for-future-page, etc.).

No field is silently skipped. If a field ends the run without a state, the plan isn't done.

### Step 9 — Emit the build sheet

Write a **build sheet** — an actionable spec a developer follows to build the page in Studio. The sheet is a markdown document with a fixed shape. Every line is either an instruction or a mapping; no purpose prose, no click-by-click UI. Ship it as `docs/<template-slug>-build-sheet.md` in the customer's repo (or print inline if no `docs/` directory exists).

**Structure:**

```
BUILD SHEET · <Template name>
Connected → <ct_uid> · URL {{entry.url}}        (or: Freeform · /<url>)

## Decisions made        ← 5–6 one-liners, each overridable
## Components            ← one table
## Sections S1…Sn        ← children first; per-section format below
## Template              ← assembly
## Proposed schema       ← ONLY when no schema existed
Unmapped fields: <field> (<reason>) · <field> (<reason>)
```

**Decisions made** — 5-6 one-liners covering: template pattern (Connected vs Freeform + CT + URL), any split/seal calls on components, any marketer-open areas (Modular Blocks / Section Slots), any fields deliberately unmapped, any schema reuse/extension calls.

**Components table:**

| Component | Tier | Status | Key props |
|---|---|---|---|
| Product Card | Layer-2 sealed | reuse — `components/ProductCard.tsx` | — |
| Card Grid | Layer-2 layout | **build** | Cards (slot) · columns · gap |
| Heading | Layer-1 atomic | **build** | text · level |

*"Sealed" = Layer-2 with all data props bound and no slots — brand-consistent, cannot be recomposed. Contrast with slot-based Layer-2 containers that leave regions marketer-fillable.*

**Per-section format** — three blocks:

```
### S2 · Product Rail
**Connect:** content type `campaign_page` → schema `featured_products` (multiple ref → `product`)

    Drop Card Grid                                   (Brand · Patterns)
    └─ in Cards slot → drop Repeater · bind Items → featured_products
       └─ inside → drop Condition · content type is product
          └─ inside → drop Product Card

**Bind — Product Card** (root: Repeater Data)

| Prop | → Field |
|---|---|
| Image | `hero_image` |
| Name | `name` |
| Price | `price` |
| Link | `url → href` *(bind the leaf, not the link object)* |

**Expose:** Card Grid → Columns (**Rail columns**), Gap (**Rail spacing**)
```

Notation:
- `→` binds: `prop → field`
- `└─` drills in (tree double as step list — every node is a short action)
- Bindings inside a Repeater note their root: *(root: Repeater Data)*
- Condition guards: `Condition: content type is product` (References) / `Condition: is of type quote` (Modular Blocks)
- Exposed labels are **bold + unique within the section**

**Template block:**

```
### Template · Campaign Landing
New Template → Connected → `campaign_page` → URL `{{entry.url}}`

| # | Drop section | Auto-binds to |
|---|---|---|
| 1 | Campaign Hero | `hero` |
| 2 | Product Rail | `featured_products` |

**Set exposed props:** Rail columns `3` · Hero media side `right`
```

**Proposed schema block** (only when no usable schema existed):

| Field | UID | Type | Binds to |
|---|---|---|---|
| Hero | `hero` | group (eyebrow, headline, subcopy, image, cta) | S1 |
| Featured Products | `featured_products` | multiple reference → `product` | S2 repeater |

**Unmapped fields:** `<field>` (reason) · `<field>` (reason)

### Step 10 — Close with two offers (developer decision points)

The build sheet is the plan. Two things can happen next; ask both, in one closing block:

> **To make this buildable:** \<N\> new components need code + registration → \<names with tiers\>. \<Existing components\> register as-is.
>
> **Offer 1 — code phase.** Want me to scaffold + register these components in your repo now?
>
> **Offer 2 — Studio-canvas phase.** Once code is done, want me to author the Sections + Template automatically?
>   - **A** — via API (fastest): chains `author-composition-via-api` per Section + Template. Requires a management token in env.
>   - **B** — via Studio canvas (slower, produces canvas trail): chains `build-section` + `build-connected-template` through Playwright MCP. Requires `install-playwright-mcp` done.
>   - **C** — hand me the sheet; I'll do it in Studio's UI myself.

If the developer accepts **Offer 1**: hand off to `register-component` per new atomic + Layer-2, following the palette conventions.

If the developer accepts **Offer 2A**: for each Section in the sheet, hand off to [`author-composition-via-api`](../author-composition-via-api/SKILL.md) passing the Section's drop-tree + binding table as the composition-node structure. Post the Template last.

If the developer accepts **Offer 2B**: for each Section in the sheet, hand off to [`build-section`](../build-section/SKILL.md) / [`build-repeating-section`](../build-repeating-section/SKILL.md) passing the sheet's Section block as input. `build-section`'s LLM-execution rules (mouse.down/move/up sequence, stable selectors, Layers tree for invisible nodes) apply.

If **Offer 2C**: the sheet's drop-trees and bind tables are already formatted for a developer to follow in Studio's UI — every node is a drop instruction, every table is a bind mapping.

**Whichever path executes Offer 2, close with [`verify-setup`](../verify-setup/SKILL.md).** Every path lands at the same verified end state.

## Inputs needed from the user

1. The design artefact (Figma URL, screenshot path, PDF path, sketch, or natural-language description).
2. The target Content Type name (if known; otherwise propose one from the design's page kind).
3. Any known design-system constraints — "we already have `<Card>`", "our grid always uses `<ThreeColumn>` with 24px gaps", etc.
4. Whether the design is greenfield (no existing code) or paired with a production page being migrated (if migrating, run [`discover-sections`](../discover-sections/SKILL.md) alongside).

Do NOT invent designs. If the user says "figure out a design for a blog post," push back — ask for the design artefact or use [`plan-studio-architecture`](../plan-studio-architecture/SKILL.md) which handles the requirements-first path.

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] Every visual leaf in the design is classified as a Layer-1 atomic with a proposed scalar prop type + CMS field binding.
- [ ] Every content-shaped wrapper is classified as a Layer-2 container with slot props (and any bindable scalar props on itself).
- [ ] Every layout decision (columns, gaps, breakpoints, vertical rhythm) is classified as a Layer-2 layout component. No layout decision is "TBD via Design Panel."
- [ ] Every Section is rooted at exactly one schema scope per the schema-shape rule; polymorphic scopes call out the needed Condition Blocks.
- [ ] The Content Type shape is proposed with concrete field types + UIDs.
- [ ] The plan is emitted as a single machine-readable YAML (or equivalent) document ready to hand to `register-component` + `build-section` + `plan-studio-architecture`.
- [ ] No **Layer-1 atomic** proposes an `array`, `object`, or `React.ReactNode` prop (atomic = one scalar → one visual). Components with `array` / `object` props ARE valid and register as **Layer-2 self-iterating** (Step 3b) or **self-composing** (Step 3c) shapes.
- [ ] Every `array` prop bound to a **Reference** field has `data_sources.resolvedReferences` planned; `array` props bound to Groups / Modular Blocks / scalar multi-values do NOT.
- [ ] No layout component proposes a free-integer `columns` prop or a generic `<Box>` registration.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Skipping the layout classification (Step 4) | Every layout decision drifts to Studio's Design Panel per Section → design-system drift | Enumerate every recurring layout in the design and register a specific Layer-2 layout component for it (`<TwoColumn>`, `<Stack>`, etc.) |
| Proposing atomics per Section instead of per shape | Ends up with `<HeroTitle>`, `<CardTitle>`, `<FooterHeading>` — every one a `string` prop that could reuse a single `<Heading>` | Same atomic for same shape across the design; use registered variants (`choice` prop) if the visual really differs |
| Over-exposing slots | Every Section author has to fill every slot for every drop; component becomes tedious | Slot only what varies per usage; scalar-bind everything that's same-per-usage. See `from-designs-to-sections` § *When to expose a slot vs bind a scalar* |
| Merging two schema scopes into one Section | Auto-binding won't match — a Section rooted at both CT root AND a Reference scope simultaneously isn't a valid shape | Split into two Sections per the schema-shape rule |
| Missing Condition Blocks on polymorphic References or Modular Blocks | List Section renders nothing per iteration when the source is multi-CT or polymorphic | Note the required Condition Blocks per allowed type on every polymorphic Section |
| Emitting the plan as prose | Downstream skills can't consume prose; ambiguity re-enters the flow | Emit YAML (or equivalent structured document) that `register-component` / `build-section` can be pointed at |

## See also

- `from-designs-to-sections` — the taxonomy this skill applies. Read first.
- [`plan-studio-architecture`](../plan-studio-architecture/SKILL.md) — takes the plan this skill emits (or a requirements doc) and orders the build sequence.
- [`register-component`](../register-component/SKILL.md) — mechanics of registering each Layer-1 and Layer-2 output.
- [`build-section`](../build-section/SKILL.md) — mechanics of authoring each Section output.
- [`discover-sections`](../discover-sections/SKILL.md) — companion skill for the *code-first* path (existing React codebase).
- [`design-section-from-jsx`](../design-section-from-jsx/SKILL.md) — for individual JSX components, propose the linked-schema shape.
- [`figma-generate-components`](../figma-generate-components/SKILL.md) — when the customer wants raw React code generated from Figma frames alongside this decomposition.
- [`adapt-collection-component`](../adapt-collection-component/SKILL.md) — when the design uses a legacy production wrapper with an array/object prop.
