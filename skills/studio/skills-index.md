# Studio skills: index

The `studio` skill is the only one loaded always. It reads this file to route the rest.

Two lookups below. The **Trigger table** is exact-match against phrases in the user's message. The **Topic map** is a fallback when no phrase matches but the topic is Studio-shaped.

**Resolving a skill file:** every guide is `<name>.md` in this same folder (fallback: `../<name>/SKILL.md`).

Every name below is written `<name>` for readability. Apply this rule to each. Read them from disk. Never rely on remembered summaries. **If it doesn't resolve, say the pack looks mis-installed and name the skill. Never fall back silently to general knowledge**, because a silent fallback is indistinguishable from the pack working.

---

## Trigger table

If the user's message contains any phrase in the left column, Read the skill in the right column and follow it.

> **Mandatory atomic-and-reusable rule: applies to EVERY row below.** Never register or author a component that renders more than one piece of content. Decompose it first (`decompose-jsx-to-atomics`). Check for an existing atomic or Section before creating one. Header / footer / nav / menus are shared Sections with their menus as **Repeaters over a field**, never hardcoded lists. One atomic prop binds one CT field. See the `studio` router § Standing rule.
>
> **Mandatory plan-first rule: applies before every build row below.** If the request is to build/create/implement anything larger than one already-scoped piece ("build me a rewards page", "implement this design", "add this page to Studio", "build the site", "migrate this route"), Read [`plan-studio-architecture`](plan-studio-architecture.md) **first** and get the plan explicitly approved. Only then run the build skills it names. Skipping this is what produces a single monolithic template with no Sections, no Section Slots and no reuse, forcing the user to re-prompt. Straight to a build skill only when the user is iterating on a piece from an already-approved plan. **Exception: a whole-project ask** ("convert my project to Studio", "make it Studio-compatible") routes to [`convert-project-to-studio`](convert-project-to-studio.md) and its scoping gate first. `plan-studio-architecture` runs only if the user picks the one-page or full-site option there.

> **Mandatory auth preflight: applies before every row below.** Settle the credential before the first API call, OAuth-first per `authenticate-cma`: `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, hand the user `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (interactive, so it cannot be run for them). `403 error_code 316` means wrong org, not missing auth.

> **Mandatory done-rule: applies after every build row below.** Eight deliverables are mandatory on every build and all eight fail silently: `cslp.appendTags`, `studioAttributes` + `$`-twins per component, `thumbnailUrl` per registration, `ui_preview` per Section, stack Live Preview + preview token, the `/canvas` route, **publishing every Section and Template** (an edit creates an unpublished version. Delivery keeps serving the old one), and **a template actually composed of Sections**. A single component bound to the whole page body renders perfectly and fails no other check, so count `section-composition` nodes before reporting done. Read `complete-the-build`. It is the handover gate, and `plan-studio-architecture` commits to it up front. Never report a build finished with any row outstanding.

| If the user says… | Read |
|---|---|
| convert my project to Studio, make my project Studio compatible, Studio-compatible project, add Studio to my existing site without touching pages, minimal Studio setup, Studio as a fallback route, works with my locales in Studio | `convert-project-to-studio` |
| add Studio to my app, is my project compatible, before I install | `analyze-project-fit` |
| enable Studio, make this project Studio ready, make this project Studio enable, Studio setup, set up Studio, install Studio in my app | `convert-project-to-studio` |
| install only the Studio SDK, add Studio SDK only, package installation only | `install-studio` |
| install Live Preview, Live Preview standalone, receive edits from Contentstack | `install-live-preview` |
| install Playwright MCP, automate Studio verification, drive Studio in tests | `install-playwright-mcp` |
| install Contentstack MCP, authenticate CMA without pasting authtoken, provision via MCP tools, OAuth for provisioning | `install-contentstack-mcp` |
| which token do I use, OAuth instead of authtoken, 401 error_code 105, 422 Stack not found, authtoken is not valid, management token vs authtoken, do I have to paste a token, we're logged in with OAuth | `authenticate-cma` |
| I need https locally, mixed-content block on localhost, mkcert canvas | `setup-local-https-canvas` |
| configure Studio project, set canvas URL, set Base URL, change environment, Settings Configuration page, canvas config disabled/blank | `configure-studio` |
| enable Live Preview, set up Visual Experience, canvas is blank, preview events not arriving | `enable-visual-experience` |
| provision Studio project, create compositions CT, delivery token setup | `provision-studio-project` |
| seed the stack, create page content types, seed entries | `provision-studio-stack` |
| register breakpoints, tablet/mobile switcher, canvas breakpoints | `register-breakpoints` |
| which components should I register, design our Studio library, what should the component library look like, atomic + layout primitives for Studio, we're starting fresh: what do we register, map our design system to Studio | `design-component-library` |
| is this atom or layout, classify this component, what shape is this, audit my registered components, which of my registrations are compounds, sanity-check my palette, review this component before I register it | `classify-existing-component` |
| match the existing design, build it like the other templates, follow the existing pattern, same as the current sections, what pattern do the existing templates use, how are the existing templates built, don't rebuild it differently | `match-existing-pattern` |
| compose a hero from primitives, build a feature grid in Studio, which primitives for this testimonial, translate this section into a primitive tree, compose a pricing tile | `compose-marketing-section` |
| register component, add my React component to Studio, palette missing my components, no thumbnail on my components, palette shows text placeholder instead of image | `register-component` |
| array prop binding rules, object prop shape, imageurl accepts string or object, link prop leaves, entry.title not resolving | `register-component-prop-contracts` |
| component must be layout-agnostic, null-safe rendering, component breaks when binding is empty | `register-component-render-contracts` |
| cslp tags, dollar props, studioAttributes contract, values not editable in Visual Editor | `register-component-cslp` |
| nothing clickable in Visual Editor, Visual Builder stuck on "Initializing the editor", can't add / reorder / delete list items in Visual Editor, no "+" on an empty list, new entry shows "Your text here" or its fields can't be clicked, image under an overlay can't be selected | `make-visual-editor-editable` |
| component registered but not in palette, registration fails silently, registration pitfalls | `register-component-pitfalls` |
| register JSON RTE, render json_rte, **HTML RTE, rich text field, markdown field, RichText component, rich text renders as raw HTML, RTE shows `<p>` tags as text, rich text renders blank, embedded entries in RTE, embedded assets in RTE, embed a card inside rich text, custom element type in RTE, registerRTERenderer, registerJSONRTE deprecated** | `register-json-rte` |
| BYOC, use my components in Studio, Studio with my design system | `byoc-end-to-end` |
| generate components from Figma, Figma to React, import my design system | `figma-generate-components` |
| import design tokens, use my Tailwind colors in Studio, register CSS variables | `import-design-tokens` |
| set default value, blank on drop, palette preview empty | `wire-component-default-data` |
| show data from X here, external API in composition, use query params, feature flag value | `wire-external-data` |
| render a section with my own data, section per array item, render a composition with my data | `render-with-own-data` |
| pass data into a slot, slot children can't see props, dropped component needs the parent's value | `wire-slot-data` |
| which prop do I use for my own data, data prop vs context, bring your own data | `understand-bring-your-own-data` |
| variant alias, Personalize-driven render, cookie/header variant | `wire-variant-alias` |
| share state between sections, cart count in Studio, use my Redux store, Bring Your Own State, BYOS, stateVariable, getState/setState, action prop, author should pick which function the button calls | `wire-studio-state` |
| set up canvas route, MISSING_CANVAS_URL, where does StudioCanvas mount, canvas iframe is blank in Studio | `setup-section-preview` |
| make every URL go through Studio, wire catch-all template route, template URL 404s, wildcard or single page, header/footer disappeared after adding Studio, duplicate header on Studio pages, my 404 page stopped working | `setup-template-preview-routes` |
| CSR or SSR, Next App Router setup, hydration mismatch, SEO meta missing, Live Preview broken after switching render mode | `configure-csr-vs-ssr` |
| here's the design, here's a Figma link, here's a screenshot, map this design to Studio, decompose this design, how would I build this in Studio, what components do I need for this design | `decompose-design` |
| here are all the page designs, decompose this whole site, multi-page decomposition, site-wide plan, build the marketing site, N templates | `decompose-site` |
| here's the whole Figma board, build every section in this file, all the hero variants, turn this design file into sections, decompose the whole design file | `decompose-site` |
| build the skeleton first, no data yet, connect the data later, structure without bindings, placeholder section | `author-composition-via-api` |
| populate entries from CSV, seed content from JSON, import content from our API, ingest content into this CT, backfill CMS content, import Markdown blog posts | `import-content` |
| add a field to blog_post, rename title to headline, extract hero to a Global Field, change field type, migrate CT schema, evolve content type | `migrate-ct-schema` |
| reference inside a reference is empty, nested reference not resolving, how deep can references go, how many levels of reference does Contentstack support, the data is two references deep | `resolve-reference-depth` |
| what does reference depth count, how deep should I fetch, depth stopped helping, stub count | `understand-reference-depth` |
| error_code 141, stub will not resolve, reference fetch fails, depth pitfalls | `resolve-reference-depth-pitfalls` |
| include_all_depth, error_code 141, include reference paths processing limit, reference chain too deep, deeper reference scan | `resolve-reference-depth` |
| the field is buried four groups deep, reference inside a modular block inside a group, the logo is inside a group inside a reference, group and blocks nested references | `resolve-reference-depth` |
| make this component reusable, break this page into sections, my whole page is one component, decompose this React component, this section is too big, why can't I reuse this, break down my component | `decompose-jsx-to-atomics` |
| which components should be sections, migration inventory | `discover-sections` |
| we have blog_post entries already, propose Sections from my existing CT schema, map existing CT to Sections, adding Studio on top of existing content | `discover-sections-from-ct` |
| one component renders all my blocks, the whole page is one modular blocks field, split this blocks page into Sections, split the sections field into sections, how do I decompose a page that is one array | `decompose-blocks-page` |
| my template has only one Section, the template has a single node, I built a monolith, the page renders but there are no Sections, why is there only one section | `decompose-blocks-page` |
| design schema for my Hero, what fields does this section need, migrate this component to a section | `design-section-from-jsx` |
| build a hero section, create card grid, section has no thumbnail, blank tile in Sections accordion | `build-section` |
| drag and drop does not commit on the canvas, playwright dragTo does nothing in Studio, mousedown mousemove sequence | `drive-studio-canvas-ui` |
| basic field component or my own component, simple vs styled section, which component type for a section | `build-section-component-choice` |
| section renders blank on canvas, section authoring pitfalls, section saved but wrong | `build-section-pitfalls` |
| what does the Contentstack MCP do, is MCP the right tool, MCP scope and limits | `understand-contentstack-mcp` |
| card grid, list of N items, iterate related posts | `build-repeating-section` |
| Connected or Freeform?, what kind of template, should this be a landing page | `choose-connected-vs-freeform` |
| build a blog template, PDP template, connected to a content type | `build-connected-template` |
| build a freeform template, static page in Studio, one-off landing page | `build-freeform-template` |
| page builder, section picker, authors choose the sections, reorder sections per page, modular page, one template many layouts, let marketing add sections | `build-page-builder-template` |
| pin an entry to freeform, additional entry data | `pin-entry-to-freeform` |
| pin a query, iterate latest entries, filtered list on freeform | `pin-query-to-freeform` |
| expose this prop, let authors override the headline, per-instance override | `expose-section-props` |
| repeat per item, list of blocks, iterate references | `use-repeater` |
| modular block repeater, reference repeater, blocks render empty | `use-condition-block` |
| carve a section slot, drop zone in a section, swap point inside a section | `use-section-slot` |
| default section for a slot, pre-fill empty slot, only allow these sections, restrict what drops into a slot | `configure-slot-defaults` |
| embed a Studio band, marketer-editable PDP region, promo strip, one editable section | `embed-composition` |
| build pages in Studio, I just want to compose, no code | `author-without-code` |
| compositions from JSON, API author composition, seed compositions, headless author, bulk import | `author-composition-via-api` |
| compositions REST API, Studio API service, create composition endpoint, list compositions, composition references API, managed composition API | `use-compositions-api` |
| composition entry body, url_metadata pair, what to POST to the CMA | `author-composition-entry` |
| static_value binding by API, static value renders the default, where the literal goes | `author-composition-static-values` |
| binding types list, node anatomy, where bindings live in the ui tree, repeater binding shape | `author-composition-bindings` |
| compress the ui spec, zlib encode composition, preflight validate the ui tree | `author-composition-encoding` |
| repeat a card over a multi-reference, repeat over group-multiple, repeater recipe by API | `author-composition-repeater-recipes` |
| nested repeaters by API, list inside each iterated item, repeaterUID chain | `author-composition-nested-repeaters` |
| author a section by API, selectedField priority, section scoping, section-slot node shape | `author-composition-sections` |
| Pattern B by API, fill a section slot by API, wrapper section with a slot | `author-composition-section-slot-fill` |
| exposed section props by API, per-instance override headlessly | `author-composition-exposed-props` |
| section thumbnail missing after API create, API never sets thumbnail | `author-composition-thumbnails` |
| linked_sections by API, author a template headlessly, complete freeform composition body | `author-composition-templates` |
| composition returns 200 but does not resolve, API authoring pitfalls, verify the write | `author-composition-pitfalls` |
| skeleton first then bind, read component source before authoring, free-form primitive | `author-composition-practice` |
| move compositions between stacks, remap uids on migration, composition schema remap | `author-composition-migration` |
| production wrapper needs template-instance swap, per-CT rendering inside a list, adapter for legacy carousel, wrap a production band into a List Section | `adapt-collection-component` (if native array-prop path doesn't fit) |
| visual parity, compare with live URL, drift between composed and hand-coded, screenshot diff, migration QA, make it look exactly like my existing design, keep the same design, the section doesn't match my design, preserve the existing look, match my CSS/styling | `verify-visual-parity` |
| migrate this page to Studio, swap route to StudioComponent | `migrate-page-to-studio` |
| deploy Studio site, deploy to Launch, Contentstack Launch, production env vars, blank page in prod | `deploy-studio-site` |
| upgrade Studio SDK, bump studio-react version, breaking change in Studio | `upgrade-studio-sdk` |
| verify Studio setup, smoke test, is Studio working | `verify-setup` |
| is this finished, anything missed, ready to hand over, why is the palette all blank tiles, no thumbnail on my sections, why can't I click the text to edit it, Visual Builder does nothing, definition of done | `complete-the-build` |
| Studio broken, help debug Studio, canvas blank, composition not rendering, binding wrong | `troubleshoot` |
| canvas won't load, canvas 404, SDK not initialized in canvas, Composition Loading Error, Component Loading Error, all/every component not registered in canvas | `troubleshoot-canvas` |
| cookie banner in canvas, chat widget over the panel, hide analytics in Studio, gate GTM, isStudioCanvas | `gate-third-party-scripts` |
| URL renders the homepage, two templates match the same pattern, /blog/post-1 404s, wildcard stopped matching | `troubleshoot-composition-resolution` |
| binding shows nothing, wrong value rendering, literal {{ | `troubleshoot-data-binding` |
| SSR render failure, use client mismatch, hydration Studio, registry undefined in server | `troubleshoot-ssr-rendering` |
| what's a slot, swap point, drop zone | `understand-section-slots` |
| what's a Section, Section vs Template, reusable page parts | `understand-sections` |
| what's a Template, template vs section, one template N pages | `understand-templates` |
| Canvas URL, /canvas vs full origin | `understand-canvas-url` |
| StudioCanvas vs StudioComponent, when to use which | `understand-canvas-vs-component` |
| what does installing Studio add, three SDKs, how Studio pieces fit | `understand-installation` |
| linked schema, why does a section auto-bind, section data shape | `understand-linked-schemas` |
| auto-binding algorithm, how does the section pick up template data | `understand-auto-binding` |
| headless composition authoring, ui zlib tree, six binding types | `understand-authoring-headlessly` |
| first time with Studio, brand new, zero knowledge | `start-here-zero-knowledge` |
| give me a Studio tour, walk me through Studio | `studio-tour` |
| plan a Studio project, architecture plan, sections vs templates for my app, **build me a page, implement this design in Studio, add this page to Studio, build the site, create a page in Studio** | `plan-studio-architecture` (**first, then the build skills it names**) |

If several rows match, follow the ordering the sequence implies: `analyze-project-fit` first, then provisioning, install, configure, register, author, verify, and troubleshoot. `enable-visual-experience` gates install. `install-studio` gates everything after.

---

## Topic map

Grouped by intent. Use when the user's message is Studio-shaped but no trigger phrase matches. Pick the closest by name and Read the file.

### 1. Start here — route before any state change

- **start-here-zero-knowledge**: zero-knowledge onboarding orchestrator.
- **studio-tour**: intent-driven walkthrough that routes to specialist skills.
- **analyze-project-fit**: read-only diagnostic of the user's project. Run before any install.
- **convert-project-to-studio**: whole-project orchestrator. Asks minimal / one page / full site (minimal recommended), then wires Studio as a fallback renderer behind the app's existing routes with the app's own 404 kept, every locale included. Nothing migrated or decomposed.
- **plan-studio-architecture**: analyze the starting point (existing code, part-built project, design, or prose), then print a plan for approval: Sections + linked schemas, Section Slots, registered **and** built-in components, CTs, Connected-vs-Freeform per page, build order. **Nothing is built until it's approved.** Run first for any non-trivial build request.
- **match-existing-pattern**: **MANDATORY before authoring a Template or Section in a project that already has compositions.** Inflates every composition's `ui`, derives how the project builds (repeater + condition + sections, section list, single component, atoms), and reports the patterns as layer trees. With one pattern, build that way. With several, the user picks from previews. Prevents the rework of authoring something structurally foreign to what is already there.
- **choose-connected-vs-freeform**: Connected default. Freeform is last resort. Emits the next skill.

### 2. Install and configure the app

- **install-studio**: install + wire studio-react + Live Preview + Delivery SDK.
- **install-live-preview**: Live Preview alone, without the full Studio SDK.
- **configure-studio**: set Environment, Language, Canvas URL on the Studio project.
- **enable-visual-experience**: stack-level Live Preview + Visual Experience gate. Do this first.
- **setup-local-https-canvas**: mkcert cert for the canvas app (mixed-content block on localhost).
- **upgrade-studio-sdk**: bump the seven studio-* packages together, read CHANGELOGs, smoke-check.
- **install-playwright-mcp**: optional MCP to automate the click-through verification skills.
- **install-contentstack-mcp**: discover and verify MCP execution first; configure the current host when needed. OAuth login and callable tools are separate checks. Record limitations before using HTTP fallback.

### 3. Provision the Contentstack side

- **authenticate-cma**: how every API call is authenticated: the OAuth-first credential ladder (verified from the CLI's own resolver), scope headers, token refresh, and the 401/422 signature table. Read before writing any `curl`.
- **provision-studio-project**: bootstrap the compositions CT + publish + delivery-token via API.
- **provision-studio-stack**: seed page CTs, global fields, entries, assets outside the compositions CT.
- **migrate-ct-schema**: evolve a live CT schema safely (add / rename / retype / remove fields. Extract to Global Field). Risk-classified, dry-run-first, dual-write for high-risk changes, rollback via before-snapshot.
- **import-content**: bulk-ingest entries into CTs from a customer-owned source (JSON / CSV / Markdown / existing Contentstack stack). Idempotent + resumable. Competitor-CMS migrations are out of scope. Use `@contentstack/cli-cm-import` for those.

### 4. Components — plan and register

- **design-component-library**: meta-planning skill. Apply the atom + layout taxonomy to the user's design system BEFORE any registration is written. Emits a decomposition sheet with the 10-primitive proposal and DS token gaps flagged. Run first when a project is starting fresh with a component library or when the user asks "what should I register".
- **classify-existing-component**: diagnostic. Runs Q1 of the four-question framework on **one** component and stops: Atom, Layout, or Compound. Routes to the right next skill (`register-component` for atoms/layouts, `decompose-jsx-to-atomics` for JSX compounds, `decompose-design` for design-input compounds). Use when auditing an existing registry, sanity-checking before registration, or triaging "authors can't rearrange this" reports.
- **decompose-jsx-to-atomics**: break an existing React component (often a whole page in one file) into Layer-1 atomics, Layer-2 containers and Layer-3 Sections so its parts become reusable. Run before `discover-sections` on an existing codebase. The code-input twin of `decompose-design`.
- **register-component**: read a React component, infer prop schema, emit a `registerComponent` call.
- **register-json-rte**: register the unified RTE renderer (`registerRTERenderer`) covering **JSON RTE, HTML RTE and Markdown** in one call, plus embedded entries/assets and custom element types. The skill name says json-rte for history. The API is not JSON-RTE-only.
- **register-breakpoints**: register default/tablet/mobile at SDK boot.
- **import-design-tokens**: Tailwind / CSS vars / JSON tokens into Studio's Design Panel.
- **figma-generate-components**: turn Figma frames into React components + registry entries via the Studio Figma plugin.
- **wire-component-default-data**: per-prop `defaultValue` so a component renders on drop before any binding.

### 5. Component contracts — read when registering

- **register-component-prop-contracts**: array and object binding rules, tolerant image and link signatures, `{{entry.*}}` resolution.
- **register-component-render-contracts**: the layout-agnostic rule and the null-safe rendering contract.
- **register-component-cslp**: `$` CSLP props plus the `studioAttributes` contract. Emit both or neither.
- **register-component-pitfalls**: what fails silently when registering, and the fix.

### 6. Designs to a plan

- **decompose-design**: take one design (Figma / screenshot / mock) and emit a build sheet + three-layer inventory + proposed CT shape. **THE entry point for greenfield single-page builds starting from a design.** Drives the whole flow end-to-end: the build sheet, then an offer to scaffold code, then an offer to author via CMA API or Playwright MCP, then verification.
- **decompose-site**: multi-page orchestrator. Wraps `decompose-design` per template, deduplicates atomics + Layer-2 components across pages, identifies Global Field candidates, emits a consolidated site plan + per-template build sheets in dependency order. **Use for greenfield multi-page marketing sites**, and for a whole Figma board of section variants: § Step 1b collapses variant frames into `choice` props instead of one Section per frame.
- **decompose-blocks-page**: execute the split when a page body is one modular-blocks field and one component renders every block type: the scope-filter prop, occurrence pinning when a type repeats, rebuilding the root slot from the pre-decomposition version so sibling nodes survive, and the field-name ceiling on Section reuse. The authoring half of `discover-sections-from-ct`.
- **discover-sections**: inventory a codebase for section candidates (components that recur across routes).
- **discover-sections-from-ct**: inventory an EXISTING Content Type for Section candidates. Walks the schema tree (root + Groups + References + Modular Blocks) and proposes one Section per scope with the correct linkedSchemaKind. The counterpart to `discover-sections` for teams starting with populated CMS content rather than existing route files.
- **design-section-from-jsx**: from a JSX component, propose the section's linked-schema shape.

### 7. Sections

- **build-section**: link a section to a structural schema (CT / GF / Group / Modular Block / Block / Reference).
- **build-repeating-section**: greenfield List Section: parent + child Section pattern iterating a multi-valued field.
- **compose-marketing-section**: given a design comp and already-registered primitives, pick the primitive tree that composes the section on the canvas. Points at the four canonical recipes (Hero, Feature Grid, Testimonial, Pricing) or drafts a new composition when the shape diverges.
- **adapt-collection-component**: compatibility adapter for wrapping a legacy production wrapper into a Studio List Section (wrapper-with-slot + Repeater + leaf adapter). Reach for this only when the native array-prop path (`build-repeating-section` § array-prop alternative) won't fit: Modular Block polymorphism, template-author child-swap, or non-reducible leaf shapes.
- **expose-section-props**: expose specific component props so template authors override per instance.
- **build-section-component-choice**: basic field components vs your own registered components: the simple-vs-styled tradeoff.
- **build-section-pitfalls**: what fails silently on the canvas when authoring a Section.
- **drive-studio-canvas-ui**: the drag-and-drop event sequence that actually commits on the canvas. Read before automating a drop, from any build skill.

### 8. Section Slots and smart containers

- **use-section-slot**: carve a slot into an already-designed section for per-instance swaps.
- **configure-slot-defaults**: give a Section Slot a default section for its empty state, and an allowed-sections whitelist gating what drops in.
- **wire-slot-data**: carry an owning component's data into whatever an author drops into its `slot` prop, bindable under Component Default Data.
- **use-repeater**: Repeater bound to a multi-valued field on a section or template canvas.
- **use-condition-block**: inside a Repeater over modular blocks / references, condition per item shape.

### 9. Templates

- **build-connected-template**: content-type-bound template. Every entry renders at a derived URL.
- **build-freeform-template**: static template with Pinned Entries and Pinned Queries.
- **build-page-builder-template**: the author-composes-the-page pattern: a Modular Block of section types, one Section per block, one template with a Repeater + a Condition Block per block. One template renders every layout.
- **pin-entry-to-freeform**: pin one entry to a freeform template as a Pinned Entry.
- **pin-query-to-freeform**: pin a CDA query so a Repeater source iterates dynamic content.

### 10. Routes and template URLs

- **setup-section-preview**: mount `<StudioCanvas />` in the app + set Canvas URL on the project.
- **setup-template-preview-routes**: wildcard (catch-all) vs dedicated routes. Wildcard also wires site-chrome preservation + 404 handling.
- **configure-csr-vs-ssr**: choose CSR (`useCompositionData`) vs SSR (`sdk.fetchCompositionData`).

### 11. Data binding

- **wire-external-data**: non-Contentstack data via the `data` prop on `<StudioComponent />`.
- **render-with-own-data**: render a composition (page or standalone section) against a `context` object you already hold, via `<StudioComposition />` + spec-only `sdk.fetchComposition`.
- **wire-studio-state**: declared state variables authors can bind, a custom store via `getState`/`setState`/`subscribe`, and named functions wired to buttons through `action` props (BYOS).
- **wire-variant-alias**: Personalize variant alias from cookie/header into `<StudioComponent />`.
- **embed-composition**: embed ONE editable region in a code-owned page via `useCompositionData({ compositionUid })`.
- **resolve-reference-depth**: walk a reference chain one hop at a time by declaring each hop's path, then stop and ask the user for a path, an entry uid or a depth as soon as a path cannot be derived. Why `include_all_depth` measured inert, why `include[]` takes schema paths rather than payload paths, and telling an unresolved stub apart from genuinely empty content.
- **resolve-reference-depth-pitfalls**: `error_code 141` and the pitfall table for walking reference depth.
- **make-visual-editor-editable**: builder mode, list tags (`<field>` and `<field>.<N>`) so items can be added, moved and deleted, the empty-list "+", new entries editable before anyone types (`fetchTemplateEntry`), and overlays that block selection.

### 12. Author by API — start here and the contract

- **author-composition-via-api**: write composition JSON directly via the CMA (headless / seed / migration).
- **author-without-code**: end-to-end authoring path for content teams on an already-installed project.
- **use-compositions-api**: create/read/list/update/delete compositions via the managed Studio API service (validated, `ui` compressed for you, your own credential forwarded: OAuth first, a session authtoken only as the last rung). The higher-level counterpart to `author-composition-via-api`.
- **author-composition-practice**: skeleton-first authoring, read component source, free-form primitives.
- **author-composition-entry**: the CMA body and the `url` + `url_metadata` pair. Read first when authoring by API.
- **author-composition-static-values**: how a `static_value` binding's key resolves to the literal in the entry.
- **author-composition-bindings**: every binding type, node anatomy in the `ui` tree, Repeater binding shapes. Read second.
- **author-composition-encoding**: compress the `ui` tree safely and preflight-validate it before publishing.

### 13. Author by API — recipes and reference

- **author-composition-repeater-recipes**: repeat a card over a multi-reference or GROUP-MULTIPLE field, with full node trees.
- **author-composition-nested-repeaters**: a list inside each iterated item, and the `repeaterUID` chain that resolves it.
- **author-composition-sections**: Section scoping rules, `selectedField` priority, `section-slot` node shape.
- **author-composition-section-slot-fill**: Pattern B: a wrapper Section's slots filled by another Section, with full node trees.
- **author-composition-exposed-props**: per-instance overrides on a placed Section, by API.
- **author-composition-thumbnails**: why the API never sets a Section thumbnail, and what to do instead.
- **author-composition-templates**: populate `linked_sections`, plus a complete Freeform composition body.
- **author-composition-pitfalls**: verify a `200` actually resolved, and the full API-authoring pitfall table.
- **author-composition-migration**: move compositions between stacks: uid, index and schema remaps.

### 14. Ship and verify

- **complete-the-build**: the ten always-mandatory deliverables (CSLP tags, `studioAttributes`, component + section thumbnails, Live Preview, `/canvas`, publishing, a template actually composed of Sections, builder mode, and new entries editable in Visual Editor) and the verification block that proves them. Run at the end of every build, and cite it in the plan at the start.
- **verify-setup**: layered smoke test (Delivery / Live Preview / Visual Editor / Studio).
- **verify-visual-parity**: brownfield migration: drive a browser to compare composed vs production Section-by-Section, classify drift by cause class, fix at the source (adapter / registration / wrapper CSS).
- **deploy-studio-site**: Contentstack Launch project, environments and env vars, composition Deploy, Live Preview gating, region config.
- **migrate-page-to-studio**: final swap of a route from hand-coded JSX to `<StudioComponent />`.
- **gate-third-party-scripts**: keep cookie banners / chat widgets / GTM / pixels out of the canvas via the SDK's editor-mode contract (`isStudioCanvas`).
- **byoc-end-to-end**: orchestrator for the whole BYOC arc (register, section, template, publish, in that order).

### 15. Troubleshoot — route by symptom

- **troubleshoot**: symptom router. Classify the failure and hand off to the right specialist.
- **troubleshoot-canvas**: canvas won't load, blank iframe, SDK not initialized.
- **troubleshoot-composition-resolution**: wrong URL renders, template pattern collisions, 404s.
- **troubleshoot-data-binding**: bound fields render nothing / wrong value / literal `{{`.
- **troubleshoot-ssr-rendering**: SSR/RSC failures, `use client` boundary, registry singleton.

### 16. Concepts — what is X, not how do I X

- **understand-sections**: a section is a reusable page part.
- **understand-templates**: templates compose sections. One template renders N live pages.
- **understand-section-slots**: designated swap points inside a section.
- **understand-linked-schemas**: the section's declared data shape. Why auto-binding works.
- **understand-auto-binding**: the algorithm matching section schema to template CT.
- **understand-canvas-url**: why it's a relative path, not a full URL.
- **understand-canvas-vs-component**: `<StudioCanvas />` (Studio iframe) vs `<StudioComponent />` (visitor routes).
- **understand-authoring-headlessly**: the entry `ui` zlib tree + `data_sources` shape, six binding types.
- **understand-bring-your-own-data**: pick between the three render-time surfaces: the `data` prop, `<StudioComposition context>`, and `<Slot data>`.
- **understand-installation**: what installing Studio actually adds to a project.
- **understand-contentstack-mcp**: what the Contentstack MCP does and does not do, before you install it.
- **understand-reference-depth**: what depth counts (reference hops, not groups or blocks) and when it is finished.

## Ordering hints

Some skills gate others. When multiple are relevant, run in this order:

```
enable-visual-experience  →  provision-studio-{stack,project}  →  analyze-project-fit
                                    ↓
                              convert-project-to-studio  (existing app: drives the next four)
                                    ↓
                              install-studio
                                    ↓
                              configure-studio  →  register-breakpoints
                                    ↓
                              register-component  (+ register-json-rte if json_rte fields)
                                    ↓
                              setup-section-preview  →  build-section
                                    ↓
                              setup-template-preview-routes  →  choose-connected-vs-freeform
                                    ↓
                              build-{connected,freeform}-template
                                    ↓
                              verify-setup  →  (troubleshoot-* only if verify fails)
                                    ↓
                              deploy-studio-site
```

Concepts (`understand-*`) are pulled on-demand, not part of the sequence.

## What to do if nothing matches

Answer from general Studio knowledge and say so explicitly. If the question keeps recurring across sessions, that's a missing skill. Flag it.
