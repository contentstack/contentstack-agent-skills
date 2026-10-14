---
name: design-component-library
---

## When to use

Decide the SHAPE of a Studio component library (which atomic and layout primitives to register) BEFORE any `registerComponent` call is written. Applies the atom + layout taxonomy to the user's design system so authors compose sections on the fly without visual drift.

Use when the user says "which components should I register", "design our Studio library", "what should the component library look like", "we're starting fresh, what do we register", "atomic + layout primitives for Studio", or when someone brings a design system (Tailwind + shadcn, Chakra, MUI, a custom kit) and asks how it maps to Studio. Do NOT use to write registration calls for one component (use `register-component`). Do NOT use to break one over-large existing component into pieces (use `decompose-jsx-to-atomics`). Do NOT use for per-page decomposition of a specific design (use `decompose-design`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Design a Studio component library

## Context

The trap is registering either (a) one giant Hero with 20 props, or (b) ten differently-shaped Heros. Both fragment the design system: (a) hides variety behind a monolith authors can't extend without engineering. (b) lets every Hero pick its own spacing and type scale. The alternative is a small set of **atomic** and **layout** primitives: the 10-primitive pattern this skill walks.

## The four-question decision framework

This skill walks the four-question framework below. **The framework is an open validator**. It works on any input (React component, Figma frame, verbal description) regardless of what's already registered:

- **Q1. Classify: Atom, Layout, or Compound?** Look at the input in isolation. A component that carries a single content unit is an Atom. One that arranges children via slots is a Layout. One that does both content AND arrangement is a Compound (refuse and decompose recursively). This is a validator question. It tells you what shape the component actually is.
- **Q2. Does the library already have it?** Only after Q1 confirms atom or layout, check reuse. On a fresh project the answer is trivially "no" for the first primitives. In an existing library, check the registry. With legacy monoliths, check the atom/layout registry, not the monolith list.
- **Q3. Which props?** For each proposed prop, does it vary per-instance AND represent functional/content intent (not visual polish)?
- **Q4. Which are Exposed?** For each schema prop, is it author-understandable AND DS-portable?

**Halt if any answer is ambiguous.** Never guess. Ask the user to disambiguate before proceeding.

This skill's job is to produce that primitive list for the user's specific design system BEFORE any registration is written. Get it right up front and the registration work that follows is mechanical.

## The rule of thumb: expose only when the value

1. **Varies per instance, AND**
2. **Represents functional or content intent, not visual polish.**

Concretely:
- **Good:** `level: h1 | h2 | h3` on Heading (semantic hierarchy, so DS tokens set size and weight)
- **Good:** `variant: default | secondary | ghost` on Button (intent maps to color + border tokens)
- **Good:** `text` on Heading, `href` on Button, `src` on Image (content)
- **Avoid:** `size: sm | md | lg | xl` on Heading (level already decided the size)
- **Avoid:** `color: hex` on anything (drift risk: use `emphasis: default | muted | inverse` instead)
- **Avoid:** `borderRadius`, `fontWeight`, `letterSpacing`, `boxShadow`, `padding: 32` (design-system concerns)

## Task

Walk the user through a five-step decomposition of their design system into a primitive list ready to hand to `register-component`.

### Step 1: Confirm the design system

Ask (only if not stated):
- Which UI library are you on? (Tailwind + shadcn/ui, Chakra, MUI, custom Radix, custom tokens)
- Where are your semantic tokens defined? (CSS variables, Tailwind config, theme file)
- Does the DS already expose semantic variant names (primary / secondary / default) or raw color tokens?

Do NOT invent tokens. Every semantic option in a primitive's schema must map to an existing DS token. If a token doesn't exist for a proposed option, flag it and offer to defer that primitive until the DS adds the token.

### Step 1b. The split that makes a library reusable: content binds, design stays static

**Measured on a 58-section production Studio site: 300 bound props vs 1803 static. 86% of every prop set is design, not content.**

An atom therefore has **few content props and many design props**, and they are wired differently:

| | Content props | Design props |
|---|---|---|
| Examples | `text`, `title`, `href`, `media`, `alt` | `size`, `color`, `align`, `variant`, `tag`, `gap`, `padding_*` |
| Wired as | **bound** to a CT field | **static value** set on the canvas |
| Who decides | the author, per entry | the composer, per placement |
| Count per atom | 1 to 3 | 4 to 13 |

Real signatures from that site:

```
heading      content: text                         design: tag, color, align, variant, size
body-string  content: text                         design: size, color, align, variant
cta-button   content: title, href, open_in_new_tab design: style, icon_position, full_width, align, variant
media        content: media, alt                   design: fill, aspect_ratio, fit
```

**Never model a design prop as a CT field.** `gap`, `align` and `variant` as content fields produce a schema an author cannot understand and a section that drifts visually per entry. If it changes how the thing looks rather than what it says, it is a static value.

The corollary is what makes the library reusable: **the same four atoms compose every section**, differing only in their static design values. `heading` is used 23× across that site, `cta-button` 33×, `stack` 66×, not one variant per section.

### Step 2: List the four content atoms

Every marketing surface needs the same four content-only atoms:

| Atom | Props | Notes |
|---|---|---|
| **Heading** | `text`, `level: h1..h4`, `emphasis: default | inverse` | `level` drives DS tokens for size + weight. `emphasis: inverse` is for text over dark BackgroundMedia. |
| **Description** | `text`, `emphasis: default | muted | inverse` | Paragraph body copy. No size, no maxWidth. |
| **Button** | `label`, `href`, `variant`, `size`, `icon` | Variants + sizes mirror shadcn's `cva` (or the DS's equivalent) exactly. |
| **Image** | `src`, `alt`, `aspect: auto | 1:1 | 4:3 | 16:9 | 21:9`, `fit: cover | contain` | No borderRadius, no shadow. |

For each atom, confirm the DS has tokens for every semantic option. If the DS uses different variant names (e.g. `emphasis` values named `primary/secondary/accent` on Chakra), keep the DS's names. The schema should read like the DS.

**Body copy needs one atom per rich-text shape, not one `Description`.** The production reference registers four, because the render path differs per storage format. See [`register-json-rte`](register-json-rte.md#rte-field-to-component):

| Atom | For | Prop type |
|---|---|---|
| `body-string` | plain single-paragraph copy | `plaintext` |
| `body-multiline` | plain multi-paragraph copy | `plaintext` |
| `body-json-rte` | JSON RTE | `json_rte` |
| `body-html-rte` | HTML RTE / Markdown | `json_rte` (or `any` on an SDK without the widened binding) |

**Add these atoms when the designs call for them**: each is a real atom on the reference site, and each is one an agent otherwise inlines into a bigger component: `eyebrow` (kicker above a heading), `icon`, `breadcrumb`, `cta-row` (a group of buttons), `numbered-item` / `step-number` (ordered lists), `share-buttons`, `form-embed`, and `shape` / `accents` (decorative, no content props at all).

### Step 3: List the six layout primitives

| Layout | Props | Slots | Notes |
|---|---|---|---|
| **Section** | `spacing: compact/comfortable/spacious`, `background: none/surface/muted/brand/inverse`, `contentAlign` | `children` | Outer padded wrapper. Spacing is semantic, not px. |
| **BackgroundMedia** | `image`, `overlay: none/subtle/strong`, `focalPoint`, `height: standard/tall/full` | `children` | Background image behind foreground content. |
| **SplitRow** | `ratio: 50-50 | 60-40 | 40-60 | 70-30 | 30-70`, `verticalAlign`, `reverseOnMobile` | `leftSlot`, `rightSlot` | Two-column layout. |
| **Stack** | `spacing: tight/normal/loose`, `alignment` | `children` | Vertical grouping, the workhorse. |
| **Grid** | `columns: 2 | 3 | 4`, `spacing` | `children` | N-column responsive grid. Collapses to 1 on mobile. |
| **Card** | `variant: default/outline/ghost`, `padding` | `header`, `content`, `footer` | Compound container, mirrors shadcn Card. |

**Two more the production reference relies on, both easy to omit and expensive to retrofit:**

| Layout | Props | Slots | Why it earns a place |
|---|---|---|---|
| **Box** | none | `children` | A bare slot wrapper, **49 uses** on the reference site, second only to Stack. It gives a grouping seam with no styling opinion, so a slot can be filled without inheriting spacing. Without it, composers reach for Stack and inherit gap they then have to cancel. |
| **Columns (named slots)** | `split`, `align`, `gap`, `stack_on_mobile` | `left`, `center`, `right` | Distinct from Grid: **named** slots let a composer target a specific column, and let a template author swap one side only. Grid's single `children` slot cannot express that. |

Stack carries the spacing vocabulary. On the reference site: `direction`, `gap`, `align`, `align_mobile`, `justify`, `max_width`, `margin_x/y`, `padding_x/y`, `width`, `height`. Every one is static. It is used **66×**. Treat it as the workhorse and give it the full vocabulary up front, because adding a spacing prop later means editing every placement.

**Name by layer, with one prefix.** The reference uses `alpha-` throughout: `alpha-atom-heading`, `alpha-stack`, `alpha-section-shell`, `alpha-card-shell`. A 60-primitive palette is unnavigable otherwise. The prefix groups them, and `-atom-` marks the layer at a glance. Pick any prefix. Apply it to every primitive.

**Group them in the palette too: the name is not enough.** Each registration declares the group it appears under, and the reference uses exactly two:

```ts
const ATOMS_GROUP  = 'Alpha Atoms';
const LAYOUT_GROUP = 'Alpha Layout';
// …
{ type: 'alpha-atom-eyebrow', sections: [ATOMS_GROUP], thumbnailUrl: T.text, … }
```

Decide the group names here, at library-design time. `sections` + `thumbnailUrl` mechanics belong to [`register-component`](register-component.md) § Palette group + thumbnail.

### Design props are `choice` with fixed options: this is what enforces the split

Step 1b says design stays static. **`choice` is the mechanism that makes it stick.** Every design prop on the reference declares a closed option list and a default, so an author picks from a menu and cannot type a raw value:

```ts
props: {
  text:        { type: 'string', defaultValue: 'New Feature' },              // content
  color:       { type: 'choice', options: ['brand','default','inverse','muted'], defaultValue: 'brand' },
  variant:     { type: 'choice', options: ['text','badge'],  defaultValue: 'badge' },
  badge_color: { type: 'choice', options: ['green'],         defaultValue: 'green' },
}
```

One content prop, three design props, closed options on each. A `string` design prop (`color: '#6c5ce7'`, `gap: '24px'`) re-opens exactly the drift the library exists to prevent.

**Give every prop a `defaultValue`.** It is what lets a composition omit design props entirely and still render. The authored section then carries only its content bindings, and the primitive supplies the rest.

Confirm the DS has:
- Padding tokens for `spacing: compact/comfortable/spacious` at both Section and Card levels.
- Background theme tokens for `background: none/surface/muted/brand/inverse`.
- Gap tokens for `Stack.spacing` and `Grid.spacing`.
- Card border/shadow tokens for `Card.variant`.
- Overlay opacity tokens for `BackgroundMedia.overlay`.
- Min-height tokens for `BackgroundMedia.height`.

If any is missing, list it as a **DS gap**. The primitive can still register but the token must land before the option is enabled.

### Step 4: Sanity-check against target section types

Ask which section types the user needs from day one. Common set:

- Hero: needs Section + BackgroundMedia + SplitRow + Stack + all 4 atoms
- Feature Grid: needs Section + Stack + Grid + Card + all 4 atoms
- Testimonial row: needs Section + Grid + Card + SplitRow + Stack + all 4 atoms
- Pricing tiles: needs Section + Stack + Grid + Card + all 4 atoms (+ a Condition Block for tier highlighting)
- CTA band: needs Section + Stack + all 4 atoms
- Logo strip: needs Section + Grid + Image

Confirm every section on the user's list can be built from the 10-primitive set. If any needs an atom or layout not on the list (e.g. a `Rating` atom for testimonials, a `Tabs` layout for a comparison table), note it as a **future addition**. Do NOT add it to the initial registration. Grow the library additively.

### Step 5: Emit the decomposition sheet

Give the user a plain-text summary they can paste into a PR description:

```
Studio component library — initial 10 primitives

ATOMS (content-only)
  Heading      · props: text, level, emphasis
  Description  · props: text, emphasis
  Button       · props: label, href, variant, size, icon    (mirrors shadcn Button)
  Image        · props: src, alt, aspect, fit

LAYOUTS (composition)
  Section          · props: spacing, background, contentAlign, children
  BackgroundMedia  · props: image, imageAlt, overlay, focalPoint, height, children
  SplitRow         · props: ratio, verticalAlign, reverseOnMobile, leftSlot, rightSlot
  Stack            · props: spacing, alignment, children
  Grid             · props: columns, spacing, children
  Card             · props: variant, padding, header, content, footer    (mirrors shadcn Card compound)

DESIGN-SYSTEM TOKEN CHECK
  All semantic options map to existing DS tokens — no gaps
  OR
  Gaps: <list — token that must land before shipping the primitive>

TARGET SECTION TYPES COVERED
  Hero (5 variants) · Feature Grid · Testimonial · Pricing · CTA band · Logo strip

NOT INCLUDED (deferred, add additively)
  <list any section types that would need a new atom or layout>

NEXT STEP
  Run register-component for each of the 10 primitives, in one PR.
```

## Inputs needed from the user

- **Design system name**: Tailwind + shadcn / Chakra / MUI / custom
- **Where tokens live**: CSS vars / Tailwind config / theme file
- **Target section types for day one**: Hero, Feature Grid, Testimonial, Pricing, other

If any is missing, ask before decomposing. Do NOT invent DS tokens or section types.

## Acceptance

This skill succeeds only when ALL of the following are true:
- [ ] **Every atomic component carries its CSLP tags**: `studioAttributes` spread on the root element **and** `wrap: false` in its register entry and each bindable prop's `$`-twin spread on the element rendering it. Verified in the DOM, not assumed: the root and each bound text/image element must show `data-cslp`. Without this the atom renders correctly but is invisible to Visual Editor and Live Preview. See [`register-component` § The `studioAttributes` contract](register-component.md) and § The `$`-twin contract.

- [ ] User confirms the design system + where tokens live.
- [ ] All 10 primitives listed with their prop schemas.
- [ ] Every semantic option is either mapped to a DS token or explicitly flagged as a gap.
- [ ] User's target section list is confirmed buildable from the 10 primitives OR future additions are flagged.
- [ ] Decomposition sheet emitted for the PR description.

If the user asks for a primitive that doesn't fit the atom/layout taxonomy (e.g. "register a Hero"), stop and explain the rule of thumb. Do not silently register the monolith.

## What "done" looks like: a production reference

Measured on a live 58-section Studio site (contentstack.com 2025), for calibration:

| Signal | Value | Reads as |
|---|---|---|
| Sections | 58 | one per marketing pattern, not per page |
| Nodes per section | **9.1 avg**, depth 3.8 | genuinely decomposed, a 1-node section means the component swallowed the page |
| Props static vs bound | **86% / 14%** | design lives on the canvas, content in the CT |
| Reuse of the top atom | `cta-button` 33×, `heading` 23×, `stack` 66× | the same primitives everywhere, varied by static values |
| Studio primitives | 32 condition blocks, 17 section slots, 15 repeaters | polymorphism and swap points are used, not avoided |

If a proposed library would produce sections averaging 2 to 3 nodes, or would bind design props to CT fields, it is not decomposed enough. Go back to Step 1b.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Modeling a design prop (`gap`, `align`, `variant`, `size`) as a CT field | Produces a schema authors can't reason about, and lets a section drift visually per entry. 86% of props on the production reference are static for this reason | If it changes how the thing looks rather than what it says, it is a static value set on the canvas |
| One `Description` atom for all body copy | The four rich-text shapes render through different paths. A single plain-text atom shows JSON RTE or Markdown as literal characters | Register `body-string` / `body-multiline` / `body-json-rte` / `body-html-rte` per `register-json-rte` |
| Skipping a bare `Box` because Stack "already wraps things" | Stack carries spacing, so every grouping inherits gap the composer must then cancel. The reference uses Box 49× | Register a props-free slot wrapper alongside Stack |
| Unprefixed primitive names | A 60-entry palette with no grouping is unnavigable in the component picker | One prefix for every primitive, with the layer in the name (`x-atom-heading`, `x-stack`) |
| Exposing `size` on Heading | Layout drift: every H1 picks its own size | `level` drives size via DS tokens. `size` never appears |
| `color: hex` on any atom | Color drift across the library | `emphasis: default/muted/inverse` maps to DS tokens |
| Padding in pixels on Section | Spacing scale fragments | `spacing: compact/comfortable/spacious` maps to Tailwind padding tokens |
| Registering `Hero` as an atom | Monolithic Section: new variant needs a code change | Register the 4 atoms + 4 layouts. Compose Heros on canvas |
| A `Rating` atom before you need it | Library bloat, unused primitives | Grow additively. Add only when a section actually needs it |
| Semantic option without a DS token | Silent visual failure at render | Add the token before enabling the option in the schema |

## See also

- `register-component`: the mechanical registration once the shape is decided.
- `decompose-jsx-to-atomics`: for breaking one existing over-large component into its parts.
- `decompose-design`: for taking a single design and mapping it to the primitive set + a Content Type shape.
- `import-design-tokens`: get the DS tokens into Studio's Design Panel before registration.
