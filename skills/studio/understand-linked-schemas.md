---
name: understand-linked-schemas
---

## When to use

Explain the **linked schema** on a Section (the declared data shape) and why declaring it once makes the Section auto-bind onto any template with a matching content type.

Use before `build-section` or `build-connected-template` when the user is new to Studio. Also when the user asks "why doesn't my Section auto-bind?", "what's a linked schema?", "do I have to wire each binding every time?". Do NOT use to actually edit a linked schema: for that, edit the Section in Studio. Concept only.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# What is a linked schema?

## The one-line answer

**A linked schema is the data shape a Section says it needs (declared once on the Section) so that when the Section is dropped on any template whose content type has that shape, Studio binds every inner prop to the matching CMS fields automatically.** No re-wiring per template.

## Why this exists

Without a linked schema, every time you drop a Section onto a new template, you'd have to wire every prop's binding by hand. That's tedious and error-prone, and it defeats reuse. A Section that takes 10 minutes to wire up per template isn't really reusable.

With a linked schema, the Section says up front: "to render me, you need to give me a content shape with a `title` (string), a `body` (rich text), and a `cover` (image)." Studio then matches that declaration against the template's connected content type and binds the fields automatically.

## A concrete example

You have a Section called **"Blog Article Header."** It contains a Hero atomic component with props:

```
<Hero
  title="..."       // bound to ???
  subhead="..."     // bound to ???
  cover="..."       // bound to ???
/>
```

When you author the Section, you declare its **linked schema**:

```
linked_schemas: {
  title:   { field_type: "Single line text", required: true },
  subhead: { field_type: "Multi line text",  required: false },
  cover:   { field_type: "File (image)",     required: true },
}
```

This says: "any content type with a `title`, optional `subhead`, and `cover` can drive this Section."

Now you create three connected templates against three different content types:

| Template | Connected CT | CT has these fields | Section drops and… |
|---|---|---|---|
| Blog post template | `blog_post` | `title`, `subhead`, `cover`, `body`, `author`, … | **Auto-binds all three slots silently** |
| Case study template | `case_study` | `title`, `cover`, `body`, `client`, … (no subhead) | **Auto-binds `title` + `cover`. Leaves `subhead` empty** |
| Product launch template | `product_launch` | `name`, `description`, `image` | **No match by field name**: Section drops unbound and Studio asks you to pick fields manually (or the template author edits the CT to add matching fields) |

Same Section. Three templates. Zero manual binding when the shape matches.

## What "the shape matches" actually means

Studio's auto-binder matches on three signals, in order:

1. **Field name (UID)**: the Section's linked-schema field UID equals a field UID on the template's connected CT.
2. **Field type**: the type matches (Single Line Text binds to Single Line Text. Not a Multi-line being squeezed into a Single Line).
3. **Required-ness**: required fields on the linked schema MUST exist on the CT. Optional ones may be missing.

If all three line up for a given prop, Studio binds it. If even one mismatches, that prop drops unbound and the template author is prompted.

## Why declare a linked schema at all (vs. binding per template)

Three benefits:

| Without linked schema (bind per template) | With linked schema (declare once) |
|---|---|
| Drop Section, wire 6 bindings, save | Drop Section, and all 6 bindings are done |
| Add a new template against a similar CT, and repeat all 6 bindings | Add a new template, and auto-bind is instant if the CT matches |
| Forget to wire one binding, which produces a silent empty render | Linked schema enforces the required props are filled |
| Rename a CMS field, which breaks every template that uses the Section | Rename a CMS field, fix the linked schema once, and every template re-binds |

## What if the template's CT doesn't match the linked schema?

Three outcomes depending on the kind of mismatch:

| Mismatch | What Studio does |
|---|---|
| Required field missing on CT | Section drops unbound. Right-panel Settings shows the required field with a red "no source" warning. Author must either pick a different field (rare, they share a UID by convention) or add the field to the CT. |
| Optional field missing on CT | Section drops. That prop renders empty (`""` / `null`). No warning. |
| Field exists on CT but type differs | Section drops unbound for that prop. Studio asks the author to pick a compatible field manually. |
| Field exists on CT but a different UID (e.g. CT calls it `headline`, Section linked schema calls it `title`) | Section drops unbound for that prop. The author maps the binding manually one time. This is rare: teams usually align CT field names with the Section's expected UIDs. |

## How linked schemas appear in Studio

- **Section author** sets the linked schema when authoring the Section, in the Section's Settings panel, "Linked Schema" tab.
- **Template author** doesn't see the linked schema directly. They just experience the auto-binding (or the prompt to fix a mismatch). The schema is the contract Studio uses behind the scenes.

## What linked schemas are NOT

| Misconception | Reality |
|---|---|
| "Linked schema = the connected content type" | No. The linked schema is the Section's declared expectation. The connected content type is what a template is attached to. They're matched, not the same thing. |
| "Linked schema defines new CMS fields" | No. It references the shape of fields you've already defined in your CMS (or the conventions you want CTs to follow). It doesn't create CT fields. |
| "I have to use the exact same UIDs the Section expects" | Not strictly, but it makes auto-binding silent. Different UIDs require manual binding on first drop. |

## Next steps

| If you want to… | Skill / doc |
|---|---|
| Create a Section with a linked schema | `build-section` |
| Understand what happens when a Section drops on a template | `understand-auto-binding` |
| Inspect a Section's linked schema | Open the Section in Studio, then in the right panel open Settings, then Linked Schema |

## Sections have no data of their own: `selectedField` scopes the slice

The linked schema declares what fields the Section CAN read, but the Section itself is data-less at author time. When it's placed on a template, the SDK calls `getScopedData(pageEntry, selectedField)`:

- With `selectedField` set, `template` inside the section becomes that field's value only.
- With `selectedField` unset, `template` becomes the whole page entry.

**Repeater or one item: the `cardinality` question.** Studio asks it in exactly one case: the section's `selected_field` has `multiple: true` AND `data_type` `group`, `global_field`, `file` or `link`. Its prompt: *"This schema supports multiple items. Add a repeater to render each item automatically, or skip if you only need a single section for now."* When authoring by API, **ask the user the same question** before building the section, and record the answer:

| Answer | `linked_schemas[].cardinality` | Section `ui` | Bindings |
|---|---|---|---|
| Add: every item | `"collection"` | Root Repeater, `items` bound `{ "type": "template", "value": { "path": {} } }` | `repeater` bindings on the iteration item |
| Skip: one item | `"single"` | No root Repeater | `template` paths on one element (`title`, not `0.title`). Placed alone it shows the first element. Inside a page-side Repeater, the current item |

Do **not** ask, and write no `cardinality`, when: there is no `selected_field` (whole entry), the field has `multiple: false`, or it is a `reference` or `blocks` field. Those always get a root Repeater with a Condition Block per content type or block (`author-composition-repeater-recipes`). Studio also skips the question once the section has bound content, and keeps the existing structure: a root Repeater means `"collection"`.

```jsonc
"linked_schemas": [{ "content_type_uid": "blog_post", "selected_field": "features", "cardinality": "single" }]
```

Consequence: the Section's own canvas always shows **one empty placeholder**, not the rendered card: the data only arrives at template-render time. See [`build-section`](build-section.md) § How a Section gets its data for the set-vs-unset decision rule. Wire shapes and reference-iteration handling in [`author-composition-via-api`](author-composition-via-api.md) § Authoring a Section composition: scoping rules.

## See also

- `understand-sections`: the parent concept
- `understand-auto-binding`: what happens at drop time when a linked schema matches
- `build-section` § How a Section gets its data: the `selectedField` decision rule
- `author-composition-via-api` § Authoring a Section composition: full wire shapes for `selectedField` + `resolvedReferences`
