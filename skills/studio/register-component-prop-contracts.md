---
name: register-component-prop-contracts
---

## When to use

The prop-shape contracts a registered component must honour: array and object binding rules, why the live site fetches only the fields bindings name, image (`<file_field>.url`) and link signatures, and why `{{entry.title}}` does not resolve outside a Connected template URL pattern.

Part of the component-registration set. Start at [`register-component`](register-component.md), which routes here.

## Array & object props: binding rules

`array` and `object` **do** bind to CMS fields, but under specific conditions that are easy to miss. Registering a `type: "array"` prop and expecting the picker to bind it to any Reference field will silently degrade to a manual-entry sub-field in cases the SDK doesn't cover. Two paths:

**Bindable: `type: "array"` bound to a multi-value field.** The SDK reads the bound array directly, the array arrives at the component populated, and the component renders items with its own `.map()`. No Repeater, no Condition Block. Valid sources:

- **Reference multi (or single)**: needs `data_sources.resolvedReferences` on the composition so CDA returns `?include[]=<field>`. Otherwise the array arrives as `{ uid }` stubs. This is the case that catches migrators. It's easy to bind and see stub UIDs render, missing the resolvedReferences step.
- **Group multi (`multiple: true` on a Group field)**: the group values are stored on the entry itself. No resolution needed. Array arrives populated as-is.
- **Modular Block**: the block payload is on the entry. No resolution needed. Note that Modular Blocks are polymorphic (each item can be a different block type). If your `.map()` renders every item the same, the array-prop path works. If it needs per-block-type rendering, use a Repeater + Condition Block instead (see below).
- **Scalar multi-values**: a `multiple: true` single-line-text field arrives as an array of strings. No resolution needed.

Common requirements across all four:

- The prop is `type: "array"` on the registration.
- The wrapper's per-item render works against the shape delivered by the CMS for that field type.
- The list is single-shape (no per-iteration variant authoring or template-author swap).

This is the **preferred path** for wrapping an existing production component whose interface already takes an array of items. See `build-repeating-section` § When to skip the Repeater entirely: the array-prop alternative.

**Layout fidelity (not just data shape) decides Repeater vs array-prop.** A Repeater renders items **uniformly in sequence**. It cannot reproduce a bespoke or asymmetric layout (a bento mosaic, a 1-big-plus-3-small grid, a carousel). When the list is interactive, or its layout depends on item position or count (the component computes its values), bind the whole array/object to the real component (`array` / `object`) and let its own markup + CSS run; this is the exception the [Section rule](SKILL.md#section-rule) allows, not a default for keeping the production layout verbatim. The render is pixel-identical to the live site, provided every field the component reads reaches it (see § Studio fetches only the fields your bindings name). Reach for a Repeater only when the layout genuinely IS a uniform list, or when items are polymorphic and need per-type rendering (Repeater + Condition Block).

**Bindable: `type: "object"` bound to a matching entry Group / Global Field.** Same idea for a single-entry-object shape (a nested `cta: { label, href }` binding into an entry Group with matching sub-fields). Groups live on the entry, no `resolvedReferences` step.

**From SDK 2.0, an `object` prop must declare `properties`.** The same holds for a group, a global field, or a modular block bound as an object. List each sub-field the component reads (`cta: { type: "object", properties: { label: { type: "string" }, href: { type: "href" } } }`).

**When array/object won't fit: reach for the Repeater or the adapter pattern.** If the list iterates a **Modular Block** (polymorphic, each item can be a different block type), template authors need to **swap a different child Section per template instance**, or the production leaf's shape doesn't reduce cleanly to array-item scalars, use one of:

- **`build-repeating-section`**: greenfield parent+child+Repeater pattern with a Section Slot for template-author swaps.
- **`adapt-collection-component`**: compatibility-adapter pattern for wrapping a legacy production component whose leaf can't be simplified.

Both surface author variability the array-prop path can't. Choose by the constraints above, not by default.

The narrow non-CMS use for `type: "array"` / `type: "object"` remains: authoring-time-only configuration where a marketer should type values in by hand (e.g. a "tags" prop not stored in CMS).

**Before you register a whole-array/object component (a `Card Grid` / `Article Grid` that `.map()`s internally), confirm a matching multi-valued field exists on the CT it will bind against.** A single array prop collapses the entire list to **one binding point**. Studio never exposes the per-item fields, so binding correctness rests entirely on that one array field resolving. If the target CT has **no** multi-Reference / Modular Block / `multiple:true` Group / scalar-multi to feed it (e.g. an `Article List` page CT that holds only `Title`/`URL`/`SEO` and references its articles nowhere), the prop has nothing to bind to and the component renders its `defaultValue` array forever, placeholder cards that read as real content in Design Mode. Two correct moves:
- **The source lives in a different CT** (articles, products): add a multi-Reference on the page CT ([`migrate-ct-schema`](migrate-ct-schema.md)) or pin a query ([`pin-query-to-freeform`](pin-query-to-freeform.md)) **before** binding, or
- **Prefer atomic + Repeater**: register the leaf card's fields as atomic components and iterate with a Repeater + child Section ([`build-repeating-section`](build-repeating-section.md)), so per-item binding is visible and verifiable in Studio rather than hidden inside one array prop.

`build-section` Step 5e enforces this at bind time. Catching it at registration saves a round trip.

### Lists passed as a prop

An array prop renders, but its items are only editable in Visual Editor if the component spreads their tags. Studio sends `$<prop>` for the whole list and `$<prop>Items`, an array with one tag per item. Spread `$<prop>` on the list's wrapper and each item's tag on its element, through the `itemTag` helper. Declare both:

```tsx
import type { Cslptag } from "@contentstack/studio-react";

interface GalleryProps {
  images?: { url?: string; description?: string }[];
  $images?: Cslptag;
  $imagesItems?: Cslptag[];
}
```

```tsx
<ul {...$images}>
  {images.map((img, i) => <li key={img.url ?? i} {...itemTag($imagesItems, i)}>…</li>)}
</ul>
```

Fields inside each item carry their own tags under `item.$`. Without `itemTag`, studio-registry 2.0.1's item tags (`<field>.$0`) show "Invalid CSLP tag" in Visual Editor and the list has no "+". The helper, the full pattern and the check are in [`register-component-cslp` § Lists passed as a prop](register-component-cslp.md#lists-passed-as-a-prop).

## Studio fetches only the fields your bindings name

On the live site the SDK does not fetch whole entries. It builds the Delivery API query from the composition's bindings: `include[]` for the references they cross, and an `only[]` projection listing the fields they name. **Inside the Studio canvas and Visual Builder it skips the projection and fetches every field.** So a component that reads fields no binding names renders correctly while you author, then receives a stripped object on the published page: a product card bound to a whole referenced entry got `{ uid }` with no title, price or images, and nothing logged an error.

**Prefer one binding per field.** Register the leaves the component renders (`title`, `price`, `image` → `product.image.url`, `imageAlt`) instead of one `object` prop for the whole entry. Each binding adds its field to the projection, and each field gets its own `$`-twin for Visual Editor.

**When a component genuinely needs the whole entry** (a production card that reads a dozen fields, or a computed price), the options in `@contentstack/studio-react` 2.0.1 are:

| Option | How | Caveat |
|---|---|---|
| Name the extra fields in `extendQuery` | Pass `{ extendQuery: { "<content_type_uid>": { only: [["<reference_field>", "title"], ["<reference_field>", "price"]] } } }` as the options argument of `fetchCompositionData` / `useCompositionData`. A plain string means a field on the entry itself (`["BASE", "<field>"]`). The key is the content type of the entry being fetched: the template's connected type, or a pinned entry's type | **Deprecated.** 2.0.1 still merges these `only` pairs into the projection, but logs "`extendQuery` is deprecated and will be removed in the next major". Its "tick the references in Studio" advice covers `include[]`, not field projection. No replacement for per-field projection exists in 2.0.1 that we could confirm |
| Fetch the data yourself | Fetch the entry in the app and pass it through `data` ([`wire-external-data`](wire-external-data.md), [`render-with-own-data`](render-with-own-data.md)) | The fields are no longer bindable in Studio for that prop |

**Verify outside the editor.** Open the published route in a plain browser tab (not the canvas, not Visual Builder) and check the component's props, or the Delivery API request's `only[...]` parameters in the Network tab. An editor-only check cannot catch this.

## Image props: always bind `<file_field>.url`, alt text separately

**The binding rule.** Bind every `imageurl` prop to the file field's **`.url`** leaf (`hero_image.url`, or `images.0.url` for the first of a multiple file field), never to the file field itself. A file field is an asset object (`{ uid, url, filename, title, description, … }`), and in 2.0.1 `imageurl` accepts **only a string**: a bound asset object is reported as a type mismatch ("Data Mismatch Found" in the editor, a console warning on the live site) and the image renders nothing. **Alt text is a second prop**: a `string` prop (`imageAlt`) bound to the asset's `description` (or `title`), so the image and its alt are each one binding.

```ts
props: {
  image:    { type: "imageurl", displayName: "Image" },      // bind → hero_image.url
  imageAlt: { type: "string",   displayName: "Image alt" },  // bind → hero_image.description
}
```

**Defense in depth: still accept `string | { url }`.** Bindings authored before this rule, or by hand through the API, can still point at the object. If the component's TypeScript signature demands one shape, the other silently fails: icons "map correctly" but render invisible, or the object gets `.toString()`'d and the URL area shows `[object Object]`. Both bugs ship to production without a warning.

Contract for every `imageurl` prop:

```tsx
type ImageProp = string | { url?: string } | null | undefined;

function coerce(img: ImageProp): string | undefined {
  if (!img) return undefined;
  return typeof img === "string" ? img : img.url;
}
```

Every registered component's `imageurl` prop declares its TS type as `string | { url?: string } | null | undefined`, and the component internally calls a coerce helper (or inlines `typeof img === "string" ? img : img?.url`. Never `img?.url ?? img`: an asset object with no `url` falls through to the object itself and renders `[object Object]`). This is a first-class contract, peer of the null-safety and `$`-twin contracts, not a pitfall row. The coercion is the safety net. The `.url` binding is the rule.

## Tolerant link signatures: bind the leaves, not the whole link object

Contentstack's `link` field is a two-property object: `{ title: string; href: string }`. Studio's picker binds each leaf separately. A component with an `href`-typed prop expects a URL string, not the whole link object. Binding the object silently ships `[object Object]` into the DOM.

Contract for every navigable component:

- **`href`-typed prop**: TS type: `string | null | undefined`. Never accept `{ href: string }`. Bind against `linkField → href`.
- **Label**: separate `string` prop bound against `linkField → title`.
- **A single object prop for the whole link is an anti-pattern.** If the design conceptually has one "link" object, still register the leaves as separate props (`ctaLabel: string`, `ctaHref: href`) and let the picker bind each. Two clicks in the picker, zero mystery renders.

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

## `{{entry.title}}` and other unresolved placeholders: what a Connected template URL pattern resolves depends on `url_metadata.url_source`

Which placeholders a Template URL Pattern resolves depends on the composition's `url_metadata.url_source`:

- **`content_type_url_pattern` or `legacy_url`**: Studio matches the request path against the CT's `url` field only. **`{{entry.url}}`** is the one placeholder that resolves.
- **Pattern sources (`user_specified_pattern`, `default_url_pattern`)**: the SDK matches the request path against the pattern and queries on each variable: entry fields (`{{entry.slug}}`), a field of an included reference, `{{taxonomy:<uid>}}`, and `{{entry_created_date:year}}`-style dates.

A variable the SDK doesn't recognise (`{{author.name}}`) is never processed, and a placeholder anywhere other than the URL pattern is left **literal in the response**. The SDK does not template-expand it.

Where this bites:

- Composition **canonical URL** field with `{{entry.title}}` renders literally in the `<link rel="canonical">` tag. Google indexes the literal string. SEO ranking dies silently.
- Template preview iframe URL with a non-`{{entry.url}}` placeholder never resolves. Iframe stays on the placeholder URL.
- OG image / social preview URLs with placeholders produce broken share cards.

```
URL Pattern: /blog/{{entry.url}}      ✓ resolves to entry.url (any url_source)
URL Pattern: {{entry.url}}            ✓ site root only (entry url "/"). Every other template needs a prefix
URL Pattern: /blog/{{entry.slug}}     ✓ only with a pattern source (user_specified_pattern / default_url_pattern); ✗ with content_type_url_pattern / legacy_url
URL Pattern: /author/{{author.name}}  ✗ not a recognised variable, never resolves
```

If you need a title-based slug, populate the CT's `url` field with the slug at entry time (Contentstack workflows / hook / manual), do not template-expand at render time.
