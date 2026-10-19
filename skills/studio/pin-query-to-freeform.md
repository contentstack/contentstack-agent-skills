---
name: pin-query-to-freeform
---

## When to use

Pin a CDA query (filter + sort + limit) to a Freeform template so Repeater sources iterate dynamic content like top 3 featured products. Use Studio UI, driven through Playwright per [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md). Don't hand the clicks to the user or switch to the API unless they ask; that's [`author-composition-via-api`](author-composition-via-api.md).

Use when a Freeform template needs to iterate a dynamic list of entries (top 3 featured products, latest 5 articles, sorted catalog). Phrases: "pin a query", "iterate latest entries", "filtered list on freeform". Re-runs every render so content stays fresh. For single-entry pinning use `pin-entry-to-freeform`.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Pin a CDA query to a Freeform template

> **Prerequisite:** this skill assumes you've already chosen Freeform via `choose-connected-vs-freeform`. If you haven't, run that first. Connected is the recommended default in Studio and most pages should use it (including one-off pages, via a single-entry CT). Freeform is the documented exception, not a parallel option. This skill remains valid for the legitimate Freeform cases. It just shouldn't be your starting point.

## Context

Freeform templates can pin a CDA query so a Repeater iterates a dynamic list of entries, for example the top 3 featured products or the latest 5 articles. The query (filter + sort + limit) is stored on the template and re-runs on every render, so content stays fresh as authors publish new entries. Pinned queries differ from pinned entries: a pinned entry returns a single record (bind directly to `template.*`), while a pinned query returns a list and must be consumed by a Repeater whose items resolve against `repeater.*`.

## Task

1. Confirm you are on a Freeform template: the canvas header shows the `FREEFORM MODE` badge.
2. Deselect any component on canvas (click empty canvas area) so the right-panel Data tab shows template-level pins, not component-scoped ones.
3. In the right panel, open the **Data** tab, find the **Pinned Queries** section, and click **Create Query**.
4. In the New Query modal, fill the required **Name** and **Content Type** fields.
5. Configure the query one of two ways:
   - **By hand**: set the **filter**, **order**, and **limit** fields directly.
   - **Natural language**: type a prompt in the Tell me what data you need box. Studio converts the prompt to a stored CDA query at save time. This conversion is one-shot: it is NOT re-evaluated at render. To tune the query later, re-open the modal.
6. **Save** the query. It appears in the Pinned Queries list.
7. Use the query on canvas: drop a **Repeater** component, click **Bind items** in Properties, and pick **Pinned Queries**, then `<name>`.
8. Drop a card or item component inside the Repeater body. Its bindings resolve against `repeater.*`: each iteration represents one entry from the query result.
9. Every item is an entry of the one content type you picked in step 4, so the Repeater itself needs no **Condition Block**, and neither does a reference field that points at a single CT. Add a Condition Block only where an item renders a **multi-CT** reference field and needs a different layout per referenced content type (a content-type check on that reference). See `use-condition-block`.

## Inputs needed from the user

| Input | Prompt |
| --- | --- |
| `templateName` | Freeform template name |
| `contentTypeUid` | Content type the query returns |
| `filterExpression` | Filter (e.g. `featured = true`) or natural-language prompt |
| `sortBy` | Sort spec (e.g. `price asc`) or blank |
| `limit` | Result limit (e.g. 3, 5, 10) |

## Acceptance

- In the target Freeform template's right panel, the Data tab's Pinned Queries list shows the new query by name.
- Dropping a Repeater on canvas and opening **Bind items** shows the query under **Pinned Queries**.
- After binding the Repeater and adding a child card with `repeater.*` field bindings, the canvas (with Repeater Preview Mode on) renders one card per returned entry, respecting filter, sort, and limit.
- Publishing a new entry that matches the filter causes it to appear in the rendered list on the next render, no template edit required.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Leaving filter and sort blank | Returns an unbounded, arbitrarily ordered result set | Always set at least a filter or a sort plus a sensible limit |
| Expecting the natural-language prompt to re-evaluate at render | The prompt is converted to a stored CDA query once at save time. Render uses the stored query only | To change query behavior, re-open the Pinned Query modal and edit (or re-prompt) |
| Binding a Repeater to a single-result query | A Repeater expects a list. One entry is wasted scaffolding | Use `pin-entry-to-freeform` for single-entry pinning and bind directly to `template.*` |
| Selecting a component before opening the Data tab | Tab shows component-scoped pins, not template-level | Click empty canvas to deselect, then open Data tab |
| Forgetting a Condition Block for a **multi-CT** reference inside the Repeater | Items of a multi-CT reference can be different content types, so one card layout cannot bind all of them. Single-CT references and the Repeater itself need no Condition Block (step 9) | Add a Condition Block with a content-type check only where a multi-CT reference needs a different layout per content type. See `use-condition-block` |
| Binding child fields to `template.*` instead of `repeater.*` | `template.*` resolves to template-level pins, not the current iteration item | Inside a Repeater body, child bindings must use `repeater.<field>` |
