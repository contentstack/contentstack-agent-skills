---
name: wire-studio-state
---

## When to use

Wire shared state and app behavior into Studio: declared state variables authors can bind, a custom store (Redux / Zustand / signals / web storage) via `getState`/`setState`, and named functions authors attach to buttons through `action` props.

Use when a composition needs state shared across components, or an author needs to wire a button to app logic. Phrases: "share state between sections", "cart count in Studio", "use my Redux store", "Bring Your Own State", "BYOS", "author should pick which function the button calls", "action prop", "stateVariable", "getState/setState". Do NOT use for external read-only data passed once into a page (that's `wire-external-data`), for personalization branching (`wire-variant-alias`), or for plain per-prop defaults (`wire-component-default-data`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Wire Studio state + functions (BYOS)

## Preflight: is BYOS in the installed SDK? Check the EXPORT, not the version

**Runtime-verified, and the reason a version check is not enough:** public npm's `@contentstack/studio-react` **`1.7.0` does NOT contain BYOS**: zero occurrences of `useStudioState` in its `dist`. `1.9.0` (the `latest` tag on 2026-10-05) does. Other builds can also report `1.7.0` and still carry the feature. **Same version number, different contents.** So never gate on a version string. Gate on whether the symbol is actually there:

```bash
npm ls @contentstack/studio-react --depth=0        # what is installed
grep -rq "useStudioState" node_modules/@contentstack/studio-react/dist \
  && echo "BYOS present" || echo "BYOS ABSENT"
```

Do **not** use `node -e "require('@contentstack/studio-react/package.json')"`: the package's `exports` map doesn't expose `./package.json`, so it dies with `ERR_PACKAGE_PATH_NOT_EXPORTED`. `npm ls` works.

**Availability has two independent halves**: the SDK in your app and the Studio editor. The editor half (declared variables in the Data Picker, the `action` prop picker) is **not yet rolled out on every data center**, so a stack whose editor lacks it can't author BYOS even with a correct SDK build. Check the DC alongside the export: [`analyze-project-fit`](analyze-project-fit.md) § 2b.

**`BYOS ABSENT` means stop.** Releases up to `1.7.0` are ABSENT; `1.9.0` ships it. This chapter applies only to a build that ships it. Either obtain such a build, or fall back to component-local state (a plain `useState` inside one registered component, no author binding, no cross-component sharing) and say so explicitly. Don't emit `useStudioState` against a package that can't import it.

## Context

Registered components give Studio your markup. **BYOS gives it your behavior.** Three independent pieces:

| Piece | Gives you | API |
|---|---|---|
| **State variables** | Values shared across components / sections / templates, bindable by authors | `state.variables`, `registerComponentStateVariable` |
| **Storage** | Where values live: session, local, or your own store | `storage`, `getState`, `setState`, `subscribe` |
| **Functions + action props** | Logic authors invoke by name from a button | `registerStudioFunctions`, `type: "action"` |

**Why this matters.** Without BYOS every interactive piece must be a self-contained registered component with behavior baked in: authors re-bind props and nothing else. With it, an author-dropped "Add to cart" calls your `cart:add`, and every component reading `cart:count` updates. Skipping BYOS is the difference between Studio composing your app and Studio decorating it.

## Decide what's actually needed: don't wire all three by reflex

| Evidence in the app | Reach for |
|---|---|
| Two components must agree on a value (cart count, active filter, theme) | **State variable** |
| The app already owns that state in Redux / Zustand / signals | State variable + **`storage: "custom"`** |
| Value should survive reload / revisit but there's no app store | `storage: "session"` / `"local"` |
| An author should choose what a button does | **Function + `action` prop** |
| Read-only data fetched once for a page (pricing, geo, inventory) | **Not BYOS**, `wire-external-data`'s `data` prop |
| One prop varying per template instance | **Not BYOS**, `expose-section-props` |

## Task

1. **Declare the variables.** Only **declared** variables are author-bindable. Undeclared keys work in code via `useStudioState("key")` but never reach the Data Picker. Pick the tier deliberately:

   - **`init` tier**: `state.variables` in `studioSdk.init`, for keys the app owns globally.
   - **`component` tier**: `registerComponentStateVariable(key, def)` at component **module scope**, for keys a component owns.

   ```ts
   registerComponentStateVariable("cart:filter", { type: "string", defaultValue: "all" });

   export function CartFilter() {
     const [filter, setFilter] = useStudioState<string>("cart:filter");
     // …
   }
   ```

   **Precedence (observed runtime behavior):** `component` **beats** `init` for the same key, deterministically and **regardless of module evaluation order**. Same-tier re-declaration keeps the **first**. A runtime `set` always beats a declared default. So a component can own its key without coordinating with the init file.

   Types: `string · number · boolean · choice · array · object`. `choice` **requires** `options`.

2. **Choose storage.** Omitting `state` entirely keeps the SDK's in-memory Map (back-compatible). Providing `state` without `storage` gives the built-in **session** store, unless `getState`/`setState` are present, which implies `custom`.

   | `storage` | Behavior | Requires |
   |---|---|---|
   | `"session"` | `sessionStorage`, survives reloads, cleared with the tab | - |
   | `"local"` | `localStorage`, survives across visits | - |
   | `"custom"` | delegates to the app's store | **`getState` + `setState`** |

   `storageKey` (built-in stores only) defaults to `"cs-studio:state"`.

3. **For `custom`, wire all three functions, and don't skip `subscribe`.**

   ```ts
   state: {
     storage: "custom",
     getState: (key) => store.getState().studio[key],
     setState: (key, value) => store.dispatch({ type: "studio/set", key, value }),
     subscribe: (key, listener) => store.subscribe(listener),   // returns unsubscribe
     variables: { "cart:count": { type: "number", defaultValue: 0 } },
   }
   ```

   `getState`/`setState` are mandatory for `custom`. **Without `subscribe` the flow is one-way**: Studio's own writes land, but a `dispatch` from elsewhere in the app never re-renders Studio-bound components. Wire it whenever anything outside Studio mutates these keys.

   A `getState` returning a fresh object/array per call is safe: the hook caches per key and re-reads only on a version change, so it won't trip React's "getSnapshot should be cached" warning.

4. **Read/write from the right place.**
   - In React, use `const [v, setV] = useStudioState<T>(key)`, `setV(next)` or `setV(prev => …)`. SSR-safe: the server renders the declared default and subscribes only on the client.
   - Outside React (handlers, analytics, business logic), use `studioState.get / set / subscribe / reset`. Same store instance as the hook and author bindings.
   - `getStudioStateSnapshot()` returns `[{ key, value }]` for declared variables, which is what the picker lists.

5. **Register functions if authors should choose behavior.** `ctx` is `{ get, set, subscribe }` over the same store. Registrations **merge**. Re-registration overwrites with a dev warning (HMR).

   ```ts
   registerStudioFunctions({
     "cart:add": (ctx, args) => {
       ctx.set("cart:count", (prev) => (prev ?? 0) + 1);
       ctx.set("cart:last_added", args?.sku ?? "");
     },
   });
   ```

   Namespace the names (`cart:add`, `coupon:apply`): the registry is flat and a collision silently overwrites in production, where the dev warning doesn't fire.

6. **Expose `action` props so authors can attach them.** `action` is a first-class prop type alongside `string`, `number`, `boolean`, `choice`, `href`, `imageurl`, `datestring`, `array`, `object`, `slot`, `json_rte`, `any`, see [`register-component`](register-component.md).

   ```ts
   props: {
     label:      { type: "string", defaultValue: "Add to cart" },
     onCtaClick: { type: "action", displayName: "CTA Click Function" },
   }
   ```

   The component just calls the prop, `onCtaClick?.({ sku })`. The SDK wraps the author's chosen function. Extra positional args are forwarded verbatim, so `onSelect(id, meta)` loses nothing. From your own code, call `callStudioFunction("cart:add", { sku })`.

7. **SSR: declare on the client before hydration.** Server init declares at module scope, but the **client** init is usually a lazy import that evaluates after hydration, so state-bound nodes hydrate against undeclared keys and mismatch the server HTML. Statically import a module that declares:

   ```ts
   // lib/register-state-variables.ts — imported STATICALLY from _app / root layout
   registerGlobalStateVariables(studioStateConfig.variables ?? {});
   ```

   That declares at the `init` tier, so component declarations still win.

8. **Verify.** Open the Data Picker on a component prop: every **declared** variable appears under Component Props with its current value. Bind one, change it from a second component, and confirm the first re-renders. For `custom`: mutate the key from outside Studio (a dispatch in the console) and confirm the bound component updates. If it doesn't, `subscribe` is missing. For an `action` prop: bind it, click in the canvas, and confirm the registered function ran.

## Inputs needed from the user

1. `variables`: the keys to share, each with type + default (and `options` for `choice`). Derive candidates from the app: values already lifted into a store or passed through several components.
2. `storage`: `session` / `local` / `custom`. Default `session` unless the app already owns the state.
3. `getState` / `setState` / `subscribe`: required for `custom`. Ask which store and how it reads/writes.
4. `functions`: named logic authors should be able to attach, if any.

## Acceptance

- [ ] **Preflight passed**: the installed `@contentstack/studio-react` actually exports the state APIs (≥ 1.7.0). Nothing was written against a version that can't import them.
- [ ] Every variable authors need is **declared** (init or component tier): nothing relies on an ad-hoc key being bindable.
- [ ] The tier choice is deliberate, and no key is declared in both places expecting init to win.
- [ ] `storage` is set explicitly, and for `custom` both `getState` and `setState` exist.
- [ ] **`subscribe` is wired** whenever anything outside Studio mutates these keys, verified by mutating from outside and watching a bound component update.
- [ ] Declared variables appear in the Data Picker under Component Props. A value set by one component is observed by another.
- [ ] If authors should control behavior, functions are registered **and** exposed via `action` props, not hardcoded in the component.
- [ ] SSR apps statically import a module calling `registerGlobalStateVariables`. No hydration mismatch on state-bound nodes.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Expecting an undeclared key in the Data Picker | Only declared variables are author-bindable. Ad-hoc keys are code-only by design | Declare it at the init or component tier |
| `storage: "custom"` without `getState`/`setState` | The SDK can't read or write a store it doesn't know | Both are mandatory for `custom` |
| Custom store without `subscribe` | One-way: external mutations never re-render Studio-bound components. Looks like a stale-render bug | Pass `subscribe(key, listener)` returning an unsubscribe |
| Lazy client init on an SSR app | Client declarations evaluate after hydration, so state-bound nodes mismatch the server HTML | Static import + `registerGlobalStateVariables` (step 7) |
| Assuming init `state.variables` overrides a component declaration | Component tier wins by design, regardless of module order | Component declaration is authoritative. Init covers keys no component owns |
| Interactive components with no `action` props | Authors can't attach behavior: interactivity stays hardcoded and the component is a black box | Add `type: "action"` props and register the functions |
| Unnamespaced function names | Flat registry. A collision overwrites silently in production (the dev warning is dev-only) | Namespace them: `cart:add`, `checkout:apply` |
| Using BYOS for read-only page data | Shared mutable state is the wrong tool for a value fetched once | `wire-external-data`'s `data` prop |

## See also

- [`register-component`](register-component.md): where `action` props are declared
- [`wire-external-data`](wire-external-data.md): read-only external data, not shared state
- [`wire-variant-alias`](wire-variant-alias.md): user-state branching via Personalize
- [`expose-section-props`](expose-section-props.md): per-instance prop overrides
