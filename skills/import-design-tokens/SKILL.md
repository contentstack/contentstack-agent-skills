---
name: import-design-tokens
description: "Read a project's design tokens from Tailwind, CSS variables, or JSON and register them with Studio so the Design Panel offers them for spacing, colors, typography, radius, shadow."
allowed-tools: Read Grep Glob
---

## When to use

Read a project's design tokens from Tailwind, CSS variables, or JSON and register them with Studio so the Design Panel offers them for spacing, colors, typography, radius, shadow.

Use when the user wants Studio's Design Panel to show THEIR tokens instead of Studio's defaults — e.g. "use my Tailwind colors in Studio", "register my CSS variables", "I have a tokens.json from Style Dictionary". Run AFTER `register-component`. Do NOT use to register breakpoints (use `register-breakpoints`). Do NOT use to register fonts as static assets; tokens only.

# Import design tokens into Studio

## Context

Studio's right-panel **Design Panel** lets authors style component instances — spacing, color, typography. By default it shows Studio's built-in tokens (generic sans-serif, neutral grays). For a brand-consistent site, replace those with the customer's design system tokens.

The mechanism is `registerDesignTokens(tokens, options)` from `@contentstack/studio-react`. **The payload is sectioned, not flat** — colors and spacing are top-level globals; everything else nests under a section that maps to a Design-panel control. The full surface is in `docs/20-bring-your-own-components/configure-design-tokens-in-studio.md`.

| Source concept                        | Goes in                                                                                                                                               | Value shape                                                                                                |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Colors                                | `colorTokens` (global)                                                                                                                                | any CSS color string — `"#0052ff"`, `"rgb()"`, `"hsl()"`, `"var(--…)"`                                     |
| Spacing scale                         | `spaceTokens` (global)                                                                                                                                | a length **with a unit**: `` `${number}${unit}` `` (e.g. `"16px"`, `"1.5rem"`) — a bare number is rejected |
| Font sizes / weights / line-heights   | `typography.fontSize` (string), `typography.fontWeight` (**number**), `typography.lineHeight` (number or length), `typography.letterSpacing` (length) | per-field `Record<string, …>`                                                                              |
| Named text styles (incl. font family) | `typography.style[name]` → `{ fontFamily, fontWeight, fontSize, lineHeight, letterSpacing }`                                                          | `fontFamily` exists **only here**, not as a top-level token                                                |
| Radius                                | `border.radius`                                                                                                                                       | length with unit                                                                                           |
| Shadow                                | `shadow.style[name]` → `{ inset?, x, y, blur?, spread?, color? }` (a structured object, **not** a CSS box-shadow string), plus `shadow.color`         | one entry = one layer; a multi-layer shadow can't be expressed as a single token                           |

> **Do not use the old flat shape** (`color`, `spacing`, `radius`, a typography object with a top-level `fontFamily`, or `shadow` as a box-shadow string). It does **not** compile against the installed SDK — `tsc` rejects it with "Object literal may only specify known properties". The section names above are the real ones.

Tokens are read once at registration time — they don't hot-reload. If the user changes their Tailwind config, re-run this skill (or restart the app).

Reference: `docs/20-bring-your-own-components/configure-design-tokens-in-studio.md`, `docs/30-composition/style-components-with-the-design-panel.md`.

## ⛔ Prerequisites — without these the panel stays empty or locked

Registering tokens cleanly can still produce **zero visible effect**. Three conditions gate whether the author ever sees or can use them. Check all three — registering tokens against a project that fails any of them looks like a silent no-op.

1. **`allowedValuesLevel` must be set to `"tokens"` (or `"arbitrary"`).** This is the decisive one. `registerDesignTokens(tokens)` called with **no options** leaves `allowedValuesLevel` at the SDK default `"dynamic"`, which permits **only data-binding** — registered tokens never appear as selectable values, so every design control looks disabled. Always pass the options arg (Task step 4). The three levels (from `@contentstack/studio-registry` `AllowedDesignValues`):
   - `"dynamic"` (SDK default) — only data can be bound; **tokens are not pickable**
   - `"tokens"` — authors pick from your registered tokens (the design-system default; use this)
   - `"arbitrary"` — tokens, data binding, **and** free-form CSS values
2. **"Enable Freeform Feature" must be ON** at the project level (Studio → Settings → Configuration). The Design tab only renders with Freeform on; with it off the right panel collapses to **Settings only** and *no* component — not even Studio's built-ins — can be styled. (See `docs/30-composition/style-components-with-the-design-panel.md`; toggle via `configure-studio`.)
3. **Custom components need a `styles` group** in their `registerComponent` config, or they show no Design controls even with Freeform on. Built-ins have styles implicitly; your own components don't. (See `register-component` and `docs/20-bring-your-own-components/component-schema-prop-types.md`.)

If the user reports "every field is disabled" or "there's no Design tab," walk these three in order — #1 explains disabled controls, #2 explains a missing tab on *every* component (built-ins included), #3 explains a missing tab on *only their own* component.

## Task

1. **Parse tokens from `tokenSource`.**

   **`tokenSource=tailwind`** — Import the config:
   ```ts
   import config from "../tailwind.config";   // or .ts
   const theme = config.theme?.extend ?? config.theme ?? {};
   ```
   Pull `theme.colors`, `theme.spacing`, `theme.fontFamily`, `theme.fontSize`, `theme.borderRadius`, `theme.boxShadow`. Tailwind uses nested objects for color shades (`{ primary: { 500: '#…' } }`) — flatten to a token name like `primary-500`.

   **`tokenSource=css`** — Parse `:root { --primary: …; }` rules from the CSS file. Map each `--*` var to a token name under the right section (user must annotate which `--*` vars are which scope — ask if unclear).

   **`tokenSource=json`** — Parse Style Dictionary / Theo / DTCG JSON. For DTCG `$value` references, resolve them to literals before registration (Studio doesn't follow `$value` chains).

   **`tokenSource=manual`** — Ask the user to paste the token list with explicit scope annotations.

2. **Filter to the requested `scopes`** and **map each scope to its real section** (the user-facing scope names are friendly aliases):

   | `scopes` value | Target section                                                                                                                      |
   | -------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
   | `color`        | `colorTokens`                                                                                                                       |
   | `spacing`      | `spaceTokens`                                                                                                                       |
   | `typography`   | `typography.fontSize` / `.fontWeight` / `.lineHeight` / `.letterSpacing`, and `typography.style[name].fontFamily` for font families |
   | `radius`       | `border.radius`                                                                                                                     |
   | `shadow`       | `shadow.style[name]` (decompose each box-shadow into `{x,y,blur,spread,color}`)                                                     |

   Drop scopes the user didn't request. **Normalize lengths**: `spaceTokens` and `border.radius` values must carry a unit — a bare `8` is invalid, use `"8px"`.

3. **Build the `registerDesignTokens` payload.** Use the sectioned shape:
   ```ts
   const tokens = {
     colorTokens: {
       primary:      "#0052ff",
       "primary-500":"#0052ff",
       "neutral-50": "#f9fafb",
     },
     spaceTokens: { xs: "0.25rem", sm: "0.5rem", lg: "1.5rem" },
     typography: {
       fontSize:   { body: "1rem", "heading-1": "3rem" },
       fontWeight: { regular: 400, bold: 700 },          // numbers, not strings
       lineHeight: { tight: 1.1, normal: 1.5 },
       style: {
         "heading-1": {
           fontFamily: '"Inter", system-ui, sans-serif', // fontFamily lives ONLY here
           fontWeight: "700",                            // string inside style
           fontSize:   "3rem",
           lineHeight: 1.1,
         },
       },
     },
     border: { radius: { md: "0.5rem", full: "9999px" } },
     shadow: {
       style: {
         card: { x: "0px", y: "1px", blur: "3px", color: "rgba(0,0,0,0.1)" },
       },
     },
   };
   ```

4. **Call it with an explicit `allowedValuesLevel`.** This is two-arg — the options arg is what makes the tokens *usable*, not just registered:
   ```ts
   registerDesignTokens(tokens, { allowedValuesLevel: "tokens" });
   ```
   Use `"tokens"` so authors pick from the registered set (the design-system default). Use `"arbitrary"` only if the user explicitly wants authors to also type raw CSS values. **Never** omit the options arg — the default `"dynamic"` leaves the controls unusable (see Prerequisites). To *add* your tokens on top of Studio's defaults instead of replacing them, also pass `allowDefaultDesignTokens: true`; most enterprise installs want the default (replace) behaviour.

5. **Wire the call.** Add it to the same file as `registerComponent` calls (`src/register-components.tsx` or `src/register-studio.ts`). Call it **once**, before any component registrations OR before `<StudioCanvas />` mounts — whichever comes first.

6. **Verify in Studio.** Confirm the three Prerequisites first (Freeform ON, the component has `styles`, `allowedValuesLevel` set). Then open a composition with a registered component selected → **Design** tab → the controls should offer the customer's tokens by name (e.g. "primary-500", "lg") and let you select them. If the tab is missing or every control is disabled, re-check the Prerequisites — that's the cause, not the token payload.

## Inputs needed from the user

1. `tokenSource` — required. Auto-detect a default if there's an obvious match (`tailwind.config.{js,ts}` exists → suggest `tailwind`; `tokens.json` exists → suggest `json`).
2. `tokenSourcePath` — required for tailwind/css/json modes; skip for manual.
3. `scopes` — default to all five.

If the user has tokens spread across multiple sources (e.g. Tailwind colors + a separate `typography.json`), invoke this skill once per source.

## Acceptance

- [ ] `registerDesignTokens(tokens, { allowedValuesLevel: "tokens" })` exists in the registration file — **two args**, options never omitted.
- [ ] Payload uses the sectioned shape (`colorTokens` / `spaceTokens` / `typography` / `border` / `shadow`), NOT the flat `color` / `spacing` / `radius` shape.
- [ ] `tsc` (or the project's build) compiles the payload with no "unknown property" errors.
- [ ] Color values are valid CSS color strings; `spaceTokens` and `border.radius` values carry a unit; `typography.fontWeight` values are numbers.
- [ ] Shadows are expressed as `{x,y,blur,spread,color}` objects, not box-shadow strings.
- [ ] No `$value` reference strings remain unresolved in JSON-source mode.
- [ ] Prerequisites confirmed: Freeform ON, the target component has a `styles` group, `allowedValuesLevel` set — and tokens are actually selectable in the Design panel when a registered component is selected.

## Common pitfalls

| Pitfall                                                                  | Why it bites                                                                                                                                         | Fix                                                                                                   |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Calling `registerDesignTokens(tokens)` with no options                   | `allowedValuesLevel` defaults to `"dynamic"` — only data-binding is allowed, so registered tokens aren't selectable and every control looks disabled | Always pass `{ allowedValuesLevel: "tokens" }`                                                        |
| Using the flat shape (`color`, `spacing`, `radius`, a box-shadow string) | Does not compile against the installed SDK; `tsc` errors with "Object literal may only specify known properties"                                     | Use the sectioned shape — `colorTokens`, `spaceTokens`, `typography`, `border.radius`, `shadow.style` |
| Putting `fontFamily` at the typography top level                         | `fontFamily` only exists under `typography.style[name]`                                                                                              | Nest it: `typography.style.heading.fontFamily`                                                        |
| Bare numbers for spacing/radius (`8`, `0.5`)                             | `spaceTokens` / `border.radius` require `` `${number}${unit}` ``                                                                                     | Add the unit: `"8px"`, `"0.5rem"`                                                                     |
| Expecting one shadow token to hold a multi-layer box-shadow              | `shadow.style[name]` is a single `{x,y,blur,spread,color}` layer                                                                                     | Register one entry per layer, or pick the dominant layer                                              |
| Tokens registered but no Design tab appears at all                       | Freeform is off (right panel = Settings only)                                                                                                        | Enable "Enable Freeform Feature" in Studio → Settings → Configuration (`configure-studio`)            |
| Design tab appears for built-ins but not your component                  | Your `registerComponent` has no `styles` group                                                                                                       | Add a `styles` group to the component (`register-component`)                                          |
| Registering a `var(--…)` color not defined in the canvas-app stylesheet  | Studio shows the token name but the canvas renders unstyled                                                                                          | Resolve the `var()` to a literal at import time, or load the same stylesheet in the canvas app        |
| Importing Tailwind's full theme (defaults + extend)                      | Duplicate keys; first registration wins silently                                                                                                     | Read `theme.extend`, or use `resolveConfig` and the merged result                                     |
| Forgetting to re-run after editing the source file                       | Tokens are read once at startup                                                                                                                      | Add a comment in the registration file: "Re-run import-design-tokens after editing tailwind.config"   |

## See also

- `docs/20-bring-your-own-components/configure-design-tokens-in-studio.md` — full token-surface reference (sectioned schema, CSS-variable emission)
- `docs/30-composition/style-components-with-the-design-panel.md` — what the Design Panel shows authors; the Freeform requirement
- `register-component` — register components FIRST, with a `styles` group, so the Design Panel has something to apply tokens to
- `configure-studio` — enable "Enable Freeform Feature" (gates the Design tab)
- `register-breakpoints` — separate skill for responsive breakpoints
- `register-json-rte` — separate skill for JSON RTE renderer (also a registry call but unrelated to tokens)
