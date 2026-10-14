---
name: decompose-jsx-to-atomics
---

## When to use

Break an existing React component (often a whole page in one file) into Layer-1 atomics, Layer-2 containers and Layer-3 Sections, so its parts become reusable instead of one monolithic block.

Use when the customer HAS code and a component is too coarse to reuse: a page-level component, a "section" that renders six unrelated things, or anything you'd otherwise register whole. Phrases: "make this component reusable", "break this page into sections", "my whole page is one component", "decompose this React component", "this section is too big", "why can't I reuse this". Run BEFORE `discover-sections` on an existing codebase, and before `register-component` on any component larger than one content field. Do NOT use for a design artifact with no code (that's `decompose-design`) or to derive a schema from a component's existing props (that's `design-section-from-jsx`).

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Reuse preflight: mandatory when the project already has compositions.** Before naming a single new atomic, component or Section, run [`match-existing-pattern`](match-existing-pattern.md) § Step 1b: it groups existing Sections by the schema they bind and ranks the component palette by real usage. Decomposition is where reuse has to bite. Once this step names `Heading` instead of the project's `alpha-atom-heading`, the duplicate survives into the plan and into the build. Mark every row reuse, extend, or new, and never new without having looked.

# Decompose existing JSX into atomics and Sections

## Context

**The failure this exists to prevent.** With an existing codebase, nothing used to look inside a component. `discover-sections` counts how many routes use a component name. `design-section-from-jsx` reads its props. So a page written as one `<RewardsPage>` produced one registered component and one Section covering the whole page. The consequences compound:

| Symptom the customer reports | Actual cause |
|---|---|
| "Nothing is reusable. I can't put the hero on another page" | The hero was never a separate piece, it's markup inside a page component |
| "Authors can only change text, not rearrange anything" | One Section = one block on the canvas. Nothing to reorder |
| "We never used slots / repeaters / exposed props" | A monolith has no seams, so those primitives never come up |
| **"The data doesn't bind properly to entries"** | One coarse prop takes a whole object, often typed `any`, which the binder then flattens (see [`register-component` § The `any` flatten trap](register-component.md)). Atomic props bind one field each and can't flatten |

An existing React component is **not** a reason to skip decomposition. It's the input to it: **a component becomes a Section by being broken up**, and its parts become the reusable pieces.

Taxonomy (Layer-1 atomic / Layer-2 container / Layer-3 Section) is defined once in [`decompose-design`](decompose-design.md) and applied to visual input by [`decompose-design`](decompose-design.md). This skill applies the same taxonomy to **code**. Don't re-derive the layers here. Read them there.

## Task

1. **Read the render tree, not the prop list.** Open `componentPath` and walk what it returns. Props tell you what the current caller passes. The render tree tells you what the component actually contains. That's where the reusable pieces are hiding. Note for each element: tag/component, what content it renders, and where that content comes from (a prop, a literal, a `.map()`, a fetch).

2. **Classify every leaf as a Layer-1 atomic, one piece of content each.**

   | In the JSX | Atomic | Prop type |
   |---|---|---|
   | `<h1>`, `<h2>`, heading, title, label | `Heading` / `Text` | `string` |
   | `<p>` of **plain** copy, no formatting possible | `Text` / `Paragraph` | `string` |
   | `<img>`, background image | `Image` | `imageurl` |
   | `<a>`, button with a destination | `Link` / `Button` | `href` (+ `string` label) |
   | **Formatted copy**: `dangerouslySetInnerHTML`, a markdown renderer, `ReactMarkdown`, `<div>` holding `<strong>`/`<ul>`/`<a>` from data, anything an author can style | **`RichText`** | `json_rte` (JSON RTE) or `any` (HTML RTE / Markdown) |
   | Copy that **truncates**, "read more", accordion body, `<details>`, show/hide | **`CollapsibleText`** | as above |
   | Formatted copy that can **embed a card or media** mid-flow | `RichText` **+ `registerRTERenderer`** with `embeddedEntry` / `embeddedAsset` | as above |
   | A date, price, count | `Text` | `datestring` / `number` |
   | An interactive control (form field, toggle, carousel arrow) | **stays inside a registered component**: built-ins can't express behavior | - |

   **On an existing codebase, flag the upgrade: don't perform it.** Code that renders prose through a plain `<p>` is often just what was quickest to write. Two cases, very different costs:

   - The CT field is **already rich text** and the code renders it plainly, so switching to `RichText` is **free**: no schema change, and it fixes markup currently showing as literal characters.
   - The field is **plain text** holding prose, so suggest `json_rte`, state that it is a schema change on live entries ([`migrate-ct-schema`](migrate-ct-schema.md)), and proceed with plain text if the user declines.

   Say it as a recommendation with the cost attached, then respect the answer. Never migrate a field as a side effect of decomposing a component.

   **Deciding plain vs rich:** ask whether an author could ever want **bold, a link, a list, or an embed** in that copy. If yes it is rich text. `Text`/`Paragraph` render `String(text)` and would show the markup as literal `<p>` characters. Body copy, descriptions and long-form prose are rich text far more often than they look. Headings and labels almost never are. Mapping: [`register-json-rte` § Which component for which field](register-json-rte.md#rte-field-to-component).

   **A hardcoded literal is still an atomic.** `<h1>Join our rewards</h1>` becomes a `string` atomic bound to a CT field. That's precisely how the author gains the ability to edit it. Leaving literals in code is the single biggest source of "why can't I change this text".

3. **Classify wrappers as Layer-2 containers with slots.** A `<div>`/`<section>` that exists for layout (grid, two-column, card shell, band with a background) becomes a registered component with a **`slot` prop**, not a hardcoded parent. The layout stays in your code (where the design system lives). What goes inside becomes author-controlled. See [`use-section-slot`](use-section-slot.md).

4. **Every `.map()` is a list, but check WHAT it iterates before calling it a Repeater.** Two different answers, and getting it wrong models runtime data as content:

   | The `.map()` iterates | It is | Skill |
   |---|---|---|
   | A **CMS field** on the entry: Modular Blocks, multi-Reference, multi-Group, scalar list (`entry.modular_blocks.map(…)`) | **Repeater** bound to that field, item shape as its own child Section | `build-repeating-section`, `use-repeater` |
   | Items whose type varies per entry (Modular Blocks, multi-CT references) | Repeater **+ a Condition Block per type** | `use-condition-block` |
   | **Runtime / external data**: a fetch result, search results, cart contents, anything in `useState` (`searchResults.map(…)`) | **Not a Repeater and not a CMS field.** The component owns it. Feed it through the `data` prop | `wire-external-data` |

   **Modeling runtime results as a CMS field is a real failure mode**, not a harmless mismatch. Flight-search results or an API response have no entry to bind to. You'd be creating content fields nobody can populate. Test: could an author edit these items in Contentstack? If no, it's external data.

   Iterating with a fixed index (`items[0]`, `items[1]`, `items[2]`) over a CMS field is the Repeater case wearing a disguise. Decompose it as a Repeater, not three atomics.

   **A partially-handled block list is a bug worth surfacing.** Code like `if (block.hasOwnProperty("marquee")) return <Marquee …/>` renders **nothing** for every other block type, silently. Enumerate the CT's block types and give each a Condition Block, or state explicitly that the others are unsupported.

5. **Draw Layer-3 Section boundaries: one per recognizable page part.** A Section is a hero, a form band, a feature grid, a CTA strip. **One Section for a whole page is a defect, not a shortcut.** If your boundary list has one entry and the page has visibly distinct regions, go back to step 1.

   Boundary test, in order:
   - Could a person point at it and name it? If yes, it is its own Section.
   - Could it plausibly appear on another page? If yes, it is definitely its own Section.
   - Does it read from a different part of the entry (a group, a reference, a block list)? If yes, it is its own Section, scoped to that field.

6. **Dedupe against what already exists.** Before proposing anything new, check the codebase and Studio for pieces that already cover it: `grep -rl "<Heading\|<Text\|<Image" src` for atomics already registered, plus the Studio-side reuse inventory, [`match-existing-pattern`](match-existing-pattern.md) § Step 1b, which groups existing Sections by `linked_schemas` and ranks the component palette by real usage. **Both halves, not just the grep.** The codebase says what is registered. Only the project says what is used, and an atom nothing uses is not a convention to build on. Two Sections that differ only in spacing are one Section with an exposed prop, not two.

7. **Emit the binding map: one atomic prop, one CT field.** This is what fixes the binding complaints:

   ```
   Hero band  (Section, scoped to entry.hero group)
     Image      image       → entry.hero.image        (imageurl)
     Heading    headline    → entry.hero.headline     (string)
     Text       body        → entry.hero.body         (string)
     Link       cta         → entry.hero.cta.href     (href)
   ```

   **A single prop taking the whole object is the failure mode**, not a shortcut. `content: { type: "any" }` fed the `hero` group renders blank. The binder recursively unwraps single-key objects for every type except `object`/`array`. Bind field-by-field. Use `object`/`array` only when the component genuinely consumes a whole group or list.

8. **Print the breakdown, then hand off.**

   ```
   DECOMPOSITION — <component path>

   Was: 1 component rendering the whole page.
   Now: <N> Sections · <M> Layer-1 atomics · <K> Layer-2 containers

   Sections (build in this order):
     1. <Hero band>        scope: entry.hero        reusable on: any page with a hero
        atomics: Image, Heading, Text, Link
     2. <Offers list>      scope: entry.offers      Repeater + child Section per offer
        atomics (child): Image, Heading, Text
     3. <Signup form>      stays one registered component — interactive

   Reused, not rebuilt:
     <Heading / Text / Image already registered — no work>

   New CT fields needed:
     <entry.hero.headline (string), entry.hero.image (file), …>
   ```

   Then run [`register-component`](register-component.md) for each atomic and container not already registered, [`design-section-from-jsx`](design-section-from-jsx.md) if a Section's linked schema doesn't exist, [`build-section`](build-section.md) per Section in the printed order, and [`build-repeating-section`](build-repeating-section.md) for any list. If a plan is in flight, feed this breakdown into [`plan-studio-architecture`](plan-studio-architecture.md) Step 2 rather than building straight away.

## Worked example: a page component becomes four reusable pieces

```jsx
// Before — one component, nothing reusable
export function RewardsPage({ data }) {
  return (
    <main>
      <section className="hero">
        <img src={data.heroImage} />
        <h1>Join our rewards</h1>              {/* hardcoded */}
        <p>{data.heroBody}</p>
        <a href={data.ctaHref}>Sign up</a>
      </section>
      <div className="grid">
        {data.offers.map((o) => (
          <article key={o.id}><img src={o.icon} /><h3>{o.title}</h3><p>{o.text}</p></article>
        ))}
      </div>
      <RewardsSignupForm categories={data.categories} />
    </main>
  );
}
```

| Piece | Layer | Becomes |
|---|---|---|
| `<img>`, `<h1>`, `<p>`, `<a>` in `.hero` | 1 | 4 atomics, one CT field each, including the hardcoded `<h1>`, now editable |
| `.hero` wrapper | 2 | Hero band container (layout stays in code) |
| `.grid` + `.map()` | 3 | **Offers list** = Repeater over `entry.offers` + child **Offer card** Section |
| `<article>` internals | 1 | 3 atomics on the child Section, reusable wherever a card appears |
| `RewardsSignupForm` | 2 | Stays one registered component: interactive, plus an `action` prop so an author picks the submit behavior |

**Result:** 3 Sections (Hero band, Offers list, Signup form) + 1 child Section (Offer card), 7 atomics, all reusable on any future page. Before: one block an author could not rearrange, reuse, or restyle.

## Every atom is born with its CSLP tags: not retrofitted

An atom that renders correctly but carries no `data-cslp` is invisible to Visual Editor: authors can see it and cannot click it. Nothing errors, so it ships. A real audit of 19 atomic components found **0** carrying the node-level tag.

So write the tags into the atom as you create it. This is the shape for **every** atom this skill produces, two attribute bags, always both:

```tsx
// The template. `studioAttributes` on the root, one `$`-twin per bindable prop.
type Props = {
  headline?: string;
  $headline?: Record<string, string>;   // injected by the SDK, never built by hand
  studioAttributes?: Record<string, string>;
};

export default function AtomHeading({ headline, $headline, studioAttributes, ...rest }: Props) {
  return (
    <h2 {...rest} {...studioAttributes} {...$headline}>
      {headline}
    </h2>
  );
}
```

| Bag | Spread on | Without it |
| --- | --- | --- |
| `studioAttributes` | the atom's **root** element | the node cannot be selected on canvas or in VB |
| `$<prop>` | the element rendering that prop | that field has no inline click-to-edit |

Three rules that follow, and they are not optional:

1. **One root element per atom.** A fragment (`<>…</>`) has nowhere to put `studioAttributes`. If an atom genuinely cannot have a single root, register it with `wrap` instead.
2. **Root only.** Spreading `studioAttributes` on an inner element makes Studio measure the wrong box, so selection and drop-targeting land in the wrong place.
3. **Never hand-build a `$`-twin.** It arrives as a prop when the field is bound. Constructing one yourself produces a tag pointing at nothing.

The full contract, the `wrap` alternative and the `cslp: { appendTags: true }` prerequisite live in [`register-component` § The `studioAttributes` contract](register-component.md). Do not restate them, but do not ship an atom without them either.

## Inputs needed from the user

1. `componentPath`: the component to decompose. If they point at a route file, decompose the page component it renders.
2. `entryShape`: the content type / entry the page reads from, if it exists. Without it, propose the CT fields in step 7 and hand them to `design-section-from-jsx`.
3. Nothing else. Don't ask which parts to split. Propose the breakdown and let them correct it.

## Acceptance

- [ ] The **render tree** was read, not just the prop list.
- [ ] **Every atomic component carries its CSLP tags**: `studioAttributes` spread on the root element **and** `wrap: false` in its register entry and each bindable prop's `$`-twin spread on the element rendering it. Verified in the DOM, not assumed: the root and each bound text/image element must show `data-cslp`. Without this the atom renders correctly but is invisible to Visual Editor and Live Preview. See [`register-component` § The `studioAttributes` contract](register-component.md) and § The `$`-twin contract.
- [ ] **Every leaf is an atomic with exactly one content field**, hardcoded literals included.
- [ ] **Every `.map()` was classified before being converted**: a CMS field becomes a Repeater (+ Condition Block for varying types), runtime or external data becomes the `data` prop, **not** a Repeater. No runtime list was modelled as a CMS field.
- [ ] **Partially-handled block lists were surfaced**: every block type has a Condition Block, or the unsupported ones are stated.
- [ ] **More than one Section**, unless the page genuinely has one region, and if it's one, that's stated with a reason.
- [ ] Every atomic prop binds to **exactly one CT field**. No prop takes a whole object except a deliberate `object`/`array`.
- [ ] Existing atomics and Sections were **reused, not duplicated**.
- [ ] Interactive parts stayed inside a registered component, with `action` props where an author should choose behavior.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Registering the page component whole because "it's used on one route" | Reuse count is a prioritization signal, not a qualification gate. A one-off page component is the **strongest** decomposition candidate. It's where the monolith is | Decompose first, then register the parts. See `discover-sections` § scoring |
| Reading props instead of the render tree | Props describe today's caller. The reusable pieces are in what the component renders | Walk the JSX return value |
| Leaving hardcoded copy in code | Authors then can't change it and file it as a bug. "Why can't I edit this heading" is almost always a literal that was never made an atomic | Every literal string/image becomes an atomic bound to a CT field |
| `.map()` kept as a hardcoded list | Content can't grow, adding a fourth offer needs a developer | Repeater + child Section (+ Condition Block for blocks/references) |
| Turning a **runtime** `.map()` into a Repeater: search results, a fetch response, `useState` contents | There's no entry behind it, so you create CMS fields nobody can populate and the Repeater binds to nothing | Ask "could an author edit these items in Contentstack?" If no, use `wire-external-data`'s `data` prop |
| Converting a block list that only handles one block type | The other types render nothing today and will keep rendering nothing, the gap just moves into Studio | Enumerate the CT's block types. One Condition Block each, or say which are unsupported |
| One Section for the whole page | Nothing to reorder, nothing reusable, and the author never meets slots or repeaters | One Section per recognizable region. One-Section pages need a stated reason |
| One coarse prop taking the whole object (`type: "any"`) | The binder recursively unwraps single-key objects for every type except `object`/`array`, the component renders blank with no error | Bind field-by-field. `object`/`array` only when the component truly consumes a group or list. See `register-component` § The `any` flatten trap |
| Splitting on styling differences | Two "different" heroes that differ by padding become two Sections to maintain | One Section + an exposed prop, see `expose-section-props` |

## See also

- [`decompose-design`](decompose-design.md): the Layer-1/2/3 taxonomy this applies
- [`decompose-design`](decompose-design.md): the Layer-1/2/3 taxonomy this applies
- [`decompose-design`](decompose-design.md): same taxonomy, visual input instead of code
- [`discover-sections`](discover-sections.md): which components recur across routes. Run this after decomposition
- [`design-section-from-jsx`](design-section-from-jsx.md): derive a Section's linked schema once boundaries are drawn
- [`register-component`](register-component.md): register each atomic and container. Prop types and the `any` trap
- [`build-repeating-section`](build-repeating-section.md) · [`use-section-slot`](use-section-slot.md) · [`expose-section-props`](expose-section-props.md)
