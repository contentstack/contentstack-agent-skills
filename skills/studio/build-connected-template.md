---
name: build-connected-template
---

## When to use

Scaffold a Connected (content-type-bound) Studio template by dropping sections, wiring linked-schema bindings, and saving. Every entry of that CT renders at a derived URL. Use Studio UI, driven through Playwright per [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md). Don't hand the clicks to the user or switch to the API unless they ask; that's [`author-composition-via-api`](author-composition-via-api.md).

Use for a Connected template, a page bound 1:1 to a content type (blog post, product) where every entry renders at a derived URL. Phrases: "build a blog template", "PDP template", "connected to a content type". Assumes `install-studio` is done.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

> **Pattern preflight: mandatory.** Before the first write, run [`match-existing-pattern`](match-existing-pattern.md): read the Templates and Sections already in the project, **reuse what already covers this schema**, and build to the pattern they use. Skip it only when the project has no compositions at all. Authoring something structurally foreign to what is there is rework, and it is invisible until someone opens the Layers panel.

# Build a Connected Template in Studio

> **Approved plan required.** This skill builds. It does not decide. If there is no plan the user has explicitly approved (Sections with their linked schemas, Section Slots, per-Section components (registered vs built-in), bindings, and the template kind), **stop and run [`plan-studio-architecture`](plan-studio-architecture.md) first**, then come back with the approved block for this piece. Building without it is how a project ends up as one monolithic template with no Sections, no slots and no reuse. Exception: the user is explicitly iterating on a piece already in an approved plan.

## STOP: apply the Section-qualification rule before dropping anything

Before dropping components or bindings directly on this Template, check the **golden rule** from [`plan-studio-architecture`](plan-studio-architecture.md) § Step 2:

- **Reused across Templates?** Any bound compound component that appears on more than one Template MUST be built as a Section first (`build-section` or `build-repeating-section`), then dropped here.
- **Schema iteration (Modular Block / multi-Reference / group-multiple)?** MUST become a **List Section** (Repeater + CBs). Never author the iteration directly on the Template.

Only when BOTH answers are no is it correct to drop registered components straight onto this Template. When in doubt, build the Section first: Sections are cheap to add, direct-drop is expensive to unwind.

## Context

Templates compose Sections. Build Sections first via `build-section`. See `understand-templates` § Templates compose Sections.

**Connected is the default flavor**: including one-off pages backed by a single-entry CT.

A **Connected template** is bound to one content type. Every entry renders through it at a URL derived from the CT's `url` field (or VX preview URL, or per-template override). What makes it Connected:

1. **Content-type binding** (chip in canvas chrome).
2. **Linked-schema auto-binding**: Studio reads each section's `linked_schemas` and wires it to a matching field on the CT.

Studio uses one preview entry at a time (auto-picked, most recently updated matching the URL pattern). Bindings record field paths, not entry UIDs.

Two render surfaces:
- **Studio canvas iframe**: `<StudioCanvas />` on the canvas route, for authoring.
- **Live site**: `<StudioComponent />` on ONE catch-all (`app/[[...slug]]/page.tsx` / `<Route path="*">`). Studio resolves every URL via `sdk.fetchCompositionData(...)`. Per-template routes are NOT needed. Without the catch-all, the derived URL 404s even after Deploy.

This skill creates the template, drops sections, confirms bindings, saves. It does NOT publish/deploy.

## Task

1. **Confirm prerequisites.** Before touching the UI, verify (ask the user to confirm if you can't check):
   - Studio project exists and is linked to the stack.
   - Content type `contentTypeUid` exists and has at least one entry.
   - **A URL pattern is available.** Studio resolves which entry to preview by matching the request path against a URL pattern. **One of these five sources must be in play**: `custom_preview_url` (set in the stack's Visual Experience settings), `content_type_url_pattern` (page CT with `url_pattern`), `default_url_pattern` (Studio-generated default, applied automatically for connected templates when nothing else is configured), `user_specified_pattern` (authored via the canvas's Edit URL flow), or `legacy_url` (binding against a CT `url` field on every entry). You do NOT need a CT `url` field. Studio's `default_url_pattern` covers the no-config case. Only verify upfront if the project uses the `legacy_url` path: in that case every entry must have `url` populated AND starting with `/` (without a leading slash the entry is invisible to the matcher. Canvas opens blank with "No composition for /…").
   - At least one **published** entry exists for the connected CT. Connected canvas fetches via the CDA. Unpublished entries return 404. Canvas appears blank.
   - At least one Section composition exists whose `linked_schemas` references a field on `contentTypeUid`, otherwise auto-binding will silently leave every section unbound. If unsure, list sections via the Studio Sections tab and check each one's `linked_schemas`.
   - For a custom URL pattern: prefer configuring the **Preview URL** in the stack's **Settings**, under **Visual Experience**, rather than per-template overrides. If the CT already has a `url` field with a pattern, Studio will derive from it automatically.

2. **Open the Templates tab** in the target Studio project. Empty state shows an illustration with a **+ New Template** button. Populated state shows a list with columns Title · Connected Content Type · Publish Status · Modified At · Actions.

3. **Click `+ New Template`** (top right). The Create New Template chooser modal opens with the Connected Template option ready to create.

4. **Fill in the modal:**
   - Title: `templateName`
   - Connected Content Type: pick `contentTypeUid` from the dropdown (lists every CT in the stack)
   - Click **Create Connected Template**

5. **Verify the canvas chrome** once Studio opens the new template:
   - Composition title matches `templateName` (top bar)
   - Content-type chip matches `contentTypeUid`
   - `PREVIEW ENTRY :` (entry name) with a `⇄` swap icon. Studio auto-picks the most recently updated entry that satisfies the URL pattern
   - URL line directly below evaluates against that entry (no `{{...}}` leftovers)

   **Symptom: "No entry has a URL field populated yet" (canvas shows the message, no preview entry is auto-selected):** this is the editor's `MISSING_CT_PATTERN_URL_FIELD` error, raised **only** under `url_source: "content_type_url_pattern"` (or `legacy_url`). Those sources resolve the preview entry by querying for a populated `url` **field**, with no pattern substitution. So it means: the connected CT isn't a page type, OR no entry of that CT has its `url` field set. **If the CT is a singleton with no `url_pattern` by design** (a fixed-URL page), don't add a pattern you don't want, just set the entry's `url` field by hand (e.g. `/rewards`). The source only needs a non-empty `url`, not a CT pattern. Switch to `user_specified_pattern` only when the URL must derive from a different field (`{{entry.slug}}`, a reference). See [`author-composition-entry` § Which `url_source` to write](author-composition-entry.md#url-metadata-matched-pair). Fix: ensure the CT is `is_page: true` with a `url` field + `url_pattern` (see [URL pattern rule below](#single-entry-vs-multi-entry-url-pattern-rule)). For every entry, set the `url` field, then click `⇄` and pick a preview entry. After a CT `url_pattern` change, re-save + republish entries so `entry.url` recomputes, otherwise old entries still carry stale URLs.

6. **(Optional) Edit the URL pattern.** Only if `urlPattern` is provided OR the derived URL is wrong. Click the pencil icon, then Edit URL. Use Insert chips for `{{entry.<field>}}`, `{{environment}}`, `{{taxonomy:<uid>}}`. **Save** validates + refetches. **Avoid `{{locale}}`**: carry locale via routing + SDK `locale` query option.

   <a id="single-entry-vs-multi-entry-url-pattern-rule"></a>**Single-entry vs multi-entry URL pattern rule.** Connected templates split into two cases that need different URL shapes:

   - **Single-entry template** (homepage, about, pricing: one entry, one URL): a literal URL like `/home` works. The matcher only needs to resolve one path.
   - **Multi-entry template** (blog posts, products, recipes: many entries through one template): the literal pattern `/blog/:slug` does NOT work. The `:slug` placeholder comes back **literal**: Contentstack's **CMS-side** CT URL-pattern compiler (separate from the Studio SDK pattern compiler) doesn't substitute `:slug`, the entry's `url` field saves as `/:slug` instead of a real slug, and the SDK has no per-entry URL to match against. **The proven shape:** CT `url_pattern: "/:title"`, Contentstack's CMS slugifies the title field into `entry.url` (`:title` is the working CMS substitution token, `:slug` is treated literal) + CT `url_prefix: "/<route>/"` (e.g. `/blog/`), composition `url: "/<route>/{{entry.title}}"` with `url_metadata.url_source: "content_type_url_pattern"` and `url_queries: ""`. The SDK then queries entries by `entry.url`. CT pattern and composition URL must be **consistent by construction**. After changing the CT pattern, re-save + republish every entry so `entry.url` recomputes.

   **URL traps: same symptom ("No composition for /…"), different fixes:**

   - **(a) Literal URL on a multi-entry template.** A composition `url` like `/home` works for single-entry, but a multi-entry template needs a placeholder. **Fix:** use `/<route>/{{entry.url}}` or `{{entry.title}}` (NOT `:slug`, see rule above).
   - **(b) Entry `url` field missing leading slash.** SDK matches the full request path. `url: "home"` never matches `/home`. **Fix:** every entry's `url` starts with `/`.
   - **(c) API-set `user_specified_pattern` reverts.** `url_metadata.url_queries` is only generated by the UI's Edit-URL and Save flow. **Zero-UI workaround:** make the CT a page type (`is_page: true` + CT-level `url_pattern`), set composition `url_metadata.url_source: content_type_url_pattern`, put `{{entry.x}}` in composition `url`.
   - **(d) `:slug` placeholder comes back literal.** Contentstack's CT URL pattern recognizes `:title` but treats `:slug` as a literal string: `url_pattern: "/:slug"` saves and stays `/:slug`, never substituting. **Fix:** use `:title` in the CT pattern (Contentstack slugifies it). Use `{{entry.title}}` in the composition URL.

7. **Drop the primary section.** If `primarySectionUid` was provided, drag it from the left palette (Sections category) or the Sections sidebar onto the empty canvas. Drop targets highlight as you drag.

8. **Confirm auto-binding.** When the section drops, Studio reads its `linked_schemas` and tries to bind to a matching field on the connected CT:
   - **One match**: bound silently. Verify by selecting the section, then opening the **Settings** tab in the right panel.
   - **Multiple matches**: bound to one. Switch via the dropdown in the section's right-panel **Settings** tab.
   - **No match**: drops unbound. Either (a) add a matching field to the CT, (b) edit the section's `linked_schemas`, or (c) manually pick a compatible field from the section's Settings if one exists.
   For sections that render lists, the section internally uses a Repeater bound to the matched field. Per-item field bindings inside the section read from `repeater.<field>` and resolve automatically, no per-template wiring needed.

9. **Fill any Section Slots.** If the section exposes a Section Slot (e.g. `Hero Strip` slot for a CTA), drag a component (Button, Link, registered component) into the slot's outlined region on the canvas. Slots are carved out of the section's structure: drop into the outlined region, not the surrounding section frame.

10. **Override exposed props per template instance.** Select the section, then open the **Settings** tab in the right panel. Each exposed prop (e.g. Card Title) shows an input. Type the per-template override (e.g. `"Related Blogs"`). This stores on the template instance, not on the section composition itself.

11. **(Optional) Drop individual components and bind them.** From the left palette (Basic / Media / Container / Smart Containers / Registered Components / HTML Elements). Select the component on canvas, open the **Data** tab in the right panel, and click the binding chip on a prop. The Data Picker opens: pick `entry.<field>`, a reference field, or a context value (including `repeater.<field>` when inside a Repeater).

12. **Sanity-check with a swap.** Click `⇄` next to PREVIEW ENTRY and pick an entry with different content shapes (long titles, missing images, empty references). Canvas re-renders instantly. Empty fields mean the entry lacks the value, not that the binding is wrong. Don't re-edit the binding to "fix" an empty render. Swap back and confirm.

13. **Save.** Top bar **Save** persists the template to Contentstack. This does NOT publish. Deploy is a separate step that moves the template through the publishing workflow to an environment.

14. **Smoke-test on the live site.** Hit the derived URL on the host app. The catch-all route should match it and mount `<StudioComponent />`. If the canvas iframe renders but the live URL doesn't, the catch-all route is missing. Add it via [`setup-template-preview-routes`](setup-template-preview-routes.md) (default = ONE catch-all that handles every URL. No per-template route needed) before claiming success. The live page fetches its data via `sdk.fetchCompositionData(...)` under the hood.

15. **Connected templates preview at the ENVIRONMENT base URL, NOT the Canvas URL.**
    - **Sections** preview at the **Canvas URL** (in Studio, open the project, go to Settings, and open Configuration).
    - **Connected templates** preview at the **environment base URL** + resolved path (`Stack → Settings → Environments → <env> → Base URL`).

    If sections render but a connected template shows "localhost didn't send any data" or "SDK Not Initialized", env base URL is wrong (common cause: scheme mismatch, env says `http://localhost:5173` but dev server is HTTPS-only via mkcert).

    **Fix:** `GET /v3/environments/<env>` first, show the user the current `urls[]` and the change, and get approval. Then `PUT /v3/environments/<env>` with the full `urls[]` array (every existing locale entry kept, only the scheme of the affected one changed) so it matches the served canvas-app. A PUT with only one entry drops the other locales' URLs.

16. **Multiple-file fields bind to `.0.url`, not the field name.** When a CT has a `file` field of type multiple (an asset array), and you bind it to a scalar prop like `imageurl`:

    - Wrong: `entryBind("imageurl", "images")` binds the array, which renders "No image" (or the array's `.toString()`).
    - Right: `entryBind("imageurl", "images.0.url")` picks the first asset's URL.

    If the prop should iterate (multiple images), use a **Repeater** bound to the array and bind `imageurl` to `repeater.url` inside the repeater item. The `.0.url` shortcut is for single-image props only.

## Inputs needed from the user

Ask in this order. Stop if any required input is missing.

1. `contentTypeUid`: content type uid (required)
2. `templateName`: human title (required)
3. `urlPattern`: optional override. Leave blank to use CT-derived URL
4. `primarySectionUid`: optional. Leave blank to skip auto-drop and let the user choose interactively

If the user doesn't know the content-type UID, point them at `app.contentstack.com`, where they open the stack, go to **Content Models**, and click a model. The UID is on the right-rail.

## Acceptance

Succeed only when ALL of the following are true. If any fails, surface exactly which step broke and stop.

- [ ] A new row appears in the Studio Templates list with `templateName` as title and `contentTypeUid` populated in the Connected Content Type column
- [ ] The canvas opens cleanly on reload: preview-entry URL line evaluates without `{{...}}` leftovers
- [ ] Every section dropped is either bound (linked-schema match shown in right panel) or explicitly flagged unbound with the reason
- [ ] Bound props render real values from the auto-picked preview entry. Swapping the preview entry re-renders without errors
- [ ] Save completed without error (top bar reverts from dirty to clean state)
- [ ] Hitting the derived URL on the host app's catch-all route renders the page (a 404 means the catch-all is missing or the URL pattern doesn't match what Studio expects. Do not claim success)
- [ ] **The finished tree is composed of Sections, not one component.** Read the saved composition back and count `section-composition` nodes in `ui` and entries in `linked_sections`. **Both zero means you built a monolith**, the outcome the approved-plan guard at the top of this skill exists to prevent. It is easy to reach without noticing: a page whose whole body is one modular-blocks field invites a single component bound to the array, which renders correctly and passes every check above. Stop, decompose per the approved plan, and rebuild the tree from Sections. See § Post-build structural check below.

## Post-build structural check

The acceptance list above is all render-time: a monolithic template passes every line of it. This check is the only one that catches the structural failure, so run it after saving and before reporting success.

```bash
# requires:
#   STUDIO_API  Studio API base URL for your region
#   PROJECT     Studio project uid
#   UID         the saved template's composition uid
#   CS_AUTH     one auth header resolved per authenticate-cma, e.g. "authorization: Bearer $CS_OAUTH_ACCESS_TOKEN"
#   CS_SCOPE    the scope header, e.g. "organization_uid: <org-uid>"
# Decode the saved template's ui and count what it is actually made of.
curl -s "$STUDIO_API/projects/$PROJECT/compositions/$UID" -H "$CS_AUTH" -H "$CS_SCOPE" \
| python3 -c '
import sys, json, zlib, base64
c = json.load(sys.stdin)["composition"]
ui = c["ui"]
if isinstance(ui, str):
    ui = json.loads(zlib.decompress(base64.b64decode(ui[5:])) if ui.startswith("zlib:") else ui)
n = []
def walk(x):
    if not isinstance(x, dict): return
    if x.get("type") == "section-composition" or x.get("metadata", {}).get("compositionUID"): n.append(x)
    for a in (x.get("slots") or {}).values():
        if isinstance(a, list): [walk(i) for i in a]
walk(ui)
ls = c.get("linked_sections")
ls = json.loads(ls) if isinstance(ls, str) else (ls or [])
print(f"section-composition nodes: {len(n)}  linked_sections: {len(ls)}")
print("MONOLITH — decompose before reporting success" if not n and not ls else "composed of Sections")
'
```

Two numbers, and they must agree: every placed Section is both a `section-composition` node in the tree **and** an entry in `linked_sections`. A node without its `linked_sections` entry is the missing-`linked_sections` trap: the page renders, the editor misbehaves later.

**If you are converting an existing monolith,** lift each top-level node into its own Section composition (`place_composition_as: "section"`), then replace the node with a `section-composition` referencing it. The bindings inside the node move with it unchanged and resolve exactly as before. Verify by diffing rendered text length before and after. It should not move. Node uids must stay unique across the tree, so generate them rather than deriving them from a truncated slug.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| "Template did not load." | URL pattern doesn't match anything the host app's catch-all routes through Studio | Fix the pattern or wire the catch-all. See [template preview routes](setup-template-preview-routes.md). Per-template routes are NOT the fix. The catch-all covers every URL. |
| Bound value renders empty | Current preview entry lacks that field | Swap via `⇄`, don't re-edit the binding |
| Registered component drops blank | Missing default data on the component | Developer needs to add Component Default Data. Not a Studio-side fix |
| Section drops unbound | No `linked_schemas` match on the CT | Add a matching field, edit the section's `linked_schemas`, or bind manually from Settings |
| **One component bound to the page's whole blocks field** | The fastest way to make a page render, and it passes every render-time acceptance check, so nothing flags it. But the page is one node: nothing inside is separately editable, reorderable or reusable in Studio, and the next page repeats the work instead of reusing a Section | Treat a single `*_sections` / modular-blocks field as a **list of Sections to build**, not one prop to bind. Run the post-build structural check above. Two zeros means rebuild from Sections |
| "No element is currently selected" in the right panel | Nothing on canvas is selected | Click the component on canvas first |
| Editing URL from the composition list | That view is read-only for URLs | Edit from the canvas navbar pencil icon |
| Assuming Save with preview entry = X pins the template to X | Bindings record field paths. Preview entry is authoring-only | Treat preview-entry swaps as visual diagnostics, not state |
| Dropping a Rows / Box wrapper before the first real component | Leaves visible "Drop Here" placeholder zones in canvas + screenshots. Rows is an e2e-test scaffolding habit, NOT a Studio authoring pattern. | Drop the first section directly onto the canvas root slot. Wrap in a container ONLY for explicit layout (e.g. `hstack` for two cards side-by-side). |
| Adding a Repeater for a non-list use case | Repeater iterates a multi-valued field. Single-hero + single-body needs zero iteration | Use Repeater ONLY when the field is genuinely a list (Modular Block list, multi-Group, multi-Reference). For one-of-each: drop directly. |
| Leaving empty "Drop Here" zones at the bottom | Saved compositions render those zones as visible placeholders in screenshots and at runtime in builder mode | Before Save, switch to Layers and delete any orphan empty Box / Slot rows |

## Driving the canvas

Moving a component on the Studio canvas through browser automation has a required event sequence, and the high-level drag helpers do not satisfy it. See [`drive-studio-canvas-ui`](drive-studio-canvas-ui.md) before attempting a drop.

## See also

- Pair with `install-studio` (SDKs) and `setup-template-preview-routes` (host-app **catch-all route** mounting `<StudioComponent />`, one route handles every URL).
