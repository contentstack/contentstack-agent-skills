---
name: decompose-design
---

## When to use

Take a **design artifact** (a Figma frame or URL, a screenshot, a PDF mock, a wireframe, a whiteboard photo, a hand-drawn sketch, or a natural-language description of a page) and emit a full three-layer decomposition ready to feed the downstream Studio skills. Output is a machine-readable inventory of Layer-1 atomics, Layer-2 containers, Layer-2 layout components, Layer-3 Sections, and a proposed Content Type shape.

Use as the FIRST skill on any greenfield Studio build starting from a design (no code yet), or before running `plan-studio-architecture` when the input is visual rather than a requirements doc. Phrases: "here's the design", "here's a Figma link", "here's a screenshot of the page", "map this design to Studio", "how would I build this in Studio", "how do I decompose this page", "decompose this design", "what components do I need for this design". Do NOT use when the customer already has a React codebase. Reach for `discover-sections` and `design-section-from-jsx` instead. Do NOT use for backend/data-model-only questions (no visual design).

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Reuse preflight: mandatory when the project already has compositions.** Before naming a single new atomic, component or Section, run [`match-existing-pattern`](match-existing-pattern.md) § Step 1b: it groups existing Sections by the schema they bind and ranks the component palette by real usage. Decomposition is where reuse has to bite. Once this step names `Heading` instead of the project's `alpha-atom-heading`, the duplicate survives into the plan and into the build. Mark every row reuse, extend, or new, and never new without having looked.

# Decompose a design into Studio's three layers

> **The sheet is not the build.** A decomposition that names N Sections and then gets authored as one component bound to the whole page body renders correctly and passes every render-time check. Whoever executes this sheet must count `section-composition` nodes before reporting done, [`build-connected-template`](build-connected-template.md) § Post-build structural check. When the page body is one modular-blocks field, [`decompose-blocks-page`](decompose-blocks-page.md) is the recipe.

## Context

Studio composes pages from three layers: **Layer-1 atomic components** (one CMS field each), **Layer-2 containers with slots** (holding atomics or nested containers, encoding design-system layout in code), and **Layer-3 Sections** (canvas compositions rooted at a schema scope).

This skill runs the taxonomy over a specific design artifact. Every downstream skill in the Studio flow (`register-component`, `build-section`, `build-connected-template`, `plan-studio-architecture`) assumes this decomposition is already done. When it's not, developers guess piece-by-piece and produce inconsistent registrations (over-exposed slots, under-exposed slots, missed layout components, wrong Section boundaries).

Ship this decomposition BEFORE registering anything. Registrations are expensive to redo. The plan you emit here is what makes them right the first time.

## The four-question decision framework

This skill runs **all four questions** of the [decision framework](design-component-library.md) once per identified section on the design. The framework is an open validator. It doesn't assume any specific pre-registered library:

- **Q1. Classify: Atom, Layout, or Compound?** For each irreducible fragment of the design, ask what shape it is. A single content unit is an Atom. A slot-carrying arrangement is a Layout. Both content AND arrangement is a Compound. Refuse and decompose further, running Q1 recursively on each sub-fragment until every leaf is an atom or a layout. Sections themselves are compositions of primitives, not primitives. A marketing section design almost always starts as a compound that decomposes to Section + Stack + atoms.
- **Q2. Does the library already have it?** Check the target project's existing registry **and** the Studio project itself. [`match-existing-pattern`](match-existing-pattern.md) § Step 1b returns the palette ranked by usage plus every Section grouped by the schema it binds. If a matching primitive exists, mark the row as reuse. If a Section already covers the target schema, the row is reuse or extend, not a build. Otherwise mark as new registration. Aggressively dedup across sections on the same design.
- **Q3. Which props?** For each proposed prop on a new primitive: varies per-instance AND functional/content intent (not visual polish)? Refuse props that fail either half.
- **Q4. Which are Exposed?** For each schema prop: author-understandable AND DS-portable? If both, mark as Exposed Prop candidate. Never expose atom props.

Every "Components" row in the emitted sheet ends with the Q1 to Q4 verdict for that component. When a customer designer or developer reads the sheet, they can see WHY each primitive was proposed. No black-box decisions.

**Halt if any Q1 to Q4 answer is ambiguous.** Ask the user to disambiguate before adding to the sheet.

## Audience: who consumes the sheet, and how it gets executed

**The developer** is the sole audience. The sheet is not for content managers. It's a machine-readable build plan. It gets executed one of three ways, in priority order:

### Execution path 1: API authoring (fastest, most reliable, no canvas clicks)

For every Section + the Template on the sheet, chain to [`author-composition-via-api`](author-composition-via-api.md). It writes the composition JSON directly through the CMA: no Studio UI, no drag-drop, no iframe timing issues. Every drop-tree in the sheet maps 1:1 onto the composition's node tree. Every bind row maps 1:1 onto a `bindings` entry. Deterministic, idempotent, replayable.

**Prerequisites:** a CMA credential resolved per [`authenticate-cma`](authenticate-cma.md) (OAuth first); a management token only if the user prefers one. The same credential serves API authoring.

This is the **default handoff** for `decompose-design`. Ship the sheet, then loop over Sections calling `author-composition-via-api` per Section, then post the Template.

### Execution path 2: Playwright MCP driving the Studio canvas

For customers who want the canvas trail (for review, screenshotting, or matching what a human author would do), chain to [`build-section`](build-section.md) per Section, then [`build-connected-template`](build-connected-template.md). These skills drive the Studio canvas via [Playwright MCP](install-playwright-mcp.md) using the proven `mouse.down/move/up` sequence documented in `drive-studio-canvas-ui` § LLM execution caveat. Slower than API path, but produces a real Studio canvas trail you can screenshot.

**Prerequisites:** Playwright MCP installed (`install-playwright-mcp`) + a running Studio session in a browser the MCP can drive.

### Execution path 3: Developer follows the sheet in Studio's UI manually

Only when neither API creds nor Playwright MCP is available. The sheet's drop-trees and bind tables are formatted to be read top-to-bottom in Studio's canvas: every node is a drop-target instruction, every table is a prop-to-field binding. Slowest path. Last resort.

### Which path does `decompose-design` recommend?

Determined by what the environment provides:

| Environment signal | Handoff |
|---|---|
| A CMA credential resolves per `authenticate-cma` (OAuth first) | **Path 1: API authoring.** Chain to `author-composition-via-api` per Section + Template. |
| No CMA credential, but Playwright MCP installed | **Path 2: canvas automation.** Chain to `build-section` + `build-connected-template`. |
| Neither | **Path 3: manual.** Print the sheet. Instruct the developer to follow it in Studio's UI. |

Content managers benefit from what the sheet produces (exposed props, slots, modular-block areas) but they don't consume the sheet. If a content manager is doing this without a developer, run [`author-without-code`](author-without-code.md) instead. That's their skill.

## Task

### Step 0: Work from whatever input you were given, and close the gaps yourself

**A user hands over one artifact, not a dossier.** The rules in this skill were derived from a session with a Figma link and a CSS dump and the shipped component and a live canvas to measure against. That is not the normal case. Each input alone still supports an accurate build, provided the missing numbers are **derived rather than guessed**, and provided whatever remains uncertain is **reported instead of silently invented**.

| Given | Directly readable | Derive it | Cannot know: assume + report |
|---|---|---|---|
| **Figma link / node id** | element tree, names, x/y/w/h, Layout panel gaps | gaps from child coordinates (`96 − 72 = 24`). Gutters from `(total − n×col) / (n−1)`. Font size from glyph-band height. Line pitch from baseline deltas | which values are theme tokens. Whether a color has a registered counterpart |
| **CSS dump (Copy as code)** | every gap, padding, width, font-size, line-height, color, `display:none` | tree order from the comment sequence + `order:` values. Variant count from repeated blocks | which frames are components vs one-off frames |
| **Screenshot only** | order, alignment, relative emphasis | ratios against a known width. Font size by cap-height measurement | exact px on anything. Say so explicitly |
| **Component source only** | real prop names, block uids, derived values, breakpoint classes | comp values by reading Tailwind classes (`gap-12` means 48px, `text-7xl` means 72px) | which variant the user actually wants built |

**Ask for one more artifact only when it changes the outcome.** A Figma link plus the host codebase is the strongest pair. The link gives geometry, the code gives uids and token names. If you have the link and the project, you already have ~everything. Do not stall waiting for a CSS paste.

**Never let a missing input become a silent default.** An unknown gap becomes an explicit row in Deviations (§ Step 9), not a quiet `md`. The user's job is to correct a short, named list, not to discover what you assumed.

### Step 0b: With more than one artifact, reconcile them BEFORE building

More input is not more context to skim. It is **corroboration**, and it only pays if the sources are checked against each other first. Two artifacts that agree turn an assumption into a fact. Two that disagree are the single most valuable signal available, and they are worthless if the disagreement is discovered halfway through a build.

**Each source is authoritative for different things. Never let one answer a question another owns:**

| Question | Authority | Not authoritative |
|---|---|---|
| What should this instance look like: sizes, gaps, colors, order | **the comp** (Figma / CSS) | the component, which shows a configuration, often another variant |
| What are the real field / block / prop names | **the component + registration** | the comp, whose layer names are cosmetic |
| Is this value expressible at all | **the registration + component** | the comp, which has no notion of a token scale |
| Which value applies in this context | **the component's derivation logic** (`isDark ? …`) | the atom's own default |
| Which variants exist | **the component's type switch** | the comp, which shows only what was laid out |

**Build the reconciliation table before authoring a single node.** One row per value the sources disagree on:

| Value | Comp says | Code says | Resolution |
|---|---|---|---|
| Card top border | `6px #899CFA` | `border_width` default `thin` (3px) | comp wins: set `thick`. The default was never the design |
| Icon size | 48px | `icon_size` default `lg` (36px) | comp wins: instance override, the default is not the spec |
| Quote block gap | 30px | `gap-12` (48px) | **flag**: differing enough to be a different variant or a drifted implementation. Ask |
| Hero gap | 16px | shipped hero `gap-6` (24px), centered | **different variant**: shipped is the centered hero, comp is left-aligned. Do not "correct" toward the code |
| Stat color | `#899CFA` | `text-blue-accent` | same value, and the code names the token, so the ask is "expose `blue-accent`", not "add a hex" |

**Resolution rules, in order:**

1. **The comp wins on values**: the user is asking for this design, not for what shipped last quarter. A registration default that differs from the comp is not a counter-argument. It is the thing the comp is overriding.
2. **The code wins on names and feasibility**: uids, prop names, token names, derived values, and whether the comp's value can be expressed at all.
3. **A large disagreement means a different variant, not an error.** Two heroes differing by alignment and spacing are two components. Match the comp and say which shipped component it is not.
4. **Anything unresolved after those three is a question, asked before building**: one line, with both numbers in it. Cheaper than a rebuild.

With one artifact, this step is skipped and its uncertainty lands in Deviations instead. **Do not down-weight a rich input set by building from the most convenient source and treating the rest as background.**

### Step 1: Ingest the design

Accept the artifact in whatever form the customer supplies:

- **Figma URL or frame node ID**: request read access. Use the Figma MCP or a screenshot dump. Identify every frame that maps to one page + its child components.
- **Screenshot / image / PDF page**: inspect visually (Read tool + image viewing). Identify sections stacked top-to-bottom.
- **Wireframe / sketch**: same as image. Less fidelity but same decomposition rules apply.
- **Natural-language description**: "the page has a hero with a title on the left and an image on the right, then a three-across card grid…". Enumerate the sections + their contents mechanically.
- **HTML/CSS mock**: parse the markup. Each block-level region is a candidate Section, each leaf element is a candidate atomic.

Output of this step: a numbered list of visual regions (Sections) top-to-bottom, each with a short description.

### Step 2: Identify Layer-1 atomics

For every design region, list every **leaf visual element** that renders one piece of content:

- Any heading / title / label probably becomes a `string` atomic (`<Heading>`, `<Text>`).
- Any paragraph / body copy becomes a `string` atomic (`<Text>`, `<Paragraph>`).
- Any image becomes an `imageurl` atomic (`<Image>`).
- Any button or link becomes an `href` atomic (`<Button>`, `<Link>`).
- Any date / time-ago / "N min read" becomes a `datestring` or `number` atomic.
- Any badge / status pill / tag becomes a `choice` or `string` atomic.
- Any rich-text block (mixed formatting, embedded assets, lists) becomes a `json_rte` atomic (`<RichText>`).
- Any paragraph of **body copy or prose**, even if the mock shows it unformatted, becomes a `json_rte` atomic (`<RichText>`), not a plain-text atomic. A mock only shows one state. The author will eventually want a bold word or a link, and changing the field type later means a schema migration. Call it out in the sheet so the reader can downgrade it to plain text if they disagree.
- Any copy the design **truncates** ("read more", a fade-out, an accordion, "show details") becomes `<CollapsibleText>` on the same rich-text field.
- Any card, quote or media that appears **inside the flow of a text block** (rather than beside it) becomes an **embedded entry/asset** in that rich-text field, which needs `registerRTERenderer`. Record the content types an author may embed. See [`register-json-rte`](register-json-rte.md#rte-field-to-component).

For each atomic, record:
- Proposed component name (`<Heading>`, `<Image>`, etc. Reuse across the design, don't invent new atomics per Section unless the visual really differs).
- Proposed prop schema (one scalar prop, plus its Studio prop type).
- Proposed CMS field the prop binds to (naming pattern: `entry.<field>` or `item.<field>` if inside a Repeater).

Never propose a Layer-1 atomic with an `array`, `object`, or `React.ReactNode` prop. That's not atomic (atomic = one scalar that renders one visual). Those props are valid Studio prop types, but the component that owns them is a **Layer-2 self-composing shape**. See Step 3.

### Step 1c: Search the host codebase for the section before decomposing it

**A brownfield project usually already implements the design you were handed.** Grep the component directory for the section's name and its parts before deriving anything from the comp. The existing code is a higher-fidelity source than the design file, because it is what actually shipped.

```bash
ls components/                      # the directory layout names the domains
find components -iname '*carousel*' -o -iname '*card*' -o -iname '*hero*'
```

Four things it gives you that a comp cannot:

| Read from the code | Why it beats the comp |
|---|---|
| **Real Modular Block uids**: `case_study_card_with_image_statistics`, `case_study_card_with_testimonial` | Condition Blocks authored against real uids bind to the existing CT. Invented names (`stat_card`) need a schema change that was never necessary. |
| **Which variants exist** | The type switch enumerates every branch, the definitive variant list, where a comp only shows the ones the designer laid out. |
| **Design-token names behind literal colors** | `text-blue-accent` tells you `#899CFA` is a named theme token, so "add it to the registration's color options" is a precise ask rather than a guess. |
| **Real dimensions and ratios** | `min-h-[472px]`, `lg:basis-[31.7%]` confirm the comp's numbers survived implementation. |

Record what you find as reuse rows in Q2 of the framework. **Finding the section implemented does not mean dropping a composite onto the canvas**. The standing rule still says compose from atoms unless the user asks to reuse. It means the atoms you compose carry the same uids, tokens and dimensions the shipped code uses.

### Step 2b: Every element in the comp ends in exactly one state (element-coverage discipline)

Steps 8 and 8b check coverage from the **schema** side. This step checks it from the **design** side, and it is the cheapest of the three to skip by accident.

**Enumerate the region's child elements from the artifact itself, never from your summary of it.** Re-read the Figma node, or re-view the screenshot, at the moment you write the atomic list. A one-line description written earlier in the run ("hero: heading plus two CTAs") is a lossy paraphrase. Anything it dropped is invisible from then on, because every later step reads the summary rather than the design.

Each element must end this run in one of three states:

- **Mapped**: becomes an atomic (Step 2) or a Layer-2 component (Step 3).
- **Absorbed**: carried by a layout prop rather than a component: a divider that is really `border`, spacing that is really `gap`, a background that is really the section's `background` choice. Say which prop absorbs it.
- **Dropped**: deliberately out of scope, with a reason on the sheet.

No element is silently skipped.

**Worked failure.** A hero comp read, top to bottom: a small muted eyebrow "Our platform", a six-line heading, then two side-by-side CTAs: "Explore our platform" (brand fill) and "Try for free" (secondary fill). It was decomposed from the shorthand "eyebrow, heading, two CTAs" and authored as heading + two buttons. The eyebrow never appeared in the atomic list, so it never reached the sheet, the section, or the CT, and the library already had a registered `Eyebrow` atom with `text` / `color` / `variant` props. Nothing errored. The section was simply missing a piece of the design, and no later step could detect it, because the omission happened before the first artifact was written.

Count the elements in the comp and count the rows on the sheet. If the second number is smaller, name which elements are Absorbed or Dropped, and why.

### Step 3: Identify Layer-2 components

Layer 2 = any registered component that's not a pure Layer-1 atomic. Three concrete shapes to look for:

**3a. Container with slots**: wrappers holding other components in fixed shape regions:

- Card frames (border, radius, padding around a title + body).
- Modal / panel chrome (header + body + footer).
- Split / two-up shapes (`left` + `right`).
- Callout boxes (icon + message + action).
- Author cards (avatar + text block).

For each, record:
- Proposed component name (`<Card>`, `<AuthorCard>`, `<Callout>`).
- Slot props (`body`, `left`, `right`, `header`, `content`).
- **Whether the container also binds to CMS scalars.** If some regions of the container are same-content-every-usage (e.g. `authorName` always binds to `author.name`), those become scalar bindable props on the container itself, not slots.
- Proposed scope (does this container bind to the CT root, a Group, a Reference, or is it purely structural).

**3b. Self-iterating component (`type: "array"` prop)**: a component that receives a bound multi-value field and renders `.map()` internally, without a Studio Repeater. Use when the list rendering is straightforward (single-shape items, no per-iteration variant authoring, no template-author child-swap):

- Bullet list of feature items (`<FeatureList>` bound to a **multi-value Group**, the values are already on the entry, no extra resolution needed).
- Compact tag strip (`<TagList>` bound to a **multi-Reference** of tag entries).
- Logo bar (`<LogoBar>` bound to a **multi-Reference** of brand entries).

For each, record:
- Proposed component name.
- One `array` prop (e.g. `items`, `tags`, `logos`) with `items: { type: <inner shape> }`.
- Proposed CMS field binding: multi-value Group, multi-value scalar, Modular Block, or multi-Reference.
- **Reference-only requirement**: if the source is a Reference (single or multi), populate `data_sources.resolvedReferences` on the composition so CDA includes the referenced entries. Without it, References arrive as `{ uid }` stubs. Groups, Modular Blocks, and scalar multi-values live on the entry itself and need no resolution. The array arrives populated as-is.

Do NOT use this shape when the design needs per-iteration variant authoring, Modular-Block polymorphism, template-author child-swap, or Studio's canvas Preview Mode showing N rendered children. Those cases want a **List Section with a Repeater** (Step 5). Decide between array-prop, Repeater-in-Simple-Section and List Section every time a list appears in the design. Don't guess.

**3c. Self-composing component (`type: "object"` prop)**: a component that receives a bound object shape and renders its subfields internally. Use when a nested Group has a fixed structure that always renders the same way:

- Address block bound to a `location` Group with `street / city / zip` subfields.
- Contact card bound to a `contact` Group with `email / phone / role`.
- Nested stat block bound to a `stats` Group.

For each, record:
- Proposed component name.
- One `object` prop with `properties: { … }` matching the Group's subfields.
- Proposed Group binding.

**3d. Layout container**: covered in Step 4.

For every Layer-2 component (any shape above), pick one of two design intents:

- **Content shape** (3a / 3b / 3c): the component knows a specific content pattern. The fill is either slot-driven (3a) or data-driven (3b / 3c).
- **Layout shape** (Step 4): the component encodes a design-system layout rule (columns, gaps, breakpoints).

A component can be BOTH: a hybrid layout+content component that renders a design-system 3-column grid AND binds to a multi-Reference through an internal `.map()`. Record it under the layout list with its array binding noted.

### Step 4: Identify Layer-2 layout components

Every layout decision (grid tracks, gaps, breakpoints, spacing rhythm) that recurs across the design gets its own registered layout component:

- A 2-column split (hero image + text) becomes `<TwoColumn>`.
- A 3-across card grid becomes `<ThreeColumn>` (or `<Grid columns={choice}>`).
- Vertical spacing between Sections on the Template becomes `<Stack>`.
- Constrained content width becomes `<Container>` or `<PageWrapper>`.

For each layout component, record:
- Proposed name.
- Slot props per region (`col1`, `col2` / `left`, `right` / `items` for repeating).
- Design-system values encoded in the component's CSS (columns, gap at each breakpoint).

Do NOT propose registering `<Grid>` with a free-integer `columns` prop that lets authors invent unauthorized column counts. Constrain to design-system-approved values via a `choice` prop, or register named variants (`<TwoColumn>`, `<ThreeColumn>`, `<FourColumn>`).

Do NOT propose registering `<Box>`. A generic wrapper is either an unnecessary registration (skip it) or actually a specific layout component (name it accordingly).

### Step 4b: Map the comp's spacing to the library's token scale (never eyeball it)

Every gap, padding and column width in the comp is a **number the design tool already knows**. Read it, then map it to the nearest registered token. Guessing "looks like medium" is how a section renders plausibly and measures wrong. A canvas that looks fine is not evidence, because a wrong token still produces a tidy layout.

**Get the numbers, don't estimate them.** Best input, when the user can supply it, is Figma's **Copy as code**, then **CSS (all layers)**: it emits every frame's `display` / `flex-direction` / `gap` / `padding` / `width` / `font-size` / `line-height` / `color` as exact values, nested in tree order, with layer names as comments. It needs no MCP access and it removes the measuring step entirely. Ask for it by name.

Failing that, the Layout panel gives Flow / Gap / Padding / Width / Height per frame. When a frame's gap is not shown, derive it from child coordinates: a child ending at `y=72` followed by one starting at `y=96` is a 24px gap. Column gutter comes out of the same arithmetic: three 400px columns inside 1296px means `(1296 − 3×400) / 2 = 48px`.

**A CSS comment is a LAYER NAME, not the text on screen.** Figma emits each layer's name as the comment above its block. For a text layer the two usually match, until someone overrides the text inside a component instance, which changes what renders but leaves the layer name at its original value. The dump then reads as authoritative and is wrong.

```css
/* Personalized by design */   /* layer name — the design actually reads "Our products" */
/* Button */                    /* no text at all: the label is an instance override */
```

Worked failure: a section was built with the heading "Personalized by design" taken straight from the comment, while the design said **"Our products"**. And because the CTA's layer was simply named `Button`, a label was **invented** rather than flagged. Both shipped looking deliberate.

Two rules follow:

- **Never source copy from a CSS dump alone.** Take text from a screenshot, the Figma text content, or the user. Use the dump for geometry, type and color, the things it is authoritative for.
- **A layer named generically (`Button`, `Label`, `Text`) means the dump has no copy for that node.** That is a Deviations row or a question, never a placeholder you make up. Inventing copy is the one gap a reviewer cannot spot, because invented text looks exactly like real text.

**Read the CSS for what is not built, too.** A layer carrying `display: none` is in the comp's code but not in the design, mark it **Dropped** (Step 2b) rather than building it. And `color` values map straight onto the token scale: `rgba(255,255,255,0.98)` is the `strong` (98%) text token, `0.67` is `light`, `#212121` / `#2B2D3B` / `#313A31` were each an exact card-background token. Matching a literal color against the registered scale is how you tell an exact hit from an approximation.

**Then map each number onto the registered scale.** Read the scale out of the registration (`options` + `defaultValue`), never from memory:

| Comp value | Nearest token | Note |
|---|---|---|
| 16px | `sm` | exact |
| 24px | `md` | exact |
| 48px | `xl` | exact |
| 80px | `2xl` | exact |
| 20px | `sm` or `md` | **no exact token**: pick one, say which, and say the delta |

Record the mapping on the sheet as `gap: 48px → xl`, not `gap: xl`. The comp value is the requirement. The token is the implementation. Reviewers can only check the second against the first if both are written down.

**A comp's "Fixed 1138px" is usually a result, not a prop.** Web layouts are fluid between breakpoints. The design tool can only show one frozen width. Before reaching for a `max_width` prop, check whether the number falls out of the gutters:

```
content width = frame width − (2 × horizontal padding)
```

Worked example: a hero comp reads `Width Fixed (1138px)`, `Left 72px`, so its board is `1138 + 72 + 72 = 1282`. The built section used `padding_x: md`, which resolves to `desktop:px-18` = 72px, and measured 1085 at a 1229 frame, 845 at 909, 559 at 591. Every point fits `frame − 2×gutter`, so at the comp's own 1282 the content is **1138 exactly**. Nothing needed capping. The comp width was the gutters doing their job.

Only add a `max_width` when the content stops short of the gutters: a text column narrower than its siblings, a centered measure. Then map it like any other value, and check what the prop actually wraps: a component named `Container` may be a full layout shape (split, media slot, heading props) rather than a width wrapper, in which case using it for width alone drags in an entire unwanted structure.

**A shipped page is the strongest artifact of all. Ask for it when the design is already live.** View-source (or right-click, then Inspect) on the production page gives the real copy, the real hrefs, the real class names and the real element count, none of which a design file can guarantee. Reconcile it as the top authority for what shipped, above both the comp and the component source.

Worked example: a comp showed 5 cards and one body sentence. The live page had **6** cards, four slide indicators instead of three, and different copy in every card. The comp's gradient turned out to match the live CSS exactly, which also proved the token chosen from the library was the wrong one.

**Watch for designs that decouple semantic tag from visual size.** Production markup routinely does this (`<h2 class="h1-standard">`, `<h3 class="cs-h4">`), using a heading level for document structure and a different class for the type scale. Many heading atoms cannot express it: they derive the class from the tag (`HEADING_CLASS[tag]`), so asking for `h2` yields `h2`-sized text and nothing offers the h1 scale on an h2. When you hit this, **match the visual size and record the semantic deviation**, because a wrong heading level is a fixable a11y note whereas wrong type sizing reads as a broken build.

**Flag what the scale cannot express.** A token scale is deliberately coarse, and a component's prop surface is coarser still. Worked example: a feature grid whose comp has a **48px column gutter and an 80px row gap** was built on a layout component exposing a single `gap` choice applied to both axes. Both values exist on the scale (`xl`, `2xl`), but the component cannot hold both, so the grid renders 48px rows against the comp's 80px. That is not a build error to hide. It is one of three decisions, and the sheet must name which:

1. **Accept the delta**: note `row gap 48px vs comp 80px` on the sheet and move on.
2. **Extend the registration**: add a `row_gap` prop (a library change, so it needs the owner).
3. **Mirror the comp's structure**: the comp itself often nests: two row frames inside a vertical parent, the 80px being the parent's gap. Rebuilding that nesting reproduces both values with the existing props, at the cost of a grid that no longer wraps freely.

Whichever is chosen, the delta is on the sheet. A spacing mismatch that nobody wrote down gets rediscovered by whoever compares the built page to the comp.

### Step 5: Draw Section boundaries (Layer 3)

Apply the **schema-shape rule**: each Section is rooted at exactly one schema scope. A new scope means a new Section.

For each Section candidate:

- Identify the schema scope it binds against: CT root / Global Field / Group / Modular Block / Reference (single) / Reference (multi).
- Classify as **Simple Section** (no root Repeater) or **List Section** (root Repeater over a multi-value field).
- List the Layer-2 containers + Layer-1 atomics dropped inside it.
- For List Sections iterating a polymorphic scope (multi-CT Reference, Modular Block), note the **Condition Blocks needed per allowed type**.

### Step 6: Propose the Content Type shape

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
- Field UID (snake_case, e.g. `hero_title`; Contentstack field UIDs are lowercase letters, digits and underscores).
- Which Section(s) bind to it.

### Step 7: Apply the governance dial

Before writing the sheet, classify each field / prop on the target Content Type into one of three governance states. This is a design-system decision: how much of the page is a marketer allowed to change?

- **Content, bound and sealed.** Headlines, copy, images, links, prices. The CMS entry drives the value. The component reads it. The marketer cannot override on this page. Default for anything semantic.
- **Layout/style, exposed props with token-constrained values.** Columns, media side, gap, background, variant, alignment. Marketers pick from design-system-approved options via a `choice` prop. They don't invent new values.
- **Variable areas, marketer-open.** Story flows, campaign bodies, promoted-content strips. Modular Blocks or a Section Slot lets the marketer add / reorder / choose per-page without code.

**Target: five marketer decisions per page, not fifty.** Fully data-driven Sections expose nothing (all-bound). A Section that exposes every prop is a design failure: authors either drift the design system or ignore Studio entirely. The governance dial output for each Section: "content bound + these three exposed props + this one slot for variable content."

### Step 8: Every CT field ends in exactly one state (unmapped-fields discipline)

Walk every field on the target Content Type. Each must end this run in one of four states:

- **Bound**: used by an atomic or Layer-2 scalar prop inside a Section.
- **Exposed**: used by an exposed section prop (per Step 7's governance dial).
- **Handled outside Studio**: SEO metadata read by the framework's `<Head>`, route-level fields consumed by the app, etc. Note explicitly.
- **Unmapped**: not used by this design. Listed on the sheet's `Unmapped fields:` one-liner with a reason (deprecated, planned-but-not-yet, held-for-future-page, etc.).

No field is silently skipped. If a field ends the run without a state, the plan isn't done.

### Step 8b: Every binding resolves to a real (or proposed) field (binding-resolvability discipline)

Step 8 checks each CT field against its design usage. This step checks the **reverse**: every binding the sheet proposes must resolve to a field that either **already exists on the target CT** or is **explicitly listed under `Proposed schema`**. A binding that points at neither is an **orphaned bind**. It resolves to `undefined` at runtime and the component silently renders its `defaultValue`, which looks like real content on the canvas but ships empty. This is the single most common decomposition failure.

Walk every bind row on the sheet:

- **Scalar bind** (`entry.<field>` / `item.<field>`): the field must exist on the CT (or the iterated item's CT), or appear under `Proposed schema`. If it's neither, STOP: either the design maps to a field that isn't there (add it to `Proposed schema`) or you named the wrong field.
- **Collection bind** (any `type: "array"` / `type: "object"` prop, or a Repeater/List-Section source). The **multi-valued source field must exist or be proposed**: a multi-Reference, Modular Block, `multiple:true` Group, multi-value scalar, or a Pinned Query (Freeform). A `Card Grid` / `Article Grid` whose `items` prop has **no backing multi-valued field on the CT** is the classic trap: e.g. an `Article List` CT holding only `Title`/`URL`/`SEO` while the articles live in a separate `Article` CT the page never references. When the list lives in another CT, the fix is a **multi-Reference on the page CT** (add it to `Proposed schema`) or a **Pinned Query**, never a collection bind with nothing behind it.

Output of this step: zero orphaned bindings. Every bind row traces to an existing field or a `Proposed schema` line. If a required source doesn't exist and can't be added, the region can't be data-driven: drop it to static, or re-scope the CT. This is the same contract [`build-section`](build-section.md) § Step 5d/5e enforces at bind time and [`register-component`](register-component.md) warns about at registration. Catching it here, in the plan, is cheapest of all.

### Step 9: Emit the build sheet

Write a **build sheet**, an actionable spec a developer follows to build the page in Studio. The sheet is a markdown document with a fixed shape. Every line is either an instruction or a mapping. No purpose prose, no click-by-click UI. Ship it as `docs/<template-slug>-build-sheet.md` in the customer's repo (or print inline if no `docs/` directory exists).

**Structure:**

```
BUILD SHEET · <Template name>
Connected → <ct_uid> · URL /<route>/{{entry.url}}   (or: Freeform · /<url>)

## Decisions made        ← 5–6 one-liners, each overridable
## Components            ← one table
## Sections S1…Sn        ← children first; per-section format below
## Template              ← assembly
## Proposed schema       ← ONLY when no schema existed
## Deviations            ← every value that is NOT an exact match (see below)
Unmapped fields: <field> (<reason>) · <field> (<reason>)
```

**Deviations**: the build will not be a pixel-exact reproduction, and the honest move is to say exactly where. One row per value that is approximated, assumed, or impossible, so the user's manual pass is a short named list rather than a hunt:

| Value | Comp | Built | Why | Fix owner |
|---|---|---|---|---|
| Card row gap | 80px | 48px | layout component exposes one `gap` for both axes | library: add `row_gap` |
| Stat color | `#899CFA` | white | `blue-accent` exists in the theme, absent from the registration's color options | library: extend options |
| Card padding | `32/24/24` | `24` all round | `padding_y` is a single value | library: per-side padding |
| Heading to list gap | 42px | 48px | no 42px step on the token scale (`lg` 32, `xl` 48) | accept, or add a step |

Three rules for this table:

- **An empty table is a claim.** Only leave it empty when every value was matched exactly. A build with no deviations listed reads as pixel-perfect and gets trusted as such.
- **Name the fix owner.** library (registration or component change), schema, or accept. It tells the user which items they can act on and which need a developer.
- **Distinguish approximated from impossible.** A 42px gap rounded to 48 is a judgment call the user may overrule. A gradient that no prop can express is not.

**Decisions made**: 5-6 one-liners covering: template pattern (Connected vs Freeform + CT + URL), any split/seal calls on components, any marketer-open areas (Modular Blocks / Section Slots), any fields deliberately unmapped, any schema reuse/extension calls.

**Components table:**

| Component | Tier | Status | Key props |
|---|---|---|---|
| Product Card | Layer-2 sealed | reuse: `components/ProductCard.tsx` | - |
| Card Grid | Layer-2 layout | **build** | Cards (slot) · columns · gap |
| Heading | Layer-1 atomic | **build** | text · level |

"Sealed" = Layer-2 with all data props bound and no slots, brand-consistent, cannot be recomposed. Contrast with slot-based Layer-2 containers that leave regions marketer-fillable.

**Per-section format**: three blocks:

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
- `└─` drills in (tree double as step list: every node is a short action)
- Bindings inside a Repeater note their root: (root: Repeater Data)
- Condition guards: `Condition: content type is product` (References) / `Condition: is of type quote` (Modular Blocks)
- Exposed labels are **bold + unique within the section**

**Template block:**

```
### Template · Campaign Landing
New Template → Connected → `campaign_page` → URL `/campaigns/{{entry.url}}`

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
| Featured Products | `featured_products` | multiple reference to `product` | S2 repeater |

**Unmapped fields:** `<field>` (reason) · `<field>` (reason)

### Step 10: Close with two offers (developer decision points)

The build sheet is the plan. Two things can happen next. Ask both, in one closing block:

> **To make this buildable:** \<N\> new components need code + registration, namely \<names with tiers\>. \<Existing components\> register as-is.
>
> **Offer 1: code phase.** Want me to scaffold + register these components in your repo now?
>
> **Offer 2: Studio-canvas phase.** Once code is done, want me to author the Sections + Template automatically?
>   - **A**, via API (fastest): chains `author-composition-via-api` per Section + Template. Requires a CMA credential resolved per [`authenticate-cma`](authenticate-cma.md) (OAuth first); a management token only if the user prefers one.
>   - **B**, via Studio canvas (slower, produces canvas trail): chains `build-section` + `build-connected-template` through Playwright MCP. Requires `install-playwright-mcp` done.
>   - **C**, hand me the sheet. I'll do it in Studio's UI myself.

If the developer accepts **Offer 1**: hand off to `register-component` per new atomic + Layer-2, following the [palette conventions](register-component.md).

If the developer accepts **Offer 2A**: for each Section in the sheet, hand off to [`author-composition-via-api`](author-composition-via-api.md) passing the Section's drop-tree + binding table as the composition-node structure. Post the Template last.

If the developer accepts **Offer 2B**: for each Section in the sheet, hand off to [`build-section`](build-section.md) / [`build-repeating-section`](build-repeating-section.md) passing the sheet's Section block as input. `build-section`'s LLM-execution rules (mouse.down/move/up sequence, stable selectors, Layers tree for invisible nodes) apply.

If **Offer 2C**: the sheet's drop-trees and bind tables are already formatted for a developer to follow in Studio's UI, every node is a drop instruction, every table is a bind mapping.

**Whichever path executes Offer 2, close with [`verify-setup`](verify-setup.md).** Every path lands at the same verified end state.

## Inputs needed from the user

1. The design artifact (Figma URL, screenshot path, PDF path, sketch, or natural-language description).
2. The target Content Type name (if known. Otherwise propose one from the design's page kind).
3. Any known design-system constraints: "we already have `<Card>`", "our grid always uses `<ThreeColumn>` with 24px gaps", etc.
4. Whether the design is greenfield (no existing code) or paired with a production page being migrated (if migrating, run [`discover-sections`](discover-sections.md) alongside).

Do NOT invent designs. If the user says "figure out a design for a blog post," push back, ask for the design artifact or use [`plan-studio-architecture`](plan-studio-architecture.md) which handles the requirements-first path.

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] Every visual leaf in the design is classified as a Layer-1 atomic with a proposed scalar prop type + CMS field binding.
- [ ] When two or more artifacts were supplied, a reconciliation table was produced **before** authoring, each disagreement resolved by the precedence rules, and anything still unresolved raised as a question rather than assumed (Step 0b).
- [ ] The build ran from whatever artifact the user supplied. Missing numbers were derived (Step 0), not defaulted, and anything underivable is a named row in Deviations.
- [ ] The sheet carries a **Deviations** table naming every approximated / assumed / impossible value with its fix owner. Empty only when every value matched exactly.
- [ ] The host codebase was searched for an existing implementation of the section, and any real block uids / token names / dimensions found there are used instead of derived ones.
- [ ] Every distinct **item shape** in a repeating region is built, not just the first. Each has its own Condition Block under one Repeater.
- [ ] The atomic list was written while re-reading the artifact, not from an earlier summary of it. Every element in the comp is Mapped, Absorbed or Dropped (Step 2b) with no silent omissions.
- [ ] Every design prop the comp determines (direction, variant, size, color, gap, alignment) has a value on the sheet. "Registered default" is a value only when it was checked against the comp.
- [ ] Every content-shaped wrapper is classified as a Layer-2 container with slot props (and any bindable scalar props on itself).
- [ ] Every layout decision (columns, gaps, breakpoints, vertical rhythm) is classified as a Layer-2 layout component. No layout decision is "TBD via Design Panel."
- [ ] Every Section is rooted at exactly one schema scope per the schema-shape rule. Polymorphic scopes call out the needed Condition Blocks.
- [ ] The Content Type shape is proposed with concrete field types + UIDs.
- [ ] The plan is emitted as a single machine-readable YAML (or equivalent) document ready to hand to `register-component` + `build-section` + `plan-studio-architecture`.
- [ ] No **Layer-1 atomic** proposes an `array`, `object`, or `React.ReactNode` prop (atomic = one scalar that renders one visual). Components with `array` / `object` props ARE valid and register as **Layer-2 self-iterating** (Step 3b) or **self-composing** (Step 3c) shapes.
- [ ] Every `array` prop bound to a **Reference** field has `data_sources.resolvedReferences` planned. `array` props bound to Groups / Modular Blocks / scalar multi-values do NOT.
- [ ] No layout component proposes a free-integer `columns` prop or a generic `<Box>` registration.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Skipping the layout classification (Step 4) | Every layout decision drifts to Studio's Design Panel per Section, which produces design-system drift | Enumerate every recurring layout in the design and register a specific Layer-2 layout component for it (`<TwoColumn>`, `<Stack>`, etc.) |
| Proposing atomics per Section instead of per shape | Ends up with `<HeroTitle>`, `<CardTitle>`, `<FooterHeading>`, every one a `string` prop that could reuse a single `<Heading>` | Same atomic for same shape across the design. Use registered variants (`choice` prop) if the visual really differs |
| Over-exposing slots | Every Section author has to fill every slot for every drop. Component becomes tedious | Slot only what varies per usage. Scalar-bind everything that's same-per-usage |
| Merging two schema scopes into one Section | Auto-binding won't match. A Section rooted at both CT root AND a Reference scope simultaneously isn't a valid shape | Split into two Sections per the schema-shape rule |
| Missing Condition Blocks on polymorphic References or Modular Blocks | List Section renders nothing per iteration when the source is multi-CT or polymorphic | Note the required Condition Blocks per allowed type on every polymorphic Section |
| Emitting the plan as prose | Downstream skills can't consume prose. Ambiguity re-enters the flow | Emit YAML (or equivalent structured document) that `register-component` / `build-section` can be pointed at |
| Building a region from a pre-composed composite (`*-feature-card`, `*-hero`) because the palette has one | Fastest path, identical on canvas, and the shape is now fixed in code. Internal spacing can't be matched to the comp, the author can't restructure it, and the design stops being a composition | Compose from atoms + layout primitives by default. Use a composite only when the user asks to reuse one. Router § Standing rule |
| Building from one artifact while others sit unread | Extra sources are corroboration, not background. Skimming them means the disagreements (a 3px default against a 6px comp border, a 36px default against a 48px icon) surface after the build instead of before it | Reconcile every source into a table first, then author (Step 0b) |
| Resolving a comp-vs-code conflict silently | Each source is authoritative for different things. Letting the code overrule the comp on a value builds last quarter's design. Letting the comp overrule the code on a uid invents a schema | Apply the precedence rules: comp wins on values, code wins on names and feasibility, large gaps mean a different variant |
| Ignoring the live page when the design already ships | Production markup carries the real copy, hrefs, element counts and class names. A comp can be older or newer than what shipped, so building from it alone reproduces a design nobody is running | Ask for view-source on the live URL and reconcile it as the top authority for what shipped |
| Assuming a heading atom can size text independently of its tag | Production decouples them (`<h2 class="h1-standard">`). Most atoms derive the class from the tag, so the requested level silently brings its own size | Match the visual size, record the semantic level as a deviation |
| Treating CSS-dump comments as text content | They are layer names. A text override inside a component instance leaves the name stale, so the dump confidently supplies the wrong copy, and a layer named `Button` supplies none at all | Source copy from the rendered design or the user. Use the dump for geometry, type and color |
| Inventing copy for a node the artifact does not supply | Invented text looks identical to real text, so no reviewer can spot it and it ships | Flag it as a Deviations row or ask. Never fill the gap silently |
| Stalling for more input than the user gave | The normal case is one artifact. A Figma link alone supports gaps from child coordinates, gutters from arithmetic and font size from glyph bands | Derive what is derivable (Step 0). Ask for a second artifact only when it changes the outcome |
| Shipping a build with no deviation list | Silence reads as pixel-perfect, so wrong spacing is trusted instead of corrected. The user then hunts for what moved | Emit the Deviations table. Empty only when every value matched exactly |
| Decomposing a design the host codebase already implements | The shipped component names the real Modular Block uids, every variant, and the theme token behind each literal color. Deriving them from the comp instead invents uids that need a schema change and turns named tokens into guesses | Grep `components/` for the section before decomposing, Step 1c |
| Building only the first item shape of a mixed list | A carousel reading A-B-C-A-B-C is **three** card shapes, not one. Building A alone leaves two thirds of the design unbuilt, and the canvas looks plausible so nothing flags it | Count the distinct shapes in the list, not the items. One Condition Block per shape, every one built, see [`author-composition-practice`](author-composition-practice.md) § Skeleton first, bind later |
| Placing N copies of a repeating shape instead of one Repeater child | Five cards look right and are fixed at five. Editing one leaves four stale, and the binding pass has nothing to point at a collection | One child inside a `repeater`, `items` left unbound in the skeleton. See [`author-composition-practice`](author-composition-practice.md) § Skeleton first, bind later |
| Decomposing from your own earlier summary of the design | A paraphrase written mid-run silently drops elements: an eyebrow, a caption, a second CTA. Every later step reads the summary, so nothing can detect the loss | Re-read the Figma node / screenshot while writing the atomic list. Reconcile element count vs sheet rows (Step 2b) |
| Leaving design props off the sheet because "the default will do" | The registered default is the library's choice, not the comp's, a stack defaults to `column` and side-by-side CTAs render stacked, with no error | Record every design prop the comp determines. See [`author-composition-practice`](author-composition-practice.md) § Skeleton first, bind later |
| Estimating spacing instead of reading it off the design tool | A gap picked by eye lands on the wrong token: a comp specifying 16px gets built as 24px. The section still looks tidy, so nothing flags it, and it only surfaces when someone measures against the comp | Read Flow / Gap / Padding from the Layout panel, or derive from child coordinates. Record `48px → xl`, not `xl` (Step 4b) |
| Silently absorbing a value the token scale or prop surface can't express | The build quietly disagrees with the comp, one `gap` prop covering both axes cannot hold a 48px gutter and an 80px row gap | Name the delta on the sheet and pick one of the three options in Step 4b: accept, extend the registration, or mirror the comp's nesting |

## See also

- [`plan-studio-architecture`](plan-studio-architecture.md): takes the plan this skill emits (or a requirements doc) and orders the build sequence.
- [`register-component`](register-component.md): mechanics of registering each Layer-1 and Layer-2 output.
- [`build-section`](build-section.md): mechanics of authoring each Section output.
- [`discover-sections`](discover-sections.md): companion skill for the code-first path (existing React codebase).
- [`design-section-from-jsx`](design-section-from-jsx.md): for individual JSX components, propose the linked-schema shape.
- [`figma-generate-components`](figma-generate-components.md): when the customer wants raw React code generated from Figma frames alongside this decomposition.
- [`adapt-collection-component`](adapt-collection-component.md): when the design uses a legacy production wrapper with an array/object prop.
