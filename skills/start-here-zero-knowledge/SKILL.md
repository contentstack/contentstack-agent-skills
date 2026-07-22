---
name: start-here-zero-knowledge
description: "Zero-knowledge onboarding orchestrator. Walks new users through the conceptual ladder and nudges them to build their first real Section + Template."
allowed-tools: Read Grep Glob
---

## When to use

Zero-knowledge onboarding orchestrator. Walks new users through the conceptual ladder and nudges them to build their first real Section + Template.

Use as the VERY FIRST skill when a user says "I'm new to Studio", "what is Studio?", "I want to add Studio to my site", "how do I start with Studio", "show me Studio from scratch". Also defensively when `build-section` / `build-connected-template` is invoked by someone unfamiliar with Sections. Do NOT use as reference for someone who's shipped a Section.

# Start here — Studio from zero

## Why this skill exists

Studio's value depends on a mental model the user must internalise BEFORE they start building. Skip it and they'll:

- Drop atomic components straight onto routes (one-off pages, no reuse)
- Hand-wire bindings per page (slow; defeats the point)
- Build "Sections" as new React components in their repo (misunderstanding — Sections are composition data, not new code)
- Skip linked schemas (forfeits auto-binding; back to manual wiring)
- Build N templates as N separate page routes (forfeits the catch-all + URL pattern reuse)

This skill is the on-ramp. It walks five concepts in 10–15 minutes, then routes to the right first action.

## Task

### Step 1 — Frame the problem (no jargon yet)

Tell the user verbatim:

> Before any code, here's the problem Studio solves and the new vocabulary you'll need.
>
> **Today's problem.** Every new page on your site is engineering work. A new blog post, a new product, a campaign landing — each one is a route file + a component arrangement + data wiring. Marketing waits on engineering. Engineering rewrites the same hero-grid-CTA pattern for every layout. Adding a page = a deploy.
>
> **Studio's premise.** Engineers register your atomic React components ONCE. Authors then compose **Sections** (reusable parts of a page like a hero or a CTA strip — bound to CMS data once) and arrange those Sections into **Templates** (whole-page recipes). New pages = new entries in your CMS, not new code.
>
> The whole game is **bind once → reuse everywhere**. Sections and Templates are how Studio expresses that.

### Step 2 — Walk the concept ladder (run each in order)

These seven concept skills explain the whole mental model — ~12 minutes total. Run in order; each builds on the last:

1. **`understand-sections`** — what a Section is. The "part of a page" unit.
2. **`understand-linked-schemas`** — how a Section declares the data shape it needs.
3. **`understand-auto-binding`** — what happens when a Section drops on a Template. Why dropping "just works."
4. **`understand-section-slots`** — how to make ONE Section serve multiple Templates by leaving swap points open.
5. **`understand-templates`** — what a Template is and how Sections compose into one. Key mental-model rung: **Templates compose Sections.** A Template is a page-level container; Sections are the units that fill it. Build Sections first, then assemble them into a Template — Templates never model fields directly.
6. **`understand-canvas-vs-component`** — the two SDK mounts split by *what they render*: `<StudioCanvas />` is **Section-only** (one `/canvas` route, used inside Studio's iframe for Section building / authoring / previewing — Templates never render through it). `<StudioComponent />` renders **Templates** — on your real visitor routes AND inside Studio's template-preview iframe (Studio iframes the env Base URL + Template URL, which is the same route a visitor hits). Sections never render standalone; they only appear inside a Template.
7. **`understand-canvas-url`** — the Canvas URL field that comes up during setup (it points Studio at the `<StudioCanvas />` route used for Sections).

After these the user can answer in plain language: *"A Section is a reusable part of a page with its CMS binding declared. A Template is a stack of Sections. When I drop a Section on a Template, Studio matches its linked schema to the Template's content type and auto-binds every prop. Section Slots let one Section serve many Templates with a child-component swap point. Sections author through `<StudioCanvas />` at the `/canvas` route inside Studio's iframe. Templates render through `<StudioComponent />` on my real routes — visitors hit those routes directly, and Studio iframes the same routes when previewing a Template."*

### Step 3 — Branch by project shape

Ask: **"Are you adding Studio to an existing website, or starting a brand-new one?"** Branch:

#### Path A — Existing website (most common)

The user already has a React app (Next/Vite/CRA/Remix), a Contentstack, and live content. Adding Studio is incremental.

Sequence:

1. `analyze-project-fit` — read-only diagnostic; pins React 18 if needed, detects framework, picks the install branch.
2. `enable-visual-experience` — turn on Live Preview at the stack level (UI-only step).
3. `install-studio` — adds the three SDKs and wires the canonical init.
4. (Optional) `setup-local-https-canvas` — only if you need HTTPS-on-localhost for service workers / secure cookies / strict policy. Plain `http://localhost:<port>` works for the basic Studio iframe.
5. `setup-section-preview` — adds the `/canvas` route mounting `<StudioCanvas />`, sets Canvas URL.
6. `register-component` — register the user's first 3–5 atomic components (the ones they'll use in the first Section).
7. `build-section` — author the first Section. **Stop here and celebrate** — the first Section authored against real components is the moment Studio "clicks."
8. `setup-template-preview-routes` — add the catch-all (or dedicated route) that mounts `<StudioComponent />` for visitors.
9. `build-connected-template` — author the first Template against an existing content type; drop the Section on it.
10. `verify-setup` — run the layered smoke test.

After step 7 the user has proof the loop works (register → Section → render in canvas). After step 9 they have a live URL rendering a Template against their existing CMS data.

#### Path B — Brand-new website (greenfield)

The user is starting from scratch. They still need React + a CMS first.

Sequence:

1. Scaffold a React app (Vite + React 18 recommended; `npm create vite@latest -- --template react-ts` then pin to 18 — `npm create vite@latest` defaults to React 19 today, which the SDK doesn't yet support. The SDK's `^18.0.0` peerDep will reject the install with an ERESOLVE error rather than silently installing and breaking at runtime, so the incompatibility surfaces immediately — but you still need to downgrade to React 18 before proceeding).
2. Set up a Contentstack with at least one content type that has fields you'll bind a Section to (e.g. `blog_post` with `title`, `subtitle`, `cover`, `body`).
3. Then run the same chain as Path A from `analyze-project-fit` onwards.

For Path B specifically: build 2–3 atomic components first (Hero, FeatureCard, CTA) so there's something to register in step 6. A `register-component` skill on a half-built component is wasted effort.

### Step 4 — Set expectations

Tell the user verbatim:

> Two things you'll feel in the first hour:
>
> 1. **The first Section feels like overhead.** You register a component, declare a linked schema, then drop it once. *Why didn't I just import the component on a page?* Because the second time you use it on a different Template, you'll feel the payoff — zero re-wiring. By the fifth use it's a 10× return.
>
> 2. **You'll be tempted to skip Sections and bind components directly on Templates.** Don't. Template-level direct binding works for the Template you just authored, but the binding doesn't travel — when you make a similar Template tomorrow, you'll wire it again. Sections + linked schemas are what make today's binding usable tomorrow.
>
> If a part of a page appears on more than one Template, make it a Section. If you're not sure: make it a Section anyway; downside is small.

### Step 5 — Hand off to the first procedural skill

Print the user's tailored plan as a numbered list (from Step 3's appropriate path), and offer to invoke the first skill (`analyze-project-fit`). Wait for explicit user confirmation before any state-changing skill runs.

## Inputs needed from the user

1. `projectShape` — `existing` or `new`. Determines the branch in Step 3.

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] The frame in Step 1 was printed (the user got the "problem and premise" narrative before any jargon).
- [ ] The user was guided through (or directly read) all six concept skills in Step 2 — order matters: Sections → linked schemas → auto-binding → slots → Templates → Canvas URL.
- [ ] The user confirmed their `projectShape`.
- [ ] The user received their branched, numbered plan (Path A or Path B).
- [ ] Step 4's expectation-setting was printed verbatim — both warnings (first-Section-feels-like-overhead, don't-skip-Sections).
- [ ] The user was nudged toward Sections + Templates rather than left to invent their own pattern.
- [ ] The user explicitly confirmed before any state-changing skill was invoked.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Skipping the concept ladder and going straight to `install-studio` | User ends up wiring page-by-page; never realises Sections exist; ships a one-off integration that doesn't compound | Always run Step 2 first, even if the user is impatient. The 10-minute investment prevents weeks of rework. |
| Letting the user write Section-shaped React components in their repo | Sections are composition data, not new components. New React code "to be a Section" is wasted work. | Run `understand-sections` — make sure they see "a Section is composed from atomic components you already have." |
| Treating Path B (greenfield) as "easier" | It isn't — greenfield users still need a CMS stack with real content types and entries before Studio is meaningful. Empty stack = nothing to bind. | Step 3 Path B explicitly sequences CMS setup before Studio install. |
| Recommending `build-section` before `register-component` | A Section can't exist without registered atomic components to compose. | Path A step 6 (`register-component`) comes BEFORE step 7 (`build-section`). |
| Pushing the user toward complex setups (Section Slots, exposed props) on day one | These are advanced — premature complexity confuses new users | Keep the first chain to: register components → one Section → one Connected Template. Section Slots and exposed props are post-success additions. |

## See also

- `understand-sections`, `understand-linked-schemas`, `understand-auto-binding`, `understand-section-slots`, `understand-templates`, `understand-canvas-vs-component`, `understand-canvas-url` — the seven concept skills this orchestrator runs
- `plan-studio-architecture` — the architecture planner that follows the concept ladder. Takes the user's project requirements (paragraph or bullets) and produces a printed plan: which pieces are Sections, which pages are Connected templates, the content model, the build order. Run BEFORE `byoc-end-to-end`.
- `byoc-end-to-end` — the procedural macro that walks the plan in execution mode. After concepts are crisp AND the architecture plan exists, run `byoc-end-to-end` to see the full BYOC arc (register components → build Sections → expose Slots → assemble into Templates → SSR/CSR wiring → verify → ship) named on one page.
- `analyze-project-fit` — first procedural skill on either path
- `studio-tour` — broader walkthrough; this skill is the zero-knowledge entry that precedes the tour
