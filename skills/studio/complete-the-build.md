---
name: complete-the-build
---

## When to use

The definition of done for any Studio build. Ten deliverables that decide whether the thing you built is usable by a marketer rather than merely rendering. Every one of them is silent when missing: nothing errors, the page still loads, and the gap only surfaces when a non-developer opens Studio and can't find, recognize, or edit anything.

Phrases: "is this finished", "anything missed", "why is the palette all blank tiles", "why can't I click the text to edit it", "no thumbnail on my sections", "Visual Builder does nothing", "ready to hand over". Also run it **unprompted** at the end of any build (component registration, Section, Template, page migration) and cite it in the plan up front so the user knows these are coming.

Do NOT use for: debugging a component that renders wrong (`troubleshoot-data-binding`), a canvas that won't load (`troubleshoot-canvas`), or first-time install (`install-studio`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Complete the build: the ten things that are never optional

For setup-only work, use `convert-project-to-studio` and `verify-setup` for completion. Registration, thumbnails, section structure, and publishing below apply only to authored components/compositions. Do not expand an enablement request into authoring to satisfy this checklist. HTTP reachability alone does not establish that the editor renders or live edits work.

Architecture is half the job. A perfectly decomposed set of Sections with no thumbnails, no CSLP tags and Live Preview switched off is a **developer's** artifact: it renders, and nobody else can use it. These ten close that gap, the eighth from the other direction: a template that ships every one of the others and still has no Sections at all.

Each is owned by exactly one skill. This file is the checklist and the gate: read the owner for the how.

| # | Deliverable | Applies to | Owner skill | Failure when missing |
|---|---|---|---|---|
| 1 | `cslp: { appendTags: true }` in SDK init | once per project | [`install-live-preview`](install-live-preview.md) | Both tag bags arrive empty everywhere at once, no component fix helps |
| 2 | `studioAttributes` spread on the root **and** `wrap: false` in the register entry, plus `$prop` twins on bound elements | **every** registered component | [`register-component-cslp`](register-component-cslp.md) § The `studioAttributes` contract | Element renders but Visual Editor can't select or inline-edit it. `wrap: false` without the spread is worse: the node is unselectable entirely |
| 3 | `thumbnailUrl` data URI | **every** `registerComponent` call | [`register-component`](register-component.md) | Palette renders a text placeholder. A 20-component palette is an unbrowsable text wall |
| 4 | `ui_preview` asset | **every** Section composition | [`author-composition-thumbnails`](author-composition-thumbnails.md) § Section thumbnails | Blank tile in the Sections accordion, authors can't tell sections apart. The CMA never populates it: a scripted build leaves every Section blank and nothing errors |
| 5 | Live Preview enabled on the stack + preview token | once per project | [`enable-visual-experience`](enable-visual-experience.md) | Canvas blank / edits never reflect. Looks like a broken install |
| 6 | The `/canvas` route mounted | once per project | [`setup-section-preview`](setup-section-preview.md) | `MISSING_CANVAS_URL`. Nothing can be authored at all |
| 7 | **Published** to the environment the project targets | **every** Section and Template, and again after every tree edit | [`author-composition-via-api`](author-composition-via-api.md) | Delivery serves the previous version, or nothing. The CMA looks perfect and the canvas resolves the composition |
| 8 | **The template is composed of Sections**, not one component bound to the page body | **every** Template | [`build-connected-template`](build-connected-template.md) § Post-build structural check | Nothing. The page renders correctly, matches production and passes every other check here: it simply has no Sections, no Section Slots and no reuse, and an author cannot rearrange it. The only way to see it is to count `section-composition` nodes |
| 9 | Live Preview `mode: "builder"` (with `editInVisualBuilderButton: { enable: false }`) | once per project | [`install-studio`](install-studio.md) | Visual Editor opens on "Initializing the editor…" and nothing is clickable. Nothing errors |
| 10 | A **new** entry is editable on the page: `fetchTemplateEntry` completes it, lists carry `<field>` and `<field>.<N>` tags | **every** Template | [`make-visual-editor-editable`](make-visual-editor-editable.md) | A new entry shows "Your text here", its empty fields and image can't be clicked, and list items can't be added, moved or deleted |

**Why this matters.** Every failure above is silent and asymmetric: the developer's own loop (SSR renders, unit tests, a page in the browser) passes in all six cases, because none of them affect rendering. They only affect the editor, which is the audience the entire exercise exists for. That asymmetry is why these get skipped, and why they need a gate rather than good intentions.

## The two thumbnail systems are not the same thing

They are constantly conflated, and fixing one does nothing for the other.

| | Components (#3) | Sections (#4) |
|---|---|---|
| Field | `thumbnailUrl` in the `registerComponent` call | `ui_preview` on the composition entry |
| Lives in | your code | the CMA (a `file` field pointing to an asset) |
| Made by | you, as an inline SVG data URI | Studio's editor on Save, or set by API |
| Shows up in | the palette's Registered Components | the palette's Sections accordion |

Between the two, **nothing in the Components panel is ever a blank tile.** That is the acceptance bar, not "most tiles have pictures".

### Unpublished is the hardest of the runtime seven to see

(Deliverable 8 is invisible in a different way: it never misrenders at all. Only a node count finds it.)

Every other row fails visibly once you look. This one hides behind a completely healthy CMA:

- the composition exists, is bound, and carries its `ui_preview`
- the canvas **resolves the right composition** and reports the right `url`
- delivery serves the previous published version, or nothing at all

So the page renders the **old** tree while every check you'd naturally run says the new one is correct. Measured: seven freshly rebuilt sections, all `publish_details: (NONE)`, cost four dev-server restarts, a URL swap and a `url_metadata` change before anyone checked publish state, because the symptom (old components rendering) points at the template, not at the sections it links.

**Rebuilding a tree creates an unpublished version on a published composition.** Editing is not shipping. Publish after every write, and after every edit. See [`author-composition-via-api`](author-composition-via-api.md).

## Verification block: run this, don't assert it

```bash
# 3 — every registration has a thumbnail (counts must be equal)
grep -c "registerComponent" <registration-file>
grep -c "thumbnailUrl"      <registration-file>

# 2 — both halves, counted separately; all three numbers should agree
grep -c  "registerComponent" <registration-file>
grep -c  "wrap: false"       <registration-file>
grep -rl "studioAttributes"  <components-dir> | wc -l

# 1 — appendTags actually on
grep -rn "appendTags" <init-file>

# 9 — builder mode and the completer
grep -rn 'mode: "builder"\|fetchTemplateEntry' <init-file>

# 10 — on a NEW entry's page: one <field> tag and a <field>.<N> tag per item, for every list
curl -s "<new entry URL>" | grep -o 'data-cslp="[^"]*"' | sort -u
```

```bash
# 4 — sections missing ui_preview, over the CMA (never the CDA — it hides unpublished sections)
#
# ⛔ The discriminator is `place_composition_as` ("section" | "page"), NOT a `type` field.
#    Filtering on `type` matches nothing and reports a clean run having inspected zero
#    sections — a false pass, measured on a live project holding 94.
# ⛔ `limit` is capped at 100 server-side. Page with `skip`, or you audit the first 100 only.
# requires:
#   CMA_HOST   your region's CMA host, e.g. api.contentstack.io
#   API_KEY    the stack api_key (the CMA scope header)
#   CS_AUTH    one auth header resolved per authenticate-cma, e.g. "authorization: Bearer $CS_OAUTH_ACCESS_TOKEN"
#   COMP_CT    the compositions content type uid (the Studio project's contentTypeUid)
skip=0; all='[]'
while :; do
  page=$(curl -s -H "api_key: $API_KEY" -H "$CS_AUTH" \
    "https://$CMA_HOST/v3/content_types/$COMP_CT/entries?limit=100&skip=$skip&include_count=true")
  count=$(jq '.count' <<<"$page")
  all=$(jq -n --argjson a "$all" --argjson b "$(jq '.entries' <<<"$page")" '$a + $b')
  skip=$((skip + 100)); [ "$skip" -ge "$count" ] && break
done
echo "$all" | COUNT="$count" python3 -c "import os,sys,json; e=json.load(sys.stdin); \
sec=[x for x in e if x.get('place_composition_as')=='section']; \
blank=[x['title'] for x in sec if not x.get('ui_preview')]; \
unpub=[x['title'] for x in sec if not (x.get('publish_details') or [])]; \
print(f'read {len(e)} of {os.environ[\"COUNT\"]} | {len(sec)} sections | {len(blank)} blank | {len(unpub)} UNPUBLISHED'); \
print('blank:', *blank[:20], sep='\n  '); \
print('unpublished:', *unpub[:20], sep='\n  ')"
```

**Assert the field exists before trusting a pass.** If the compositions CT has no `ui_preview` field, the CMA **silently drops the key on write**, every section reads back blank while every write returns `200`:

```bash
curl -s -H "api_key: $API_KEY" -H "$CS_AUTH" \
  "https://$CMA_HOST/v3/content_types/$COMP_CT" \
| python3 -c "import sys,json; f=[x['uid'] for x in json.load(sys.stdin)['content_type']['schema']]; \
print('ui_preview field:', 'present' if 'ui_preview' in f else 'MISSING - writes will no-op')"
```

**#2 is only verified in the DOM.** Open a page in Studio, inspect a rendered atom: its **root** element must carry `data-cslp`, and each bound text/image element must carry its own. With `wrap: false` that root is the component's own element: if you still see an SDK wrapper `<div>` around it, the entry is missing `wrap: false`. If the root carries no attributes at all, the component is missing the spread. A tagged root with bare fields means the `$`-twins were dropped, Visual Editor then looks like it "half works". A real audit of 19 atomic components found **0** spreading `studioAttributes`, nothing anywhere reported it.

**#4 must be re-read, not assumed.** A `200` on the PUT is not proof: if the compositions CT lacks the `ui_preview` field the CMA silently drops the key. Re-read the entry and confirm `.entry.ui_preview.url` resolves.

## Where this runs in the build

Not a final sweep. Items 1, 5 and 6 are **preflight**. They gate everything after them. Items 2, 3 and 4 are **per-piece**, done as each piece is created, never batched to the end:

```
preflight  : 1 appendTags · 5 Live Preview + token · 6 /canvas route · 9 builder mode
per component : 2 CSLP tags · 3 thumbnailUrl   ← at registration time, same commit
per section   : 4 ui_preview                   ← immediately after the composition write
handover      : re-run the verification block; report counts, not adjectives
```

**Batching to the end is how it gets skipped.** A build script that writes 40 sections and leaves thumbnails "for a follow-up command" produces 40 blank tiles, because the follow-up never runs. One live project ended up with **50 of 79 sections** blank exactly this way.

## Saying it in the plan: plain language for a non-technical approver

These belong in the plan's Layer 1 summary, in this vocabulary, never by their field names:

| Deliverable | How to say it |
|---|---|
| 2 + 5 + 9 + 10 | you can click any text or image on a preview of the real page and change it right there, add, move and remove list items, and edit a brand-new page the same way |
| 3 | each of your building blocks shows a picture of itself, so you can tell them apart when adding one |
| 4 | each reusable block shows a picture of itself in the block list |
| 1, 6 | (don't mention: plumbing, no user-visible promise) |

Print them under a heading like **"What you'll be able to do yourself"**: the approver is deciding whether this is worth doing, and "editable in place, on the real page" is the whole answer.

## Acceptance

- [ ] All six rows verified by the commands above (or the DOM check for #2), and the **counts printed**, never "thumbnails added" without the number.
- [ ] `registerComponent` count **equals** `thumbnailUrl` count in every registration file.
- [ ] Zero Section compositions with an empty `ui_preview`, audited over the **CMA**, including sections created as a side effect (clones, rescopes, batch builds). The audit filtered on **`place_composition_as`**, paged past `limit=100`, and printed how many entries it actually inspected: `0 sections` is a broken audit, not a clean one.
- [ ] A rendered atom's root shows `data-cslp` in the DOM **and** its bound fields show their own.
- [ ] **Every Section and Template is published to the environment the Studio project targets**, verified by a non-empty `publish_details`, not by the write returning `200`. Re-published after every tree edit.
- [ ] Nothing was reported as done while any row was outstanding. The honest phrasing is "created, thumbnail pending", then finish it.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Editing a composition's tree and not republishing | The edit creates an unpublished version, delivery keeps serving the old one. The CMA, the canvas and the resolved `url` all look right, so the investigation goes to the template instead of the sections | Publish after every write **and** every edit, assert `publish_details` is non-empty |
| Treating these as polish to do later | All six are invisible to the developer loop, so "later" never arrives: the user discovers them when they open Studio and can't work | Preflight items gate the build, per-piece items ship in the same step that creates the piece |
| Filtering compositions on a `type` field | There is no such field: the discriminator is `place_composition_as`. The audit matches nothing and reports success having inspected **zero** sections. Measured on a live project holding 94 | Filter on `place_composition_as == "section"` and print the inspected count, so an empty match is visible |
| Trusting a single page of results | `limit` is capped at 100 server-side, so a project with 141 compositions silently audits the first 100 | Page with `skip` until `count` is reached |
| Auditing `ui_preview` over the delivery API | The published list is short: one project read 86 compositions on the CDA vs **122** on the CMA, hiding 36 blank sections | Audit over the CMA |
| Fixing `thumbnailUrl` and calling section thumbnails done (or vice versa) | Two unrelated systems, two different panels | See § The two thumbnail systems |
| `thumbnailUrl` pointing at a CDN / asset / `/public` URL | The palette renders inside Studio's iframe. External requests fail silently, which leaves a blank or broken tile, identical to no thumbnail | Inline SVG data URI |
| Auditing components one by one when tags are missing everywhere | Almost always `cslp.appendTags` off (#1), not a component bug | Check the SDK config first |
| Screenshotting a Section's own canvas to fill `ui_preview` | A section canvas has no preview entry, so every bound prop renders its default, measured 0 to 1.2% ink coverage. Near-identical "Your headline here" tiles are worse than blank, because they stop reading as empty and every capture-when-missing pass then skips that section forever | Re-save in the editor (real render), pick an image in the Edit Section modal, or generate a schematic from the composition's own `ui`, [`author-composition-thumbnails`](author-composition-thumbnails.md) § Fix D |

## See also

- [`plan-studio-architecture`](plan-studio-architecture.md): prints these six in the plan up front, so the user approves a build that includes them
- [`byoc-end-to-end`](byoc-end-to-end.md): the execution macro, this checklist is its Phase 6 gate
- [`authenticate-cma`](authenticate-cma.md): how the audits above authenticate, OAuth-first, no pasted session token
- [`verify-setup`](verify-setup.md): proves the installation works, this proves the build is usable
- [`verify-visual-parity`](verify-visual-parity.md): proves it matches the design
