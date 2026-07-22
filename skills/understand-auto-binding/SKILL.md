---
name: understand-auto-binding
description: "Explain how Studio auto-renders data when a Section drops on a template — the algorithm matching the Section's linked schema to the template's content type."
allowed-tools: Read Grep Glob
---

## When to use

Explain how Studio auto-renders data when a Section drops on a template — the algorithm matching the Section's linked schema to the template's content type.

Use after `understand-linked-schemas` when the user asks "how does data appear?", "do I have to wire bindings by hand?", "why did my Section render empty when dropped?". Also before `build-connected-template` so the user knows what happens at the drop. Do NOT use to wire bindings — for that, see `wire-external-data` / `build-connected-template`.

# How auto-binding works

## The one-line answer

**When you drop a Section onto a template, Studio reads the Section's linked schema, looks at the template's connected content type, and pairs every Section prop with the matching CT field automatically — no manual wiring per drop.** The Section then renders against a real entry as soon as it lands.

This is what makes Sections worth using. Without it, reuse would be theoretical — you'd re-wire every drop.

## What "auto" actually means

Three things happen the instant you release the drag:

1. **Schema match** — Studio compares the Section's linked schema to the connected content type's fields, by **field UID**, **field type**, and **required-ness** (see `understand-linked-schemas`).
2. **Binding** — for every linked-schema entry that finds a CT field match, Studio writes the binding (`prop ← field.uid`) into the template instance.
3. **Render** — the Section's atomic React components receive the bound data from the **preview entry** Studio fetches (top-bar PREVIEW ENTRY in the canvas) and render *immediately* against that real content.

No save, no refresh, no manual binding click. The canvas redraws with real CMS data the second the drop completes.

## A concrete walkthrough

You have a `blog_post` content type with fields: `title`, `subtitle`, `body`, `cover`, `author`, `publish_date`.

You have a Section called `BlogArticleHeader` whose linked schema is:

```
title:    Single Line, required
subtitle: Multi Line,  optional
cover:    File,         required
```

You create a connected template against `blog_post` and drag `BlogArticleHeader` onto the empty canvas. At drop time Studio:

| Section prop | Matches CT field? | Binding written |
|---|---|---|
| `title` | yes (`blog_post.title`) | `props.title ← entry.title` |
| `subtitle` | yes (`blog_post.subtitle`) | `props.subtitle ← entry.subtitle` |
| `cover` | yes (`blog_post.cover`) | `props.cover ← entry.cover.url` *(see Multiple-file note below)* |

The PREVIEW ENTRY in the canvas top bar is auto-set to the most recently updated `blog_post`. The Section renders its hero card with the entry's actual title, subtitle, and cover image. **Zero clicks beyond the drop.**

## What "scope" means and why it changes the match

The matching scope is whichever content level you're *inside* when you drop the Section. There are three common scopes:

| Drop scope | What the Section binds against | Example |
|---|---|---|
| **Page root** | The template's connected content type — top-level fields on the preview entry | Drop `BlogArticleHeader` straight onto a blog-post template → binds to top-level `blog_post` fields |
| **Inside a Repeater** bound to a reference / Modular Block | The repeated item's shape (each loop iteration is one referenced entry / one block) | Drop `RelatedPostCard` inside a Repeater bound to `blog_post.related_posts` → binds to each `related_post` entry's fields, not the parent post's |
| **Inside a Section Slot** | The slot's host scope (usually the same as the Section the slot lives in) | Drop a `Button` into a `cta` slot inside a hero Section → binds against the hero Section's host scope |

Drop scope matters because the same Section dropped at page root vs inside a Repeater binds to *different* fields — the Repeater changes the field reference frame to the iteration item. Studio handles this automatically; you don't choose the scope — it's wherever your drag-and-drop lands on the canvas.

## What happens when auto-binding can't find a match

| Situation | What Studio does | Author's next step |
|---|---|---|
| Required prop has no matching CT field | Section drops *unbound* with a red warning in right-panel Settings | Either add the missing field to the CT, or pick a compatible field manually from the dropdown |
| Optional prop has no matching CT field | Section drops, that prop renders empty | Usually leave alone; it's optional |
| Multiple CT fields could match (e.g. both `title` and `headline` are Single Line Text) | Section drops bound to one (first match wins); right-panel Settings shows the dropdown to switch | Switch the binding via the dropdown |
| The Section's linked schema is empty | Section drops *fully unbound* — Studio can't infer anything | Either author the linked schema (recommended), or bind each prop manually per template (works but loses reuse benefits) |

## What changes for the visitor at runtime

Nothing extra. The same auto-bound prop references that Studio's canvas renders against become the live-site renderer's data fetch. `sdk.fetchCompositionData({ url })` returns the composition spec **with bindings resolved**; `<StudioComponent />` reads the prop values from the fetched entry and renders. The visitor sees the same content the canvas does — same render path.

## Why this matters

| Without auto-binding | With auto-binding |
|---|---|
| Every Section drop requires 5–15 manual bindings | Drops "just work" if the CT shape matches |
| Section reuse loses 80% of its value to wiring overhead | Section reuse delivers the full speed benefit |
| Authors must understand the React prop names | Authors don't need to know prop names — they only see CT fields |
| Renaming a CMS field breaks N templates silently | Linked schema is the single source of truth — fix once, everywhere re-binds |
| New template against same CT = re-wire every Section | New template = instant productivity |

This is why "Studio is to your Components what your CMS is to your Content" works: the same way a CMS treats *content* as data that snaps into shapes, Studio treats *composition* as data that snaps onto content shapes.

## How to inspect what auto-binding did

After dropping a Section on a template:

- **Right-panel Settings tab** — shows each prop with its current binding chip. Green = bound, red = unbound.
- **Right-panel Data tab** (when a sub-component is selected) — shows the data picker; the current binding appears in the picker breadcrumb.
- **Layers panel** — every node is selectable; clicking any shows its bindings in the right panel.

If something rendered empty, the right panel tells you which prop didn't bind and to what.

**Note on what you see on the canvas:** auto-binding wires the props at drop time, but the canvas renders defaults until Preview Mode is toggled — seeing defaults isn't a binding failure. See `use-repeater` for the two-mode mental model.

## What can go wrong (real failure modes)

| Symptom | Likely cause | Fix |
|---|---|---|
| Section renders blank even though the entry has content | A `file` (multiple) field bound directly to a scalar `imageurl` prop | Bind to `field.0.url` instead (see `wire-external-data`) |
| Section auto-binds but renders the wrong field | Two fields had matching UIDs; first match wins | Switch the binding in the right-panel Settings dropdown |
| Section drops unbound on a CT that "looks right" | Field UIDs differ (`title` vs `headline`) | Rename the CT field OR change the Section's linked schema to match — best to align on convention |
| Repeater renders only one row | Repeater isn't bound to an array field, or the binding scope is wrong | See `use-repeater` |

## Next steps

| If you want to… | Skill |
|---|---|
| Create the Section that will auto-bind | `build-section` |
| Author the linked schema so auto-binding can work | `build-section` (linked-schema step) |
| Drop a Section into a template and see auto-binding live | `build-connected-template` |
| Diagnose a Section that didn't auto-bind | `troubleshoot-data-binding` |

## Data-flow at render time — `selectedField` re-scopes the section

Drop-scope (page / Repeater / Slot) is what this skill covers — the UI-level "where did I drop it, what fields are visible." A separate mechanism runs at render time: `getScopedData(pageEntry, selectedField)` on the Section's linked-schema entry. `selectedField` set → the Section's `template` becomes that one field's value; unset → `template` is the whole page entry. The Section's own canvas always shows one empty placeholder because the scoping only happens at template-render time. See [`build-section`](../build-section/SKILL.md) § *How a Section gets its data* for the set-vs-unset decision rule.

## See also

- `understand-linked-schemas` — the declaration that makes auto-binding work
- `understand-sections` — what Sections are
- `build-section` § *How a Section gets its data* — `selectedField` model + set-vs-unset rule
- `author-composition-via-api` § *Authoring a Section composition* — wire shapes
- `docs/32-sections/auto-binding-by-drop-location.md` — long-form reference
