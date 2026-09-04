# Edit tags: what `addEditableTags()` produces and where each key goes

Checked against `@contentstack/utils` 1.9.1 (`addTags`, exported as `addEditableTags`) and the
Live Preview SDK's empty-block and add-instance code. Use this to make a first tagging pass complete
by construction, not by diligence.

## The call

```js
addEditableTags(entry, contentTypeUid, true, locale /*, { useLowerCaseLocale: false } */);
```

- Mutates the entry and returns nothing. It attaches a `$` object at every level: the entry, each
  group, each block instance, and each resolved reference.
- Call it **once per top-level entry**. A resolved reference that carries `uid` and
  `_content_type_uid` (which `includeReference()` and REST `include[]` preserve) gets its own `$`,
  rebased to the referenced entry: `author.<author_uid>.<locale>.title`, not
  `blog_post.<post_uid>.<locale>.author.0.title`. A separate call per referenced entry is needed
  only when references were fetched separately and merged by hand, or when a GraphQL query omitted
  `system { uid content_type_uid locale }`.
- The third argument must be `true` in React and JSX so the values are objects you can spread.
- `locale` and `contentTypeUid` are lowercased; pass `{ useLowerCaseLocale: false }` for stacks with
  mixed-case locale codes.

## The `$` key convention

| Key on `$` | Attribute it holds | Value | Spread it onto |
|---|---|---|---|
| `<field>` | `data-cslp` | `<ct>.<entry>.<locale>.<field>` | the element rendering a scalar; the wrapper of an array, group, or asset |
| `<field>__<index>` | `data-cslp` | `<ct>.<entry>.<locale>.<field>.<index>` | the element wrapping instance `<index>`; lives on the **parent's** `$` |
| `<field>__parent` | `data-cslp-parent-field` | `<ct>.<entry>.<locale>.<field>` | nothing. The SDK does not read this attribute; skip it |

Nesting follows the data, so read tags off the object at the same depth as the value:

| Value | Tag | Resolves to |
|---|---|---|
| `entry.group.title` | `entry.group.$.title` | `…group.title` |
| `entry.blocks[i]` | `entry.$["blocks__" + i]` | `…blocks.<i>` |
| `entry.blocks[i].hero` | `entry.blocks[i].$.hero` | `…blocks.<i>.hero` |
| `entry.blocks[i].hero.title` | `entry.blocks[i].hero.$.title` | `…blocks.<i>.hero.title` |
| `entry.author[i].title` | `entry.author[i].$.title` | `author.<author_uid>.<locale>.title` (rebased) |

## Rule: enumerate from `$`, never from the JSX

```js
// once, while previewing
console.log(Object.keys(entry.$));
```

Diff that list against what the page renders. Any key never spread onto an element is a field the
canvas cannot reach, and reading the JSX will not show you the gap. Do the same on each block and
group object.

## Per-field-kind checklist

| Field kind | Spread | Empty state while previewing |
|---|---|---|
| Scalar (text, number, boolean, date, select) | `entry.$.field` on the element that renders the value | Render a placeholder box that keeps the tag and has height. Nothing rendered means nothing clickable |
| Link | `entry.$.link` on the `<a>` | Same as scalar |
| RTE (HTML string) | `entry.$.rte` on the container that receives the HTML | Same as scalar |
| JSON RTE | Render with `jsonToHTML` first (it mutates the entry), then `entry.$.body` on the container | Same as scalar |
| Asset (file) | `entry.$.image` on the `<img>` or its wrapper | Placeholder box or omit. The SDK draws no add button for assets |
| Single reference | Reference fields always arrive as arrays. `entry.$.ref` on the wrapper; `entry.ref[0].$.title` on the leaf, already rebased | Wrapper with the empty-block contract below |
| Multiple reference, multiple scalar | `entry.$.field` on the wrapper **and** `entry.$["field__" + i]` on each instance; leaves inside a reference instance use the referenced entry's `$` | Empty-block contract below |
| Modular blocks | `entry.$.blocks` on the wrapper; `entry.$["blocks__" + i]` on each block wrapper; `block.$.hero` on the block-type element; `block.hero.$.title` on fields inside | Empty-block contract below |
| Group | `entry.$.group` on the group wrapper; `entry.group.$.field` inside | A group object is never absent; its fields follow the scalar rule. A multiple group follows the multiple rules as well |

**Why the container tag matters for multiple fields.** Add and reorder controls appear on an
instance only if `closest('[data-cslp="<container value>"]')` finds an ancestor. Leaves alone give
the canvas nothing to attach them to. An optional `data-add-direction="vertical"` or
`"horizontal"` on the container overrides the SDK's layout detection.

## Empty-block contract

The SDK renders its own "Add <field display name>" button, but only on an element that satisfies
all three:

1. carries the class `visual-builder__empty-block-parent` (exported as `VB_EmptyBlockParentClass`);
2. carries its own `data-cslp` for the field, that is the container tag `entry.$.field`;
3. that field path exists in the content type schema.

So the wrapper has to stay in the DOM when the array is empty, which a plain `items.length > 0 &&`
guard removes:

```jsx
import { VB_EmptyBlockParentClass } from "@contentstack/live-preview-utils";

{related.length > 0 || isPreview ? (
  <ul
    className={related.length === 0 ? `list ${VB_EmptyBlockParentClass}` : "list"}
    {...post.$?.related_post}
  >
    {related.map((r, i) => (
      <li key={r.uid} {...post.$?.[`related_post__${i}`]}>
        <a href={r.url} {...r.$?.title}>{r.title}</a>
      </li>
    ))}
  </ul>
) : null}
```

Hover and click on the marked wrapper draw no outline; the button is the affordance.

## Verify

- `document.querySelectorAll('[data-cslp]')` in DevTools should account for every key you expect
  from `Object.keys(entry.$)` at each level.
- Hover each region in builder mode: the outline and toolbar label name the field you intended.
- Hover an instance of a multiple field: add and reorder controls appear between instances.
- Clear a multiple or block field and reload the canvas: the "Add …" button appears where the field
  renders, and adding an instance inserts it into the canvas and the form.
