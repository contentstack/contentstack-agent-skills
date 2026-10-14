---
name: studio-tour
---

## When to use

Intent-driven end-to-end walkthrough that meets the user wherever they are and routes them through setup, registration, sections, templates and ship via specialist skills.

Use when the user wants Studio working end-to-end but has not picked a starting point ("just walk me through", "I want to ship a page", "I have components, what next"). This skill orchestrates. It delegates to specialists at each step. Do NOT use when the user has a specific named task. Invoke that skill directly.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Studio Tour: start here

## Context

Studio sits between three things a user already has (a React component library, a Contentstack, an app routing layer) and one thing they want (visually composed pages with real CMS data, editable post-publish without code changes). The journey from "I want to use Studio" to "page rendering" is six stages. Many users don't realize some are optional.

This skill identifies the user's current stage, names what they're really trying to do, and routes to the right specialist.

Studio is three things in one (surface this early if the user hasn't seen it):

1. **A visual page builder**: drag-drop composition for content authors
2. **A real-data preview surface for composed components**: the missing rung between Storybook (isolated, fake data) and the live URL (composed, real data, post-deploy)
3. **An on-the-fly editor for layouts / components / look-and-feel**: when pages are built through templates, swap sections / reorder / re-bind without a redeploy

## The six stages

```
1. Stack          → API key, Delivery Token, Preview Token, Environment, Language (Contentstack)
                    + Live Preview on (enable-visual-experience)
2. App SDKs       → install-studio + install-live-preview into the user's React app
3. Studio project → Playground Canvas (no app) OR Website Canvas (with canvas route)
                    + Environment + Language
4. Registered     → register-component for each custom component the user already has
   components       (skip on Playground; required for Website Canvas to use brand components)
5. Sections       → build-section: connect a structural schema (CT / GF / Group / MB / Block /
                    Reference; never a scalar field) + drop registered components + bind props
6. Templates      → build-connected-template (CT-bound; covers both repeatable pages AND
                    one-off pages backed by a single-entry CT). Drops sections; saves.
                  → Deploy when ready (deploy-studio-site)
```

Stages 3-6 happen inside Studio's web UI (no API tokens needed: the user's browser session is the auth). Stages 1-2 + 4 touch the user's app code or Contentstack and may need credentials.

## Task

This skill is a **discovery + routing flow**, not a doing-flow. Walk it through 4 phases.

### Phase 1: Discover the user's intent

Map the supplied `userGoal` to one of these named intents. If unclear, ask one clarifying question, never guess.

| If the user said something like… | Intent |
|---|---|
| "try it without installing anything", "explore", "see what it looks like" | **try** |
| "understand what Studio does", "decide if it fits my project", "evaluate" | **understand** |
| "build my first page", "ship a real page" | **build** |
| "bring my React components into Studio" | **byoc** (bring your own components) |
| "I have a page idea but don't know how to model it" | **model** |
| "swap a section / move things around / change the layout" | **edit** (existing Studio user) |
| "troubleshoot a broken canvas" | redirect to `troubleshoot-canvas` (NOT this skill) |
| "verify my setup" | redirect to `verify-setup` |

State the named intent back before proceeding ("Sounds like you're trying to **build** a real page. Let me walk you through the path.").

### Phase 2: Map their current state to the six stages

Take `existingState` and translate it onto the stage list. Identify the lowest unfinished stage. That's the current step.

| `existingState` value | Stages completed | Lowest unfinished |
|---|---|---|
| `none` | (none) | Stage 1 / 2 |
| `studio-project-only` | 1, 3 (partial: Playground) | Stage 2 if they want Website Canvas, else go to 5 |
| `sdks-installed` | 1, 2 | Stage 3 |
| `canvas-route-mounted` | 1, 2, 3 (Website Canvas) | Stage 4 |
| `components-registered` | 1-4 | Stage 5 |
| `sections-exist` | 1-5 | Stage 6 |
| `templates-exist` | 1-6 | Done, go to deploy / edit |

If the user picked combinations that don't make sense (e.g. `templates-exist` without `sections-exist`), ask one clarifying question. Don't assume.

### Phase 3: Route based on intent + state

Pick the next specialist skill (or doc page) from this matrix.

| Intent | Current stage | Next concrete step |
|---|---|---|
| **try** | none | Run `install-studio` only IF user wants real components. Otherwise: create the project in Studio, leave the Canvas URL blank to use the Playground Canvas, then start authoring directly in Playground (no app setup needed). |
| **try** | studio-project-only | Author a small section in Playground using Studio's defaults. Skip steps 2 + 4. Use `build-section` with `linkedSchemaUid` blank (static-only). |
| **understand** | any | Reading path, in order: `start-here-zero-knowledge`, `understand-templates`, `understand-sections`, `choose-connected-vs-freeform`. |
| **build** | none | Sequence, in order: `analyze-project-fit`, `enable-visual-experience`, `install-studio`, `setup-section-preview` (or stay on Playground if exploring), `register-component` (one per component), `build-section`, `build-connected-template`, `setup-template-preview-routes`, `verify-setup`, then optionally `deploy-studio-site`. |
| **build** | sdks-installed | Resume at `setup-section-preview`, then continue the build sequence. |
| **build** | components-registered | Resume at `build-section`, then `build-connected-template`. |
| **byoc** | any | `register-component` per component, then `wire-component-default-data` for sensible defaults. Optionally `figma-generate-components` if Figma is the source of truth, or `import-design-tokens` to pull tokens. |
| **model** | any | Walk content modeling first (CT / Global Field / Modular Block / Reference). Then `build-section`. If sections need iteration over a list, `use-repeater` + `use-condition-block`. If a single value should be overridable per template, `expose-section-props`. If a region should be template-author-defined, `use-section-slot`. |
| **edit** | templates-exist | Direct to the relevant in-Studio action: re-bind a prop, swap a section, re-order. No skill needed. This is what Studio's runtime editor is for. If an entire layout change is needed, route to `build-connected-template` or rebuild a section with `build-section`. |

### Phase 4: Map the path end-to-end

Before they start the next skill, **describe the full path** so they know what they're getting into. Example for `build` intent from `none`:

```
Path: from zero → a Blog Post page rendering at /blog/<slug>

1. analyze-project-fit     → read-only check: React version, existing SDKs, data center
2. enable-visual-experience → Live Preview on the stack, delivery + preview tokens
3. install-studio          → SDKs in your app, 3 packages, env vars
4. setup-section-preview   → canvas route mounted, Canvas URL set on the project
5. register-component (×N) → your Hero, Card, Button etc. appear in Studio's palette
6. build-section           → Hero Strip section linked to a gf_hero Global Field
7. build-connected-template → Blog Post template, drops Hero Strip, connected to blog_post CT
8. setup-template-preview-routes → /blog/:slug route in your app mounting <StudioComponent />
9. verify-setup            → smoke test: open the URL, see a real entry render

Estimated wall-clock for a fresh setup: 30–60 min the first time, 10 min for the second blog-post template.

Skills you can skip:
- setup-section-preview → if you're fine on Playground Canvas (no deploy though)
- register-component → if you only want Studio's defaults (less interesting for production)
```

Then ask: "Ready to start with step 1?", and on confirmation, invoke the first specialist skill.

## Inputs needed from the user

In this order:

1. `userGoal`: free-form sentence describing what they want. Don't accept anything generic like "use Studio". Ask for specifics until one of the named intents lands.
2. `existingState`: comma-separated state markers. If user doesn't know, ask one clarifying yes/no per item: "Do you have an app with @contentstack/delivery-sdk installed already? Do you have a Studio project in your Contentstack account?"
3. `frameworkOrTarget`: required for `install-studio` / `setup-section-preview` / `configure-csr-vs-ssr` downstream. Ask now to avoid asking later.

## Acceptance

- [ ] User's intent named explicitly (one of: try / understand / build / byoc / model / edit), confirmed back to them
- [ ] Current state mapped to the six stages, with the lowest-unfinished stage identified
- [ ] Next specialist skill (or doc page for understand intent) named and the reason for picking it stated
- [ ] Full path through remaining stages described before the user starts work
- [ ] On confirmation, the next specialist skill is invoked OR the doc page is opened
- [ ] User does NOT leave the tour without a clear next action

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Guessing the intent from vague input | Wrong path. User wastes time on the wrong skill | Ask one clarifying question. Never assume between try / build / model |
| Skipping the Playground vs Website Canvas distinction | User installs SDKs they didn't need (try intent) OR is stuck without deploy (build intent) | Surface Playground Canvas early for try intent. Surface Canvas URL setup for build intent |
| Inviting the user to "build a section" without first checking they have registered components | Section composes only Studio defaults. Brand wrong | Confirm step 4 (registered-components) before step 5 (build-section) for Website Canvas users |
| Treating troubleshoot / verify intents as "tour" cases | The user wanted a focused diagnostic, got a journey overview | Recognize troubleshoot-canvas / verify-setup keywords and redirect immediately |
| Forgetting the 3-in-1 framing for understand intent | User leaves still thinking Studio is "just a page builder" | Open with the three-things-in-one explanation at the top of this skill (§ Context) |

## Driving the canvas

Moving a component on the Studio canvas through browser automation has a required event sequence, and the high-level drag helpers do not satisfy it. See [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md) before attempting a drop.

## See also

- Every specialist skill referenced in the Phase 3 routing matrix
