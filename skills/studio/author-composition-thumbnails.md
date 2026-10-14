---
name: author-composition-thumbnails
---

## When to use

Section thumbnails are set by the UI and never by the API. What that means when authoring headlessly, and how to supply one yourself.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

<a id="section-thumbnails-ui-preview"></a>

## Section thumbnails: (the UI sets it for you. The API never does)

**Symptom:** every API-authored Section shows a blank/placeholder tile in Studio's **Sections** accordion, while UI-authored ones show a picture of the section. Nothing errors.

**Why.** Studio's Sections accordion renders `section.ui_preview.url` (`ui_preview` is a `file` field holding an asset). When an author saves a Section **in the Studio UI**, the app screenshots the canvas node, converts the base64 to a blob, uploads it as an asset, and PUTs `{ entry: { ui_preview: <assetUid> } }` on the composition entry, fire-and-forget, master locale, then invalidates the sections query so the tile appears without a reload. **That whole chain lives in the editor.** A composition entry created by CMA has `ui_preview` empty forever.

Same asymmetry family as `linked_sections`: the UI populates a field behind the scenes, so API authoring must do it explicitly.

### Fix A: zero-script backfill (best when the sections already exist)

Open each Section in Studio and hit **Save**, no edits needed. The screenshot/upload/PUT chain runs on save and backfills `ui_preview` with a real render of the section. Cheapest correct fix, and the thumbnail is an actual screenshot rather than a placeholder. Only worth scripting instead when the section count makes clicking impractical.

### Fix B: pick an image in the Edit Section modal (no canvas render, no script)

Studio's **Edit Section** modal has a preview-image field: open it, **Choose** an existing asset or **Upload** one, Save. That writes `ui_preview` on the entry directly (`useEditSectionComposition`, then `handleImageSelect`, then `handleSubmit`), with no screenshot and no CMA scripting.

Use this when Fix A isn't practical: the section can't render standalone (needs page context), the canvas is slow to load, or you want a designed thumbnail rather than a screenshot of the live section. Trade-off: the image is whatever you pick, so it drifts from the section's real appearance as the section changes. Fix A stays the better default when the section renders cleanly.

### Fix C: set it from the API

Three calls per section. `ui_preview` takes an **asset uid string** on write. It reads back as an asset object with `.url`.

```bash
# 1. Upload the thumbnail asset
curl -X POST "https://<cma-host>/v3/assets" \
  -H "api_key: <stack-api-key>" -H "$CS_AUTH" \
  -F "asset[upload]=@hero-section.png" \
  -F "asset[title]=Hero Section Preview"
# → { "asset": { "uid": "blt<assetUid>", ... } }

# 2. Point the composition entry at it (master locale — compositions are master-only)
curl -X PUT "https://<cma-host>/v3/content_types/<compositions-CT>/entries/<section-entry-uid>" \
  -H "api_key: <stack-api-key>" -H "$CS_AUTH" \
  -H "Content-Type: application/json" \
  -d '{"entry": {"ui_preview": "blt<assetUid>"}}'

# 3. Publish BOTH the asset and the entry to the environment the project targets
```

**Publish the asset too.** An unpublished asset gives the accordion a uid that resolves to nothing, a blank tile again, indistinguishable from never having set the field.

**Precondition:** the compositions CT must carry the `ui_preview` file field. If it's missing, the CMA silently drops the key on write: 201/200 returned, field reads back absent. See [`provision-studio-project`](provision-studio-project.md).

**What to use as the image.** A real screenshot of the rendered section is what the UI produces and what authors expect. A generated placeholder (labeled color block) is acceptable as a stopgap and still beats a blank tile, but say so rather than presenting it as a preview.

### MANDATORY: a section without `ui_preview` is not finished

This is not a follow-up task or a nice-to-have. **Attaching the thumbnail is part of creating the section**, in the same run, before you report the section as built.

- Write the composition, **immediately** attach `ui_preview`, and only then report success.
- Creating five sections means five thumbnails. Batch the write and the thumbnail together per section, or run a backfill over every section lacking one at the end of the batch. Never move on to the next page while any section you created is blank.
- **Never report "section created" for a section whose `ui_preview` is unset.** Say "created, thumbnail pending" and then finish it.
- If the thumbnail step errors, that is a failure to **report and retry**, not to skip silently. Cosmetic means "does not corrupt data". It does not mean optional.

The symmetric rule for components is `thumbnailUrl` on every `registerComponent` call (see [`register-component`](register-component.md)). Both are rows in [`complete-the-build`](complete-the-build.md), the handover gate. Between the two, **nothing in the Components panel is ever a blank tile**: sections carry `ui_preview`, components carry `thumbnailUrl`.

**How this gets missed in practice** (observed, twice): a build script writes the compositions and the thumbnail is left to a separate command that then does not get run. The sections look finished in every check except the one an author actually sees. Put the thumbnail call inside the build script.

### Fix D: generate one from the composition's own `ui` (scripted, no canvas, no clicking)

No script for this ships with the pack. Write one in the project (or inline in the build script) that, per section:

1. Reads the composition entry over the CMA and decodes its `ui` (`zlib:` + base64).
2. Renders a schematic: containers in their real direction and gap, the outermost repeater as three items, media as a framed block, static text as text.
3. Screenshots it at 1440×810 (Playwright or similar).
4. Uploads the PNG as an asset titled `<Title> Preview` and PUTs its uid into `ui_preview`.

Give it an entry-uid mode, a "backfill every section lacking `ui_preview`" mode, and a dry-run mode that renders without uploading. Use it when Fix A is impractical at scale: one live project had **50 of 79 sections** blank, backfilled in a single run.

It sits between Fix B and Fix C: no hand-picked image, no per-section curl, and the result tracks the section's real structure. It is still a schematic, not a render. For a true screenshot of a bound section, Fix A remains better.

**Why not script the canvas screenshot instead.** A section canvas has no preview entry selected (`PREVIEW ENTRY: No preview entry`), so every bound prop renders its registration default. Measured across 11 captures: **0 to 1.2% ink coverage**, content confined to the top 8% of the frame. Uploading those fills the accordion with near-identical "Your headline here" tiles, worse than a blank tile, because they stop reading as empty, and once `ui_preview` is set every capture-when-missing trigger skips that section forever.

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Posting `ui` as `{ slots: … }` | The `ui` field IS the root node, not a wrapper around one. Without its own `uid` and `type: "page"` the create fails `422 The root node of a composition must have type "page", got "undefined"`, and the message reads like a child-node problem, so the fix gets applied one level too deep | Give `ui` a `uid` and `type: "page"`, put the tree under its `slots`, and point `props.children` at the slot id |
| Reading `static_value` as a map when generating the image | Buckets are arrays of `{key, value, _metadata}` rows, so `sv[type][key]` is always `undefined` and every label silently renders as a placeholder bar | Flatten rows to `key → value` first. `choice` values arrive as single-element arrays |
| Drawing every repeater as three items | A nested repeater iterates a field within one item (a logo, a tag). Three-by-three turns one slide into a nine-column grid | Only the outermost repeater repeats. Nested ones render one item |
| Auditing `ui_preview` coverage over the delivery API | The published list is short: one project read 86 compositions on the CDA vs **122** on the CMA, hiding 36 unpublished sections that were also blank | Audit over the CMA, never the CDA |
| Assuming an unpublished thumbnail always shows blank | Measured otherwise: the accordion loaded unpublished preview assets fine (1440×810, `naturalWidth > 0`), Studio's own save-path upload never publishes either | Publishing still matters for anything reading `ui_preview.url` through the **delivery** API. Verify in the accordion rather than assuming either way |
