---
name: plan-studio-architecture
---

## When to use

Analyze the starting point (existing codebase, part-built Studio project, a design, or nothing) and print an architecture plan for approval: Sections + linked schemas, Section Slots, registered vs built-in components, CTs + Global Fields, Connected vs Freeform per page, build order.

Use when the user describes a project and asks "what should I build", "how should I structure this", "Section or Template", "what CTs do I need", "build order". **Also run FIRST for any build request that isn't one already-scoped piece** ("build me a rewards page", "implement this design in Studio", "add this page to Studio", "build the site") because those go straight to a monolithic template otherwise. Also defensively when `build-section`/`build-connected-template` is invoked without decomposing first. Do NOT use to actually build. Do NOT use before concept ladder is crisp (run `start-here-zero-knowledge`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Plan the Studio architecture from project requirements

## Purpose

Given requirements, classify Sections, Connected templates, the content model, and build order. Planning-only. Produces a printed plan and hands off to `byoc-end-to-end`.

## The four-question decision framework: applied to the plan's component inventory

Every component in the emitted plan carries a Q1 to Q4 verdict from the [decision framework](design-component-library.md). The plan produces the sequence: "here's what to register, in what order, with what shape". The framework's four questions decide the shape.

- **Q1. Classify: Atom, Layout, or Compound?** For each component in the plan's inventory, classify what shape it is. Atom means a single content unit. Layout means a slot-carrying arrangement. Compound means refuse. Decompose into atoms + layouts, add each fragment to the inventory, and reclassify. The plan's component list has zero compounds.
- **Q2. Does the registry already have it?** Check the existing project registry AND earlier steps of THIS plan's build order. If a primitive matching the classified shape exists, the plan marks it as reused. If not, it adds a new-registration step to the build order before any Section that depends on it.
- **Q3. Which props?** Each primitive's proposed schema is emitted with a per-prop check against the varies-per-instance-AND-functional-intent rule. Refuse polish props at plan time, cheaper than discovering them in code review.
- **Q4. Which are Exposed?** Each schema prop's exposure status is emitted at plan time. This lets the design review sign off on the exposure surface BEFORE registration ships.

**The plan halts** if any component's Q1 to Q4 verdict is ambiguous. Ask the user to disambiguate. Add the resolution to the plan. Only then proceed to the build order.

## Task

### Step 0: Analyze the real inputs first. A plan is ALWAYS produced.

**Every path ends in a plan**: existing codebase, partially-built Studio project, a design, or nothing but a sentence. What changes is where the facts come from. Never plan from prose when code exists: you'll invent Sections for components that are already there and miss the ones that matter.

Detect the scenario, then gather:

```bash
# Is there an app to read?
ls package.json 2>/dev/null && node -e "console.log(Object.keys(require('./package.json').dependencies||{}).filter(d=>/contentstack|next|react/.test(d)).join(' '))"

# Routes / pages that already exist — include src/app, and expect locale segments
find app src/app pages src/pages src/routes \( -name 'page.*' -o -name '*.astro' -o -name '*Route.*' \) 2>/dev/null | head -40

# Components that already exist, and which are already registered with Studio
ls src/components components 2>/dev/null | head -40
grep -rn "registerComponent" src app lib 2>/dev/null | head -20

# Studio already wired? (compositions, canvas route, init) — grep by CONTENT;
# a fixed path list produces false negatives on src/app and locale-prefixed routes
grep -rln "StudioComponent\|StudioCanvas\|studioSdk.init" src app pages 2>/dev/null | head
```

#### 0a: Ask the project what already exists. Code cannot tell you.

The greps above inventory the **codebase**. They cannot see the Sections and Templates already authored in the Studio project, so a plan built from code alone proposes rebuilding pieces that are already there, and misses the reuse the user is paying for.

List them, and score reuse from the live tree rather than by eye:

```bash
# requires:
#   STUDIO_API  Studio API base URL for your region
#   PROJECT     Studio project uid
#   CS_AUTH     one auth header resolved per authenticate-cma, e.g. "authorization: Bearer $CS_OAUTH_ACCESS_TOKEN"
#   CS_SCOPE    the scope header, e.g. "organization_uid: <org-uid>"
# Every composition in the project, split into Sections and Templates, with the
# number of Templates each Section is actually placed on. Pages past limit=100.
cs='[]'; skip=0
while :; do
  page=$(curl -s "$STUDIO_API/projects/$PROJECT/compositions?limit=100&skip=$skip" -H "$CS_AUTH" -H "$CS_SCOPE" | jq '.compositions // []')
  cs=$(jq -n --argjson a "$cs" --argjson b "$page" '$a + $b')
  [ "$(jq length <<<"$page")" -lt 100 ] && break
  skip=$((skip + 100))
done
echo "$cs" | python3 -c '
import sys, json, collections
cs = json.load(sys.stdin)
use = collections.Counter()
for c in cs:
    ls = c.get("linked_sections")
    ls = json.loads(ls) if isinstance(ls, str) else (ls or [])
    for r in ls: use[r.get("uid")] += 1
secs = [c for c in cs if c.get("place_composition_as") == "section"]
pages = [c for c in cs if c.get("place_composition_as") in ("page", "template")]
print(f"templates: {len(pages)}   sections: {len(secs)}")
for c in sorted(secs, key=lambda x: -use[x["uid"]]):
    n = use[c["uid"]]
    slug = c.get("composable_uid") or c["uid"]
    print("  %2d template(s)  %s" % (n, slug))
'
```

The listing caps at 100. A larger project needs `&skip=100`, `&skip=200` … merged before counting, or the tail
of the inventory silently reads as zero-use.

Read the output as a reuse map:

- **Used by 2+ Templates**: proven reusable. Reuse it. Never author a second copy.
- **Used by 1**: reusable in principle. Before adding a near-identical Section, check whether one exposed prop covers both (§ Reuse across Templates).
- **Used by 0**: orphaned. Either the plan places it, or it is dead weight worth reporting.

**Reuse tells you WHAT exists. It does not tell you HOW it is built.** A plan that proposes new Templates without
matching the project's existing build pattern produces work that renders but is structurally foreign, no Repeater, no
Condition Blocks, nowhere for an author to drop a Section. Run [`match-existing-pattern`](match-existing-pattern.md)
now, before the plan names a single new composition, and state the chosen pattern in the plan. It is mandatory
whenever the listing above returns any composition at all.

**A Section binds `template.<field>`, so two Templates can share it only if their page content types name that field identically.** Sections whose binding fields differ are not reuse candidates however alike they look, see [`decompose-blocks-page`](decompose-blocks-page.md) § Step 5. State that limit in the plan rather than promising reuse the schema cannot deliver.

#### 0b: Classify EVERY component. No component goes unexamined.

Routing "decompose the coarse ones" isn't coverage: coarse is a judgment call, and the component that quietly holds four atomics is exactly the one that gets waved through. **Walk the whole component inventory and record a verdict for each**, using one test:

> **Does it render more than one heading / image / body / list?** If yes it is **coarse**: read its render tree via [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md). If no, it is genuinely atomic: register it as-is.

```bash
# Every component file, with a rough leaf count to triage by
for f in $(find src app components -name '*.tsx' -o -name '*.jsx' -o -name '*.js' 2>/dev/null | grep -iE 'component|section|block|card|hero|header|footer|nav|menu'); do
  n=$(grep -oE '<(h[1-6]|p|img|ul|ol)\b' "$f" 2>/dev/null | wc -l | tr -d ' ')
  m=$(grep -c '\.map(' "$f" 2>/dev/null)
  echo "$n leaves, $m maps  $f"
done | sort -rn | head -40
```

Print the verdict table in the plan. **An unclassified component is an incomplete plan**:

| Component | Leaves | Verdict | Action |
|---|---|---|---|
| `<RewardsPage>` | 9 | coarse | decompose into 3 Sections |
| `<Marquee>` | 1 | atomic | register as-is |
| `<Header>` | 6 | coarse **+ shared** | decompose into one shared Section (see 0b) |

#### 0c. Shared shells first: header, footer, nav, menus

These are the highest-value reusable Sections in any project and the ones most often missed, because **route-based scanning under-counts them**. They usually live in a layout (`app/layout.tsx`, `_app.tsx`, a `<Shell>`), so a scan that counts route files sees them once and scores them low, even though they render on **every page**.

```bash
# Shared shells: check the LAYOUT, not the routes
grep -rn "Header\|Footer\|Nav\|Menu\|Breadcrumb" \
  app/layout.* src/app/layout.* app/**/layout.* pages/_app.* src/App.* 2>/dev/null | head
```

Treat anything rendered from a layout as **shared by construction**. Reuse count is effectively every page, whatever the route scan says. For each:

| Shell | Decompose into | Binds to | The list inside is |
|---|---|---|---|
| **Header** | logo (`imageurl`) · brand/site name (`string`) · nav (list) · CTA (`href` + label) · optional search slot | a Global Field reused by every page CT, or a singleton `site_config` entry | **nav links in a Repeater** over a multi-Group / multi-Reference, never hardcoded `<li>`s |
| **Footer** | logo · legal/copyright (`string`) · link columns (nested list) · social icons (list) | same Global Field / `site_config` | **columns in a Repeater**, and **links inside each column in a nested Repeater**, see `author-composition-nested-repeaters` |
| **Nav / menu** | one link atomic per item: label (`string`) + href (`href`) | the multi-valued field the Repeater iterates | the Repeater's child Section: build once, reuse in header, footer, sidebar, mobile drawer |
| **Breadcrumb** | label + href per crumb | derived or a multi-Group | Repeater |

**How a shell reaches a singleton entry:** pin the `site_config` entry on the header and footer **Sections themselves** (Data tab → Pinned Entries, see [`pin-entry-to-freeform`](pin-entry-to-freeform.md)), with no `linked_schemas`, and place them on Templates with no selected field. A reference field on every page type instead leaves header and footer blank on each new entry until an editor picks the settings entry.

**Two failure modes to head off explicitly:**

- **Hardcoded nav.** A `<ul>` of literal `<li><a href="/deals">Deals</a></li>` means an author cannot add a menu item without a developer. Every menu item is a **Repeater iteration bound to a field**. That is the whole point of putting the header in Studio.
- **A shared shell rebuilt per page.** If the plan lists "Homepage Header" and "Deals Header", that's one Section with the same binding twice. Name it once, reuse it, and use an **exposed prop** for any per-page variation (a different CTA label, a transparent variant).

| Scenario | Signals | Gather from | Notes |
|---|---|---|---|
| **A. Existing codebase** | `package.json` + route/component files present | **[`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md) FIRST** on any page-level or coarse component: it reads render trees and produces the atomics/Sections this plan then assembles. Then [`discover-sections`](discover-sections.md) for what recurs across routes, [`analyze-project-fit`](analyze-project-fit.md) for install state + data center, and [`discover-sections-from-ct`](discover-sections-from-ct.md) if the stack already has populated content types | The scan is the source of truth. The user's description is context. Plan against what's on disk. Skipping decomposition here is what yields one Section per page. `discover-sections` counts component names and cannot see inside a monolith |
| **B. Partially-built Studio project** | `registerComponent` calls, existing compositions, `/canvas` route | Everything in A, plus list existing Sections/Templates in Studio | **Plan the delta, not a rebuild.** Anything already correct is `[exists]` and gets left alone |
| **C. Design / Figma / screenshot** | User supplies a design, no code | [`decompose-design`](decompose-design.md) (one page) or [`decompose-site`](decompose-site.md) (several) | Feed its component/Section inventory into Step 2 |
| **D. From scratch, prose only** | No code, no design | The user's `requirements` text | Ask for detail if it's a one-liner. Don't plan off a single sentence |
| **E. Whole-project conversion, scope not chosen** | Existing codebase plus a "convert / make Studio-compatible" ask with no page named | [`convert-project-to-studio`](convert-project-to-studio.md) **first**: its gate offers minimal (recommended), one page, or full site | Plan only for what the user scoped there (option 2: one page, option 3: every page type). Option 1 needs no plan from this skill |

**Print an inventory of what already exists before planning anything new**: registered components, Sections, Templates, content types, Global Fields. Every plan item in Step 9 then carries a status so the user sees the delta:

- `[exists]`: already correct, no work
- `[modify]`: exists but needs a change (a prop added, a binding fixed, a slot carved)
- `[create]`: new

A plan that lists everything as `[create]` on an existing codebase means Step 0 was skipped.

### Step 1: Parse the requirements into a list of pages and features

Combine the Step 0 analysis with the user's `requirements` and extract (**where they disagree, the code wins**: the user's description is often about intent, the code is about reality):

- **Pages**: distinct URLs / routes the visitor sees (homepage, product detail, blog post, about, contact, category landing, etc.).
- **Reusable structural blocks**: the parts that appear on multiple pages (header, hero, feature grid, testimonial strip, CTA, footer, related-items, etc.).
- **Data sources**: content types the user already has (or wants), external data hints (Shopify, third-party API), pinned-query language ("show all products tagged X").

Print the parsed list back. Ask the user to confirm or correct.

### Step 2: Classify reusable structural blocks as Sections (NOT pages)

**Golden rule: when a piece qualifies as a Section (build BEFORE touching a Template).** Skills sometimes jump straight to Template authoring and drop components + bindings directly on the Template. That's wrong whenever either of the two conditions below fires. The piece must be built as a Section first, then dropped on the Template.

**Sections are the default. Reuse is a prioritization signal, NOT a qualification gate.** A page is decomposed into Sections that a Template assembles. That's the idiomatic Studio shape, and it holds at reuse count 1. Do not produce a plan whose Template is one monolithic `ui` tree of directly-dropped components because "this page is a one-off." A single-use page still gets its hero, its form, its content band as separate Sections.

Why, beyond reuse:

- **It's the authoring surface.** Sections are what a template author sees, reorders, swaps, and drops into slots. Components dropped straight onto a Template give authors a flat tree with no meaningful units. They can re-bind props and nothing else.
- **Independent preview.** A Section renders on its own `/canvas` and can be verified in isolation. A monolithic Template can only be checked by loading the whole page.
- **Scoped data.** `selectedField` scoping exists at the Section layer. Inline everything on the Template and every binding is an absolute path off the page entry.
- **Reuse arrives later.** "One-off" pages routinely grow a second instance. Retrofitting a Section after the fact means re-authoring bindings. Starting with one costs two extra compositions today.

Three conditions make a Section **mandatory**, but the default already is a Section, so these are the cases where skipping it is a defect, not a judgment call:

1. **Reuse across Templates.** A bound compound component appearing on more than one Template MUST become a Section. Otherwise every Template repeats the drop-and-bind work and any binding tweak is applied N times. **Reuse count 1 does not exempt a piece from being a Section**. It only lowers its build priority.
2. **Schema iteration with bindings.** Any Modular Block field, multi-Reference field, group with `multiple: true`, or otherwise-iterated collection whose items need bound rendering MUST become a **List Section**, not authored inline on the Template. The iteration wiring belongs at the Section layer where it's reusable and testable. Putting it at Template level fragments it across every Template that needs the same iteration.

   **A List Section has TWO build paths: pick by layout fidelity, don't default to Repeater.** If the collection has a **bespoke or asymmetric layout** (a mosaic, a feature strip, a carousel), or you are **migrating and must preserve an existing design**, build it by binding the whole array to the real production component (`type: "array"`, see [`register-component-prop-contracts`](register-component-prop-contracts.md) § Array & object props), so the component's own layout renders pixel-identically on the first pass. Use a **Repeater + Condition Block** only when the list is a **uniform** grid/row, OR items are **polymorphic** and need per-item authoring. A Repeater renders items uniformly in sequence. Choosing it for a bespoke layout is the #1 cause of first-render design drift (the "why is it a plain sequence?" re-prompt).
3. **Any bound region an author should be able to move, swap, or remove.** If it's a recognizable page part (hero, form band, feature grid, CTA) it's a Section, reuse count irrelevant.

Build the Section first (`build-section` for Simple, `build-repeating-section` for List), THEN drop it on the Template. Direct-drop of registered components on a Template is reserved for genuine one-offs that are not a page part (a stray spacer, a single decorative element) and should be a rare line in the plan, called out as an exception with a reason.

For each reusable structural block (header, hero, footer, feature grid, etc.) mark it as a **Section**. Sections aren't pages. They're units that pages assemble.

For each Section, identify what it should bind to:

- **Bound to a Global Field** if the same field set is reused across multiple CTs (e.g. a `card_meta` GF with title + image + cta, used by ProductCard, FeaturedCategoryCard, RelatedItemCard, etc.)
- **Bound to a CT** if the Section is specific to one CT's shape (e.g. ProductCard bound to `product` CT)
- **Bound to a Group / Modular Block / Reference field** on a parent CT if the Section renders the nested shape (these are usually child Sections that drop into a parent's Slot, see Path B in `build-section`)
- **Atomic / static** if the Section is layout-only with no CMS bindings (rare. Usually still has at least a brand-config reference)

For any Section whose linked schema has Global Field / Modular Block / Group / Reference fields, flag those as **Slot candidates** (per the heuristic in `understand-section-slots`). Default to exposing a Slot. Only inline when certain the nested shape is single-use.

Also flag each Section's **`selectedField` decision**. Studio scopes Section data via `getScopedData(pageEntry, selectedField)`, and the set-vs-unset choice depends on the Section's data shape:

- **One Repeater over one field** (e.g. Card Grid over `related_posts`): set `selectedField = <that field>`. The Section reads `template` as the field's value directly.
- **Multiple fields on the page entry** (e.g. Header reading `brand` + `nav_links` + `signin_label`): leave `selectedField` unset. `template` becomes the whole page entry. Keep original `template.<field>` paths.

Setting `selectedField` on a multi-field Section loses access to everything outside the scoped path. See [`build-section`](build-section.md) § How a Section gets its data for the mechanism and [`author-composition-via-api`](author-composition-via-api.md) § Decision rule for the wire shapes.

### Step 2b: Pick the RIGHT primitive per piece. `registerComponent` is not the default answer.

**The failure mode this prevents:** everything becomes a registered component, because registering is the easiest thing to do. The plan then looks complete while the author ends up with a page they can only re-bind (no reordering, no swapping, no restyling, no reuse) and never discovers that Studio had a primitive for what they wanted. Registering is one tool out of many, and it is the least author-editable of them.

**Migrating an existing design? Fidelity outranks editability on the first pass.** Pick the primitive that reproduces the current render exactly, usually reuse the real production component whole (`object` / `array` binding), because its own markup + CSS already are the design. Introduce built-in decomposition and Repeaters as a SECOND, opt-in phase, once the user has confirmed the render matches and explicitly asks for per-field / per-item authoring. Decomposing on the first pass is what forces the user to re-prompt "the design doesn't match". Get parity first, add editability second.

**This governs a Section's internals. It never governs the page.** Keeping a carousel or a card grid whole is fidelity. Binding one component to the page's entire body is a monolith. The two are easy to confuse when the body happens to be a single modular-blocks field. Fidelity-first means this Section keeps the production component inside it. It is not permission for the Template to hold one node. A Template still gets one Section per schema scope on the first pass ([`decompose-blocks-page`](decompose-blocks-page.md)), each of which may keep its production component whole. Parity and decomposition are not in tension at that level. The measured proof is that splitting a blocks page into one Section per block type leaves the rendered output byte-identical.

Work through each piece from Steps 1 to 2 and pick from **evidence**, not convenience:

| Evidence in the code / design / content model | Primitive | Skill |
|---|---|---|
| Plain copy (headline, body, caption, CTA label) mapping 1:1 to a field | **Built-in field component** (`Heading` / `Paragraph` / `Text` / `Image` / `Link` / `RichText`) | `build-section-component-choice` § Basic field components vs custom |
| Interactive: local state, handlers, cookies, modals, carousel logic | **Registered component** (mandatory, built-ins can't express behavior) | `register-component` |
| Pixel-sensitive: bespoke CSS, animation, layering | **Registered component** | `register-component` |
| Static presentational layout (image + heading + body + link) | **Decompose into built-ins**: authors get full editing. This is the case most often wrongly registered | `build-section-component-choice` § Register it whole, or decompose it |
| A styled shell wrapping editable content | **Registered component with a `slot` prop** + built-ins inside | `register-component`, `use-section-slot` |
| A recognizable page part (hero, form band, feature grid, CTA) | **Section**: regardless of reuse count | `build-section` |
| Multi-valued field with a **uniform** grid/row, OR polymorphic items needing per-item authoring | **List Section via Repeater** (+ **Condition Block** per block or CT for refs/MBs) | `build-repeating-section`, `use-repeater`, `use-condition-block` |
| Multi-valued field with a **bespoke layout**, or **migrating an existing design** | **List Section via array-prop reuse**: bind the whole array to the real component. Its own layout renders identically, first pass | `register-component-prop-contracts` § Array & object props, `build-repeating-section` § array-prop alternative |
| A region a template author must fill differently per instance | **Section Slot** (filled by a Section, not a raw component) | `use-section-slot` |
| One prop an author should override per template instance | **Exposed section prop**: cheaper than forking the Section | `expose-section-props` |
| Same field set across several CTs | **Global Field** (+ a Slot on the Section that renders it) | `plan-studio-architecture` § Step 4 |
| **Any rich text**: JSON RTE, HTML RTE or Markdown | **`RichText` component** (never `Heading`/`Paragraph`, which show markup as literal characters) | `register-json-rte` § Which component for which field |
| Rich text that **truncates behind "read more" / an accordion** | **`CollapsibleText`**: same content model, plus expand/collapse | `register-json-rte` |
| Rich text that **embeds entries or assets** | `RichText` **+ `registerRTERenderer` with `embeddedEntry` / `embeddedAsset` handlers**. Unregistered, an embedded entry renders as a bare delivery-API span (title only) | `register-json-rte` § Embedded entries and embedded assets |
| One-off page owning its own copy, no CT worth creating | **Freeform template** + **Pinned Entries** | `build-freeform-template`, `pin-entry-to-freeform` |
| "Show the latest / top N / filtered X" on a Freeform page | **Pinned Query** as a Repeater source | `pin-query-to-freeform` |
| Data outside Contentstack (pricing, geo, inventory) | **`data` prop on `<StudioComponent>`**: not a fake CT | `wire-external-data` |
| Two or more components must agree on a value (cart count, active filter, theme) | **Declared state variable**: author-bindable shared state. **Not in any published SDK release yet. Run that skill's export preflight before planning it in** | `wire-studio-state` |
| The app already owns that state (Redux / Zustand / signals) | State variable + **`storage: "custom"`** (`getState`/`setState`/`subscribe`) | `wire-studio-state` |
| An author should choose what a button does | **Registered studio function + `action` prop**: not a hardcoded handler | `wire-studio-state`, `register-component` |
| Route-level branch on user state / segment | **Variant alias** (Personalize), not an `if` in the tree | `wire-variant-alias` |
| Brand spacing / color / type scale the author should reuse | **Design tokens** registered with Studio | `import-design-tokens` |
| Author needs to see tablet/mobile | **Breakpoints** registered at boot | `register-breakpoints` |

**Bias check before printing the plan.** Count the primitives you selected:

- **Every interactive component's behavior hardcoded, no `action` props?** Authors can place it but not wire it. If the page has buttons that should do something the author picks, that's a function + `action` prop.
- **One Section covering a whole page?** A defect, not a shortcut. Nothing to reorder, nothing reusable, and the author never meets slots or repeaters. Run [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md) and re-plan. A single-Section page needs a stated reason, not silence.
- **Any Section whose binding is one coarse prop taking a whole object?** Decomposition was skipped. Atomic props bind one CT field each. A single prop swallowing a group renders blank when typed `any` (the binder recursively unwraps single-key objects for every type except `object`/`array`).
- **Only registered components?** Almost certainly wrong. Re-walk the table. Plain copy belongs in built-ins, lists belong in a List Section, per-instance variation belongs in a Slot or an exposed prop.
- **No Section Slots anywhere?** Legitimate for a small, fully-fixed page, but state that you checked and why none is needed. Silence reads as "not considered".
- **A list rendered without a Repeater**, or a Modular Block / multi-Reference Repeater without a Condition Block, means the plan is wrong, not merely terse.
- **A one-off page modelled as a Connected CT with a single entry** is fine and often right. A campaign page with no owned copy is the Freeform case. Decide, don't drift.

**Name the features you ruled out.** The plan prints a "Studio features considered" line listing what you rejected and why (e.g. "Pinned Query: not needed, the list is a Modular Block on the page entry"). This is how the user learns the primitive exists at all. A plan that silently omits half of Studio teaches them Studio is just component registration.

### Step 3: Classify each page as a Connected template

For every page (not a Section), pick the CT backing:

```
Q1. Does the page repeat per content item?
    ("blog post detail", "product detail", "recipe page", "author profile")
    YES → Connected template + multi-entry CT, URL pattern with {{entry.slug}} or similar
    NO  → continue to Q2

Q2. Does the page have a stable shape?
    ("homepage", "about", "contact", "pricing", "category landing", any campaign with hero copy)
    YES → Connected template + single-entry CT (or generic shape CT with one entry).
          Even short-lived / campaign pages get a single-entry CT for their owned copy.
```

For each page, print one line:

```
<page name>  →  Connected
  Backing:     <CT name + multi/single-entry>
  URL pattern: <e.g. "/blog/{{entry.slug}}" for multi-entry, "/" for single-entry, etc.>
  Reasoning:   <Q1 hit / Q2 hit>
```

If a page seems not to fit either Q1 or Q2, it almost certainly has some copy (hero title, CTA) that wasn't called out in the requirements. That copy IS content, and modeling it puts the page back on Q2 (single-entry CT).

### Step 4: Derive the content model

From Steps 2 to 3, list every CT and Global Field needed:

```
Content model:
  CT  <name>  <multi-entry | single-entry>   fields: <field (type), one line — types required>
  CT  ...
  GF  <name>                                 fields: <field (type)>
                                             reused by: <CTs / Sections>
```

**Name a type for every field, and do not default long copy to plain text.** The field type decides what an author can ever do with it, and it is expensive to change once entries exist:

| The copy is… | Field type | Renders through |
|---|---|---|
| A heading, label, name, short value | `text` (single-line) | `Heading` / `Text` |
| Body copy, description, prose an author may want to **bold, link, list, or embed into** | **`json_rte`** (or multiline + rich-text / markdown to match the team's editing convention) | **`RichText`** |
| Long prose the design **truncates**: "read more", accordion, "show details" | same rich-text type | **`CollapsibleText`** |

**Propose the rich-text type by default for body copy**, and say so in the plan: "`body` is `json_rte` so authors can format and embed. If it will only ever be a flat paragraph, tell me and I'll make it plain text." Choosing plain text silently is the costlier mistake. An author who later needs a link in a sentence needs a schema migration, whereas an over-provisioned rich-text field is merely unused.

If any rich-text field should accept **embedded entries or assets**, decide that here too, it drives the `RTE renderer` block in the build sheet and one `registerRTERenderer` call. Mapping: [`register-json-rte` § Which component for which field](register-json-rte.md#rte-field-to-component).

For each CT, check for Slot-candidate fields (Global Field / Modular Block / Group / Reference) and mark them.

For each Global Field, name which CTs/Sections reuse it. They exist because a field set is shared.

If 2+ CTs have identical or near-identical sub-shapes, propose extracting them as a Global Field.

### Step 5: Section inventory in build order

**Match every planned Section against the Step 0a listing before adding it as new.** Components get this from Q2. Sections had no equivalent, so a plan would silently propose authoring a second Hero beside one that already existed. For each planned Section, mark it:

| Mark | When | What the plan says |
|---|---|---|
| `[reuse]` | an existing Section already binds the same field and renders the same scope | name the existing `composable_uid`. Add **no** build step |
| `[extend]` | an existing Section is close, and one exposed prop would cover both cases | name it, and add the prop as the build step, never a near-duplicate Section |
| `[new]` | nothing existing binds that scope | full build step |

**Say the reuse out loud in the plan**, per Section, before the user approves it. "Hero: `[reuse]` `sec_<field>_hero`, already on 2 Templates". A plan that lists twelve `[new]` Sections when four already exist reads as twelve units of work, and the user only discovers the duplication after it is built.

Reuse is capped by the binding field: two Sections are the same Section only if their page content types name the field identically ([`decompose-blocks-page`](decompose-blocks-page.md) § Step 5). Alike-looking Sections on differently-named fields are `[new]`, and the plan should say why.

List every Section from Step 2, ordered by **dependency**:

- Child Sections (those that drop into a parent's Slot) come BEFORE the parent Sections that expose Slots for them.
- Atomic / standalone Sections (no Slot interactions) can go in any order, group them at the start for quick wins.
- Mark each Section's exposed Slots and which child Sections fill them.
- **Shared shells (header / footer / nav) are Sections like any other**: bound to a Global Field or a singleton `site_config` entry, with their menus as Repeaters. They are NOT "atomic, no binding": that classification is what leaves an author unable to edit the nav. See Step 0c.
- A link/menu-item child Section comes **before** the header and footer that iterate it. One child Section usually serves both, plus any sidebar or mobile drawer.

```
Sections (build in this order):
  1. ProductCard            bound to product CT          → standalone; no Slot
  2. FeaturedCategoryCard   bound to card_meta GF        → standalone; no Slot
  3. ProductGrid            bound to category.products   → exposes Slot, drop ProductCard
  4. FeaturedCategories     bound to homepage.featured_categories → exposes Slot, drop FeaturedCategoryCard
  5. Hero                   bound to homepage.hero group → standalone
  6. SiteNavLink          bound to site_config.nav_links item → child Section for the Repeater
  7. Header               bound to site_config GF   → logo + brand + nav Repeater (drops SiteNavLink)
  8. Footer               bound to site_config GF   → nested Repeater: columns → links
```

### Step 6: Template inventory

For each page (from Step 3):

```
Templates:
  Connected /                       homepage CT (single)        → Hero + FeaturedCategories
  Connected /category/{{slug}}      category CT                 → Hero + ProductGrid
  Connected /product/{{slug}}       product CT                  → ProductDetailHero + ProductSpecsTable + RelatedProducts
  Connected /blog/{{slug}}          blog_post CT                → BlogHeader + RichText + RelatedPosts
```

### Step 7: Build order

Print the full executable order:

```
Build order:
  0. Setup, if not already done         (analyze-project-fit -> install-studio ->
                                         enable-visual-experience — stack Live Preview + preview token ->
                                         install-live-preview with cslp: { appendTags: true } ->
                                         setup-section-preview for the COMPULSORY /canvas route;
                                         skip any step Step 0's inventory shows is already in place)
  1. Create / update CTs and Global Fields  (in the Contentstack web app)
  2. Register atomic React components       (lazy by default; layout-agnostic — see register-component)
                                         every registration ships thumbnailUrl, every component spreads
                                         studioAttributes + its $-twins — same step, never a follow-up
  3. Import design tokens                   (before any Section is authored — see import-design-tokens)
  4. Build Sections in the order from Step 5
                                         each section's ui_preview is set immediately after it is written
  5. Build Templates in the order from Step 6  (one per Connected template)
  6. Set up visitor render routes           (configure-csr-vs-ssr + setup-template-preview-routes)
  7. Verify + hand over                     (complete-the-build -> verify-setup + deploy-studio-site)

Run `byoc-end-to-end` to walk this in execution mode.
```

The inline notes on steps 0, 2, 4 and 7 are the six deliverables from [`complete-the-build`](complete-the-build.md): CSLP tags, component thumbnails, section thumbnails, Live Preview, the `/canvas` route. **Print them in the build order, don't leave them implied.** Each is invisible to a developer loop (the page renders fine without all six) and each breaks the editor for the non-developer this plan exists to serve, so a plan that omits them gets approved as complete and delivered incomplete.

### Step 8: Sanity checks before handoff

Before printing the final plan, flag any of these at the top:

- Anything with a URL listed as a Section (it's a Template).
- Reusable block (header/hero/footer/grid) listed as a Template (it's a Section).
- CT with GF/MB/Group/Reference field not exposed as a Slot.
- Global Field shared by ≥2 CTs without its own Section.
- Connected page without an identified backing CT.
- Child Section whose linked schema doesn't match its parent Repeater's iterated CT.
- Any of the six in [`complete-the-build`](complete-the-build.md) missing from the plan, or an `[exists]` component carrying no `thumbnailUrl` / no `studioAttributes` (it's `[modify]`).

### Step 9. Print the plan in TWO layers: plain language first, build sheet second

**The person approving this is often not a developer.** A plan written in Sections, linked schemas and `url_source` cannot be approved by someone who can't read it. They either say yes without understanding, or stall. So print a plain-language summary first, and keep the technical detail below it for the build steps.

Both layers, every time. The summary is not a teaser. It must cover everything the build will do.

#### Layer 1: What you'll get (plain language, no jargon)

```
WHAT YOU'LL GET — <project name>

In short:
  <2–3 sentences. What exists at the end, which pages, and who can change what
   without a developer. No product terms.>

Your pages:
  • <Page name> — <one page at /rewards | every product gets its own page>
      What's on it   : <hero banner, signup form>
      You can edit   : <headline, image, body text, button label>
      Fixed for now  : <the form's behavior — needs a developer>

Reusable blocks (built once, usable on any future page):
  <one entry per block — if a whole page is a single entry here, the plan is wrong;
   go back and break it up>
  • <Hero banner> — <used on 1 page today>
      You can edit  : <image, headline, body>
      Swap spots    : <you can drop a different offer box here per page | none>
  • <Signup form> — interactive, so it stays a developer-built block
      You can edit  : <labels, category list>

Lists that grow by themselves:
  • <The offers list repeats automatically for every offer you add — no developer needed>
  <or "None on this page">

After this you'll be able to, on your own:
  ✓ <change any wording or image on these pages>
  ✓ <reorder the blocks on a page>
  ✓ <reuse the hero on a new page>
  ✗ <change how the form submits — that needs a developer>

How you'll edit it:
  • Click any text or image on a preview of the real page and change it right there.
  • Every building block and reusable block shows a picture of itself, so you can
    tell them apart when adding one — no blank tiles to guess at.
  <these two lines are ALWAYS included and always true — they are the six
   deliverables in complete-the-build, which the build order commits to>

Size of the job:
  <2 reusable blocks · 1 page · 2 of your components hooked up · ~N new content fields>

Already in place / being reused:
  <from the Step 0 inventory — or "nothing yet, this is a fresh build">
```

**Rules for Layer 1:**

- **Ban the vocabulary, keep the meaning.** Never print Section, linked schema, `selectedField`, Connected/Freeform, Repeater, Condition Block, Section Slot, `url_source`, `resolvedReferences`, binding, prop, CT. Translate:

  | Don't write | Write |
  |---|---|
  | Section | reusable block |
  | Section Slot | swap spot: you can drop something different here on each page |
  | Connected template | one design every `<thing>` page uses automatically |
  | Freeform template | a one-off page |
  | Repeater (+ Condition Block) | the list repeats automatically for each item you add |
  | Registered component | your existing designed block, used as-is |
  | Built-in component | plain text or image you can type into and restyle yourself |
  | Exposed prop | one setting you can change per page |
  | Global Field | the same group of fields reused in several places |
  | linked schema / binding | where it gets its content from |
  | URL pattern / `url_source` | the page address |
  | Pinned query | it shows the latest ones automatically |
  | Design tokens | your brand colors and spacing, available in the editor |
  | CSLP tags / Visual Editor / Live Preview | you can click any text or image on a preview of the real page and edit it there |
  | `thumbnailUrl` / `ui_preview` | every block shows a picture of itself so you can tell them apart |

- **"You can edit" and "Fixed for now" are the point.** That's the line a non-technical approver actually cares about, and it's what makes the A-vs-B choice in Step 10 meaningful rather than abstract.
- **No counts without meaning.** "2 reusable blocks" is fine. "4 `linked_schemas`" is not.
- **Say what's reused.** If Step 0 found existing pieces, name them here. Otherwise the reader assumes everything is new and the size looks wrong.
- **"How you'll edit it" is not optional and is not a promise you can drop.** It is the plan's commitment to the six deliverables in [`complete-the-build`](complete-the-build.md). Say it in the words in that skill's plain-language table, never as `data-cslp`, `thumbnailUrl`, `ui_preview` or "Live Preview".
- **Keep it short.** A wall of plain text is no more approvable than a wall of jargon. If Layer 1 runs past roughly a screen, the plan is probably too big to approve in one go. Split the work.

#### Layer 2: Build sheet (technical. The build steps read this, not the user)

Print it under a clear heading so the reader knows they can stop at Layer 1:

```
── BUILD SHEET (technical — for the build steps; skip if you just want the summary) ──

ARCHITECTURE PLAN — <project name>

Sanity flags (reconsider before proceeding):
  - <flag>: <one-line reason and pointer to the affected piece>
  ... (or "None" if Steps 1–8 all clean)

Content model:
  <CT and GF listing from Step 4>

Sections (build in this order):
  <for EACH Section from Step 5, print EVERY line below — never just the name.
   `atomics` is what build-section and register-component consume: one atomic,
   one prop, one CT field. A Section with no atomics line was not decomposed.>
  - <Section name>  [exists|modify|create]   shared: <yes — rendered from layout | no>
      linked schema : <CT / Global Field / Group / Modular Block / Block / Reference> (+ selectedField set|unset)
      components    : <registered: Hero, ProductCard | built-in: Heading, Paragraph, Image>
      atomics       : <one line per atomic — atomic -> prop -> CT field (type)>
                      <Image      -> image    -> entry.hero.image      (imageurl)>
                      <Heading    -> headline -> entry.hero.headline    (string)>
      rich text     : <every RTE field on this Section — field (json_rte|html rte|markdown)
                       -> RichText|CollapsibleText -> embeds: entries <CT list>|assets|none
                       | none. NEVER map rich text to Heading/Paragraph.>
      repeaters     : <field iterated -> child Section -> Condition Blocks needed | none>
      section slots : <slot name -> what a template author drops there | none, and why>
      bindings      : <any binding NOT covered by the atomics lines above | none>

Templates:
  <Template inventory from Step 6 — for EACH: kind (Connected|Freeform), connected CT,
   URL pattern + url_source, and the ordered list of Sections placed on it>

Registered components needed:
  <component -> props to register, and which Section consumes it, each [exists|modify|create]>
  <and per component: thumbnailUrl [has|to add] · CSLP tags [has|to add] — an [exists] component
   with no thumbnail or no studioAttributes is [modify], not [exists]>

Built-in (field) components used:
  <Heading / Paragraph / Text / Image / Link / RichText -> which Section, bound to which field>
  <if this list is empty, say why — a plan where every visible element is a custom
   registered component is usually over-registered; plain copy belongs in built-ins>

Suggested upgrades (recommendations — the build proceeds without them if declined):
  <existing rich-text field rendered through a plain text component
     -> switch to RichText — no schema change, fixes markup showing as literal text>
  <plain multiline text field holding prose
     -> consider json_rte so authors can format and embed — schema change on N live
        entries via migrate-ct-schema>
  <long prose the design truncates -> CollapsibleText>
  <or "None — the existing model already types its rich text correctly">

RTE renderer (omit ONLY if the model has no rich-text field anywhere):
  fields        : <every json_rte / HTML RTE / Markdown field in the model -> the Section using it>
  embedded CTs  : <content types authors can embed -> the markup each renders as, per displayType
                   (block = card, inline = span, link = anchor) | none>
  embedded assets: <custom markup needed? | none — the MIME default covers it>
  registration  : <single registerRTERenderer call at bootstrap | not needed, and why>

Studio features considered:
  used     : <primitives this plan uses — built-ins, Sections, Slots, Repeater+Condition Block,
              exposed props, Global Fields, pinned entry/query, external data, variants, tokens>
  ruled out: <primitive -> one-line reason it isn't needed here>

Editing experience (mandatory — the six from complete-the-build; never listed as optional):
  preflight    : Live Preview + preview token <on | to enable> · cslp.appendTags <on | to enable>
                 · /canvas route <exists | to add>
  per component: thumbnailUrl + studioAttributes/$-twins on every registration above
  per section  : ui_preview set at write time on every Section above
  verify       : complete-the-build's verification block at handover, counts printed

Build order:
  <Step 7 listing>
```

#### Worked example: the same plan, both layers

Layer 1, as the approver sees it:

```
WHAT YOU'LL GET — Rewards page

In short:
  A rewards signup page at /rewards. Once it's built you can change every
  headline, image and piece of copy on it yourself, and reuse the hero banner
  on other pages. The signup form's behavior stays with the developers.

Your pages:
  • Rewards — one page at /rewards
      What's on it   : hero banner, signup form
      You can edit   : headline, sub-heading, hero image, form labels, category list
      Fixed for now  : what happens when someone submits the form

Reusable blocks (built once, usable on any future page):
  • Hero banner — used on 1 page today
      You can edit  : image, headline, body text
      Swap spots    : none — it's the same shape everywhere it's used
  • Signup form — interactive, so it stays a developer-built block
      You can edit  : field labels, the category list

Lists that grow by themselves:
  None on this page.

After this you'll be able to, on your own:
  ✓ change any wording or image on this page
  ✓ reorder the two blocks, or remove one
  ✓ put the hero banner on a new page without a developer
  ✗ change how the form submits, or add a new form field

Size of the job:
  2 reusable blocks · 1 page · 2 of your components hooked up · 6 new content fields

Already in place / being reused:
  Nothing yet — this is a fresh build.
```

Layer 2 for the same plan carries the detail Layer 1 deliberately hides: the hero's linked schema and `selectedField`, `type: "action"` on the form's submit prop, the `url` + `url_source` pair, which components are `[create]` vs `[exists]`, and the build order. Same plan, two audiences, never two different plans.

**Every Section line must be filled in.** A plan that names Sections without their linked schema, components, slots and bindings isn't a plan. It's a wish list, and the build step will improvise the missing parts. Same for Templates: kind + URL + which Sections go on it, or it's not decided.

### Step 10: STOP. Get explicit approval before anything is built.

**Nothing is created until the user approves this plan.** Print it, then present the architecture decision as an explicit choice and wait. Do not chain into a build skill, do not "start with the easy part", do not treat silence or a topic change as approval.

**Ask in the same plain language as Layer 1.** The approval question is the worst place to reintroduce jargon. A choice nobody understands gets answered "sounds good", which is not a decision. Ask verbatim:

> Two ways to build this. The difference is what you can change later without a developer:
>
> **A. Build it as reusable blocks (recommended).** Each part of the page becomes its own block. Afterwards you can reorder them, drop one onto a different page, restyle the text, and edit all the wording and images yourself. It's a bit more setup now.
>
> **B. Build it as one fixed page.** Faster to stand up. You'll be able to change wording and images, but **not** reorder anything, reuse a part on another page, or restyle it, those would need a developer. Splitting it up later means redoing the wiring, so this is easier to choose than to undo.
>
> I've planned for **A**. Reply **"go"** to build it, tell me what to change, or say **"B"** and I'll note the trade-off in the plan.
>
> One more: should **every `<thing>` get this design automatically** as you add more of them (recommended), or is this a **one-off page** you'll only ever have one of?

The last question is Connected vs Freeform. Ask it that way, never by those names. "Every product page looks like this" versus "this is a single campaign page" is a distinction any approver can make. "Connected or Freeform" is not.

**Rules for this gate:**

- **A is the default and stays the default.** Reuse count 1 does not downgrade a piece to "just drop a component", see § Golden rule. If the user picks B, record it in the plan as an explicit decision with its cost, so the next agent doesn't read a monolith as the intended shape.
- **One round of edits is normal.** Apply the user's corrections, reprint the changed sections, re-ask. Don't rebuild the whole plan from scratch.
- **Plain language in, plain language out.** If the user asks a question about the plan, answer in Layer 1's vocabulary. Dropping into "the Section's `selectedField` scopes it to…" mid-approval loses the approver, and an approval you talked someone into isn't one.
- **Partial approval is not approval.** "The sections look right" is not permission to create templates.
- **Carry the approved plan forward.** The build skills expect it: `build-section` per Section in order, then `build-connected-template` / `build-freeform-template`, then `register-component` for anything not yet registered. Hand each one the matching block from the plan rather than re-deciding.

## Inputs needed from the user

1. `source`. One of: an existing codebase (the default when `package.json` is present), a partially-built Studio project, a design/Figma link, or prose requirements. Determined in Step 0, not asked for.
2. `requirements`: a paragraph or bullet list of pages, features, reusable blocks, data sources. **Required only for scenario D** (from scratch, no code and no design). Ask if the user gives only a one-liner. For scenarios A to C the code or design is the primary input and this is supporting context.

## Acceptance

- [ ] **Step 0 ran and its inventory was printed**: existing routes, components, registered components, Sections, Templates, CTs. On an existing codebase the plan was built from the scan, not from the user's description alone, and items carry `[exists]` / `[modify]` / `[create]`.
- [ ] **Each piece's primitive was chosen from the Step 2b evidence table, and the "Studio features considered" block lists what was ruled out and why.** A plan built only from `registerComponent` fails this: it hides the rest of Studio from the user and leaves authors with a page they can only re-bind.
- [ ] **Every Section row names its Section Slots and its built-in (field) components, not just registered components.** A plan listing only `registerComponent` work is incomplete. Say explicitly where plain copy uses built-ins and where a template author needs a swap point.
- [ ] **Each page has an explicit Connected-vs-Freeform decision** with the connected CT (or the reason there isn't one), never left implicit.
- [ ] **The plan was printed in full and explicitly approved before any build skill ran.** Every Section line carries linked schema + components + slots + bindings. Every Template carries kind + URL + its Section list. No piece was created on an unapproved or half-filled plan.
- [ ] **The plan commits to the six deliverables in [`complete-the-build`](complete-the-build.md)**: Layer 1 carries the "How you'll edit it" lines, Layer 2 carries the Editing experience block, and the build order names them on steps 0, 2, 4 and 7. A plan that covers only Sections, bindings and templates describes something that renders but that a marketer cannot use.
- [ ] **The A-vs-B architecture choice was put to the user** (decomposed Sections vs a single template with components dropped in) and their answer recorded. If B was chosen, its cost is written into the plan.

The skill succeeds when:

- [ ] Every page in the requirements has been classified as Connected (multi-entry CT or single-entry CT), with the deciding Q1 / Q2 step printed.
- [ ] The content model lists every CT and Global Field needed, with reuse notes.
- [ ] The Section inventory is ordered by dependency (child Sections before parent Sections that use them).
- [ ] Each Section's Slot-candidate fields are flagged.
- [ ] The Template inventory names each page with its URL pattern and the Sections it stacks.
- [ ] The build order is printed as a numbered, executable list.
- [ ] Sanity flags are surfaced at the top of the plan (or "None").
- [ ] The plan ends with the handoff to `byoc-end-to-end`.
- [ ] No code was written and nothing was created in Studio. This skill is planning-only.

## Common pitfalls

| Pitfall | Why it bites | Right move |
|---|---|---|
| Calling a reusable block a "page" | Headers / heroes / footers aren't pages. They're Sections that pages assemble | Anything that doesn't have its own URL is a Section, not a Template |
| Calling a per-content-item page (blog post, product detail) a separate Template per entry | Templates iterate via URL pattern: one Template renders N entries. Building N templates means N times the maintenance | Multi-entry CT + one Connected template with a `{{entry.slug}}`-style URL pattern. The Template renders unlimited entries. |
| Skipping the content model step | Building Sections without knowing which CT backs them, so the missing field surfaces mid-build and the model has to be reworked | Model the CT first. The Section authoring depends on it. |
| Inlining a Modular Block / Group / Reference / Global Field instead of exposing a Slot | Locks the nested shape into the parent Section, throws away the reusability the field shape was set up to give you | Default to Slot. Override only when certain the nested shape is single-use. Global Field always deserves a Slot (it exists because of cross-CT reuse). |
| Building parent Sections before their child Sections | Parent's Slot has nothing to drop in when you try to verify it | Order Section build by dependency in Step 5: children before parents. |
| Producing a plan without sanity flags | The user proceeds with a flawed model. Rework cost is high | Step 8 is mandatory. Print "None" if clean. Otherwise list flags at the top of the plan in red. |

## See also

- [`design-component-library`](design-component-library.md): foundational pattern doc. Before this skill's build order sequences the work, that doc decides what to register: atomic + layout primitives instead of monolithic Sections. Read alongside [`decompose-design`](decompose-design.md) when the plan will produce a fresh component library.
- `start-here-zero-knowledge`: the conceptual prerequisite (run BEFORE this skill if the user is new)
- `understand-templates`, `understand-sections`, `understand-section-slots`, `understand-linked-schemas`, `understand-auto-binding`: the concept ladder this skill assumes is internalised
- `byoc-end-to-end`: the procedural macro that walks the plan in execution mode
- `complete-the-build`: the ten always-mandatory deliverables this plan commits to and the handover gate that verifies them
- `enable-visual-experience`, `install-live-preview`: the preflight half of those six
- `build-section`, `build-connected-template`, `build-repeating-section`, `use-section-slot`: the implementation skills the build order references
