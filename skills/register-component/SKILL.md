---
name: register-component
description: "Read a React component, infer a prop schema, and write a `registerComponent` call so Studio's palette uses the customer's component instead of built-in defaults. Lazy by default."
allowed-tools: Read Grep Glob
---

## When to use

Read a React component, infer a prop schema, and write a `registerComponent` call so Studio's palette uses the customer's component instead of built-in defaults. Lazy by default.

Use when the user wants Studio's palette to surface their components — "make my Hero available in Studio", "Studio shows defaults instead of mine", "register components in src/components". The BYOC moment. Do NOT use to register design tokens (use `import-design-tokens`). Do NOT invent prop schemas — only register props visible in source.

# Register a component with Studio

## Before you start — pick the layer

Every component you register is one of two shapes. Decide which before writing the registration:

- **Layer 1 — Atomic** (renders one CMS field). All scalar props. `<Heading>`, `<Text>`, `<Image>`, `<Button>`. → *This skill's default path.*
- **Layer 2 — Container / Skeleton / Layout** (holds other components). Has at least one `slot`-typed prop as a drop zone. `<Card>` with a body slot, `<Split>` with left+right slots. → *Same skill; § "Exposing extensible regions with slot props" covers it.*

If the thing you want to register is neither — a pure layout primitive (Grid, Stack, Container, Box), a whole page-shaped composition, or a component with an array-of-objects prop — **stop.** Read From designs to Sections — the three-layer mental model first. It's a 10-minute page that saves hours of "why doesn't my Grid work in Studio."

## Context

Studio composes pages from React components. By default it uses its **own** built-ins (Hero, Card, Button) so authors can play immediately — but for production, every component should come from the customer's library. Registering tells Studio's palette "use THIS component for type 'site-hero'" so authors drop branded components, not defaults.

The registration is a `registerComponent` call that names the component, gives it a unique `type`, and declares the **prop schema** Studio's right-panel will offer for binding. Prop types are strict and finite — exactly: `string`, `boolean`, `number`, `choice`, `href`, `imageurl`, `datestring`, `array`, `object`, `slot`, `json_rte`, `any`. There is no `text`, `link`, `color`, or `image` — common false-friends from other systems.

Reference: `docs/20-bring-your-own-components/register-components.md`, `docs/20-bring-your-own-components/component-schema-prop-types.md`.

## Task

1. **Locate the registration entry point.** Look for `src/register-components.tsx`, `src/register-studio.ts`, or `src/lib/contentstack.ts` (whichever file imports `registerComponent` from `@contentstack/studio-react`). If none exists, create `src/register-components.tsx` and ensure it's imported once at app startup (before any `<StudioCanvas />` or `<StudioComponent />` mounts).

2. **Read the component at `componentPath`.** Extract the prop names and types. Source of truth ranked by reliability:
   - Explicit TypeScript interface (`interface HeroProps { … }`) — most reliable
   - `propTypes` block — second-best
   - Destructured args + JSDoc comments — fallback only

3. **Map each prop to a Studio prop type.** Use the **exact** strings below — anything else is rejected:

   | Source shape | Studio prop type |
   |---|---|
   | `string` / `string \| undefined` | `string` |
   | `number` | `number` |
   | `boolean` | `boolean` |
   | `string` constrained to known values (union literal, enum) | `choice` (set `options:` to the literal values; **`defaultValue` is always an array — `["centered"]`, even for single-select**) |
   | URL string used as `href` | `href` |
   | URL string used as image `src` | `imageurl` |
   | ISO date string | `datestring` |
   | array | `array` — binds to a **multi-value field** (Reference multi, Group multi, Modular Block, scalar multi). Reference sources need `data_sources.resolvedReferences`; Groups / Modular Blocks / scalar multi-values live on the entry and need no resolution. See § *Array & object props — binding rules* |
   | object | `object` — binds when the shape matches an entry Group / Global Field; see § *Array & object props — binding rules* |
   | React `children` / placeholder for extensible region | `slot` — fillable at template time via `use-section-slot` § *component-slot-prop placement*. The prop turns that region of the component into an author-controlled drop target. No `defaultValue` (slots start empty). |
   | rich text (JSON RTE field — HTML payload) | **`json_rte`** *(NOT `string` — RTE renders markup; `string` would show it as literal `<p>` text)* |
   | unknown / can't infer | `any` |

4. **Set `defaultValue` for every prop** where the component has a default value in its source. The default appears as the palette tile preview — without it, the tile renders blank and authors don't know what the component looks like. Use `defaultValue:` exactly — NOT `default:` (the latter is silently ignored).

5. **Write the registration — prefer LAZY by default.** Append (or update) the registration file. The recommended shape is **lazy**: the component is downloaded only when it first renders, keeping the initial bundle small and code-splitting each registration automatically. The SDK wraps the dynamic `import()` with `React.lazy` + `Suspense` for you.

   ```ts
   import { registerComponent } from "@contentstack/studio-react";

   registerComponent({
     type: "site-hero",                                    // componentType — unique UID
     displayName: "Hero",                                  // componentName — palette label
     component: () =>                                      // ← LAZY: arity-0 thunk that returns a dynamic import
       import("./components/Hero").then(m => ({ default: m.Hero })),
     props: {
       headline:    { type: "string",   displayName: "Headline",    defaultValue: "Welcome" },
       description: { type: "string",   displayName: "Description", defaultValue: "Lorem ipsum" },
       imageUrl:    { type: "imageurl", displayName: "Image",       defaultValue: "https://…" },
       ctaHref:     { type: "href",     displayName: "CTA Link",    defaultValue: "/get-started" },
       layout:      { type: "choice",   displayName: "Layout",      defaultValue: ["centered"], options: ["centered", "split"] },
     },
   });
   ```

   If the component is the **default** export: `component: () => import("./components/Hero")` is enough. An explicit form `registerLazyComponent(config, loader)` exists with identical runtime behaviour.

   **5a. Exposing extensible regions with `slot` props.** To let template authors drop content into a region of the component (a card body, a sidebar, a CTA area), declare a `slot`-typed prop. The component renders the prop wherever the extensible region should appear; Studio surfaces it as a drop target for any component or Section.

   ```ts
   import { registerComponent } from "@contentstack/studio-react";

   registerComponent({
     type: "site-card",
     displayName: "Card",
     component: () => import("./components/Card"),
     props: {
       title: { type: "string", displayName: "Title", defaultValue: "Card title" },
       body:  { type: "slot",   displayName: "Body" },   // ← extensible region, no defaultValue
     },
   });
   ```

   The React component receives the slot as a prop (or via `children`, depending on what its TypeScript interface declares) and renders it inside its tree:

   ```tsx
   function Card({ title, body }: { title: string; body: React.ReactNode }) {
     return <div className="card"><h3>{title}</h3>{body}</div>;
   }
   ```

   At template-authoring time, the slot region shows as a dashed drop target. Authors drop a component or Section into it (see `use-section-slot` § *component-slot-prop placement* for the canonical filling pattern). Slots take ANY component or Section; there is no type constraint — slot fills are stored per-template, so the same Card can carry different filled content on different templates.

   For a richer pattern (slot count driven by another prop, slot template factories), see `docs/20-bring-your-own-components/component-schema-prop-types.md` § *slot*.

   **5b. The two valid `component:` shapes** — decided by arity:

   | Shape | `component:` value | When |
   |---|---|---|
   | **Lazy (default)** | arity-0 function returning a `Promise` (dynamic `import()`) | Every BYOC registration unless tiny+hot. |
   | **Eager** | function with ≥1 parameter (ordinary React component) | Tiny components on hot paths. |

   ```ts
   component: () => import("./components/Hero")          // ✅ LAZY
   component: Hero                                       // ✅ EAGER — function Hero(props) {…}
   component: (props) => createElement(Hero, props)      // ✅ EAGER — wrap arity-0
   ```

   ⛔ **Arity-0 trap.** A parameter-less function that does NOT return a Promise (e.g. `function Header() {…}`) is treated as a lazy loader, called outside render, and throws React #321 "Invalid hook call". Rule: **return a `Promise` (lazy), OR give it a `props` parameter (eager).**

6. **Confirm Studio palette shows the new tile.** Open the canvas, switch the palette accordion to **Registered Components**, find `Hero`. The tile should render a preview using the `defaultValue`s. If it renders blank, a prop is missing a default or the prop type was wrong.

## Inputs needed from the user

1. `componentPath` — file path to read.
2. `componentName` — display label.
3. `componentType` — unique kebab-case UID (reject duplicates; check the registration file before writing).

Do NOT invent component paths. If the user just says "register my Hero" without a path, ask which file.

## Array & object props — binding rules

`array` and `object` **do** bind to CMS fields — but under specific conditions that are easy to miss. Registering a `type: "array"` prop and expecting the picker to bind it to any Reference field will silently degrade to a manual-entry sub-field in cases the SDK doesn't cover. Two paths:

**Bindable — `type: "array"` bound to a multi-value field.** The SDK reads the bound array directly, the array arrives at the component populated, and the component renders items with its own `.map()`. No Repeater, no Condition Block. Valid sources:

- **Reference multi (or single)** — needs `data_sources.resolvedReferences` on the composition so CDA returns `?include[]=<field>`. Otherwise the array arrives as `{ uid }` stubs. This is the case that catches migrators — it's easy to bind and see stub UIDs render, missing the resolvedReferences step.
- **Group multi (`multiple: true` on a Group field)** — the group values are stored on the entry itself; no resolution needed. Array arrives populated as-is.
- **Modular Block** — the block payload is on the entry; no resolution needed. Note that Modular Blocks are polymorphic (each item can be a different block type) — if your `.map()` renders every item the same, the array-prop path works; if it needs per-block-type rendering, use a Repeater + Condition Block instead (see below).
- **Scalar multi-values** — a `multiple: true` single-line-text field arrives as an array of strings; no resolution needed.

Common requirements across all four:

- The prop is `type: "array"` on the registration.
- The wrapper's per-item render works against the shape delivered by the CMS for that field type.
- The list is single-shape (no per-iteration variant authoring or template-author swap).

This is the **preferred path** for wrapping an existing production component whose interface already takes an array of items. See `build-repeating-section` § *When to skip the Repeater entirely — the array-prop alternative*.

**Bindable — `type: "object"` bound to a matching entry Group / Global Field.** Same idea for a single-entry-object shape (a nested `cta: { label, href }` binding into an entry Group with matching sub-fields). Groups live on the entry — no `resolvedReferences` step.

**When array/object won't fit — reach for the Repeater or the adapter pattern.** If the list iterates a **Modular Block** (polymorphic — each item can be a different block type), template authors need to **swap a different child Section per template instance**, or the production leaf's shape doesn't reduce cleanly to array-item scalars, use one of:

- **`build-repeating-section`** — greenfield parent+child+Repeater pattern with a Section Slot for template-author swaps.
- **`adapt-collection-component`** — compatibility-adapter pattern for wrapping a legacy production component whose leaf can't be simplified.

Both surface author variability the array-prop path can't. Choose by the constraints above, not by default.

The narrow non-CMS use for `type: "array"` / `type: "object"` remains: authoring-time-only configuration where a marketer *should* type values in by hand (e.g. a "tags" prop not stored in CMS).

## Tolerant image signatures — accept `string | { url }` on every `imageurl` prop

Every `imageurl`-typed prop must accept both a plain URL string AND a Contentstack asset object with a `.url` field. Contentstack stores assets as objects (`{ url, filename, uid, … }`); the picker sometimes binds the object, sometimes the `.url` sub-field, depending on the depth of the picked path.

If the component's TypeScript signature demands one shape, the other silently fails — icons "map correctly" but render invisible, or the object gets `.toString()`'d and the URL area shows `[object Object]`. Both bugs ship to production without a warning.

Contract for every `imageurl` prop:

```tsx
type ImageProp = string | { url?: string } | null | undefined;

function coerce(img: ImageProp): string | undefined {
  if (!img) return undefined;
  return typeof img === "string" ? img : img.url;
}
```

Every registered component's `imageurl` prop declares its TS type as `string | { url?: string } | null | undefined`, and the component internally calls a coerce helper (or optional-chains `img?.url ?? img`). This is a first-class contract, peer of the null-safety and `$`-twin contracts — not a pitfall row.

Rationale: Studio's picker doesn't ship type-aware binding coercion today (Part 1 #2 in the product improvements backlog). Until it does, the component compensates.

## Tolerant link signatures — bind the leaves, not the whole link object

Contentstack's `link` field is a two-property object: `{ title: string; href: string }`. Studio's picker binds each leaf separately — a component with an `href`-typed prop expects a URL string, not the whole link object. Binding the object silently ships `[object Object]` into the DOM.

Contract for every navigable component:

- **`href`-typed prop** — TS type: `string | null | undefined`. Never accept `{ href: string }`. Bind against `linkField → href`.
- **Label** — separate `string` prop bound against `linkField → title`.
- **A single object prop for the whole link is an anti-pattern.** If the design *conceptually* has one "link" object, still register the leaves as separate props (`ctaLabel: string`, `ctaHref: href`) and let the picker bind each. Two clicks in the picker, zero mystery renders.

If you can't split (a shared design-system component takes `link: {title, href}`), coerce inside:

```tsx
type LinkProp = string | { title?: string; href?: string } | null | undefined;

function href(link: LinkProp): string | undefined {
  if (!link) return undefined;
  return typeof link === "string" ? link : link.href;
}
function label(link: LinkProp, fallback: string): string {
  if (!link || typeof link === "string") return fallback;
  return link.title ?? fallback;
}
```

Same shape as the image tolerance contract above.

## `{{entry.title}}` and other unresolved placeholders — Studio only resolves `{{entry.url}}` in Connected template URL patterns

Studio's Template URL Pattern field supports one placeholder: **`{{entry.url}}`**. It resolves to the CT's `url` field at render time. Every other pattern (`{{entry.title}}`, `{{entry.slug}}`, `{{author.name}}`) is left **literal in the response** — the SDK does not template-expand them.

Where this bites:

- Composition **canonical URL** field with `{{entry.title}}` renders literally in the `<link rel="canonical">` tag. Google indexes the literal string. SEO ranking dies silently.
- Template preview iframe URL with a non-`{{entry.url}}` placeholder never resolves; iframe stays on the placeholder URL.
- OG image / social preview URLs with placeholders → broken share cards.

The only supported form:

```
URL Pattern: /blog/{{entry.url}}      ✓ resolves to entry.url
URL Pattern: {{entry.url}}            ✓ resolves to entry.url (route inherits from CT)
URL Pattern: /blog/{{entry.title}}    ✗ ships literal "{{entry.title}}" — SEO break
URL Pattern: /author/{{author.name}}  ✗ same
```

If you need a title-based slug, populate the CT's `url` field with the slug at entry time (Contentstack workflows / hook / manual) — do not template-expand at render time.

## Layout contract — registered components must be layout-agnostic

A registered component is dropped by template authors into Sections, Section Slots, Repeaters, and other contexts the component author never anticipated. The component must render correctly *across* those contexts without depending on a specific ancestor.

The rule, from standard CSS architecture (BEM, Every Layout, Atomic Design — separation of concerns between layout and content):

- **The component renders at `width: 100%` of whatever container it's placed in.** It fills its cell — it doesn't decide how big its cell should be.
- **The component does NOT hard-code a `max-width` to "protect itself"** from being placed in a too-wide container. Hard-coded sizes spread layout decisions into content components and break reuse (a card capped at 300px looks fine in a 4-up grid, ridiculous in a single-product hero, crammed in a 6-up grid).
- **Container queries** (CSS `@container`) are the right tool for size-dependent internal layout inside the component — they let the component adapt to its container without knowing the ancestor.
- **Layout responsibility lives in the parent Section**, not in the component. The Section that owns the Slot / Repeater provides the layout container (grid tracks, flex with `gap` + `flex-basis`, or a `max-width`-constrained Box). The component fills the cell that container defines.

If you find yourself adding `.fs-grid > .fs-card { ... }` overrides to make a card behave inside a grid, the coupling is backwards — the card knows about the grid. Decouple: card stays `width: 100%`, grid (in the parent Section) provides the track.

## Null-safe rendering contract

Bindings resolve at runtime — and may resolve to `undefined`, `null`, an empty string, an empty array, or a placeholder value. Every registered component MUST render without throwing under those inputs.

The SDK's resolution chain: `boundValue ?? staticValue ?? defaultValue ?? placeholder`. If you set `defaultValue` on every prop, MOST cases resolve to a real value — but four paths still surface `undefined`/`null`/empty to your component:

1. **No `defaultValue` and no binding** — picker emits an unbound prop, no static value, no default → resolved value is `undefined`.
2. **Binding to a deep optional path** — e.g. `featured_image.0.url` when `featured_image` is an empty array (multi-file field with no upload yet) → `undefined`.
3. **Binding to an optional reference** — entry exists but the reference field is empty → `undefined`.
4. **Empty-string field** — Contentstack stores `""` for cleared text fields; truthy checks (`if (props.title)`) treat it as missing but JSX renders nothing — safe but easy to confuse with a render bug.

The component contract:

```tsx
// ❌ Throws when featured_image.0 is undefined
export function Card({ image }) {
  return <img src={image.url} alt={image.alt} />;
}

// ✅ Optional-chains and short-circuits cleanly
export function Card({ image, title }) {
  if (!image?.url) return null;            // render nothing when essential prop missing
  return (
    <article>
      <img src={image.url} alt={image.alt ?? ""} />
      {title && <h3>{title}</h3>}
    </article>
  );
}
```

Rules:

- **Optional-chain every nested access** — `props.image?.url`, `props.cta?.[0]?.href`.
- **Nullish-coalesce non-binding renders** — `alt={image.alt ?? ""}`, `count={items?.length ?? 0}`.
- **Decide what "missing" means** — render `null`, render a skeleton, or render a labelled empty state. **Never crash.** Compositions get authored against half-filled entries during preview; one throw kills the whole canvas.
- **Don't rely on `defaultValue` alone.** It's a safety net for unbound props, not for empty entry data.

## The `$`-twin contract — attach CSLP data attributes to every bindable prop

**Silent-failure #1 in hand-written registered components:** a bindable prop appears in `registerComponent`'s `propTypes` (or `props`), and the component renders the value fine, but **click-to-edit in Visual Editor doesn't attach** and inline editing silently fails. No error, no warning — the prop just isn't editable inline.

Root cause: the SDK passes each bindable prop as a **pair** — the resolved value AND a **`$`-prefixed twin** that carries the `data-cslp` attribute Visual Editor needs. If you don't spread that twin on the rendered DOM element, Visual Editor has no anchor to attach the edit affordance to.

**The rule — for every bindable prop that renders visible content, do both:**

1. Destructure the `$`-prefixed twin alongside the value.
2. Spread the twin on the DOM element that renders that prop's content.

```tsx
// ❌ Renders the value, but the `$`-twin never reaches the DOM →
//    Visual Editor cannot attach click-to-edit to eyebrow / badge / headline.
export function Hero({ eyebrow, badge, headline, backgroundImage }) {
  return (
    <section style={{ backgroundImage: `url(${backgroundImage})` }}>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      {badge && <span className="badge">{badge}</span>}
      <h1>{headline}</h1>
    </section>
  );
}

// ✅ `$`-twin destructured for every bindable prop and spread on the DOM node
//    that renders it. Click-to-edit now attaches to each element.
export function Hero({
  eyebrow, $eyebrow,
  badge, $badge,
  headline, $headline,
  backgroundImage, $backgroundImage,
}) {
  return (
    <section {...$backgroundImage} style={{ backgroundImage: `url(${backgroundImage})` }}>
      {eyebrow && <p className="eyebrow" {...$eyebrow}>{eyebrow}</p>}
      {badge && <span className="badge" {...$badge}>{badge}</span>}
      <h1 {...$headline}>{headline}</h1>
    </section>
  );
}
```

**Checklist for every component you register:**

- [ ] For each bindable prop that renders **visible text or an image**: `$prop` is destructured.
- [ ] For each `$prop`: `{...$prop}` is spread on the DOM element that renders that prop's content.
- [ ] Slot-typed props (`type: "slot"`) don't need `$`-twin spread — they contain child nodes, not values.
- [ ] Non-visible props (analytics IDs, aria labels not tied to a visible text) also don't strictly need a twin, but adding one costs nothing.

**Verify in the browser.** Open the component in Studio → inspect the rendered DOM → each bindable text/image node should have a `data-cslp="..."` attribute. If it doesn't, the `$`-twin is missing.

The SDK auto-injects the `$`-twin for you — you never construct it by hand. It's a naming convention: prop `foo` → destructure `$foo`.

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] The registration file contains a `registerComponent` call for the supplied `componentType` that did not exist before this skill ran.
- [ ] Every prop on the source component's TypeScript interface (or propTypes) appears in the `props:` object — no prop dropped silently.
- [ ] Every `type:` value is one of the 12 allowed strings (`string`, `boolean`, `number`, `choice`, `href`, `imageurl`, `datestring`, `array`, `object`, `slot`, `json_rte`, `any`) — not `text`, `link`, `color`, or `image`.
- [ ] Every `choice` prop's `defaultValue` is an **array** (`["centered"]`, not `"centered"`) — including single-select. Source: `ChoiceProp = PropBase<…, string[]>` in `studio-registry`.
- [ ] `defaultValue:` (not `default:`) is set on every prop where the source component has a default. **Exception: `slot` props never carry a `defaultValue`** — they start empty until template authors fill them.
- [ ] Choice props include an `options:` array of the allowed literal values.
- [ ] The registration file is imported once at app startup — verified by grep for the import in `main.tsx` / `_app.tsx` / `App.tsx`.
- [ ] Studio's **Registered Components** palette accordion shows the new tile with the supplied `displayName`.
- [ ] The tile preview renders (not blank) because the defaults are populated.
- [ ] `component:` follows one of the two valid shapes — **lazy** (arity-0 function that returns a `Promise` of the component, typically `() => import("./Foo")`) OR **eager** (function with at least one parameter, i.e. an ordinary React component). The default recommendation is lazy. A zero-parameter function that does NOT return a Promise triggers React #321 / "Invalid hook call" at render.
- [ ] The component is **layout-agnostic** — `width: 100%` of its container, no hard-coded `max-width` to "protect" against wrong contexts, no styles that rely on a specific ancestor selector (`.fs-grid > .fs-card { ... }`). Layout sizing is delegated to the parent Section, not baked into the component.
- [ ] **Call-site literal sweep** — if this component is already used in production code, grep every JSX use of it. Every literal prop set at a call site (`isInteractive={false}`, `variant="compact"`, `columns={3}`, `isLogoBgWhite={false}`) becomes a `defaultValue` on the corresponding registered prop, or a named preset. Skipping this is the single most common cause of "composed page looks 80% right but wrong on hover/motion/spacing." Sample grep: `rg -tn tsx -o "<ComponentName[^>]*/>" | head`. If the component is *new* (no production call sites yet), acceptance is trivially satisfied — but state that explicitly.
- [ ] **Tolerant image signatures** — every `imageurl` prop's TS type accepts `string | { url?: string } | null | undefined`, and the component internally coerces. See § *Tolerant image signatures* above. This is a first-class contract, not an optional nicety — Studio's picker binds sometimes the object, sometimes `.url`, and either shape must render correctly.
- [ ] **Tolerant link signatures** — every `href`-typed prop binds against a link field's `href` leaf (never the whole link object). Where the design mandates a single link prop, the component coerces `string | {title, href}` inside via `href()` / `label()` helpers. See § *Tolerant link signatures* above.
- [ ] **Palette group + thumbnail** — the registration declares `sections: ["<Brand> · Elements | Patterns | Layouts"]` (never `"Template"` or `"Section"` in the name) and a `thumbnailUrl` data URI that visually previews the tier. See `palette-conventions`.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Using `default:` instead of `defaultValue:` | Studio silently ignores `default:` — palette preview renders blank | Use `defaultValue:` exactly |
| Using `text`, `link`, `color`, `image` as prop types | These don't exist — registration is rejected at runtime | Use the 12 allowed types only |
| Registering a prop that's not actually on the component | The Data Picker offers a binding that crashes at render time | Read the source; register only props you see |
| Duplicate `type:` UID across two components | **First registration wins; duplicates are silently skipped** (the SDK's default is idempotent so HMR / RSC-plus-client / build-worker re-evaluation doesn't break). A real bug stays hidden because the second definition never lands. | Search the registration file for the UID before writing. Pass `{ strict: true }` as the second arg to `registerComponents([...], { strict: true })` to throw on duplicates instead. |
| Forgetting to import the registration file at startup | Components never appear in the palette | Add `import "./register-components"` to `main.tsx` / `_app.tsx` |
| Registering the unwrapped primitive (e.g. `Box` from a UI lib) instead of the customer's component | Loses brand styling — Studio composes pages out of unstyled primitives | Register the customer's wrapped component (e.g. `<Hero>`), not the lib primitive |
| Inferring a `string` prop as `choice` because TS uses a union of two literals | Authors can't type freeform text into a free-form field | Use `choice` only when the union is a closed set the user MUST pick from |
| Arity-0 component (`function Header() {…}` as `component: Header`) | SDK treats as lazy loader, calls outside render → React #321 "Invalid hook call". | Use lazy shape `() => import(...)` or give it a `props` param. |
| Registering eagerly when lazy would do | Eager ships in entry bundle; many components balloon TTI. | Default to lazy `() => import("./Foo")`. |
| Component depends on layout ancestor (e.g. `.fs-card` only sized by `.fs-grid`) | Renders full-bleed in a Slot/Repeater that doesn't provide that ancestor. | Decouple — see Layout contract above; layout lives in parent Section. See `use-section-slot` § *Layout container*. |
| Setting `defaultValue` on a `slot` prop | Slots start empty until authors fill them; a static default doesn't fit the model and is silently ignored. | Omit `defaultValue` on `slot` props. The slot renders as a dashed drop target until an author drops content. |
| Naming a slot prop something the component doesn't render | The slot becomes a drop target in Studio but its contents never appear at render time because the component ignores the prop. | The prop name must match what the React component's signature uses — typically `children` (for `<Card>{...}</Card>` style), but any name works as long as the component renders `{propName}` somewhere in its JSX. |
| Trying to constrain a slot to "only accept Sections of type X" | Slots accept any registered component or Section; no built-in type filter exists. Adding a constraint isn't supported. | If you need a typed value override (one specific kind of content), use an exposed Section Prop instead. If you need a typed component constraint, surface the expectation in the slot's `displayName` ("Drop a CTA Section here") so authors self-route. |
| Component throws on `undefined` / `null` / empty-array props during canvas preview | Bindings resolve at runtime; an unfilled entry field, empty multi-file field, or unbound prop surfaces `undefined` to the component. One thrown access kills the whole canvas render — author can't recover without re-binding. | See § *Null-safe rendering contract* above. Optional-chain every nested access (`props.image?.url`); return `null` or a skeleton when essential data is missing. |
| Confusing `slot` (component prop type) with Section Slot (drop region inside a Section) | They are different mechanisms at different levels — both surface drop targets, both can hold the other. | A `slot` PROP is part of a registered component's schema; a Section Slot is a Smart Container carved into a Section. The recommended composition is: declare a `slot` prop on the component → carve a Section Slot inside that prop via `use-section-slot` § *component-slot-prop placement* → authors then fill that Section Slot at template time. |
| Design tab is empty for this component when selected in the canvas | The registration didn't declare a `styles` block. The Design tab surfaces the sections listed in `styles` — no `styles` → empty tab. | Add `styles: [...]` to the registration listing the categories authors should be able to edit (`size`, `spacing`, `typography`, `background`, etc.). See `docs/20-bring-your-own-components/component-schema-prop-types.md` § *styles*. If the Design tab itself is missing (not just empty), the project's Freeform Feature is off — see [`install-studio`](../install-studio/SKILL.md) § *After install — if the Design tab is missing / disabled*. |

## After registering — plan your Section shape

Register the component first; then decide which Section(s) to author in Studio for it.

- **Compound component that iterates internally** (say `<BlogArticle>` doing `.map(sections)`, `<CardList>` doing `.map(related_posts)`) → **build top-down**. Author the wrapping Simple Section first — one Section that wraps the whole compound. Studio renders your existing page inside its canvas in ~5 minutes with no code changes. Then decompose one Section per iteration level as you need each to become author-editable.
- **Atomic component that renders one shape** (`<Card>` bound to card_ref, `<Hero>` bound to hero_group) → author its Simple Section directly. Compose it later inside a List Section when a parent iteration needs to drop it as a slot's default content.

Both directions produce the same Section chain in the end — top-down is faster for existing compound-heavy apps; bottom-up has a cleaner mental model for greenfield.

Use [`build-section`](../build-section/SKILL.md) (or [`build-repeating-section`](../build-repeating-section/SKILL.md) for List Sections) to author each Section — the skill walks the Studio-UI flow. Full worked example with a 4-level nested schema: From components to Studio compositions.

## See also

- `docs/20-bring-your-own-components/register-components.md` — full reference, including `registerComponents` (batch) and `registerLazyComponent` (code-split)
- `docs/20-bring-your-own-components/component-schema-prop-types.md` — every prop type with all options
- `docs/20-bring-your-own-components/set-component-default-data.md` — separate `wire-component-default-data` skill for advanced default data
- `wire-component-default-data` — for components whose defaults aren't representable as static `defaultValue:` literals
- `use-section-slot` — fill a `slot`-typed prop on a registered component (the `component-slot-prop` placement mode), or carve a Section Slot inside one
- `import-design-tokens` — register your design system after registering components
