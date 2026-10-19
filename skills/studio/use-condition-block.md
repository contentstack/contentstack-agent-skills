---
name: use-condition-block
---

## When to use

Wrap component bindings inside a Repeater with sibling Condition Blocks (one per block / content type) so each iteration item resolves to a specific schema before fields bind. Use Studio UI, driven through Playwright per [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md). Don't hand the clicks to the user or switch to the API unless they ask; that's [`author-composition-via-api`](author-composition-via-api.md).

Use whenever a Repeater iterates a Modular Block list or a Reference field. Without sibling Condition Blocks the iteration items have no resolved schema and every binding shows empty. Phrases: "modular block repeater", "reference repeater", "blocks render empty". Do NOT use for plain multi-valued fields (text/number arrays don't need schema disambiguation): skip Condition Block entirely.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Use a Condition Block

## Context

A Condition Block narrows the iteration item inside a Repeater to a specific schema (a Modular Block type, or a referenced content type) so that field bindings underneath it resolve. Without it, Studio cannot know which schema a given iteration item has, so the Data Picker cannot offer typed fields and the canvas surfaces the hint `Add a condition for <ct> schema, then bind the component within it to the hover fields`. Accepting that hint auto-wraps the binding in a Condition Block: this skill is the manual, deliberate equivalent.

**Model: one Condition Block per type, as sibling children of the Repeater.** Studio's **Add Condition** modal lets you tick multiple block types or content types in one go. It inserts one Condition Block per selected UID, all as siblings under the Repeater. There is no "multi-branch" mode where one Condition Block routes between several types: each CB narrows to exactly one type via its `condition.type` metadata (`modular_block` matched to a block UID, or `reference` matched to a content-type UID).

Condition Blocks are required inside a Repeater for:

- **Modular Block lists** with two or more block types (the iteration item could be any one of them).
- **Reference fields with multiple content types** (the related entry could be any one of the allowed CTs).
- **Reference fields with a single content type**: still required, because Contentstack composition schema narrows iteration item type via the Condition Block before `repeater.<field>` paths resolve. One Condition Block matching the single CT is enough.

Condition Blocks live in the palette under **Smart Containers**.

## Task

1. **Confirm a Repeater exists** bound to the Modular Block or Reference field named in `repeaterSource`. If not, stop and run `use-repeater` first: a Condition Block has nothing to discriminate without a parent Repeater iteration scope.

2. **Open the Add Condition modal.** It opens when you bind the Repeater's `items` to the field: never click **Skip**. Re-bind `items` to reopen it (it lists only types without a Condition Block yet), or accept the data picker's **Add Condition** prompt on a child of the Repeater. No Repeater action opens it. The modal lists every block type (Modular Block source) or content type (Reference source) the Repeater's binding allows.

3. **Tick every UID in `branches`** (in any order: Studio inserts them as siblings under the Repeater. Their order doesn't change the output: each item renders through the one branch that matches it, and items appear in the data's order). Confirm. Studio creates one Condition Block per selected UID, each with its discriminator (`modular_block` block UID, or `reference` content-type UID) recorded as `condition.type` metadata on the Condition Block node, not as a path expression the user writes.

4. **For each newly-created Condition Block, drop a component into the Box Studio placed inside it** (a Condition Block takes one child) and bind the component's props via the Data Picker. The Data Picker surfaces the **Repeater Data** root inside a Condition Block, narrowed to the fields of the type that Condition Block matches: pick from there. Use **Component Default Data** only for runtime values not tied to the iteration item.

5. **Save the composition and verify in Preview Mode.** Select the parent Repeater in Layers and toggle **Preview Mode** in Properties, then Configuration. Conditions apply their real type checks only in Preview Mode. In Design Mode (the default) you see the un-evaluated branch with placeholder data. Step through iterations and confirm each item routes through its matching Condition Block. Items whose UID matches none of the inserted Condition Blocks render nothing: there is no built-in default fallback.

## Inputs needed from the user

In this order. Stop and ask if any is missing: DO NOT guess `branches`.

1. `compositionName`: Section or template canvas in scope
2. `repeaterSource`: parent Repeater binding (e.g. `blog_post.body_blocks`)
3. `branches`: comma-separated block-type or content-type UIDs

If `repeaterSource` is a Reference and the user gives only one UID, still create a single-CB setup: single-CT references are NOT exempt from the Condition Block requirement.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, do not claim success: surface the failure and stop.

- [ ] In Layers the tree reads `Repeater > [Condition Block × N]`: each Condition Block is a direct child of the Repeater, or of the one Box that is the Repeater's only child (for Visual Editor's item tags: [`make-visual-editor-editable`](make-visual-editor-editable.md) § 2), never wrapping it.
- [ ] There is exactly one Condition Block per UID in `branches`. UIDs not in `branches` do not have a Condition Block.
- [ ] Each Condition Block's `condition.type` metadata is set to `modular_block` (Modular Block source) or `reference` (Reference source), matched to a specific block / content-type UID, never to a shared field name like `title`.
- [ ] Inside each Condition Block, the type-specific component's props are bound via `repeater.<field>` paths. The Data Picker shows the typed fields of that Condition Block's schema, not a generic union.
- [ ] With Preview Mode toggled on the parent Repeater, each iteration item visibly renders through its matching Condition Block. No item shows the "Add a condition for <ct> schema" hint.
- [ ] The user is informed that items whose type matches none of the inserted Condition Blocks render nothing (no built-in fallback). If that is unwanted, the user must add additional Condition Blocks for those types.

## Common pitfalls

| Pitfall | Why it breaks | Fix |
| --- | --- | --- |
| Trying to add multiple "branches" to a single Condition Block | Each Condition Block narrows to exactly one type. There is no multi-branch model | Insert sibling Condition Blocks (one per type) under the Repeater |
| Condition Block wraps the Repeater | Discriminates the parent scope, not the iteration item. `repeater.<field>` still cannot resolve | Drop Condition Block INSIDE the Repeater as a direct child sibling |
| Trying to write a path expression for the discriminator (e.g. `block.type === "hero"`) | Studio stores the discriminator as `condition.type` metadata on the node, not as a user-written path expression | Pick the block / content-type UID in the Add Condition modal. Studio handles the discriminator under the hood |
| Skipping Condition Block for single-CT Reference | Picker shows generic union, `repeater.<field>` paths fail to resolve | Add one Condition Block matching that single CT |
| Binding fields directly under Repeater on a Reference / mixed Modular Block | Canvas shows `Add a condition for <ct> schema` hint. Bindings stay broken | Accept the hint OR add Condition Blocks via the modal per this skill |
| Expecting an unmatched-fallback Condition Block | No such affordance in Studio: items with unmatched types render nothing | If you need a fallback, add a Condition Block for every type you expect. Revisit if new types are added later |
| Forgetting Preview Mode when verifying | Repeater renders only one iteration by default. You cannot see whether each Condition Block routes correctly | Select Repeater in Layers, toggle Preview Mode in Properties |

## See also

- [`use-repeater`](use-repeater.md): the Repeater that Condition Blocks sit under
- [`build-repeating-section`](build-repeating-section.md): repeating sections over Modular Blocks and References
- [`troubleshoot-data-binding`](troubleshoot-data-binding.md): when bindings inside a Condition Block don't resolve
