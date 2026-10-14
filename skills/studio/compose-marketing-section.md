---
name: compose-marketing-section
---

## When to use

Given a design comp / description of a marketing section and a library of already-registered atomic + layout primitives (see [`design-component-library`](design-component-library.md)), pick the primitive tree that composes the section on Studio's canvas.

Use when the user says "how do I build a Hero from primitives", "compose a feature grid in Studio", "which primitives for this testimonial layout", "make me a pricing tile from the atoms", "translate this Figma section into a primitive tree". Do NOT use before the primitives are registered (run `design-component-library` first). Do NOT use for whole-page decomposition (use `decompose-design`). Do NOT use to write the registration itself (use `register-component`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Pattern preflight: mandatory.** Before the first write, run [`match-existing-pattern`](match-existing-pattern.md): read the Templates and Sections already in the project, **reuse what already covers this schema**, and build to the pattern they use. Skip it only when the project has no compositions at all. Authoring something structurally foreign to what is there is rework, and it is invisible until someone opens the Layers panel.

# Compose a marketing section from primitives

## Context

Once the 10-primitive library (4 atoms + 6 layouts) is registered, every marketing section is a composition, no code change per variant. This skill walks the user from "here's what I want to build" to a specific primitive tree they can drop into Studio's canvas.

**This skill runs Q1** of the [four-question decision framework](design-component-library.md): Can this be composed from the existing 10 primitives?

- If **YES** (the common case): produce the composition tree. The user drops it on canvas.
- If **NO** (rare, genuinely new shape): halt and route to `design-component-library`, which starts at Q2 to decide what new primitive(s) to register.

Never invent a new primitive silently. Never compose from a mix of registered primitives + "and one more component we'll add later". That's Q1 = no, escalate.

Four canonical shapes cover the common cases and should be the first thing consulted:

- Hero from primitives: 5 variants (centered, split, full-bleed, thumbnail-top, two-CTA)
- Feature grid from primitives: 3-column feature callouts
- Testimonial cards from primitives: quote + avatar + author + role
- Pricing tiles from primitives: 3-tier with highlighted middle

If the user's request matches one of these shapes, compose it from the matching shape directly. Only compose from scratch when the request diverges.

## Task

Walk the user through composing one section in four steps.

### Step 1: Classify the section

Ask (if not obvious from the request):

- **1:1 or 1:many with the page entry?** A Hero binds to one landing_page entry directly. A Feature Grid iterates over N feature entries. This decides whether a Grid becomes a Repeater.
- **Does it have a background image?** If yes, BackgroundMedia is the wrapping layout under Section.
- **Is the content side-by-side or stacked?** Side-by-side means SplitRow. Stacked means Stack.
- **Does the section list distinct items with a shared shape?** Yes means Grid + Card iteration. No means a flat Stack of atoms.

Map the answers to one of these shapes:

| Shape | Wrapping layouts | List behavior |
|---|---|---|
| Single hero (1:1) | Section + optional BackgroundMedia + Stack | No Repeater |
| Split hero (1:1) | Section + SplitRow + Stack (left) + Image (right) | No Repeater |
| Item grid (1:many) | Section + Stack (intro) + Grid + Card per item | Grid is Repeater |
| Testimonial row (1:many) | Section + Stack + Grid + Card + SplitRow in footer | Grid is Repeater |
| Pricing row with highlight (1:many, conditional) | Section + Stack + Grid + Condition Block + Card | Grid is Repeater, Condition on `is_highlighted` |

If the shape doesn't match any of these, note the deviation and pick the closest. The primitive tree adapts.

### Step 2: Draw the composition tree

Produce a text tree using the format from the recipes:

```
Section (spacing: <choice>, background: <choice>, contentAlign: <choice>)
└── <optional BackgroundMedia | SplitRow>
    └── Stack (spacing: <choice>, alignment: <choice>)
        ├── Heading (text: <content or binding>, level: <h1|h2|h3|h4>, emphasis: <default|inverse>)
        ├── Description (text: <content or binding>, emphasis: <default|muted|inverse>)
        └── Button (label: <content or binding>, variant: <choice>, size: <choice>)
```

Rules for the tree:

- Every level indented under the previous with `└──` / `├──`.
- Each node lists its primitive name + non-default props inline.
- Content-bearing atoms (Heading, Description, Button, Image) show their `text` / `href` / `src`: either a literal value in double quotes or a `← entry.<field>` binding arrow.
- Layout primitives (Section, Stack, Grid, etc.) show their configuration props only: no children fields, since children are the sub-tree.
- Card compound uses labeled slot lines: `├── header:`, `├── content:`, `└── footer:` with a nested tree per slot.

### Step 3: Name the bindings vs static values

Every atom-level prop is either **bound** to a CT field or **static**. Every layout-level prop stays **static** on the Section. Split them explicitly:

```
BOUND (per entry — via Data Picker)
  Heading.text     ← entry.<field>
  Description.text ← entry.<field>
  Button.label     ← entry.<field>
  Button.href      ← entry.<field>
  Image.src        ← entry.<field>.url
  ...

STATIC (design decisions — set once on the Section)
  Section.spacing:      <choice>
  Section.background:   <choice>
  SplitRow.ratio:       <choice>
  Stack.spacing:        <choice>
  Grid.columns:         <n>
  Card.variant:         <choice>
  Card.padding:         <choice>
  BackgroundMedia.overlay: <choice>

EXPOSED PROP CANDIDATES (optional — Template author can override per drop)
  Section.background      (per-Template treatment)
  Grid.columns            (2/3/4 variations per Template)
  SplitRow.ratio          (rare — usually stays static)
```

Never expose atom props. Content flows via CMS. Visual polish stays in the DS.

### Step 4: Point at the closest recipe

If the composition matches one of the four canonical recipes, close with:

> This composition is a variation of the [Hero / Feature Grid / Testimonial / Pricing] recipe. Follow that recipe's step-by-step to build it in Studio. Substitute the tree above where the recipe's tree appears.

If it diverges, close with:

> The composition is novel enough to warrant its own recipe. Once built and validated, record it alongside the four canonical shapes above so the next request can reuse it.

## Inputs needed from the user

- **What section are you building?**: a rendered mock, a design description, or a target section type name.
- **CT relationship**: is the content 1:1 with the page entry, or a list of items?
- **Are the 10 primitives already registered?**: if not, run `design-component-library` first.

If any is missing, ask before composing. Do NOT invent primitives: the tree must use only the registered 10.

## Acceptance

This skill succeeds only when ALL of the following are true:

- [ ] User confirms the primitives are registered.
- [ ] The composition tree uses only primitives from the 10-primitive set (or explicitly flags a new atom/layout needed as a library extension).
- [ ] Bindings and static values are split explicitly.
- [ ] The tree matches (or clearly diverges from) one of the four canonical recipes. The appropriate one is linked.

If the user's request needs a primitive that isn't registered, stop and route them back to `design-component-library` for the extension conversation. Never silently invent a new primitive.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Adding a props table to an atom in the tree | The tree is composition, not registration | Only list config values as inline notes. The primitive's registered schema is the source of truth |
| Exposing an atom prop (e.g. Heading.emphasis) as an Exposed Prop | Author picks visual polish, DS drifts | Exposed Props are Section-level layout knobs only |
| Composing a "Hero" node instead of Section + BackgroundMedia + Stack + atoms | Reintroduces the monolith | Every section starts with Section as the outermost layout, atoms as the leaves |
| Binding layout props to CT fields | Layout becomes per-entry, DS control lost | Only atom-level content props bind |
| Missing a `Repeater` mention on 1:many shapes | Grid renders one iteration on drop, author sees only 1 card | Explicitly note "Grid, with a Repeater over `<field>`" when the CT relationship is 1:many |

## See also

- [`design-component-library`](design-component-library.md): the 10-primitive pattern. Run it first if the primitives aren't registered yet.
- `build-section`: once the tree is composed, actually save the Section in Studio.
- `use-repeater`: for the Repeater step on a 1:many Grid.
- `use-condition-block`: for the highlighted-tier logic in Pricing.
