---
name: register-component
---

## When to use

Read a React component, infer a prop schema, and write a `registerLazyComponent` / `registerComponent` call so Studio's palette uses the customer's component instead of built-in defaults. Lazy by default.

Use when the user wants Studio's palette to surface their components: "make my Hero available in Studio", "Studio shows defaults instead of mine", "register components in src/components". The BYOC moment. Do NOT use to register design tokens (use `import-design-tokens`). Do NOT invent prop schemas. Only register props visible in source.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Reuse preflight: mandatory when the project already has compositions.** Before naming a single new atomic, component or Section, run [`match-existing-pattern`](match-existing-pattern.md) § Step 1b: it groups existing Sections by the schema they bind and ranks the component palette by real usage. Decomposition is where reuse has to bite. Once this step names `Heading` instead of the project's `alpha-atom-heading`, the duplicate survives into the plan and into the build. Mark every row reuse, extend, or new, and never new without having looked.

# Register a component with Studio

> **Atomic check before you register anything.** Registration is where a monolith becomes permanent. If the component renders **more than one heading / image / body / list**, stop and run [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md) first. Register its atomics and containers, not the whole thing. Registering a page-level component is how a project ends up with one Section, nothing reusable, and a coarse prop that renders blank. Exception: it is genuinely interactive (form, carousel, modal) and cannot be expressed with built-ins, then register it whole and expose an `action` prop so authors can still wire behavior.
>
> **And check reuse first:** header, footer, nav and menus are shared across every page. Register the atomics once and bind their lists through a Repeater, rather than registering a per-page variant.

## Before you start: walk Q2, Q3, Q4 of the framework

This skill runs the last three questions of the [four-question decision framework](design-component-library.md). Q1 (classify: atom, layout, or compound?) is answered before you land here. If the input is a compound, `decompose-jsx-to-atomics` or `decompose-design` decomposes it into atoms + layouts before registration. If the input is already a valid atom or layout, proceed.

- **Q2** — if an existing primitive covers the shape, reuse it; don't re-register.
- **Q3** — a prop that fails either half is refused here. Let a DS token decide instead.
- **Q4** — a prop that fails either half stays static per-Section.

If any answer is ambiguous, halt and ask the user to disambiguate. Never silently register a prop that fails Q3 or expose a prop that fails Q4.

## Before you start: pick the layer

Every component you register is one of two shapes. Decide which before writing the registration:

- **Layer 1: Atomic** (renders one CMS field). All scalar props. `<Heading>`, `<Text>`, `<Image>`, `<Button>`. This skill's default path.
- **Layer 2: Container / Skeleton / Layout** (holds other components). Has at least one `slot`-typed prop as a drop zone. `<Card>` with a body slot, `<Split>` with left+right slots. Same skill. § "Exposing extensible regions with `slot` props" (in step 6) covers it.

If the thing you want to register is neither: a pure layout primitive (Grid, Stack, Container, Box), a whole page-shaped composition, or a component with an array-of-objects prop. **Stop.** Read [From designs to Sections: the three-layer mental model](decompose-design.md) first. It's a 10-minute page that saves hours of "why doesn't my Grid work in Studio."

## Context

Studio composes pages from React components. By default it uses its **own** built-ins (Hero, Card, Button) so authors can play immediately, but for production, every component should come from the customer's library. Registering tells Studio's palette "use THIS component for type 'site-hero'" so authors drop branded components, not defaults.

The registration is a `registerComponent` call that names the component, gives it a unique `type`, and declares the **prop schema** Studio's right-panel will offer for binding. Prop types are strict: only the 14 in step 3. There is no `text`, `link`, `color`, or `image` (false friends from other systems).

## Task

1. **Locate the registration entry point.** Look for `src/register-components.tsx`, `src/register-studio.ts`, or `src/lib/contentstack.ts` (whichever file imports `registerComponent` or `registerLazyComponent` from `@contentstack/studio-react`). If none exists, create `src/register-components.tsx` and ensure it's imported once at app startup (before any `<StudioCanvas />` or `<StudioComponent />` mounts).

2. **Read the component at `componentPath`.** Extract the prop names and types. Source of truth ranked by reliability:
   - Explicit TypeScript interface (`interface HeroProps { … }`), most reliable
   - `propTypes` block, second-best
   - Destructured args + JSDoc comments, fallback only

3. **Map each prop to a Studio prop type.** Use the **exact** strings below (14). Anything else is rejected:

   | Source shape | Studio prop type |
   |---|---|
   | `string` / `string \| undefined` | `string` |
   | plain-text-only `string` | `plaintext` (Single / Multi Line only) |
   | `number` | `number` |
   | `boolean` | `boolean` |
   | `string` constrained to known values (union literal, enum) | `choice` (set `options:` to the literal values. Write `defaultValue` as an **array** (`["centered"]`) for both single- and multi-select, per [`wire-component-default-data`](wire-component-default-data.md)) |
   | URL string used as `href` | `href` |
   | URL string used as image `src` | `imageurl`, always bound to `<file_field>.url` (never the asset object). Alt text is a separate `string` prop bound to the asset's `description` |
   | ISO date string | `datestring` |
   | array | `array`, binds to a **multi-value field** (Reference multi, Group multi, Modular Block, scalar multi). **`items` is required** (the per-item prop, e.g. `items: { type: "string" }`, or `items: { type: "any" }`). Reference sources need `data_sources.resolvedReferences`. Groups / Modular Blocks / scalar multi-values live on the entry and need no resolution. See [`register-component-prop-contracts`](register-component-prop-contracts.md) § Array & object props: binding rules |
   | object | `object`, binds when the shape matches an entry Group / Global Field. **`properties` is required** (a nested `props`-style map, one entry per sub-field). See [`register-component-prop-contracts`](register-component-prop-contracts.md) § Array & object props: binding rules |
   | React `children` / placeholder for extensible region | `slot`, fillable at template time via `use-section-slot` § component-slot-prop placement. The prop turns that region of the component into an author-controlled drop target. No `defaultValue` (slots start empty). |
   | rich text (JSON RTE field, HTML payload) | **`json_rte`**, not `string`. RTE renders markup, and `string` would show it as literal `<p>` text. |
   | unknown / can't infer, and the value is a **primitive** | `any`, **never for object- or array-shaped data.** See the flatten trap below |
   | A callback an **author** should be able to point at your app's logic (`onClick`, `onSelect`, `onSubmit`) | **`action`**: the author picks a registered studio function. Your component just calls the prop. Needs `registerStudioFunctions`. See [`wire-studio-state`](wire-studio-state.md). **Omit this and interactivity stays hardcoded**, so the component is a black box authors can't wire |

   ### The `any` flatten trap: why structured data renders blank

   `any` is not a harmless catch-all. The binder runs a **recursive single-key unwrap** on every prop type except `object` and `array`:

   ```js
   // Unwrap single-key objects (common in Contentstack Modular Blocks)
   // We only do this if we are not explicitly expecting an object or array.
   if (type !== "object" && type !== "array" && !handledRepeaterContext) {
     resolvedData = getFlattenedData(resolvedData);
   ```

   and `getFlattenedData` descends **as long as the object has exactly one key**, ignoring `$` and `_metadata`:

   ```js
   const keys = Object.keys(data).filter((k) => k !== "$" && k !== "_metadata");
   if (keys.length === 1) return getFlattenedData(data[keys[0]]);   // recurses
   ```

   **So a single-field block bound to an `any` prop is silently replaced by its inner value.** A block like `image_grid → { image: [...] }` or `tabs → { tabs: [...] }` has one real key, so the object you expected never arrives. The component receives the bare inner array. Read it as an object and every lookup is `undefined`. The array's indices surface as `{0,1,2,3}`. **Blank render, no error, nothing in the console.** The `_metadata` exclusion makes it worse: a block carrying one field plus `_metadata` still counts as single-key and still unwraps.

   **The fix is the prop type, not the data.** `object` and `array` are the only two types that skip the unwrap:

   | The bound field is | Use | Why |
   |---|---|---|
   | A Group / Global Field / whole block object | **`object`** | Skips the unwrap. The shape arrives intact |
   | A list: Modular Blocks, multi-Reference, multi-Group, scalar list | **`array`** | Skips the unwrap. Render with `.map()` |
   | A genuine primitive of unknown type | `any` | Flattening a primitive is a no-op, so it's safe here only |

   Match the type to the **real** shape. "The shape varies per block" is not a reason to reach for `any`. It's a reason to use `object`.

   This is a **resolver-level** behavior (`retrievePropValue`), so it bites UI / picker-authored bindings exactly as it bites API-authored ones, not an API-only footgun. It is also **not specific to Modular Blocks**: any single-key object collapses: a Group with one sub-field, a single-item wrapper, a block carrying one field plus `_metadata`. Rule of thumb: whenever the value you want is an object or a list, type the prop `object` / `array`. `any` is safe only for a genuine primitive.

   **These 14 strings govern YOUR registered components only.** Studio's built-in nodes (`header`, `plain-text`, `rich-text`, `image`, …) carry their own prop-type vocabulary. Reading an existing composition and copying a built-in's prop type into your registration can produce a string outside the 14, which is rejected. The two vocabularies overlap in places (both use `plaintext`, for example) and diverge in others. Never transplant between them. Built-in node types are cataloged in [`author-composition-bindings`](author-composition-bindings.md) § Built-in node `type` values.

4. **Set `defaultValue` for every prop** where the component has a default value in its source. The default appears as the palette tile preview. Without it, the tile renders blank and authors don't know what the component looks like. Use `defaultValue:` exactly, NOT `default:` (the latter is silently ignored).

5. **Ship a `thumbnailUrl`: every registration, no exceptions.** (This and the `studioAttributes` contract below are two of the ten in [`complete-the-build`](complete-the-build.md). Both ship in the same commit as the registration, never as a follow-up.) `thumbnailUrl` defaults to `""` in the registry, and Studio then renders a **text placeholder** instead of a preview. A palette of twenty text placeholders is unusable for the marketers this whole exercise exists to serve, and nothing errors, so it ships unnoticed.

   Rules that matter:

   - **Inline SVG data URI**, built with `encodeURIComponent`. **Never a CDN/asset URL**. The palette renders inside Studio's iframe, where external requests hit CORS or fail silently, leaving you back at a blank tile.
   - **Brand tokens for colors**, not invented hex.
   - **Preview the shape, not the pixels**: the thumbnail says what kind of thing this is (atomic / slot-shell / pattern).

   ```ts
   // Inline SVG → data URI (no network request from the canvas iframe). Swap the fills for brand tokens.
   const thumb = (svg: string) => `data:image/svg+xml,${encodeURIComponent(svg)}`;
   const HeroGlyph = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80"><rect width="120" height="80" fill="#f4f4f7"/><rect x="12" y="20" width="72" height="10" fill="#6c5ce7"/><rect x="12" y="38" width="52" height="6" fill="#a0a0b0"/><rect x="12" y="54" width="28" height="10" rx="2" fill="#6c5ce7"/></svg>`;

   registerLazyComponent(
     {
       type: "site-hero",
       displayName: "Hero",
       sections: ["Acme · Patterns"],
       thumbnailUrl: thumb(HeroGlyph),   // data:image/svg+xml,...
       props: { /* … */ },
     },
     () => import("./components/Hero").then((m) => m.Hero),
   );
   ```

   **One config object, not component-then-config.** `registerComponent(Hero, { name, … })` **throws `Component type is required.`** Verified against `@contentstack/studio-react@2.0.1`: `registerComponent` takes *one element* of the array `registerComponents` takes, so a component passed first is read as the config and `type` comes back undefined. **`type` and `component` are the only required fields**. `registerComponents([{ … }], options?)` takes an array of the same shape. The one two-argument form is `registerLazyComponent(config, loader)`: the config (everything except `component`) first, then the loader.

   **Retrofitting an existing registration file?** Every registration without `thumbnailUrl` is a blank tile today. Sweep them all: `grep -cE "register(Lazy)?Component\(" <file>` vs `grep -c "thumbnailUrl" <file>`. The counts must match.

5b. **Next.js App Router: registration must run in the CLIENT realm.** A registered component that is (or renders) a `"use client"` component cannot be registered from a Server Component module graph. On the server the SDK sees a client reference, and Next throws at render time ("Attempted to call the default export of \<module\> from the server but it's on the client") or the palette silently comes up empty because the registry that got populated was the server-side one.

   The rule: **`registerComponents()` runs from the same client boundary that runs `studioSdk.init`.** `install-studio` already creates one for init (`app/studio-init.tsx`, `"use client"`, side-effect import of `@/lib/contentstack`). Put the registration import there too, so both land in the client bundle in the right order:

   ```tsx
   // app/studio-init.tsx
   "use client";
   import "@/lib/contentstack";        // studioSdk.init
   import "@/lib/studio-components";   // registerComponent calls — SAME client boundary
   export function StudioInit() { return null; }
   ```

   Do **not** import the registration module from `app/layout.tsx`, a `page.tsx` Server Component, or any non-`"use client"` module. Pages Router / Vite / Remix don't have this split. A module-scope import in `_app.tsx` or `main.tsx` is fine. Related: [`install-studio`](install-studio.md) § App Router init boundary, and [`troubleshoot-ssr-rendering`](troubleshoot-ssr-rendering.md) for the registry-singleton symptoms.

6. **Write the registration: prefer LAZY by default.** Append (or update) the registration file. The recommended shape is **lazy**: the component is downloaded only when it first renders, keeping the initial bundle small and code-splitting each registration automatically. `registerLazyComponent` wraps the loader with `React.lazy` + `Suspense` for you.

   ```ts
   import { registerLazyComponent } from "@contentstack/studio-react";

   registerLazyComponent(
     {
       type: "site-hero",                                  // componentType — unique UID
       displayName: "Hero",                                // componentName — palette label
       props: {
         headline:    { type: "string",   displayName: "Headline",    defaultValue: "Welcome" },
         description: { type: "string",   displayName: "Description", defaultValue: "Lorem ipsum" },
         imageUrl:    { type: "imageurl", displayName: "Image",       defaultValue: "https://…" },
         ctaHref:     { type: "href",     displayName: "CTA Link",    defaultValue: "/get-started" },
         layout:      { type: "choice",   displayName: "Layout",      defaultValue: ["centered"], options: ["centered", "split"] },
         cta: {                                            // object: `properties` is required
           type: "object", displayName: "CTA",
           properties: {
             label: { type: "string", defaultValue: "Get started" },
             href:  { type: "href",   defaultValue: "/get-started" },
           },
         },
         features: {                                       // array: `items` is required
           type: "array", displayName: "Features",
           items: { type: "string", defaultValue: "Feature item" },
           defaultValue: ["First feature", "Second feature"],
         },
       },
     },
     () => import("./components/Hero").then((m) => m.Hero),  // ← LAZY loader: resolve to the component itself
   );
   ```

   **The loader resolves to the component, not the module.** `registerLazyComponent` wraps whatever the promise yields as the `default` of a `React.lazy` module, so `() => import("./components/Hero")` hands React a module object and the render fails. For a default export write `.then((m) => m.default)`.

   **5a. Exposing extensible regions with `slot` props.** To let template authors drop content into a region of the component (a card body, a sidebar, a CTA area), declare a `slot`-typed prop. The component renders the prop wherever the extensible region should appear. Studio surfaces it as a drop target for any component or Section.

   ```ts
   import { registerLazyComponent } from "@contentstack/studio-react";

   registerLazyComponent(
     {
       type: "site-card",
       displayName: "Card",
       props: {
         title: { type: "string", displayName: "Title", defaultValue: "Card title" },
         body:  { type: "slot",   displayName: "Body" },   // ← extensible region, no defaultValue
       },
     },
     () => import("./components/Card").then((m) => m.default),
   );
   ```

   The React component receives the slot as a prop (or via `children`, depending on what its TypeScript interface declares) and renders it inside its tree:

   ```tsx
   function Card({ title, body }: { title: string; body: React.ReactNode }) {
     return <div className="card"><h3>{title}</h3>{body}</div>;
   }
   ```

   At template-authoring time, the slot region shows as a dashed drop target. Authors drop a component or Section into it (see `use-section-slot` § component-slot-prop placement for the canonical filling pattern). Slots take ANY component or Section. There is no type constraint. Slot fills are stored per-template, so the same Card can carry different filled content on different templates.


   **5b. The two valid registration shapes:**

   | Shape | Call | When |
   |---|---|---|
   | **Lazy (default)** | `registerLazyComponent(config, () => import("./Foo").then((m) => m.Foo))` | Every BYOC registration unless tiny+hot. |
   | **Eager** | `registerComponent({ …, component: Foo })`, `Foo` a function with ≥1 parameter (an ordinary React component) | Tiny components on hot paths. |

   ```ts
   registerLazyComponent(config, () => import("./components/Hero").then((m) => m.Hero))  // ✅ LAZY
   registerComponent({ ...config, component: Hero })                                     // ✅ EAGER — function Hero(props) {…}
   registerComponent({ ...config, component: (props) => createElement(Hero, props) })    // ✅ EAGER — wrap arity-0
   ```

   **`component: () => import("./Foo")` runs, but does not type-check.** In 2.0.1 `registerComponent` still detects a parameter-less function as a lazy thunk at runtime, but `component` is typed `(props?) => ReactNode`, and a `Promise` of a module is not a `ReactNode` (`TS2322` under `@types/react` 19). Use `registerLazyComponent` so `tsc` and the build pass.

   **Arity-0 trap.** A parameter-less function that does NOT return a Promise (e.g. `function Header() {…}`) is treated as a lazy loader, called outside render, and throws React #321 "Invalid hook call". Rule: **lazy goes through `registerLazyComponent`; an eager component takes a `props` parameter.**

   **5c. Design tab (`styles`) and design props.** `styles` is an **object of style groups**, not an array. Each key is one group in the Design panel. The `default` group's classes arrive as `className`, every other group as a prop named after its key, and the component must apply them or the author's edits never reach the DOM. `styleSections` takes `"block"`, `"text"`, `"all"`, `"none"`, or a list of sections (`"size"`, `"spacing"`, `"typography"`, `"background"`, `"border"`, …):

   ```ts
   registerComponent({
     type: "acme-box",
     component: Box,
     wrap: false,
     props: {
       paddingBlock: {                                  // design prop: key is a camelCase CSS property
         type: "choice",
         design: true,
         options: [
           { label: "None",    value: "0" },
           { label: "Compact", value: "var(--spacing-8)" },
           { label: "Roomy",   value: "var(--spacing-16)" },
         ],
         defaultValue: "var(--spacing-8)",
       },
       children: { type: "slot" },
     },
     styles: {
       default: { displayName: "Box", styleSections: ["background", "border"] },  // → className
     },
   });
   ```

   `design: true` (only on `choice` and `string`) makes a prop a per-breakpoint CSS value edited in the Settings tab. The component receives a **generated class name** under that prop, not the CSS value, and applies it (`className={paddingBlock}`). Never name a design prop or a style group after another prop. For when to use design props versus a plain `choice` menu, see [`design-component-library`](design-component-library.md) § Design props.

7. **Confirm Studio palette shows the new tile.** **Restart the dev server first** if you changed an existing registration (see the restart rule below). Open the canvas, switch the palette accordion to **Registered Components**, find `Hero`. **The tile must show the thumbnail image**. A text placeholder means `thumbnailUrl` is missing or the data URI is malformed. A broken-image icon means you used an external URL and the iframe blocked it. The tile preview itself renders from the `defaultValue`s. If that area is blank, a prop is missing a default or the prop type was wrong.

   **Headless check (no Studio UI, dev only).** The project's registered-components list read from Studio's side can stay empty, so it can't tell you what an author will see in the palette. Read the app's own registry instead: open the canvas route (`/canvas`) in a browser, then in the DevTools console run

   ```js
   globalThis.__contentstack_studio_registry_v1.componentRegistry
     .getComponents({ registry: "user-defined" })
     .map((c) => [c.type, c.displayName, c.sections, Object.keys(c.props)])
   ```

   That is the same object `getComponentRegistryInstance().getComponents()` returns. `getComponentRegistryInstance` is exported by `@contentstack/studio-registry`, not by `@contentstack/studio-react`, and the global slot name is an SDK internal (verified on 2.0.1), so use this for debugging only and never ship code that depends on either. Every `type` you registered must be listed, with the `sections` and props you expect.

   **Restart the dev server after changing a registration.** The registry lives on `globalThis` and skips a `type` it already holds (see [`register-component-pitfalls`](register-component-pitfalls.md) § duplicate `type`). After you edit a registration (props, defaults, `component`, `styles`), hot reload re-runs the module, but the running server keeps the old entry while the browser loads the new one. The result is a hydration mismatch, old markup from the server and new in the browser, with no hint why. Stop and restart `next dev` (or the equivalent) every time.

## Inputs needed from the user

1. `componentPath`: file path to read.
2. `componentName`: display label.
3. `componentType`: unique kebab-case UID (reject duplicates. Check the registration file before writing).

Do NOT invent component paths. If the user just says "register my Hero" without a path, ask which file.

## The registration contracts: read the one you need

Registration has four contracts a component must honour. They are reference material,
split out so a task loads only what it touches.

| Read this | For |
|---|---|
| [`register-component-prop-contracts`](register-component-prop-contracts.md) | Array and object binding rules, the bound-fields-only fetch, image (`.url`) and link signatures, `{{entry.*}}` resolution |
| [`register-component-render-contracts`](register-component-render-contracts.md) | Layout-agnostic rule, null-safe rendering |
| [`register-component-cslp`](register-component-cslp.md) | `$` CSLP props and the `studioAttributes` contract. **Both or neither.** |
| [`register-component-pitfalls`](register-component-pitfalls.md) | What fails silently, and why. **Read before reporting done.** |

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] The registration file contains a `registerLazyComponent` (or `registerComponent`) call for the supplied `componentType` that did not exist before this skill ran.
- [ ] **The component spreads `studioAttributes` on its root element** (or the registration sets `wrap`), verified in the DOM by a `data-cslp` on the root. Without it the node has no CSLP tag and Visual Editor cannot select it.
- [ ] **Every bindable prop that renders visible content spreads its `$`-twin** on the element rendering it, verified by a `data-cslp` on each of those elements.
- [ ] **An empty bound value still renders its element** when its `$`-twin is present (not `null`), so a new entry's field can be clicked, and decorative overlays over images have `pointer-events: none` ([`make-visual-editor-editable`](make-visual-editor-editable.md) § 4–5).
- [ ] Every prop on the source component's TypeScript interface (or propTypes) appears in the `props:` object, no prop dropped silently.
- [ ] Every `type:` value is one of the 14 allowed strings (`string`, `plaintext`, `boolean`, `number`, `choice`, `href`, `imageurl`, `datestring`, `array`, `object`, `slot`, `json_rte`, `any`, `action`), not `text`, `link`, `color`, or `image`.
- [ ] **Any callback an author should control is an `action` prop**, not a hardcoded handler. Otherwise the component's behavior is fixed at build time. See [`wire-studio-state`](wire-studio-state.md).
- [ ] Every `choice` prop's `defaultValue` is an array (`["centered"]`), for single- and multi-select alike. It works on every SDK version. A bare value (`"centered"`) is accepted for single-select only from `studio-registry` 1.7.0, and multi-select always requires the array. Same rule as [`wire-component-default-data`](wire-component-default-data.md).
- [ ] `defaultValue:` (not `default:`) is set on every prop where the source component has a default. **Exception: `slot` props never carry a `defaultValue`**, they start empty until template authors fill them.
- [ ] Choice props include an `options:` array of the allowed literal values.
- [ ] The registration file is imported once at app startup, verified by grep for the import in `main.tsx` / `_app.tsx` / `App.tsx`.
- [ ] Studio's **Registered Components** palette accordion shows the new tile with the supplied `displayName`.
- [ ] The tile preview renders (not blank) because the defaults are populated.
- [ ] The registration follows one of the two valid shapes: **lazy** (`registerLazyComponent(config, () => import("./Foo").then((m) => m.Foo))`, the loader resolving to the component itself) OR **eager** (`registerComponent` with `component:` a function with at least one parameter, i.e. an ordinary React component). The default recommendation is lazy. A zero-parameter function in `component:` that does NOT return a Promise triggers React #321 / "Invalid hook call" at render.
- [ ] Every `object` prop declares `properties` and every `array` prop declares `items`, and the registration file passes `tsc` against the installed SDK.
- [ ] Dev only: the console registry check (step 7) lists every registered `type` on `/canvas`, read after a dev-server restart.
- [ ] The component is **layout-agnostic**, `width: 100%` of its container, no hard-coded `max-width` to "protect" against wrong contexts, no styles that rely on a specific ancestor selector (`.fs-grid > .fs-card { ... }`). Layout sizing is delegated to the parent Section, not baked into the component.
- [ ] **Call-site literal sweep**. If this component is already used in production code, grep every JSX use of it. Every literal prop set at a call site (`isInteractive={false}`, `variant="compact"`, `columns={3}`, `isLogoBgWhite={false}`) becomes a `defaultValue` on the corresponding registered prop, or a named preset. Skipping this is the single most common cause of "composed page looks 80% right but wrong on hover/motion/spacing." Sample grep: `rg -t ts -o '<ComponentName[^>]*/?>' src | head`. If the component is new (no production call sites yet), acceptance is trivially satisfied, but state that explicitly.
- [ ] **Image props**: every `imageurl` prop is bound to `<file_field>.url`, alt text is its own `string` prop bound to the asset's `description`, and the prop's TS type still accepts `string | { url?: string } | null | undefined` with internal coercion as a safety net. See [`register-component-prop-contracts`](register-component-prop-contracts.md) § Image props.
- [ ] **Tolerant link signatures**: every `href`-typed prop binds against a link field's `href` leaf (never the whole link object). Where the design mandates a single link prop, the component coerces `string | {title, href}` inside via `href()` / `label()` helpers. See [`register-component-prop-contracts`](register-component-prop-contracts.md) § Tolerant link signatures.
- [ ] **Palette group + thumbnail**: the registration declares `sections: ["<Brand> · Elements | Patterns | Layouts"]` (never `"Template"` or `"Section"` in the name) and a `thumbnailUrl` data URI that visually previews the tier (step 5).

## After registering: plan your Section shape

Register the component first. Then decide which Section(s) to author in Studio for it.

- **Compound component that iterates internally** (say `<BlogArticle>` doing `.map(sections)`, `<CardList>` doing `.map(related_posts)`): **build top-down**. Author the wrapping Simple Section first, one Section that wraps the whole compound. Studio renders your existing page inside its canvas in ~5 minutes with no code changes. Then decompose one Section per iteration level as you need each to become author-editable.
- **Atomic component that renders one shape** (`<Card>` bound to card_ref, `<Hero>` bound to hero_group): author its Simple Section directly. Compose it later inside a List Section when a parent iteration needs to drop it as a slot's default content.

Both directions produce the same Section chain in the end. Top-down is faster for existing compound-heavy apps. Bottom-up has a cleaner mental model for greenfield.

Use [`build-section`](build-section.md) (or [`build-repeating-section`](build-repeating-section.md) for List Sections) to author each Section. The skill walks the Studio-UI flow. 

## See also

- `wire-component-default-data`: for components whose defaults aren't representable as static `defaultValue:` literals
- `use-section-slot`: fill a `slot`-typed prop on a registered component (the `component-slot-prop` placement mode), or carve a Section Slot inside one
- `wire-slot-data`: carry data the component holds into whatever an author drops into its `slot` prop
- `import-design-tokens`: register your design system after registering components
