---
name: decompose-blocks-page
---

## When to use

Decompose a page whose entire body is **one modular-blocks field** into one Section per block type, when a single production component already renders every block type behind a `switch`. Covers the scope-filter prop that makes one Section render one scope, occurrence pinning when a block type repeats, and the reuse ceiling that decides which Sections two templates can actually share.

Use when the page CT has a `data_type: "blocks"` field carrying the whole page body and the codebase has one component that renders all of it. Phrases: "one component renders all my blocks", "the whole page is one modular blocks field", "split this blocks page into Sections", "my template has only one Section", "how do I decompose a page that is one array", "the page renders but there is only one node", "split the sections field into sections". Do NOT use for a design-first build (use [`decompose-design`](decompose-design.md)), for proposing scope boundaries from a schema (that is [`discover-sections-from-ct`](discover-sections-from-ct.md), which this skill executes), or for a list of like items inside one section (that is [`build-repeating-section`](build-repeating-section.md)).

> **Reuse preflight: mandatory when the project already has compositions.** Before naming a single new atomic, component or Section, run [`match-existing-pattern`](match-existing-pattern.md) § Step 1b: it groups existing Sections by the schema they bind and ranks the component palette by real usage. Decomposition is where reuse has to bite. Once this step names `Heading` instead of the project's `alpha-atom-heading`, the duplicate survives into the plan and into the build. Mark every row reuse, extend, or new, and never new without having looked.

# Decompose a one-blocks-field page into Sections

## Context

[`discover-sections-from-ct`](discover-sections-from-ct.md) already states the rule: **each block type in a `blocks` field is its own Section scope**, so a field with nine block types is nine Sections. This skill is the execution half, what to do when the code renders those nine types from a single component.

## Why this matters

A page whose body is one blocks field invites exactly one node: bind that component's array prop to the field and the entire page appears, correct in every pixel. Nothing errors. It renders, it matches production, it passes visual parity, it passes every render-time acceptance check ever written, and it is a monolith with no Sections, no reuse and nothing an author can rearrange.

That is the trap: **the monolithic build is not a broken build, it is a working build with the wrong shape.** It cannot be caught by looking at the page. It is only caught by counting `section-composition` nodes. See [`build-connected-template`](build-connected-template.md) § Post-build structural check, which is the canonical check and applies to API-authored templates too.

## Task

### Step 1: Read the block sequence from the entry, never from the DOM

Fetch a representative entry and record the ordered list of block type keys:

```js
const seq = entry[blocksField].map((b) => Object.keys(b).find((k) => !k.startsWith('_') && k !== '$'));
// e.g. ["hero","feature_grid","quote","feature_grid","cta"]
```

The rendered DOM is not a substitute. Once any decomposition exists, the DOM shows what the current Sections do, so using it to check that decomposition is circular. The entry is the only independent source.

### Step 2: Give the renderer a scope prop

One Section must render one scope. Add a filter prop to the component and register it:

```tsx
/** Render only this block type. Unset renders every block — the pre-decomposition
 *  behavior, kept so existing compositions keep working mid-migration. */
block_type?: string;
/** Which occurrence of block_type to render when the page repeats the type. -1 = all. */
block_index?: number;

const blocks = selectBlocks(all, block_type, block_index);
```

```ts
block_type:  { type: "string", displayName: "Render only this block type", defaultValue: "" },
block_index: { type: "number", displayName: "Which occurrence (-1 = all)", defaultValue: -1 },
```

Defaulting to "render everything" is what makes the migration safe: every composition authored before the prop existed keeps rendering while the templates are converted one at a time.

### Step 3: Decide grouped or pinned, per template

One Section per type renders all blocks of that type together. That is only faithful when each type's occurrences are already contiguous. Test it (do not assume):

```js
const order = [...new Set(seq)];
const grouped = order.flatMap((k) => seq.filter((x) => x === k));
const groupSafe = JSON.stringify(grouped) === JSON.stringify(seq);
```

`groupSafe` false means the page interleaves: `hero, para, para, quote, para` regroups to `hero, para, para, para, quote`, which keeps every block and still ships the wrong page. Then emit one Section per **occurrence**, each pinned with `block_index`, and place them in entry order.

### Step 4: Rebuild the root slot from the pre-decomposition version, not from the block list

Read the newest composition version whose root slot holds **no** `section-composition` node (the layout before anyone decomposed it) and rebuild from that node list. A blocks-driven page routinely carries siblings beside the blocks node: a closing CTA band, a comparison table, a content list. Building the root slot from block types alone silently drops every one of them.

Each non-blocks sibling becomes its own Section, wrapping that node verbatim, placed in its original position. Copy the node's other props too. A prop that filtered the whole array is a per-page setting and does not belong on a shared Section (see the pitfall table).

### Step 5: Key Sections by field, not by template

A Section's binding is `template.<field>`, so the field name (not the page) decides reuse. Slug Sections `sec_<field>_<block_type>` and two templates whose CTs name the field identically share Sections automatically. Templates whose CTs name it differently cannot share, no matter how alike the blocks look.

**Do not try to escape this by binding the whole entry.** An empty binding path (`path: {}`) does resolve to the entry root, and it works right up until a sibling node contributes binding paths: the SDK builds the delivery projection from declared binding paths, the whole-entry binding contributes none, and the entry arrives carrying only the sibling's fields, `["uid", "<sibling_field>", "$"]`. The blocks field is never fetched and every Section renders its empty state. Bind the real field path.

## Acceptance

- [ ] Every template's root slot holds **only** `section-composition` nodes: run `build-connected-template` § Post-build structural check.
- [ ] Section count per template equals distinct block types (grouped) or block occurrences (pinned), **plus** one per non-blocks sibling node.
- [ ] The rendered block-type sequence matches the entry's sequence, in order.
- [ ] Visual Editor can add, move and delete blocks: the page renders the blocks field's `<field>` tag and one `<field>.<N>` per block ([`make-visual-editor-editable`](make-visual-editor-editable.md) § 2).
- [ ] Every Section and every Template is published: an edit creates an unpublished version and delivery keeps serving the old one.
- [ ] A before/after fingerprint of the page (headings in order, visible text length, image sources, block sequence) is unchanged. Content that only appears after decomposing usually means the previous build had dropped a node.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Judging the build by how the page looks | A monolith renders perfectly. Every render-time check passes | Count `section-composition` nodes before reporting success |
| One Section per type on an interleaved page | Blocks regroup: content survives, order does not | Run the group-safety test. Pin occurrences with `block_index` |
| Rebuilding the root slot from the block list | Sibling nodes beside the blocks node are dropped, silently and invisibly | Rebuild from the last version with no `section-composition` node |
| Copying a whole-array filter prop onto a shared Section | One page's exclusion leaks into every template reusing it: that Section renders nothing there | Drop array-wide filter props. Per-scope Sections make them meaningless |
| Binding the whole entry to make Sections field-agnostic | Projection is built from binding paths. A sibling's paths narrow the fetch and the blocks field never arrives | Bind `template.<field>` and accept the field-name reuse ceiling |
| Naming Sections after the template | Two templates on the same field can no longer share | Slug by field: `sec_<field>_<block_type>` |
| Reading the block order from the DOM | The DOM reflects the current decomposition, so it cannot verify it | Read the order from the entry |
| Deriving a Section title by stripping a suffix | `quote` and `quote_section` collapse to one title. Composition titles are unique, so the second create fails | Keep titles 1:1 with the block type |

## See also

- [`discover-sections-from-ct`](discover-sections-from-ct.md): proposes the scope boundaries this skill executes
- [`build-connected-template`](build-connected-template.md): the approved-plan guard and the post-build structural check
- [`author-composition-via-api`](author-composition-via-api.md): writing the resulting Sections and Template through the CMA
- [`plan-studio-architecture`](plan-studio-architecture.md): the plan this decomposition belongs in, approved before any of it is built
