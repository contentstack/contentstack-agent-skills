---
name: author-without-code
---

## When to use

End-to-end authoring path for content teams on a Studio project a developer has already set up (pick a template, bind data, preview, save, publish) no code required.

Use when the user wants to compose pages WITHOUT engineering involvement: pure UI authoring against an already-installed Studio project. Phrases: "build pages in Studio", "I just want to compose", "no code". Do NOT use for installs (`install-studio`), registration (`register-component`), or troubleshooting. Those are engineering tasks.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them), and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Author a page in Studio: no code required

## Context

Studio is split into two surfaces, and confusing them is the #1 reason content authors stall.

1. **Contentstack**: where the **content** lives (entries, assets, content types). This is the CMS you already know. URL: `app.contentstack.com/.../stacks/...`.
2. **Studio**: where the **layout** lives (which sections, in what order, bound to which fields). URL: `app.contentstack.com/.../projects/...`.

A published page combines layout (Studio) with content (a Contentstack entry), which produces the URL the developer's app renders. You move between both surfaces. This skill tells you which surface to use for each step.

Two kinds of pages exist in Studio, with very different authoring flows:

| Page kind | What it is | When you'll use it | Where to start |
|---|---|---|---|
| **Connected Template** (the main authoring surface) | One layout, bound to a whole content type. Every entry of that CT renders through this layout at a URL derived from the entry (e.g. `/blog/<slug>` for every blog post). Also used for one-off pages backed by a single-entry CT (the homepage, the about page, etc. Your developer may have modelled those as single-entry CTs). | "Add a new blog post." "Add a new product." "Update the homepage hero copy." | **Contentstack**: create or edit the entry in the CT. Studio auto-renders it. |
| **Freeform template** (only if the project has the Freeform feature turned on) | One layout not tied to any content type. Its content comes from pinned entries, pinned queries, or values typed straight into the layout. | A one-off landing page the developer built as Freeform. | **Studio**: open the template from the **Templates** sub-tab. Content edits happen in the layout (Flow C). To build a new one, use `build-freeform-template`. |

**Most content-team work is content-first**: edit the entry in Contentstack, the page updates automatically. Open Studio only when the layout itself needs to change.

## Task

### 1. Open Studio and orient

Open the URL the developer shared. You should land in a **Studio project** with two tabs in the top nav:

- **Compositions**: every page-shaped layout in this project. The page splits into two sub-tabs inside: **Templates** (the page templates you'd publish at a URL: Connected Templates, plus Freeform templates if the project has Freeform turned on) and **Sections** (reusable layout blocks the developer prepared, dropped into compositions: you do not usually create these directly). This is the main authoring surface.
- **Settings**: project-level config (rarely needed by authors).

Registered React components don't have a top-level tab. They're visible from the left palette when you have a composition open. There is no UI to create or edit components from inside Studio.

If the **Templates** sub-tab is empty, stop. Ask the developer to confirm at least one template has been created. Without a starting point, you cannot author.

### 2. Decide your path from the goal

Map your `goal` to one of these three flows.

- **"Publish a new blog post / new product / new entry of an existing CT"** maps to Flow A (edit in Contentstack, no Studio needed)
- **"Change the text / image / link on an existing page"** without changing the layout maps to Flow D (Live Preview or Visual Editor: fastest path, no Studio)
- **"Update the layout of an existing page"** (reorder sections, swap a hero, change a binding) maps to Flow C (open the existing composition in Studio)

### 3. Run the matching flow

#### Flow A: New entry of a Connected content type (most common)

1. Switch to **Contentstack** (same nav, different surface).
2. Open the relevant content type, then click **+ New Entry**.
3. Fill in **every field** the Connected Template binds. If you skip a field that the template uses, the live page renders that part as empty. Hover the field name to see help text the developer wrote.
4. **Save** the entry (in CS, not Studio).
5. **Publish** the entry to the environment your site reads from (usually "production", confirm with the developer if unsure).
6. Visit the live URL. The entry should render via the template within seconds (publish latency varies).

#### Flow C: Edit layout of an existing composition

1. In Studio, open the **Compositions** tab, then click the row for the page you want to edit.
2. The canvas opens with the page as currently saved/published. The status badge (top right) shows **Draft** if unsaved changes exist, **Published** otherwise.
3. Make changes: drag sections in/out, rebind fields, change order.
4. **Save**, then **Deploy**. Save persists the draft in Studio. Deploy makes the live URL render the new layout.

#### Flow D: Just change content (text / image / link) on an existing page

For a Freeform template page, there is no template entry. Text from a pinned entry or query is edited on that entry in Contentstack (as below). Anything else lives in the layout, so use Flow C.

For a Connected template page: it's a Contentstack entry edit. Flow A, but on an existing entry: open the entry, edit the fields, click **Update**, then **Publish** (Contentstack's own publish action, not Studio's Deploy).

If you don't know whether a field is bound or static: open the composition in Studio, click the field on the canvas, and read the Properties panel. It will say either "Static" (Flow C edit) or show a binding chip pointing to an entry (Flow A-style edit on that entry).

### 4. Verify before stepping away

Open the live URL in an **incognito / private browser window** (so you're not seeing a cached or preview version) on the production environment. Check:

- The page loads at the URL you expect.
- All content is filled: no `[unbound]`, no `{placeholder}`, no broken images.
- Links work.
- Mobile width looks OK (resize the window).

If any of these fail, return to the relevant flow. Don't tell the team "it's live" until you've checked the live URL in incognito.

### 5. Bookmark where to come back

Bookmark the entry in Contentstack. That's your edit point forever. If you also need to change the layout later, bookmark the composition in Studio too.

## When to escalate to the developer

Stop and ask the developer rather than guessing if any of these are true:

- The Compositions tab is empty, or no template covers your CT.
- The section you need does not exist in the Sections palette.
- A field you need to bind isn't on the entry (the content type needs a new field, a CMS schema change).
- You see `[unbound]` after binding and don't know why.
- Publishing succeeds but the live URL still shows the old version after 5+ minutes.
- The URL pattern you need conflicts with another composition's pattern (you'll see a warning in Studio).

These are not author-fixable: they need developer changes or are bugs.

## What this skill is NOT

- Not a guide to set up Studio (use `install-studio` / `studio-tour`).
- Not a guide to register components (use `register-component`, developer task).
- Not a guide to building sections (use `build-section`, typically a developer / designer task).
- Not how Studio works internally (use `studio-tour` for that).
