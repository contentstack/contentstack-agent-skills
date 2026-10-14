---
name: adapt-collection-component
---

## When to use

Adapt an existing production wrapper into a Studio-compatible List Section by decomposing it into a wrapper Section (with `slot`) + Repeater + leaf adapter that wraps the real production card. This is the **compatibility-adapter path**: reach for it only when the native array-prop path (see below) won't work.

Use when the production wrapper's leaf takes an object shape that can't easily be reduced to scalars, when template authors need to swap different leaf Sections per template instance (Section-Slot semantics), or when the list iterates a Modular Block (polymorphic: Condition Blocks needed). Phrases: my wrapper needs template-instance swaps, per-CT rendering inside a list, migrate a carousel to Studio, wrap a legacy band in a List Section. Do NOT use if the production component already accepts an `array` prop and no per-instance swap or polymorphism is needed, use `build-repeating-section` § When to skip the Repeater entirely: the array-prop alternative instead (simpler, native, no adapter).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Adapt a production collection-shaped component into a Studio List Section

## Which path?: decide before you build

Studio has two ways to render a CMS collection through a production wrapper. Pick before writing any adapter:

**Path A: native array prop** (`build-repeating-section` § array-prop alternative). Register the production wrapper with a `type: "array"` prop, bind that prop to a Reference field on the section's linked schema, populate `data_sources.resolvedReferences`. The SDK's data-binder reads the bound array and delivers full resolved entries. The component does its own `.map()`. No Repeater, no Condition Block. Simpler and native.

Use Path A when: the production wrapper already accepts an `array` prop of full entry-like objects. The list iterates a **single Reference field** (one CT, no per-item polymorphism). Template authors don't need to swap the child Section per template instance. You don't need Studio Preview Mode to show N rendered children on the canvas.

**Path B: compatibility adapter** (this skill). Decompose into a wrapper Section registered with a `slot` prop + Repeater + leaf adapter. Use when Path A doesn't fit.

Use Path B when any of these are true:

- The list iterates a **Modular Block**, needs Condition Blocks per block type.
- Template authors need to **swap a different child Section per template instance** via the Section Slot.
- The production leaf's interface is object-shaped in ways that don't reduce cleanly to `array` items (nested objects, per-item variant flags Studio needs to expose to authors).
- You need Studio to show **real iteration preview** of N rendered children on the canvas (Preview Mode).

If Path A works, use it. This skill covers Path B: the migration path when the leaf can't be simplified into an array-item shape.

## Context (Path B)

The Path B decomposition:

- The **wrapper** (band chrome, layout container, header, CTA) becomes a registered component with a `slot` prop plus scalar props for header/CTA overrides. This is a Simple Section-shaped registration (scalar props all the way) that a List Section will drop a Repeater into.
- The **iteration** (looping over items) becomes a Repeater dropped into the wrapper's slot at template-authoring time, bound to the multi-value field.
- Each **leaf** (one card) becomes a registered adapter with scalar props, wrapping the real production card 1:1.

The leaf is the interesting reuse point: because leaf props are scalars, the Studio adapter just imports and renders the production card verbatim. Layout drifts at the wrapper. Leaf pixels stay identical.

## Task

1. **Inventory the target component.** Read the production component + every call site. Record: which props are arrays/objects vs scalars, what layout the wrapper does (grid vs carousel vs stack), what per-item props the leaf card takes, and any data transforms the call site does before passing `items` (subtitle composition, per-CT image fallbacks, URL building, defaults). Every literal prop value at every call site is a preset the marketer will otherwise lose.

2. **Split into three registrations.** Draw the decomposition explicitly before writing code:

   | Layer | What it does | Registration shape |
   |---|---|---|
   | **List Section wrapper** (wrapper) | Owns background, heading area, "View more" CTA, and the layout container (grid tracks, or the carousel scroll-viewport CSS) | Component with a `slot` prop for its main region + `imageurl`/`string`/`href`/`choice` props for header/CTA overrides |
   | **Iteration** | Loops over the bound multi-value field | Not a component. It's a Repeater the template author drops into the band's slot |
   | **Leaf adapter** | Renders one item | Component whose props are exactly the leaf card's scalars, mirror the production `Card`'s interface |

3. **Register the leaf card first.** Import the production leaf card into a thin adapter and re-export it registered with scalar props. If the production leaf takes an object (`item: { title, url, image }`), the adapter destructures to scalar props (`title`, `url`, `imageUrl`) and constructs the object for the real card internally. Every scalar prop gets a `defaultValue` for palette preview.

   ```tsx
   // studio-adapters/GlossaryCardAdapter.tsx
   import { CaseStudyCard } from "@/components/cards/CaseStudyCard";

   export function GlossaryCardAdapter(props: {
     title: string; url: string; imageUrl: string; description?: string;
     isInteractive?: boolean;   // ← literal from the live call site — critical
   }) {
     // Reconstruct the shape the production card expects.
     return <CaseStudyCard item={{
       title: props.title,
       url: props.url,
       image: { url: props.imageUrl },
       short_description: props.description,
     }} isInteractive={props.isInteractive ?? true} />;
   }
   ```

   **Import the real leaf, never reimplement it.** The whole point of this pattern is that leaves stay pixel-identical. A reimplementation defeats the purpose.

4. **Register the List Section wrapper with a `slot` prop.** The band owns everything around the iteration. The slot is where the Repeater lands.

   ```tsx
   // studio-adapters/GlossaryCardBand.tsx
   export function GlossaryCardBand({ heading, subheading, ctaLabel, ctaHref, items }: {
     heading: string; subheading?: string; ctaLabel?: string; ctaHref?: string;
     items: React.ReactNode;   // slot
   }) {
     return (
       <section className="…same classes the production band uses…">
         <header className="max-w-200 gap-4">
           <h2 className="h1-display-compact">{heading}</h2>
           {subheading && <p>{subheading}</p>}
           {ctaLabel && ctaHref && <a href={ctaHref}>{ctaLabel}</a>}
         </header>
         <div className="pl-4 sm:pl-6 [&>*]:basis-[90%] sm:[&>*]:basis-1/2 md:[&>*]:basis-1/3">
           {items}
         </div>
       </section>
     );
   }
   ```

   Transcribe the production wrapper's CSS **line by line**. Every class (heading typography, gap, padding, item basis, peek percentages, breakpoint splits) is a drift risk if approximated. A `// KEEP-IN-SYNC WITH <ProductionBand>` comment on both files is the minimum viable version-control gate until the visual-parity skill lands (`verify-visual-parity`).

5. **In the section, drop a Repeater into the band's slot** and bind the Repeater's source to the multi-value entry field. Inside the Repeater, drop the leaf card adapter and bind each of its scalar props to the item's fields. If the field can hold multiple content types (a heterogeneous Reference or Modular Block), wrap the leaf adapter in a Condition Block with one branch per type. See `use-condition-block`.

6. **Preserve display logic that lived at the call site.** The production call site often normalizes data before passing to the wrapper (subtitle composition, image fallbacks per CT, URL building). Studio's binding is a bare `field → prop` path. It has nowhere to put that logic. Route each piece to the right home:

   | Call-site logic | Where it goes in Studio |
   |---|---|
   | `props.copy = entry.short_description ?? entry.description` | Inside the leaf adapter: accept `copy` as prop, adapter re-routes to the right field. Or: expose both as separate props and let a preset choose. |
   | `subtitle = "Related to " + entry.title` | Static text on the band, OR bind a `string` prop to the page entry once page-scope binding is available. Until then: static text with a note in the migration doc. |
   | `image = entry.tile_data?.thumb ?? entry.image` | Per-branch Condition Block bindings: each branch points at the right path for that CT. |
   | Boolean flags set by the call site (`isInteractive={false}`, `isLogoBgWhite={false}`) | Registered as scalar props with the call-site literal as `defaultValue`. Missing this is the #1 cause of "looks similar but off." |

7. **Carry every literal prop from every call site into `defaultValue` or a preset.** Grep the codebase for every JSX use of the production wrapper. Each literal (`variant="compact"`, `columns={3}`, `showRating={false}`) becomes either a `defaultValue` on the adapter's corresponding prop, or a named preset. Skipping this is what makes the composed page "look 80% right". A missed `isInteractive={false}` literal is a typical example.

8. **Match the CSS mechanism the production band uses.** Carousels are the classic trap:

   | Production mechanism | Studio adaptation |
   |---|---|
   | Embla / Swiper (JS library that measures children) | Repeater wraps each iteration in `display:contents`, so JS libraries see zero-width items and break. Use a **CSS-only** carousel (scroll-snap + `overflow-x: auto` + item `flex-basis` with peek), OR wrap each iteration in a real DOM element (a product gap; report it to Contentstack). |
   | CSS Grid | Grid tracks on the band's slot container, leaf just fills its cell. |
   | Flexbox with `flex-wrap` | Same layout on the slot container. Leaf renders `width: 100%`. |

   For the carousel case: gap-subtracted `flex-basis` (`calc(90% - var(--gap))`) prevents the last item peek from being cropped by the container's right padding.

9. **Verify per band with the visual-parity skill.** Run `verify-visual-parity` at authored data (real entries pinned) for each band as it lands, not once at the end. Drift compounds if you defer verification. Catching it band-by-band is 10× faster than debugging a whole page.

## Inputs needed from the user

1. Path to the production wrapper component (the one taking an array/object prop).
2. Path to the production leaf card.
3. The entry field the collection binds to (Reference / Modular Block / multi-Group).
4. Any call sites of the production wrapper that carry literal props (grep-able list).

## Acceptance

- [ ] List Section wrapper registered with a `slot` prop for the iteration region + scalar props for header/CTA.
- [ ] **Every generated component carries its CSLP tags**: `studioAttributes` spread on the root element **and** `wrap: false` in its register entry, and each bindable prop's `$`-twin spread on the element rendering it. Confirmed in the DOM: the root and each bound text/image element show `data-cslp`. Without it the component renders but Visual Editor and Live Preview cannot edit it. See [`register-component-cslp` § The `studioAttributes` contract](register-component-cslp.md).
- [ ] Leaf adapter registered with scalar props only. Imports the production leaf verbatim (no reimplementation).
- [ ] Every literal prop from every production call site is preserved as a `defaultValue` or preset.
- [ ] Wrapper CSS transcribed line-by-line from production. Both files carry a `KEEP-IN-SYNC` comment naming the counterpart.
- [ ] Repeater bound to the multi-value field. Heterogeneous fields wrapped in a Condition Block (see `use-condition-block`).
- [ ] Carousel bands use CSS-only mechanisms (scroll-snap + `flex-basis`), not JS libraries that measure children.
- [ ] `verify-visual-parity` run against a pinned entry with real data. Drift classified and closed band by band.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Reimplementing the leaf card in the adapter | Diverges from production immediately. The "same code, same pixels" property is lost | Import the production leaf and pass reconstructed props. Never re-write. |
| Skipping the call-site literal sweep | Production sets `isInteractive={false}`, `variant="compact"`, etc. The adapter registers these as `defaultValue: true` (framework default). Rendered page has correct data but wrong behavior. | Grep every JSX use of the production wrapper. Carry every literal into `defaultValue` or a preset. |
| Approximating wrapper CSS classes | Heading typography drifts (`cs-h2` vs `h1-display-compact`), item basis peeks wrong, gaps mismatch | Transcribe class-by-class, add a `KEEP-IN-SYNC` comment naming the production file. |
| Using Embla/Swiper inside a Repeater | Repeater's `display:contents` wrappers zero out item widths, so the library computes garbage | CSS-only carousel (scroll-snap + `basis` + `overflow-x`). Or file the real-DOM Repeater option (product gap). |
| Data normalization dropped on the floor | Production composed subtitles / per-CT image fallbacks / URL builders lived at the call site. Studio's bindings are bare paths, so the logic silently disappears | Route each transform per the decision table in Step 6 (adapter / static / Condition Block branch / product-gap flag). |

## See also

- `build-repeating-section`: the greenfield flavor of List Section authoring (no production wrapper to preserve).
- `understand-sections`: Simple Section vs List Section distinction. How they compose.
- [`register-component-prop-contracts`](register-component-prop-contracts.md) § Array & object props: binding rules: why arrays/objects don't bind. When to reach for this skill instead.
- `use-repeater`: how to bind the Repeater to the multi-value field.
- `use-condition-block`: required inside the Repeater when the field is heterogeneous.
- `use-section-slot`: how to carve the slot the Repeater drops into.
- `verify-visual-parity`: verification loop. Run per List Section, not once at the end.
