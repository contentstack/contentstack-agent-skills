---
name: classify-existing-component
---

## When to use

Diagnose what shape an **existing** component is (Atom, Layout, or Compound) and hand off to the right next skill. Runs [Q1 of the four-question framework](design-component-library.md) as a standalone step, without committing to registration or decomposition upfront.

Use when the user has a component (already registered, or about to be) and asks what it is, not what to do about it. Phrases: "is this atom or layout?", "classify this component", "what shape is this?", "audit my registered components", "which of my registrations are compounds?", "should this be decomposed?", "sanity-check my palette", "review this component before I register it". Do NOT use to **design** a fresh library (that's [`design-component-library`](design-component-library.md)), to **break a monolith apart** (that's [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md)), to **write the registration call** (that's [`register-component`](register-component.md)), or to **derive a schema** from an already-classified atom (that's [`design-section-from-jsx`](design-section-from-jsx.md)). This skill answers what shape only, then routes.

# Classify an existing component: Atom, Layout, or Compound

## Context

The full [four-question framework](design-component-library.md) chains four questions in order: Q1 (classify), Q2 (reuse?), Q3 (props?), Q4 (expose?). Skills like `design-component-library` and `decompose-jsx-to-atomics` walk all four for a whole library or a whole monolith. This skill runs **only Q1**, on **one component at a time**, and stops.

Why break Q1 out:

- **Audit an existing registry**: a team inherits a Studio project with 30 registered components. They want to know which are honest atoms, which are honest layouts, and which are compounds that need decomposition, before committing to a decomposition run.
- **Sanity-check before registering**: a developer has a candidate component. They want confirmation of its shape before running `register-component`.
- **Triage**: a customer reports "authors can't rearrange anything" or "the data doesn't bind properly". Q1 on the offending component reveals whether it's actually a compound (single Section = single page block).

The output is one word plus a reason plus a routing recommendation. Not a full decomposition tree. That's the next skill's job.

## Task

### Step 1: Locate the component

Ask (only if not stated):

- Where's the component's source? (path to `.tsx` / `.jsx`, or the `registerComponent()` call's `component` reference)
- Is it currently registered? (grep the codebase for `registerComponent(`, or check the component palette in Studio)

If already registered, note the `type` UID. If not, note the file path.

### Step 2: Read the render tree

Open the source. Walk **what the component returns**, not its prop list. Prop lists tell you what the current caller passes. The render tree tells you what the component actually renders.

For each element inside the return, note:

- Tag or child component name (`<h1>`, `<Button>`, `<Card>`)
- What content it renders (a prop, a literal, a `.map()`, a fetch result)
- Whether it's a **content leaf** (single string / image / link / rich-text field) or a **container** (holds child elements laid out in a specific relationship)

Set aside styling wrappers (`<div className="wrapper">` around one leaf). They don't count as containers unless they hold multiple children in a designed relationship.

### Step 3 (Apply Q1) classify

| The render tree looks like… | Classification | Reason |
|---|---|---|
| One content leaf (plus styling wrappers): a `<h1>{text}</h1>` or `<img src={src} alt={alt}/>` or `<a href={href}>{label}</a>` | **Atom** | Carries a single content unit. |
| A container that arranges children via a slot (`children`, `left`/`right`, `header`/`body`/`footer`) with no hardcoded content of its own | **Layout** | Arranges child components. Doesn't own content. |
| A `<div>` with hardcoded child structure (e.g. `<div><Heading/><Text/><Button/></div>`) where the children are baked in, not slot-passed | **Compound** | Owns both arrangement AND content. Not a valid Studio primitive. |
| A page-level component that renders a `<Header/>` + `<Hero/>` + `<Grid/>` + `<Footer/>` with no slot props | **Compound** | Whole-page monolith. |
| A `.map()` over an array rendering child components inline (e.g. `products.map(p => <ProductCard {...p}/>)`) | **Compound** | Iteration is baked in. A Studio Repeater should own it, not the component. |

**Halt on ambiguity.** If the component mixes patterns (e.g. `<div><Header/>{children}</div>`) call out both signals and ask the user which one the component's real job is (arrange? contain? both?). Never guess.

### Step 4: Report the classification

Emit one paragraph in this shape:

> **Classification: [Atom / Layout / Compound]**
>
> **Reason:** [1 to 2 sentence justification grounded in the render tree. Cite the specific elements].
>
> **Confidence:** [High / Medium / Low]. [If low: which observation was ambiguous, and what would resolve it.]

### Step 5: Route to the next skill

| Classification | Next step | Why |
|---|---|---|
| **Atom**: not yet registered | [`register-component`](register-component.md) | Shape confirmed. Write the registration. |
| **Atom**: already registered, but you're auditing | Stop. It's fine. | Optionally verify the prop schema follows the [content-vs-design split](design-component-library.md) via `design-section-from-jsx`. |
| **Layout**: not yet registered | [`register-component`](register-component.md) with a `slot` prop | Layout confirmed. Write the registration with the slot contract. |
| **Layout**: already registered | Stop. It's fine. | Shape confirmed and the registration is in place. |
| **Compound**: from JSX | [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md) | Break the render tree into Layer-1 atoms + Layer-2 containers. Re-run Q1 on each fragment. |
| **Compound**: from a design artifact (Figma / screenshot) | [`decompose-design`](decompose-design.md) | Same intent, visual input. |
| **Compound**: page-level monolith | [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md), then [`discover-sections`](discover-sections.md) on the resulting fragments | A page becomes sections, and sections become primitives. |

State the recommended next skill explicitly. Do not silently transition. The caller may want to stop after classification (an audit run) rather than start a decomposition.

## Worked examples

**Example 1: Heading component**

```tsx
export function Heading({ level, text, align }: HeadingProps) {
  const Tag = level;
  return <Tag className={cn("heading", align && `text-${align}`)}>{text}</Tag>;
}
```

- Render tree: one `<Tag>{text}</Tag>`. `align` is design (className), not content.
- Classification: **Atom**. Reason: single content leaf (`{text}`), only styling around it.
- Confidence: High.
- Next: `register-component` if not yet registered.

**Example 2: TwoColumn wrapper**

```tsx
export function TwoColumn({ left, right }: TwoColumnProps) {
  return (
    <div className="grid grid-cols-2 gap-8">
      <div>{left}</div>
      <div>{right}</div>
    </div>
  );
}
```

- Render tree: a `grid` container arranging two children by slot (`left`, `right`).
- Classification: **Layout**. Reason: slot-based children (`left`, `right`). No content of its own.
- Confidence: High.
- Next: `register-component` with two `slot`-typed props.

**Example 3: HeroBand with baked-in children**

```tsx
export function HeroBand({ headline, subheadline, ctaLabel, ctaHref, imageSrc }: Props) {
  return (
    <section className="hero">
      <div className="hero-copy">
        <h1>{headline}</h1>
        <p>{subheadline}</p>
        <a href={ctaHref}>{ctaLabel}</a>
      </div>
      <img src={imageSrc} alt="" />
    </section>
  );
}
```

- Render tree: 4 content leaves (`<h1>`, `<p>`, `<a>`, `<img>`) arranged inside a designed relationship.
- Classification: **Compound**. Reason: owns both the arrangement (grid split, hero-copy stack) AND the content (heading, subheadline, CTA, image) as baked-in structure. Not slot-based.
- Confidence: High.
- Next: `decompose-jsx-to-atomics`. Split into `Heading`, `Text`, `Button`, `Image` atoms plus a `Split` or `Hero` layout with two slots. Then register each.

**Example 4: ambiguous mix**

```tsx
export function CardShell({ title, children }: Props) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}
```

- Render tree: one content leaf (`<h3>{title}</h3>`) + a slot (`{children}`).
- Classification: **Ambiguous**. This is either a Layout with a header prop, or a small Compound (owns the title AND the slot).
- Confidence: Low.
- Halt. Ask: "Should the title stay as part of the CardShell (Compound), or should authors compose their own header in the slot (pure Layout)?"

## Pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Reading the prop list instead of the render tree | Props tell you what callers pass. The render tree tells you what the component contains. A `Hero({ children })` looks like a Layout by props but might render 5 hardcoded elements inside a `<div>` before the `{children}`. | Open the file. Walk the JSX. |
| Confusing a `<div className="wrapper">` styling shell for a Layout container | A single-leaf atom often has a styling `<div>` around it. That's still an Atom. | Layout = slot-based, multiple children. Single-child styling wrapper = Atom. |
| Classifying a `.map()` as Layout | Iteration is a Studio Repeater's job, not a component's. A `.map()` inside the render tree is almost always a Compound signal. The component is baking in what should be Repeater iteration. | Classify as Compound. `decompose-jsx-to-atomics` handles the split. |
| Skipping Q1 because "it's obviously an Atom" | Every skipped classification is a future "why can't I bind this properly?" bug. | Even one-liner: cite the leaf, say Atom, move on. Takes 15 seconds. |
| Running Q1 and then running the full framework anyway | This skill is deliberately scoped to Q1. If the caller wants Q2 to Q4, run `design-component-library` (fresh) or `decompose-jsx-to-atomics` (existing). | Stop after Step 5. Route explicitly. |

## Why this exists (why-this-matters)

Q1 is the classification gate that governs whether every downstream skill's advice will actually work. Getting Q1 wrong cascades:

- Register a Compound as an Atom, and you hit **the `any` flatten trap** ([`register-component` § The `any` flatten trap](register-component.md)). The binder folds an object down to a single value and props render as `[object Object]` or nothing.
- Register a Compound as a Layout, and **authors can't rearrange anything.** The component's baked-in children override any slot fill.
- Miss a Layout that's actually an Atom, and **no slot means no author variability.** The palette entry ends up locked to whichever content the developer hardcoded.

Every downstream failure starts here. Cheap to run, catches expensive mistakes.

## See also

- [`design-component-library`](design-component-library.md): the canonical 10-primitive taxonomy and the full four-question framework (Q1 to Q4).
- [`design-component-library`](design-component-library.md): walks all four questions across a whole library. Use this when starting fresh.
- [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md): the next step after Q1 = Compound on an existing React component.
- [`decompose-design`](decompose-design.md): the next step after Q1 = Compound when input is a Figma frame or screenshot.
- [`register-component`](register-component.md): the next step after Q1 = Atom or Layout, when not yet registered.
