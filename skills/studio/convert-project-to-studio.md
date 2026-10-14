---
name: convert-project-to-studio
---

## When to use

Orchestrator for "make my existing project Studio-compatible". Asks one scoping question (minimal conversion, one page, or the whole site), then drives the minimal conversion by chaining the install skills with their answers pre-filled: Studio SDK installed, `/canvas` mounted, and Studio wired as a **fallback renderer** behind the routes the app already owns, with the app's own 404 kept. Localized apps get every locale wired, not only the default.

Use for whole-project Studio enable/setup requests, including an existing app or a new app. On a new app, run the same setup sequence and let route detection choose the optional catch-all. Use `install-studio` alone only for an explicit SDK-only request. Single-page migrations use `migrate-page-to-studio`; design-only inputs use `decompose-site`.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Convert an existing project to Studio: minimal first

> ## Verification status
>
> Orchestrator over verified skills. The route pattern it wires is the catch-all + code-route precedence pattern (code-owned routes win, the catch-all serves everything else). **The locale step (§ Step 3) is not yet runtime-verified against a `next-intl` app.** Until it is, treat the single Base URL rule there as the working model, run the redirect probe on every locale, and report anything that does not match rather than improvising around it.

## Why this skill exists

"Convert this project to Studio" has been answered with two scopes: decompose the whole site, or pilot one page. Both rebuild pages. Neither is what most teams need first, which is Studio **available** in the app without any existing page changing. Without a skill for that, the agent improvises a scope question and steers the user into a migration they did not ask for.

The minimal conversion is a fixed contract. Every request resolves in this order:

1. **A code route matches.** The project's own page renders, unchanged. Code routes win by precedence (Next.js more-specific-wins, React Router first-match).
2. **No code route matches.** The catch-all mounts `<StudioComponent />` and Studio resolves a composition for that URL.
3. **Studio has no composition either.** The project's **existing** 404 page renders. Never a blank div for visitors, never a 500. Studio's editor iframe stays exempt so unsaved templates still preview.

Plus the `/canvas` route for Section authoring. No page migrated, no component decomposed, no Section built. Authors can create Studio pages at new URLs the same day. The larger scopes are supersets of this, so minimal is always phase one.

## Task

### Step 0: Confirm this is a whole-project ask

If the user named one route or one page, stop and run [`migrate-page-to-studio`](migrate-page-to-studio.md) via the plan-first rule instead. If the input is a design with no code, run [`decompose-site`](decompose-site.md). Otherwise continue.

### Step 1: Resolve scope from the request and prior answers

For a broad enable/setup request, use minimal conversion and state that it includes the canvas and wildcard fallback. Respect explicit SDK-only, dedicated-route, and migration requests. Carry existing answers forward; do not ask a question already settled in the conversation. Ask the following only when the requested migration scope is ambiguous:

> Three ways to bring Studio into this project. Pick one:
>
> **1. Minimal conversion (recommended).** I install the Studio SDK and mount Studio as a fallback behind your existing routes. Every page you have today keeps rendering exactly as it does now. Any URL your code does not claim is served by Studio, and if Studio has nothing for it either, your existing 404 page shows. Authors can start building new Studio pages at new URLs right away. Nothing is migrated or decomposed. About an hour.
>
> **2. Minimal, then migrate one page.** Everything in 1, then we pick one route, plan it, and swap it to Studio so you can validate authoring on real content.
>
> **3. Minimal, then a full-site plan.** Everything in 1, then a consolidated plan across every page type, built in dependency order.
>
> Reply **1**, **2**, or **3**.

Record the resolved scope. A reply such as “yes” or “start” accepts an immediately preceding concrete proposal. Options 2 and 3 run minimal conversion first, then the appropriate migration planning skill. Approval for setup does not authorize unrelated migrations, publishing, or changes to other projects.

Keep this non-secret progress record in the working context and resume it after login, restart, or compaction:

```text
Scope and accepted choices:
Framework, package manager, route root, React/Studio versions:
MCP: callable/read-verified | unavailable (reason) | declined
Project, stack, region, branch, environment, locale map:
SDK initialization modules:
Canvas route and observed iframe URL:
Fallback route and observed template iframe URL:
Verification: passed | failed | unverified, with evidence per check
Next pending step:
```

Run all remaining setup steps within the accepted scope. A specialist's “next steps” section is a handoff back here, not the end of project setup.

### Step 2: Preflight

Run [`analyze-project-fit`](analyze-project-fit.md). Carry forward: framework, package manager, React major, data centre, existing Contentstack SDKs, and the i18n row. Blockers (Path B stale SDK pin, C, G) stop this skill until resolved.

Run [`install-contentstack-mcp`](install-contentstack-mcp.md) discovery before requesting stack credentials or doing API work, even if OAuth credentials already exist. This is a gate, not a silent fallback: first determine whether callable Contentstack MCP tools are available in the active host, then offer MCP configuration/authentication if they are not. Do not ask the user to fill the app's `.env` merely because MCP is not yet connected.

Use MCP for supported CMA reads and writes after a successful read probe. Use OAuth HTTP or the Studio UI for operations MCP does not expose, especially Studio project listing/configuration, Live Preview enablement, and delivery/preview-token creation. Record the reason for each fallback. MCP does not eliminate the app runtime configuration: after discovery/provisioning, the app still needs the selected stack API key, delivery token, preview token, environment, locale map, and the Studio project's exact `contentTypeUid` in its environment. Ask only for values MCP cannot discover or create, and never guess a project, stack, locale, or composition content type UID.

Then [`enable-visual-experience`](enable-visual-experience.md): stack-level Live Preview must be on before any app-side work.

### Step 3: Locale step. Detect, map, wire, verify.

Studio treats locale as a context variable, not as part of a composition URL. Composition URLs are stored without a prefix (`/rewards`). Studio builds the preview iframe address as the environment's **per-locale Base URL** plus that composition URL, and an environment holds exactly one Base URL per locale. A localized app that skips this step gets a blank canvas when an author switches language, a doubled prefix such as `/en/en`, or a middleware redirect that kills the iframe.

**The single rule this skill enforces:**

- Composition URLs never carry a locale prefix.
- The environment's per-locale Base URL carries the app's prefix when the app is prefixed (`http://localhost:3000/en`, `http://localhost:3000/fr`), and is the bare origin when it is not.
- The catch-all strips the app's locale prefix from the request path before calling Studio (`/en/rewards` becomes `url: "/rewards"` with `locale: "en-us"`), so a doubled prefix cannot come from the route side. If compositions were already authored with prefixed URLs, list them and stop. Do not guess which side to change.

**3a. Detect app-side i18n.**

```bash
# Packages
grep -E '"(next-intl|next-i18next|i18next|react-i18next|react-intl|@lingui/[a-z]+|next-international)"' package.json
# Route segment
find app src/app -maxdepth 2 -type d \( -name '[[]locale[]]' -o -name '[[]lang[]]' \) 2>/dev/null
# Next config i18n key, locale middleware, React Router locale param
grep -n "i18n" next.config.* 2>/dev/null
grep -ln "locale\|createMiddleware" middleware.* src/middleware.* 2>/dev/null
grep -rn 'path="/:\(lang\|locale\)' src 2>/dev/null | head -3
```

Record: prefix strategy (`always`, `as-needed`, or none), the default app locale code, every app locale code. Nothing found means un-localized: note that in one line and run only 3d for the default locale.

**3b. Read stack-side locales.**

```bash
# $CS_AUTH is the resolved credential header from `authenticate-cma` — on the
# OAuth path it is `authorization: Bearer <access_token>`. A bare
# `authorization: <token>` is the MANAGEMENT-token form and 401s under OAuth.
curl -sS "https://<cma-host>/v3/locales" -H "api_key: <stackApiKey>" -H "$CS_AUTH"
```

Record every enabled `code` and which one is `fallback_locale`-less (the master).

**3c. Build the locale map and show it.** App code to stack code (`en` to `en-us`, `fr` to `fr-fr`). Print the table and ask the user to confirm. **Halt on any app locale with no stack locale** — that one is fatal, since the app would serve a URL the stack cannot resolve. Do not invent a mapping and do not proceed with the intersection.

The reverse is **not** fatal: a shared stack routinely carries locales this app doesn't serve (other sites, other brands, locales not launched yet). List those as out of scope in one line, wire every app-served locale, and continue. Halting there would block the common shared-stack setup for a condition the app can't act on.

| App prefix | Stack locale | Base URL to set on `<env>` |
|---|---|---|
| `en` (default) | `en-us` | `http://localhost:3000/en` |
| `fr` | `fr-fr` | `http://localhost:3000/fr` |

**3d. Pre-flight every Base URL, not only the default.** Read `GET /v3/environments` as in [`install-studio`](install-studio.md) step 3 and check `urls[]` for **every** mapped locale. For a missing or wrong entry, print the exact `PUT /v3/environments/<env-name>` body with all locale URLs, ask for a yes, then write it. Do not write without the yes.

**3e. Redirect probe, per locale.** Run the curl from [`setup-template-preview-routes` § middleware 307](setup-template-preview-routes.md#locale-prefixed-apps-the-middleware-307-breaks-the-iframe) against `<base URL>` and `<base URL>/canvas` for every mapped locale. Any 3xx stops this skill with the three documented fixes. Prefer "locale in the Base URL" since 3d already did it. A 308 on a trailing slash means `skipTrailingSlashRedirect: true` in `next.config`.

**3f. Answers carried into the route step.** The catch-all lives inside the locale segment (`app/[locale]/[...slug]/page.tsx`, or `<Route path="/:lang/*">` registered last). It strips the prefix before building `url`. It passes the mapped stack code as `{ locale }` on the SSR fetch and the same value to `useCompositionData` on CSR. It forwards `searchQuery` untouched so Studio's own locale override still wins inside the iframe. Its not-found branch renders the app's **localized** 404 (`app/[locale]/not-found.tsx` where one exists).

### Step 4: Install

Run [`install-studio`](install-studio.md). Take the **minimal-add branch** whenever `@contentstack/delivery-sdk` or `@contentstack/live-preview-utils` is already present: do not re-init the stack, create a separate `lib/studio.ts`. The per-locale Base URL check inside it is already satisfied by 3d. Do not register components in this step. Built-in components are enough for a first Studio page, and [`register-component`](register-component.md) is offered after the conversion, not inside it.

### Step 5: Canvas route

Run [`setup-section-preview`](setup-section-preview.md). A route mounting `StudioCanvas` must exist before the catch-all. Record the actual Section iframe URL generated by the selected project/environment and ensure that exact path mounts the canvas without site chrome. Preserve a working root or locale-prefixed canvas route; do not infer its address from the template URL or add a duplicate based on a guessed concatenation rule. Verify every served locale in the browser. Canvas URL remains the configured path of that route.

### Step 6: Fallback route

Run [`setup-template-preview-routes`](setup-template-preview-routes.md) in **wildcard mode** with these answers fixed. Do not re-ask them:

| Question it asks | Answer for the minimal conversion |
|---|---|
| Route mode (step 3) | **A. Wildcard.** Code routes win by precedence, so nothing the app owns changes |
| Opt-outs | None needed. Code routes already win — routes are ranked by specificity, so `/api/*` beats the catch-all whatever the order |
| `[...slug]` vs `[[...slug]]` (step 5) | `[...slug]` when a root page exists (it nearly always does on an existing app), else `[[...slug]]`. On a locale-prefixed app, inside the segment |
| `chromeOwner` (step 5a) | **`code`.** Header and footer stay in the layout |
| 404 branch (step 5a iii) | **Reuse the project's existing not-found** (`app/not-found.tsx`, `pages/404.tsx`, or the `NotFound` component). Localized apps: the per-locale one. Create a file only when none exists. Editor-mode exemption on |
| Locale | From Step 3f |

Framework scope: Next.js App Router, Next.js Pages Router (`pages/[...slug].tsx`, existing `pages/404.tsx`), Vite + React Router (`path="*"` registered last, the old `<Route path="*" element={<NotFound />} />` removed and `NotFound` rendered from the no-spec visitor branch). Remix, Astro, or a custom router: stop and say the pack is under-specified for that router rather than guessing, per the pack's rule that silence is reported, not filled.

### Step 7: Configure Studio

Run [`configure-studio`](configure-studio.md). Environment = the one whose Base URLs were set in 3d. Language = the mapped default stack locale. Canvas URL = `/canvas`.

### Step 8: Verify

Run [`verify-setup`](verify-setup.md), then this smoke, **once per mapped locale**:

| URL | Expected |
|---|---|
| An existing code page (`<base URL>/products/some-slug`) | Renders exactly as before. Same header, same footer, same markup |
| A bogus URL (`<base URL>/definitely-not-a-page`) | The project's own 404 page. Not a 500, not a blank page, not an empty div |
| `<base URL>/canvas` | `<StudioCanvas />` renders. The 404 page here means the catch-all claimed it |
| The redirect probe from 3e | `200`, empty `redirect_url` |

Then in Studio: create a template, do not save it, open it. The canvas renders it (editor exemption works). On a localized project switch the canvas language once. The iframe reloads at the other locale's Base URL rather than going blank.

### Step 9: Report and hand off

Print, filled in:

```
Minimal conversion done.
  Existing routes:   untouched (<n> code routes win by precedence)
  Fallback route:    <path> mounts <StudioComponent /> for unclaimed URLs
  404:               <file> for visitors, editor iframe exempt
  Canvas route:      /canvas (<file>)
  Locales:           <en-us, fr-fr | single locale en-us>, Base URLs set on <env>
  Studio project:    env <env>, language <locale>, Canvas URL /canvas

Definition of done for this scope (from complete-the-build):
  [x] cslp.appendTags in the SDK init
  [x] stack Live Preview + preview token
  [x] /canvas mounted
  [x] per-locale Base URL for every locale served
  [ ] component studioAttributes / thumbnailUrl / Section ui_preview / publishing: not applicable until something is authored

Next: author a first Studio page at a URL no code route claims, then register your components (register-component) when you want them in the palette.
```

Option 2 or 3 chosen in Step 1: now run [`plan-studio-architecture`](plan-studio-architecture.md) for the scoped page(s). Option 1: stop here.

## Inputs needed from the user

1. `scope`: minimal for a broad setup request, or the user's explicit migration/SDK-only scope from Step 1.
2. Confirmation of the locale map (3c) and of every Base URL write (3d).

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] Scope and prior accepted choices are recorded. Broad setup includes canvas and fallback routing; explicit user constraints take precedence.
- [ ] MCP availability was checked in the active host and a read operation verified its target, or a concrete fallback reason is recorded.
- [ ] The verification report distinguishes HTTP reachability from rendering and live editing. Unverified browser checks are not marked passed.
- [ ] `analyze-project-fit` ran and no blocker path (B / C / G) was open when install started.
- [ ] Locale detection ran. On a localized app the map was confirmed by the user, every mapped locale has a Base URL on the targeted environment, and the redirect probe returned 200 for every locale. On an un-localized app this was stated in one line.
- [ ] No existing route file was modified or deleted. The only route files added are the canvas route and the catch-all.
- [ ] The per-locale smoke in Step 8 passed for every mapped locale: existing page unchanged, bogus URL renders the project's own 404 with no 500, `/canvas` renders `<StudioCanvas />`.
- [ ] No component was registered, decomposed, or authored as part of the minimal conversion.
- [ ] The report block in Step 9 was printed with the definition-of-done items marked as above.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Skipping the Step 1 gate and improvising "full site or one page" | Neither scope is what "make it compatible" asks for, and both start rebuilding pages | Ask the three-option gate verbatim. Minimal is the default |
| Wiring the catch-all before `/canvas` exists | The catch-all claims `/canvas` and every Section renders as a composition miss or the 404 page | Step 5 before Step 6, always |
| Optional `[[...slug]]` on an app with a root page | Both match `/`. Next.js reports a collision or the root page loses | `[...slug]` whenever any root `page.*` exists, including `app/[locale]/page.*` |
| Treating "no pages found" as greenfield | A fixed path list misses `src/app` and locale segments, so a catch-all lands in an app full of pages | Use the `find` in `setup-template-preview-routes` step 3 and confirm with `ls` before believing an empty result |
| 404 branch returns an empty `<div />` to visitors | The site never 404s. Correct for the editor iframe, wrong for everyone else | Gate on `isStudioEditorMode`: empty div in the editor, the project's 404 page for visitors |
| Unwrapped `fetchCompositionData` | It throws on a miss, so every bogus URL is a 500 instead of the 404 page | Use `resolveComposition` from `configure-csr-vs-ssr`, never a hand-rolled catch |
| Only the default locale has a Base URL | Switching language in the canvas produces a blank iframe with an error pointing at the Studio project | Step 3d checks and sets every mapped locale |
| Catch-all passes the prefixed path to Studio | `/en/rewards` never matches a composition stored as `/rewards`, or resolves to a doubled `/en/en` | Strip the prefix, pass the stack locale code separately, forward `searchQuery` untouched |
| App locale codes assumed equal to stack codes | `en` is not `en-us`. The fetch resolves nothing and the page 404s in one language only | Build and confirm the map in 3c. Halt on a mismatch |
| Decomposing or registering "while we are here" | Turns a one-hour conversion into a migration the user did not choose | Nothing beyond the fallback route until the user picks option 2 or 3 |

## See also

- [`setup-template-preview-routes`](setup-template-preview-routes.md): the route wiring, chrome and 404 handling, locale redirect probe
- [`analyze-project-fit`](analyze-project-fit.md), [`install-studio`](install-studio.md), [`setup-section-preview`](setup-section-preview.md), [`configure-studio`](configure-studio.md), [`verify-setup`](verify-setup.md): the chained skills
- [`migrate-page-to-studio`](migrate-page-to-studio.md), [`decompose-site`](decompose-site.md): the option 2 and option 3 follow-ons
