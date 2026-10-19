---
name: wire-slot-data
---

## When to use

Wrap a component's `slot` prop in `<Slot data={...}>` so components an author drops into the slot can bind the owner's data via Component Default Data.

Use when a registered component exposes a `slot` prop AND holds data the dropped component needs (a Hero banner owning its CTA's destination). Phrases: "pass data into a slot", "slot children can't see props", "dropped component needs the parent's value". Do NOT use to declare the `slot` prop (`register-component`) or to carve a Section Slot (`use-section-slot`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Wire Slot Data

## Context

A `slot`-typed prop is a region an author fills by dropping components into it. The owning component doesn't know what lands there, so it can't pass props to it: the moment a spot becomes a slot, prop-passing stops working for that subtree.

`<Slot data={...}>` bridges that. Wrap the slot's value and the components dropped inside can **bind** those keys through the `component_props` data source, with the nearest slot winning over data provided higher up.

Reach for it when **both** are true:

1. A component exposes a `slot`, a spot authors fill with whatever component fits, not one you hard-wire.
2. The owning component holds data the dropped component needs.

Two situations produce that pair, and the fix is the same for both: you're designing a fresh component and already know one region should be open, or you're opening up a spot that used to hold a fixed child receiving props directly. In the second case the data that child received still has to reach whatever replaces it.

`<Slot>` is **render-time only** (nothing is stored in the composition) and opt-in: rendering the bare slot value still works, it just carries no data.

## Task

1. **Prereq: the component is registered with a `slot`-typed prop and renders it.** See `register-component` § 5a. Exposing extensible regions with `slot` props. Without a registered slot there is no drop target and nothing to wrap.

2. **List the keys the dropped component needs.** Only values the owner holds and the child can't get itself: a destination URL, an id, a price the owner computed. Name each key by its **role in the slot**, not after the owner's variable: `destination`, not `ctaDestination`. The key names are the contract authors see in the Data Picker.

3. **Wrap the slot value, the exact `ReactNode` the renderer passed for that prop:**

   ```tsx
   import { Slot, type SlotProps, type StudioAttributes } from "@contentstack/studio-react";

   interface HeroBannerProps extends StudioAttributes {
     headline?: string;
     ctaDestination?: string;   // where the CTA should link — the banner owns this
     ctaSlot?: SlotProps["children"];
   }

   export function HeroBanner({ headline, ctaDestination, ctaSlot }: HeroBannerProps) {
     return (
       <section className="hero">
         <h1>{headline}</h1>

         {/* `ctaSlot` is an open slot — authors drop any CTA. The banner owns
             `ctaDestination`, so it carries it through the slot. */}
         <Slot data={{ destination: ctaDestination }}>{ctaSlot}</Slot>
       </section>
     );
   }
   ```

   Pass the slot prop straight through as `children`. Do not rebuild it (`Children.map` + `cloneElement`, re-wrapping each child in your own element): the renderer stamps slot identity onto that element, and `<Slot>` reads it to report the keys to the editor. Recreated children lose it: the render-time merge still happens, but the Data Picker never lists the keys.

4. **Keep `data` plain and its keys stable.** Strings, numbers, booleans, arrays, plain objects. The editor report is serialized, so functions and class instances don't survive it. A fresh object literal each render is fine (the SDK skips unchanged reports), but renaming a key breaks every binding already made against it.

5. **Rebuild the canvas bundle and reload Studio**, so the canvas runs the version of the component that wraps the slot.

6. **Bind in the canvas.** Open a composition using the component, **select a component that sits inside the slot** (not the owner). In the right panel, open the **Data** tab, click the binding chip on the prop, then open **Component Default Data** and its **Component Props** node, and pick the key. Save.

7. **For nested slots, rely on nearest-wins deliberately.** `data` shallow-merges over `component_props` inherited from further up, the same model as Repeater context. A key set both globally (the `data` prop on `<StudioComponent />`) and on a slot resolves to the slot's value inside that slot. The deepest slot wins over shallower ones.

8. **Verify on the live site**, in a normal browser tab: the dropped component renders the owner's value, even though the owner never passes it a prop.

## Inputs needed from the user

In this order. If any is missing, ask before editing code.

1. `componentPath`: the component that owns the slot.
2. `slotPropName`: which `slot`-typed prop to wrap (e.g. `ctaSlot`).
3. `dataKeys`: the mapping to expose, from key to owner value (e.g. `destination: ctaDestination`).
4. `registrationFile`: only needed if the `slot` prop is not registered yet.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, surface the failure and stop.

- [ ] `slotPropName` is registered as `{ type: "slot" }` in the component's `registerComponent` props.
- [ ] The component renders `<Slot data={...}>{slotPropName}</Slot>`, the slot prop value passed through unchanged as `children`.
- [ ] Every `dataKeys` value is JSON-plain (no functions, class instances, `Map`/`Set`).
- [ ] Selecting a component **inside** the slot in the canvas shows the keys under **Component Default Data**, then **Component Props**.
- [ ] A prop bound to a slot key renders the owner's value on the live site in a normal browser tab, verified by screenshot or rendered output.
- [ ] The slot still accepts and renders any dropped component when `data` is empty or a key is `undefined`: wrapping changes data flow, not droppability.
- [ ] For a nested slot: the inner slot's value applies inside it, and the outer value applies outside it.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Rendering the bare slot value (`{ctaSlot}`) | Dropped components have no way to reach the owner's data | Wrap it in `<Slot data={...}>` |
| Rebuilding children instead of passing the slot value through | Slot identity is stamped on the renderer's element. Recreated children lose it, so the editor never receives the keys | Pass the slot prop directly as `children` |
| Looking for the keys with the owner selected | The Component Default Data source is scoped to the selection | Select a component inside the slot |
| Binding through a CMS or external-data source | The keys only exist under Component Default Data, then Component Props | Select that source explicitly |
| Functions or class instances in `data` | The editor report is serialized. Those keys don't survive | Pass plain values only |
| Renaming a key after authors bound it | Bindings resolve to nothing, silently | Treat key names as a contract. Add a new key instead |
| Keys named after the owner's internals (`ctaDestination`) | Authors read the key in the picker with no owner context | Name by role in the slot (`destination`) |
| Same key in global `data` and slot `data` by accident | Nearest wins, so the slot value silently shadows the global one | Rename, or rely on the override deliberately |
| Using `<Slot>` on a hard-wired child | Props already reach a fixed child. The wrapper adds nothing | Pass props directly. Use `<Slot>` only for author-filled slots |
| Confusing `<Slot>` with the `slot` prop type | Different layers: the prop type declares the region, `<Slot>` carries data into it | `register-component` § 5a declares. This skill wires |
| Confusing this with a Section Slot | A Section Slot is a Smart Container element carved into a Section on the canvas | `use-section-slot` for that flow |
| Canvas not rebuilt after the edit | The canvas runs the old bundle, so no keys appear | Rebuild the canvas app and reload Studio |

## See also

- `understand-bring-your-own-data`: which of the three data surfaces fits
- `render-with-own-data`: the other bring-your-own-data surface (whole composition)
- `register-component` § 5a: declaring the `slot` prop this skill wires
- `use-repeater`: the same nearest-wins context model, for iteration
