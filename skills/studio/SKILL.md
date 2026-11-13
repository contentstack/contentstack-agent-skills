---
name: studio
description: "Contentstack Studio router: sends Studio work to the Studio MCP (built on Flux) first, and falls back to the bundled specialist guides when the Studio MCP isn't available or can't do the task (SDK install, project provisioning, component registration, sections and templates, data binding, canvas and preview routes, publishing, troubleshooting). Use when the user mentions Contentstack Studio or its concepts: the Studio SDK, canvas, compositions, Connected or Freeform templates, sections, section slots, repeaters, registering components, BYOC, Studio preview routes, or making a project Studio-ready. Also use it when Live Preview, Visual Editor, Launch hosting, content types and entries, or Personalize audiences and variants are part of Studio work (setting up Studio, the canvas, a template's content, hosting a Studio site, showing a Studio page's own version to an audience). Do not use for general Contentstack CMS, Live Preview, Visual Editor, Launch or Personalize questions that do not involve Studio."
---

# Studio router

You are working on Contentstack Studio. Studio work goes through the **Studio MCP**
first: an MCP server built on Flux, Contentstack's goal-tracking MCP framework. It tracks each goal, does every change in Contentstack and Studio step by step, asks before
each one, checks its own work, and hands changes to the site's code to you with the rules to
follow. The pack's specialist guides (one per task: install, provisioning, component registration,
section/template authoring, data binding, preview wiring, verification, troubleshooting,
migration) are the **fallback** for when Studio MCP can't be used. Its tools keep Flux's names in some hosts (for example `Contentstack_Studio_Flux`); treat those as the Studio MCP.

This SKILL.md is the only file loaded up front.

## When to use

- Anything that mentions Contentstack Studio or its concepts: the Studio SDK, canvas, compositions, Connected or Freeform templates, sections, section slots, repeaters, registering components, BYOC, Studio preview routes, or making a project Studio-ready.
- Live Preview, Visual Editor, Launch hosting, content types and entries, or Personalize audiences and variants, when they are part of Studio work (setting up Studio, the canvas, a template's content, hosting a Studio site, showing a Studio page's own version to an audience).

Use another skill for:

- Live Preview or Visual Editor problems that don't involve Studio → `cms-live-preview-visual-editor-support-assistant`
- Delivery SDK code outside Studio → `dx-delivery-sdk`
- Content model design in general → `cms-data-modeling-best-practices`
- Rendering JSON RTE fields → `cms-json-rte`
- Hosting the site on Launch → `launch-platform`
- General MCP setup outside a Studio project → `dx-mcp-server`

## Instructions

1. If the Studio MCP's tools are callable here, do the work through it (§ 1).
2. Otherwise, or for one of the reasons in § 2, say so and work from the bundled guides: resolve them as in § 3 and route through `skills-index.md` (§ 4).
3. Apply the standing rules in § 5 and § 6 on every Studio turn that uses the guides.

### 1. Studio MCP first

Studio MCP is available when its tools are callable in this host: `list_goals`, `next_step`, `preview`,
`apply`, `check` and `get_guide`. Check the tools themselves; a conversation flag or a remembered
session is not evidence.

With Studio MCP:

1. Start with `list_goals` for the request, then `next_step`, and follow the Studio MCP's instructions.
   Load `get_guide flux/router` once per conversation.
   This includes personalizing a Studio page (an audience, its own version of the page's words,
   publishing it, and the site passing the variant to Studio): ask the Studio MCP first.
2. **Ask before each change.** Use `preview` to show what will change, and `apply` only after the
   author says yes. Name goals and changes in plain words; don't show ids or JSON.
3. **The site's code.** When `next_step` hands over a `code_task` and you can open the site's code
   here, tell Studio MCP once with `next_step` `access`, then follow `get_guide studio/code-skill` for
   every code task. Studio MCP sends each task's rules with it.
4. **Don't read the bundled guides while Studio MCP is working.** The Studio MCP's guides and rules are the
   current ones; mixing in the bundled guides gives two sets of instructions for the same step.
5. **Keep a setup going.** Replies like "yes", "start" or "done" continue the Studio MCP's current goal with
   `next_step`; they are not new requests.

#### Not a reason to leave Studio MCP

These are Studio MCP working as intended. Follow what it says:

- a check that fails, or Studio MCP saying something must be fixed first;
- Studio MCP asking the author a question or for a choice;
- a missing permission or sign-in step Studio MCP explains;
- Studio MCP declining a change because the stack, project or site isn't ready for it.

### 2. When to use the bundled guides instead

Only in these cases:

1. The Studio MCP's tools aren't in this host.
2. Studio MCP doesn't respond, or the same call fails twice in a row with a server or network error.
3. Signing in to Studio MCP can't be completed.
4. `list_goals` has no goal for the request, or `get_guide studio/cant-do` says Studio MCP can't do it.
5. The author asks to use the guides.

Then:

1. **Say so once, in plain words**: Studio MCP isn't available for this (and why), so you're working
   from the Studio guides, which may be older than Studio MCP. A silent switch looks like Studio MCP ran.
2. **Mid-goal**: note the last step Studio MCP finished. Continue from the matching guide (in
   `fallback-map.md` when present, otherwise through `skills-index.md`). Never let Studio MCP and the
   guides both make changes for the same goal.
3. Work from the guides as described in § 3 to § 6 below.

**Back to Studio MCP.** When Studio MCP is reachable again, run `check` on the goal before anything else so it
sees what was done outside it, then continue with `next_step`.

**Neither works.** If Studio MCP is unavailable and a guide won't resolve, stop, say what's missing
(connect and sign in to Studio MCP, or reinstall the skill pack), and make no changes.

### 3. Resolving a skill file

The specialist guides sit next to this file, in the same folder: a skill named `<name>` is `<name>.md` beside this SKILL.md, and the lookup table is `skills-index.md` in the same folder. Every cross-reference in this file and in `skills-index.md` is written as `<name>` or `<name>.md`. Resolve all of them this way.

Fallback: if `<name>.md` isn't there, try `../<name>/SKILL.md` (a host that installed each guide as its own skill folder).

**If neither resolves, say so out loud**: "the Studio skill pack looks mis-installed, `<name>` didn't resolve", and do NOT quietly fall back to general knowledge. A silent fallback looks identical to the pack working, so the user never learns their install is broken.

### 4. Working from the guides

**Setup intent takes precedence over keyword matching.** “Enable Studio”, “make this project Studio ready”, “Studio setup”, and equivalent whole-app requests run `convert-project-to-studio` through verification. `install-studio` alone is for an explicit SDK-only request. Preserve the active setup objective across replies such as “yes”, “start”, and “OAuth done”; resume the pending step rather than routing that reply as a new task. Use the orchestrator's scoped completion checklist; authoring requirements below apply only when components or compositions are authored.

**Discover MCP execution before resolving raw HTTP credentials.** Follow `install-contentstack-mcp` to inspect callable tools in the current host and verify the target with a read call. A stored OAuth session is not evidence of a connected MCP server. Prefer available MCP operations; use OAuth HTTP for missing operations or an explicitly recorded connection limitation. Never infer tool availability solely from a conversation flag.

1. Read `skills-index.md` (in this folder). It has two parts.

2. **Trigger table.** Scan the user's most recent message against the phrases in the left column. If one row matches, Read that skill's file and follow it. If several match, run them in the order the table implies (installs before authoring, `analyze-project-fit` before anything state-changing).

3. **Topic map.** Use this when no trigger phrase fires but the topic is Studio-shaped. The user is exploring or asking a conceptual question. Pick the closest skill by name + one-liner and Read it.

4. If nothing matches after both passes, answer from general Studio knowledge, but say so, and check whether a skill is missing that should exist.

### 5. Standing rules when working from the guides

Studio MCP enforces these itself and sends them with each step. When working from the guides, they apply on every Studio turn.

#### Atomic and reusable, every time

**This applies on every Studio turn, whatever the user asked for. It is not optional and it is not only a planning concern.**

Before creating, registering, or authoring anything:

1. **Decompose first.** Never register or build a component that renders more than one piece of content. The test: does it render more than one heading / image / body / list? If yes, run [`decompose-jsx-to-atomics`](decompose-jsx-to-atomics.md) before anything else. One Section per page, or one component swallowing a whole page, is a defect, not a shortcut.
2. **Compose from atoms by default: do NOT reach for a pre-composed composite.** A palette usually contains both **atoms + layout primitives** (`*-atom-heading`, `*-stack`, `*-row`, `*-grid`, `*-section-shell`) and **composites** that already bundle a whole shape (`*-feature-card`, `*-hero`, `*-card-grid`). Dropping one composite is faster and looks identical on the canvas, and it is the wrong default: its internals are fixed in code, so the author cannot restructure it, the spacing inside it cannot be matched to a comp, and the design is no longer expressed as a composition. **Build the shape out of atoms unless the user explicitly asks to reuse an existing component.** If a composite would clearly save real work, say so and let them choose. Do not decide it silently.
3. **Reuse atoms, not shapes.** Reuse means the same `*-atom-heading` everywhere, not a ready-made card. Two things differing only in spacing are one Section plus an exposed prop, never two.
4. **Shared shells are Sections.** Header, footer, nav, menus, breadcrumbs render on every page and are the highest-value reusable pieces in any project. They are never "atomic, no binding". Their menus are **Repeaters over a field**, never hardcoded lists. Otherwise an author cannot add a menu item without a developer.
5. **One atomic prop maps to one CT field.** A single prop taking a whole object is how binding breaks: the binder recursively unwraps single-key objects for every type except `object`/`array`, so a coarse prop renders blank with no error.

If the user's request would skip this ("just register the page component", "make the whole page one section"), say what it costs (nothing reusable, authors can't reorder, bindings break) and propose the decomposed shape instead. Do it their way only if they confirm after hearing that.

#### Definition of done

**Also every Studio turn.** Eight deliverables decide whether what you built is usable by a marketer rather than only by a developer. Every one fails silently. The page still renders, nothing errors, and the gap surfaces only when a non-developer opens Studio:

1. `cslp: { appendTags: true }` in the SDK init, once per project.
2. `studioAttributes` on the root + `wrap: false` in the register entry + `$prop` twins, **every** registered component.
3. `thumbnailUrl`, **every** `registerComponent` call.
4. `ui_preview`, **every** Section composition. The editor writes this for itself by screenshotting the canvas on save, but only while it's empty: once a thumbnail is set, Studio no longer replaces it, so refresh it when the section's look changes. Use PNG, JPEG or WebP; an SVG shows as a blank tile. **A CMA-authored Section has it empty forever** unless you supply an asset uid explicitly. So "at write time" means have the asset ready and include it, not "the create call handles it". See [`author-composition-via-api`](author-composition-via-api.md) § Section thumbnails for the three ways to do it. Scripted authoring is exactly where this gets skipped, and the only signal is a blank tile in the palette.
5. Live Preview enabled on the stack + preview token, once per project, and the site reads the preview token on preview environments only (never on the live site).
6. The canvas route mounted at the project's **Canvas URL** path (often `/canvas`, but it's whatever the project's Configuration says), once per project.
7. **Published** to the environment the project targets, every Section and Template, and again after every tree edit. Delivery otherwise serves the old version while the CMA and canvas both look correct.
8. **Composed of Sections**: every Template. Read the saved composition back and count `section-composition` nodes. Zero means the page is one component bound to the whole body. The standing rule above already forbids that shape, and a build still reached it, because a monolith renders correctly and fails no other check here. Counting is the only thing that catches it.

Read [`complete-the-build`](complete-the-build.md) for the how and the verification block. The runnable node count is in [`build-connected-template`](build-connected-template.md) § Post-build structural check. Never report a build done with any of these outstanding. Say "created, thumbnail pending" and then finish it. State them in the plan up front too, so what the user approves is what they get.

#### Auth preflight

**Settle the credential before the first API call of the turn, not when one fails.** Every specialist repeats this. It lives here because it must hold even before a specialist is pulled. (With Studio MCP, sign-in is the Studio MCP's; follow what it says.)

1. Resolve OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (`~/Library/Application Support/ContentstackMCP/oauth-config.json` and its platform equivalents). **Ask the user before reading or refreshing that stored session**: it is their credential, and refreshing it rotates the refresh token, which can sign the MCP server out (its next refresh fails with `400 invalid_refresh_token`) unless the new pair is written back.
2. **Don't ask for a session `authtoken` up front.** It is a full user-session credential: every org, stack and permission the user holds. It is the last rung of the [`authenticate-cma`](authenticate-cma.md) ladder, considered only after a freshly refreshed OAuth token has been observed to fail. Prefer `csdx auth:login --oauth` or finishing the step in the Studio UI, and explain the risk before asking for one.
3. Access tokens last **59 minutes** and refresh tokens **rotate**. Tooling that refreshes must persist the new pair. A bare `curl` loop does neither, so long work belongs in a script.
4. If nothing resolves, or a refresh returns `400 invalid_refresh_token`, hand the user `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` and wait. It needs a TTY and a browser, you cannot run it for them. The region must be **in** the command. `DEFAULT_REGION` is `NA`, so omitting it silently authenticates against NA prod.
5. `403 error_code 316` is **not** an auth failure. It is a valid credential aimed at a stack outside its org. Re-authenticating fixes nothing. Check with `GET /v3/stacks` + `organization_uid`.

### 6. Rules

- Studio MCP first, every Studio request. Use the guides only for a reason in § 2, and say which one.
- When working from the guides: always re-Read the skill file. Never answer from a remembered summary. The source of truth is the file on disk.
- **A failed Read is a hard stop, not a shrug.** If a skill file won't resolve (see § 3), report it. Improvising over a broken install is worse than erroring: the user believes the pack ran when it didn't.
- When working from the guides, never skip reading `skills-index.md`. The lookup is cheap. Missing a skill is expensive.
- If the user's request implies multiple skills (e.g. "install and set up preview routes"), pull each in the order they must run: skills-index.md's Trigger table encodes that ordering.
- Prerequisite skills: many authoring skills assume `install-studio` + `configure-studio` are done. If the user's project state is unclear, run `analyze-project-fit` first.

## MCP tools

**Studio MCP (preferred for Studio work).** `list_goals`, `next_step`, `preview`, `apply`, `check` and `get_guide`. Some hosts list them under Flux's name (for example `Contentstack_Studio_Flux`). Every change goes through `preview`, then `apply` after the author's yes (§ 1).

**Contentstack MCP (when working from the guides).** Studio is MCP-first for the operations the server supports. [`install-contentstack-mcp`](install-contentstack-mcp.md) covers discovering, installing and verifying the server, and [`understand-contentstack-mcp`](understand-contentstack-mcp.md) covers what it does and doesn't do. Common tools (local server group in brackets):

- Inspect: `get_all_content_types`, `get_a_single_content_type`, `get_all_entries`, `get_single_entry`, `get_all_environments`, `get_all_languages` (`cma`)
- Change: `create_a_content_type`, `update_content_type`, `create_an_entry`, `update_an_entry`, `publish_an_entry` (`cma`)
- Delete: `delete_an_entry`, `delete_content_type` (`cma`)

The server doesn't cover every Studio operation: the Studio API project list and configuration (`/v1/projects`) and some token and Live Preview operations need OAuth HTTP or the Studio UI. Use only tools the host actually lists, and never claim an MCP call ran when none did.

## Security

These apply always, with the Studio MCP or the guides.

### Defaults

- Use MCP tools only for the Studio work the user asked for, and verify the target stack with a read call first.
- Resolve credentials OAuth-first (see § Auth preflight). Ask before reading or refreshing another tool's stored OAuth session.
- Delivery and preview tokens may reach the browser; management tokens, OAuth tokens and session authtokens never do.
- Never disable TLS certificate or hostname verification, and never ship permissive frame headers (`frame-ancestors *`, `Access-Control-Allow-Origin: *`) outside local development or the canvas route.

### Destructive Actions

Creating or changing stacks, content types, entries, compositions or Studio projects is a real mutation. Name the stack, branch and items, state what will change, and get confirmation first. This applies to MCP tool calls and OAuth HTTP calls alike. Never delete or overwrite existing content, sections or templates without explicit approval.

### Secrets

Never print, echo or store tokens, API keys or `.env` values, in chat, logs or files. If a secret appears in input, don't repeat it; recommend rotating it.

### Environment Variables

Use descriptive placeholders such as `CONTENTSTACK_API_KEY`, `CONTENTSTACK_DELIVERY_TOKEN`, `CONTENTSTACK_PREVIEW_TOKEN` and `CS_OAUTH_ACCESS_TOKEN`, and keep real values in a gitignored `.env`.
