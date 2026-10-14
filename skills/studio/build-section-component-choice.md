---
name: build-section-component-choice
---

## When to use

Decide whether a Section uses Studio's basic field components or your own registered components: the simple-versus-styled tradeoff, and what each choice costs later.

Part of the Section-authoring set. Start at [`build-section`](build-section.md).

## Basic field components vs custom registered components: the simple-vs-styled tradeoff

Studio palettes ship two kinds of nodes you can drop into a Section. **All editing happens in the right panel. Neither kind supports inline-typing in the canvas.** The real tradeoff is shape and styling:

| | **Basic field components** (palette: Basic): `Heading`, `Paragraph`, `Text`, `Image`, `Link`, `RichText`, etc. | **Custom registered components** (palette: Registered Components): your `<Hero>`, `<ProductCard>`, etc. |
|---|---|---|
| Shape | Single value (a string for `Heading` / `Paragraph` / `Text`, a URL for `Image`, a JSON tree for `RichText`). The author sets it via the right panel: either as a **static value** typed inline, or as a **binding** to a CT field. | N props as declared in `registerComponent` schema. Each prop set via the right panel: static value or binding to a CT field. |
| Visual styling | Plain HTML by default: `<h1>`, `<p>`, `<img>`. Styling comes from node `styles.default.responsiveStyles.default` set via the Design panel, OR app-side CSS targeting the rendered DOM. RTE embeds use the default serializer unless you register a custom one (see `register-json-rte`). | Whatever your React + CSS produces. Pixel-perfect. Uses your design system. |
| Layout authoring | Composable via Basic `Box` + node `responsiveStyles` (see pitfall row below). | Owned by the React component code. |
| Authoring UX | Quick: drop, type a value or bind a field in the right panel, done. Good for editorial copy that lives ONLY in the composition (not modelled in the CMS). | Higher-fidelity: drop a fully-styled block, bind props to CT fields. Right-panel surface is exactly the prop schema you registered. |
| Best for | Headlines, body copy, captions, CTA labels, RTE blocks, wherever literal copy can live in the composition itself OR map 1:1 to a CT field with no surrounding shell. | Marquee / styled / interactive sections: hero, carousel, 3D viewer, anything pixel-sensitive or with multi-field internal structure. |

**These are two render paths.** The local standalone page (custom `Hero`) and the Studio composition (Basic `Heading` + `Paragraph`) will NOT look identical by default. Treat the gap as design work, not a bug.

**Recommended pattern: hybrid.** Use both inside one Section:

- **Custom registered components** for the styled / interactive shells: the hero with its background, the carousel with its animations.
- **Basic field components** for editorial copy that doesn't need a custom shell (headline, intro paragraph, footnote) or for repeated content blocks where authors should be able to swap copy quickly via the right panel without engineering ever touching the codebase.
- **Match the Basic-component styling to your brand** by setting node `responsiveStyles` via the Design panel (typography, spacing, color), or write CSS that targets the rendered semantic DOM. For RTE, register a custom renderer (`register-json-rte`).

Decision rule:

- Is THIS region a single string / scalar value that maps 1:1 to a CT field (or is composition-local copy)? Use a Basic field component.
- Is THIS region a multi-prop / styled / interactive piece? Use a custom registered component.
- Both, in the same Section, is normal and good.

### Migrating an existing component: register it whole, or decompose it?

When a Section is being built from JSX that already exists, there's a prior question the rule above doesn't answer: does the whole `<Hero>` become **one registered component**, or does it get **decomposed into built-ins** (`Box` + `Image` + `Heading` + `Paragraph` + `Link`) that reproduce the same markup?

A Section made of one registered component is a **black box to authors**: they can re-bind its props and nothing else. No restyling, no reordering its internals, no removing the subtitle. That's often the right trade, but it must be a stated choice, not a default that happens because registering was easier.

| Signal | Verdict |
|---|---|
| Interactive: local state, event handlers, cookies, personalization, modals, carousel logic | **Must be one registered component.** Studio built-ins can't express behavior. Not a judgment call |
| Pixel-sensitive: bespoke CSS, animations, `::before` layering, container queries | **One registered component.** Decomposing means rebuilding the styling from Design-panel values, and 1:1 fidelity is unlikely |
| Static presentational: image + heading + body + link in a layout | **Decompose into built-ins.** Authors get full in-Studio editing: restyle, reorder, delete, add. This is the case that most often gets black-boxed by mistake |
| Styled shell wrapping editable content | **Hybrid**: register the shell with a `slot` prop, fill the slot with built-ins. Best of both. See `register-component` § slot prop |

**Surface the choice. Don't just pick.** For any Section that isn't forced by the first two rows, tell the user which way you're going and what it costs them:

> `Hero` is static presentational. I can either register it as one component (exact markup, authors can only re-bind props) or decompose it into Studio built-ins (authors can restyle and restructure in Studio, but I rebuild the styling and exact markup fidelity isn't guaranteed). Defaulting to **decompose** for author editability. Say the word if you want 1:1 fidelity instead.

Silence is not agreement. If the plan is to black-box a static component, that line goes in the plan explicitly with its cost.

**Binding fields is a separate axis, and it is never optional.** A registered-component Section still binds real CT fields to its props (`image.url`, `headline`, `body`). Black-box refers to author editability of structure, not to whether data is wired. Likewise a **Section Slot** is a third, unrelated concept, a swap point where a template author drops a different Section per instance. Add one only when a region genuinely needs per-instance swapping. A fixed hero doesn't. See [`understand-section-slots`](understand-section-slots.md).
