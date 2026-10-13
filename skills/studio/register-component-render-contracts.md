---
name: register-component-render-contracts
---

## When to use

Two rules a registered component must satisfy to survive the canvas: stay layout-agnostic, and render null-safe when a binding resolves to nothing.

Part of the component-registration set. Start at [`register-component`](register-component.md), which routes here.

## Layout contract: registered components must be layout-agnostic

A registered component is dropped by template authors into Sections, Section Slots, Repeaters, and other contexts the component author never anticipated. The component must render correctly across those contexts without depending on a specific ancestor.

The rule, from standard CSS architecture (BEM, Every Layout, Atomic Design, separation of concerns between layout and content):

- **The component renders at `width: 100%` of whatever container it's placed in.** It fills its cell. It doesn't decide how big its cell should be.
- **The component does NOT hard-code a `max-width` to "protect itself"** from being placed in a too-wide container. Hard-coded sizes spread layout decisions into content components and break reuse (a card capped at 300px looks fine in a 4-up grid, ridiculous in a single-product hero, crammed in a 6-up grid).
- **Container queries** (CSS `@container`) are the right tool for size-dependent internal layout inside the component. They let the component adapt to its container without knowing the ancestor.
- **Layout responsibility lives in the parent Section**, not in the component. The Section that owns the Slot / Repeater provides the layout container (grid tracks, flex with `gap` + `flex-basis`, or a `max-width`-constrained Box). The component fills the cell that container defines.

If you find yourself adding `.fs-grid > .fs-card { ... }` overrides to make a card behave inside a grid, the coupling is backwards. The card knows about the grid. Decouple: card stays `width: 100%`, grid (in the parent Section) provides the track.

## Null-safe rendering contract

Bindings resolve at runtime, and may resolve to `undefined`, `null`, an empty string, an empty array, or a placeholder value. Every registered component MUST render without throwing under those inputs.

The SDK's resolution chain: `boundValue ?? staticValue ?? defaultValue ?? placeholder`. If you set `defaultValue` on every prop, MOST cases resolve to a real value, but four paths still surface `undefined`/`null`/empty to your component:

1. **No `defaultValue` and no binding**: picker emits an unbound prop, no static value, no default, so the resolved value is `undefined`.
2. **Binding to a deep optional path**: e.g. `featured_image.0.url` when `featured_image` is an empty array (multi-file field with no upload yet), which resolves to `undefined`.
3. **Binding to an optional reference**: entry exists but the reference field is empty, which resolves to `undefined`.
4. **Empty-string field**: Contentstack stores `""` for cleared text fields. Truthy checks (`if (props.title)`) treat it as missing but JSX renders nothing, safe but easy to confuse with a render bug.

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

- **Optional-chain every nested access**: `props.image?.url`, `props.cta?.[0]?.href`.
- **Nullish-coalesce non-binding renders**: `alt={image.alt ?? ""}`, `count={items?.length ?? 0}`.
- **Decide what "missing" means**: render `null`, render a skeleton, or render a labeled empty state. **Never crash.** Compositions get authored against half-filled entries during preview. One throw kills the whole canvas.
- **Don't rely on `defaultValue` alone.** It's a safety net for unbound props, not for empty entry data.
