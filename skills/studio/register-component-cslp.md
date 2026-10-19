---
name: register-component-cslp
---

## When to use

The two halves of edit-ability: `$` CSLP props that make bound values editable in Visual Editor, and the `studioAttributes` contract that carries the node's own tag and identity. Emit both or neither.

Part of the component-registration set. Start at [`register-component`](register-component.md), which routes here.

## CSLP tags: the `$` props that make bound values editable

Also searchable as: `data-cslp`, `Cslptag`, `$title` / `$image`, `$`-twin, click-to-edit, inline editing, "Visual Builder renders but won't edit".

Full reference: [CSLP tags: the `$` props that make bound values editable](register-component.md).

**Silent-failure #1 in hand-written registered components:** a bindable prop is registered, the component renders the value fine, and **click-to-edit never attaches**. No error, no warning. The page looks finished and authors cannot touch it.

Every bindable prop arrives **twice**: the resolved value under its own name, and the CSLP tag for the field it came from under the same name with a `$` prefix. The `$` prop holds one attribute, `data-cslp`, which is the field's address in the entry. It is the anchor Visual Editer attaches the edit affordance to. Its type is exported as `Cslptag`. You never construct one by hand.

### Two things must both be true

**1. The SDK must be told to emit the tags.** The switch is `cslp.appendTags` on `studioSdk.init`:

```ts
studioSdk.init({ stackSdk: stack, contentTypeUid: "compositions", cslp: { appendTags: true } });
```

Without it **every `$` prop is `undefined`** no matter how correctly the components are written, and no element on the page carries a tag. [`install-studio`](install-studio.md) emits this. If you are registering components into a project someone else wired, grep for `appendTags` before debugging anything else.

**2. Each `$` prop must be spread on the element that renders its value.**

```tsx
import type { Cslptag } from "@contentstack/studio-react";

interface HeroProps {
  eyebrow?: string;
  headline?: string;
  backgroundImage?: string;
  // One `$` prop per bindable prop above.
  $eyebrow?: Cslptag;
  $headline?: Cslptag;
  $backgroundImage?: Cslptag;
}

// ❌ Renders every value, and nothing is editable.
export function Hero({ eyebrow, headline, backgroundImage }: HeroProps) {
  return (
    <section style={{ backgroundImage: `url(${backgroundImage})` }}>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h1>{headline}</h1>
    </section>
  );
}

// ✅ Each `$` prop spread on the element that renders its value.
export function Hero({
  eyebrow, $eyebrow,
  headline, $headline,
  backgroundImage, $backgroundImage,
}: HeroProps) {
  return (
    <section {...$backgroundImage} style={{ backgroundImage: `url(${backgroundImage})` }}>
      {eyebrow && <p className="eyebrow" {...$eyebrow}>{eyebrow}</p>}
      <h1 {...$headline}>{headline}</h1>
    </section>
  );
}
```

The spread has to land on the element rendering the value, not on a parent. A tag on the wrapper makes the whole block one edit target instead of the field.

**Checklist for every component you register:**

- [ ] `studioSdk.init` passes `cslp: { appendTags: true }`.
- [ ] For each bindable prop that renders **visible text or an image**: `$prop` is declared on the props interface as `Cslptag` and destructured.
- [ ] For each `$prop`: `{...$prop}` is spread on the DOM element that renders that prop's content, not on an ancestor.
- [ ] Slot-typed props (`type: "slot"`) hold child nodes, not values, and have no `$` prop.
- [ ] Non-visible props (analytics IDs, aria labels not tied to visible text) don't strictly need one, but adding it costs nothing.

**Verify from the rendered page, not from the source.** `curl -s <url> | grep -c 'data-cslp'`, or DevTools on the composition. Zero tags means `appendTags`. Some fields tagged and others not means those others aren't spreading their `$` prop. A tag reads `<ct_uid>.<entry_uid>.<locale>.<field_path>`, so you can confirm it points at the field you meant.

## The `studioAttributes` contract: the node's own CSLP tag and identity

The `$` props above (also called `$`-twins) cover **fields**. There is a second, separate attribute bag covering the **node**, and missing it is silent in the same way.

For every registered component the renderer passes `studioAttributes`: the node's `data-cslp` plus the `data-composable-studio-*` identifiers Studio uses to locate the node on the canvas. Spread it on the component's **root** element:

```tsx
// ✅ The pattern every built-in SDK component uses (41 of them do this).
export function Number(props: NumberProps) {
  const { studioAttributes, number, $number, ...rest } = props;
  return (
    <p {...rest} {...studioAttributes} {...$number}>
      {number}
    </p>
  );
}
```

Both bags, one component, different jobs:

| Bag | Scope | Spread on | Enables |
| --- | --- | --- | --- |
| `studioAttributes` | the node | the **root** element | node-level `data-cslp`, canvas hit-testing, selection |
| `$<propName>` | one field | the element rendering **that** prop | inline click-to-edit for that field |

### The two halves are one change: emit both or neither

**Every registered component takes `studioAttributes` and is registered `wrap: false`.**

Why this matters. Studio renders a registered component inside a wrapper `<div>` unless its entry says otherwise. That div sits between the styled container the component is placed in and the component's own root, so the CSS around it never reaches the component. A grid or flex parent styles the wrapper, and the component inside it goes unstyled.

Under `wrap: false` Studio hands the component the editor's selection ref and node ids as `studioAttributes` **instead of** putting them on a wrapper. So the two halves are a single change:

1. The component declares `studioAttributes` and spreads it on its root element.
2. Its register entry carries `wrap: false` at the top level, right after `component:`.

Emit both or neither. A component registered `wrap: false` that does not spread them **cannot be selected on the canvas**, worse than the div it was avoiding.

```tsx
import type { StudioAttributes } from '@contentstack/studio-react';

export interface HeroProps { title?: string }

const Hero = ({ title, studioAttributes }: HeroProps & StudioAttributes) => (
  <section className="hero" {...studioAttributes}>
    <h1>{title}</h1>
  </section>
);
```

```ts
{
  type: 'hero',
  component: Hero,
  wrap: false,
  displayName: 'Hero',
  props: { title: { type: 'string', displayName: 'Title', defaultValue: '' } }
}
```

**Where the spread goes.** On the **outermost** element, and **last** (after any `{...props}`) so it wins.

**The root must reach a real DOM node:**

- a plain HTML tag (`<section>`, `<div>`, `<article>`), always correct, prefer this.
- a forwarding component you already pass DOM attributes to (`<Link className={…}>`), acceptable.
- **never** a Fragment (`<>…</>`), and **never** a component you pass only semantic props to (`<Card title={…} />`). The ref would land nowhere.

If the design needs sibling roots, wrap them in one plain element and put the spread there.

**TypeScript.** Intersect the props type with `StudioAttributes` and import it with `import type`. It is a type-only export, and a value import breaks projects on `verbatimModuleSyntax`. A JavaScript component just destructures the name.

**Variants of the same rule:**

| Shape | How the spread is reached |
| --- | --- |
| Props not destructured | `(props: HeroProps & StudioAttributes)`, spread as `<section {...props.studioAttributes}>` |
| Component takes no props | `({ studioAttributes }: StudioAttributes)`, it still takes this one |

`studioAttributes` is **not content**. Never register it as a prop, never give it a CSLP tag, never put it in a `<Slot data={…}>`.

If a later edit rewrites a component's root, carry the spread onto the new root. Never leave the prop declared but unspread, and never leave `wrap: false` on a component that no longer spreads it.

**An existing `wrap` that is not `false`**: `wrap: true`, `wrap: 'section'`, is a deliberate choice about that component's markup. Leave it as written.

**Prerequisite: CSLP must be switched on.** `cslp: { appendTags: true }` gates **both** bags, not just the `$` props: with it absent, `studioAttributes` arrives empty too and no amount of correct spreading produces a `data-cslp`. Check this first when tags are missing everywhere at once, rather than auditing components one by one. See § Two things must both be true above, and [`install-studio`](install-studio.md).

**Retrofitting a component library?** Both halves have to line up, so count them separately, a mismatch is the bug:

```bash
grep -c  "registerComponent"  <file>              # registrations
grep -c  "wrap: false"        <file>              # halves in the registry
grep -rl "studioAttributes"   <components-dir> | wc -l   # halves in the components
```

All three should agree. `wrap: false` outnumbering the spreads is the dangerous direction. Those components are unselectable, where the ones merely missing `wrap: false` still render inside a wrapper.

A real audit of 19 atomic components found **0** spreading `studioAttributes`, so every one of them rendered without a node-level `data-cslp`, and nothing anywhere reported it.

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Spreading `studioAttributes` but not `$prop` | The node is selectable on canvas, but no individual field is inline-editable, looks like Visual Editor "half works" | Spread both. They are different bags with different scopes |
| Spreading `{...rest}` and assuming it carries the tags | `studioAttributes` is its own named prop, not part of `rest`. Destructuring `rest` alone silently drops it | Destructure `studioAttributes` explicitly, as the built-ins do |
| Spreading `studioAttributes` on an inner element | Studio's hit-testing measures the node's root box. On an inner element, selection and drop targeting land on the wrong rectangle | Root element only |
| Component renders a fragment (`<>…</>`) | There is no root DOM node, so the ref lands nowhere and the node is unselectable | Give it one plain root element and spread there |
| `wrap: false` set, `studioAttributes` never spread | Studio put nothing on a wrapper and the component dropped it. The node cannot be selected at all, worse than the wrapper div | Emit both halves, or neither |
| Prop declared but unspread after a root rewrite | An edit replaced the root element and the spread stayed on the old one | Carry the spread onto the new root in the same edit |
| Spread placed before `{...props}` | A later spread overwrites the attributes | Spread `studioAttributes` **last**, on the outermost element |
| Spread onto a semantic-props component (`<Card title={…} />`) | It never reaches a DOM node, so there is no ref for hit-testing | Use a plain tag, or a component that forwards DOM attributes |
| `import { StudioAttributes }` as a value | It is a type-only export, breaks builds on `verbatimModuleSyntax` | `import type { StudioAttributes }` |
| Registering `studioAttributes` as a prop | It is identity, not content. A CSLP tag or `<Slot data>` entry on it corrupts the node | Never register, tag, or bind it |
| Tags missing on every component at once | Almost always `cslp.appendTags` not enabled, not a component bug | Fix the SDK config first |

**Verify in the browser** (both bags at once): open the component in Studio, inspect the rendered DOM, and confirm the component's root element carries `data-cslp` **and** each bound text/image element carries its own. A root with no tag means `studioAttributes` was dropped. A root with a tag but bare fields means the `$`-twins were.
