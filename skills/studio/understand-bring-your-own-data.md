---
name: understand-bring-your-own-data
---

## When to use

Explain the three ways your own data reaches a composition (the `data` prop, `<StudioComposition context>`, and `<Slot data>`) and which one to pick.

Use before `render-with-own-data` or `wire-slot-data` when the user holds data outside the CMS and isn't sure which surface takes it. Phrases: "render a section with my own data", "pass data into a slot", "which prop do I use". Do NOT use to write code. Run the action skill.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Bringing your own data into a composition

## The one-line answer

**Studio compositions normally bind to Contentstack content, but three render-time props let you hand a composition data you already hold**: and each one covers a different scope. Pick by asking what part of the tree needs the data.

## The three surfaces

| Prop | Scope of the data | How authors reach it | Skill |
|---|---|---|---|
| `data` on `<StudioComponent />` | The whole composition on a route | In the Data Picker, under **Component Default Data** | `wire-external-data` |
| `context` on `<StudioComposition />` | The whole composition you mount yourself, placed at `dataSources.template`, so the composition's own template bindings resolve against it | Nothing to bind: the bindings already exist in the composition | `render-with-own-data` |
| `data` on `<Slot>` | One slot's subtree | In the Data Picker, under **Component Default Data**, then **Component Props**, scoped to the slot | `wire-slot-data` |

All three are **render-time only**. They live in your application code. Nothing extra is stored in Contentstack, and nothing about the saved composition changes.

## The decision

Ask two questions in order:

1. **Who owns the route?**
   - Studio owns it (a template renders the page), so you're on `<StudioComponent />`. External values enter through its `data` prop. See `wire-external-data`.
   - Your code owns it (a hand-written page, a loop, an embedded block), so you mount `<StudioComposition />` and supply `context`. See `render-with-own-data`.

2. **Is the data for the whole composition or for one slot?**
   - Whole composition: the props above.
   - Only for whatever an author drops into a specific `slot` prop: use `<Slot data={...}>`. See `wire-slot-data`.

The second question is independent of the first: a slot inside a `<StudioComponent />` page and a slot inside a `<StudioComposition />` subtree both carry data the same way.

## Why `context` is not `data`

They look interchangeable and are not:

- `data` (on `<StudioComponent />`) lands in the **Component Default Data** source. An author must bind a prop to it before anything renders differently. It's a new source alongside the CMS ones.
- `context` (on `<StudioComposition />`) lands at `dataSources.template`, the slot the SDK's own template fetch would fill. The composition's existing bindings resolve against it with no author action, which is what makes "render this section per array element" a one-liner.

So `data` adds a source authors bind to. `context` substitutes the template data the composition already binds to.

## A real example of each

**`data` prop**: a product page template renders on `/p/[sku]`. Live pricing comes from a commerce API. The route fetches the price and passes `data={{ livePricing }}`. An author binds the price component's prop to `livePricing.unit_price`.

**`context` prop**: an entry holds a multiple-group field of 12 features. You fetch the entry yourself and render a `feature_tile` section once per element: `<StudioComposition spec={spec} context={element} />`. Each tile's existing bindings resolve against its own element.

**`<Slot data>`**: a Hero banner exposes a `ctaSlot` so authors drop any CTA into it, but the banner owns `ctaDestination`. Props can't reach a slot, so the banner carries the value through it: `<Slot data={{ destination: ctaDestination }}>{ctaSlot}</Slot>`.

## What none of them do

| Misconception | Reality |
|---|---|
| "This stores my data in Contentstack" | No. All three are render-time props. The saved composition is unchanged. |
| "`<StudioComposition />` replaces `<StudioComponent />`" | No. `<StudioComponent />` owns a route and fetches composition + CMS data. `<StudioComposition />` renders a composition you already have data for, anywhere in your tree. |
| "`context` shows up in the Data Picker as a new source" | No. It substitutes template data. Only `data` (component or slot) adds a pickable source. |
| "A `slot` prop passes the parent's props down automatically" | No. A slot's children are author-chosen, so props can't reach them. `<Slot data={...}>` is the bridge. |
| "I need `context` to render a section outside its template" | Only if you hold the data. A section can also render through its own template route, or through `embed-composition`. |

## Next steps

| If you want to… | Skill to run |
|---|---|
| Render a composition against data you hold (loop a group array, render a section per record) | `render-with-own-data` |
| Let components dropped into a slot bind the owner's data | `wire-slot-data` |
| Bring non-CMS values into a route-rendered page | `wire-external-data` |
| Give unbound props placeholder content | `wire-component-default-data` |
| Declare the `slot` prop in the first place | `register-component` § 5a |

## See also

- `understand-canvas-vs-component`: the sibling distinction between the two mounted SDK components
