---
name: provision-studio-stack
description: "Seed a stack with page CTs, global fields, entries, and assets — the prerequisites a Studio project needs OUTSIDE the compositions CT. Covers asset upload + dedupe + publish."
allowed-tools: Read Grep Glob
---

## When to use

Seed a stack with page CTs, global fields, entries, and assets — the prerequisites a Studio project needs OUTSIDE the compositions CT. Covers asset upload + dedupe + publish.

Use when standing up a brand-new stack headlessly that a Studio project will consume (templates connect to these CTs, entries provide preview data, assets back image / file fields). Signals — "seed the stack", "create CTs + entries via API", "upload assets". Do NOT use for the compositions CT (`provision-studio-project`) or composition entries (`author-composition-via-api`).

# Provision Studio Stack (CTs, entries, assets)

## Context

A Studio project references content that lives in the stack — page CTs (e.g. `blog_post`, `product`), global fields they reuse, entries that satisfy URL patterns, and assets bound to file fields. [`provision-studio-project`](../provision-studio-project/SKILL.md) handles the stack-wide setup (Live Preview, environment, delivery + preview tokens) and creates the compositions CT. This skill handles everything else: the **content types the compositions connect to**, the **entries** that preview them, and the **assets** that fill their file fields.

All operations are CMA-only (`api.contentstack.io` and regional variants). Auth = `api_key` + `authtoken` headers.

> **MCP-authed path (optional).** If `CONTENTSTACK_MCP_READY` (from [`install-contentstack-mcp`](../install-contentstack-mcp/SKILL.md)), **most** CMA steps run as MCP tool calls — no pasted `authtoken`: global fields → `create_a_global_field` / `update_a_global_field`; page CTs → `create_a_content_type` / `update_content_type`; asset **dedupe** → `get_all_assets`, asset **publish** → `publish_an_asset`; entries → `create_an_entry` / `update_an_entry` (idempotent PUT branch) / `publish_an_entry`. **Two steps stay raw HTTP even with the MCP:** (1) the asset **binary upload** (Step 4, `POST /v3/assets` multipart — there is NO create/upload-asset MCP tool, only get/publish/update/delete); (2) the Step 7 **CDA verify** (a delivery-host read — `get_single_entry` is a CMA read and can't confirm publish state or file-field asset-URL resolution; `cda` isn't in the default `GROUPS` either). Supply the stack `api_key` upfront (the MCP can't discover it). No flag → raw curl throughout.

## Task

1. **Prerequisites.** Stack exists with delivery + preview tokens; the compositions CT has been created via [`provision-studio-project`](../provision-studio-project/SKILL.md). You have `CS_AUTH_TOKEN`, `CS_API_KEY`, the target environment name, and the region's CMA host.

2. **Create / update global fields first.** Page CTs that reference global fields (e.g. `gf_hero`, `gf_card_list`) must have those GFs in place at CT create time — Contentstack rejects CT POSTs that reference an unknown global field uid.

   ```
   POST /v3/global_fields    (idempotent — check first via GET /v3/global_fields/<uid>)
   { "global_field": { "title": "...", "uid": "<uid>", "schema": [ ... ] } }
   ```

   Use `PUT /v3/global_fields/<uid>` to update an existing one. Same auth headers.

3. **Create page content types.** For each page CT (`blog_post`, `product`, `case_study`, etc.):

   ```
   POST /v3/content_types
   { "content_type": {
       "title": "Blog Post",
       "uid":   "blog_post",
       "schema": [ /* field definitions */ ],
       "options": {
         "is_page": true,                     // makes it a page CT (URL-aware)
         "url_pattern": "/blog/:title",       // optional — drives content_type_url_pattern URL source
         "singleton": false
       }
   } }
   ```

   Idempotency: check `GET /v3/content_types/<uid>` first; PUT on exists, POST otherwise.

   **Every CT MUST include a `source_uid` field for downstream chain compatibility.** This is a contract — [`import-content`](../import-content/SKILL.md) uses `source_uid` as its idempotency key when re-running imports. Skip it and the import silently creates duplicates on every re-run.

   ```json
   {
     "display_name": "Source UID",
     "uid":          "source_uid",
     "data_type":    "text",
     "field_metadata": { "description": "Idempotency key for imports from external sources", "default_value": "", "multiline": false, "version": 3 },
     "mandatory":    false,
     "unique":       false,
     "multiple":     false,
     "indexed":      true
   }
   ```

   **Important:** field UIDs MUST NOT start with an underscore — Contentstack rejects CT creation with error 115 (`The UID must begin with a letter, and can contain only lowercase letters, numbers, or underscores.`). Use `source_uid`, NOT `_source_uid`.

   **Page CT vs non-page CT.** Set `options.is_page: true` ONLY if entries of this CT should be addressable by URL (Connected Templates resolve against these). Non-page CTs (e.g. `author`, `testimonial`) are referenced from page entries but don't get their own URL.

4. **Upload assets.** Each file referenced by an entry must exist as a stack asset first. Use multipart upload to `POST /v3/assets`:

   ```
   POST /v3/assets    (multipart/form-data)
   Fields:
     asset[upload]    = <file stream>           (required)
     asset[title]     = <human-readable name>
     asset[parent_uid] = <folder uid>           (optional — omit for stack root)
     asset[tags]      = <comma-separated tags>  (optional)
   ```

   Response: `data.asset.{uid, url, content_type, file_size, ...}`.

   **Dedupe before upload.** A naive seed re-uploads the same image on every run, leaving orphans. Before posting, list existing assets and match by title (or by SHA-256 of bytes for true dedupe):

   ```
   GET /v3/assets?query={"title":"<name>","parent_uid":"<folder>"}&limit=1
   ```

   If a match exists, reuse `data.assets[0].uid`. Cache the mapping locally (e.g. `.asset-map.json` keyed by source filename → asset uid) so cross-runs are idempotent.

   **Publish each asset** to the target environment before publishing entries that reference it — unpublished assets surface as broken images in canvas and on the live site:

   ```
   POST /v3/assets/<uid>/publish
   { "asset": { "locales": ["en-us"], "environments": ["<env name>"] } }
   ```

5. **Create entries.** For each entry payload:

   - **Resolve asset references** before POSTing. File-field shape on CMA entries:
     - Single-file field: `"featured_image": "<asset_uid>"` (string)
     - Multiple-file field: `"images": ["<uid1>", "<uid2>"]` (array of strings)

     The CDA later resolves these to full asset objects (`{ uid, url, filename, ... }`) — but on the WRITE side (CMA), pass uids.

   - **Resolve cross-entry references** by uid. Reference fields hold arrays of `{ uid: "<entry_uid>", _content_type_uid: "<ref_ct>" }` objects (a common pattern is a seed-uid map persisted at `.entry-map.json` to translate stable identifiers to server-assigned uids).

   - **JSON-RTE embeds** carry `attrs.locale` on every embedded entry / asset node. Omitting `attrs.locale` makes the embed render blank — Studio's RTE renderer matches embed locale to the page locale (P6).

   - **Idempotency.** Find by title (or another stable field) via `GET /v3/content_types/<ct>/entries?query={"title":"..."}&limit=1`. PUT on exists, POST otherwise.

   ```
   POST /v3/content_types/<ct>/entries
   { "entry": { "title": "...", /* all schema fields */ } }
   ```

6. **Publish each entry** to the target environment. Unpublished entries return 404 from the CDA — Connected Template canvas shows blank. Connected Template URL resolution also relies on the published entry existing for the connected CT (see [`build-connected-template`](../build-connected-template/SKILL.md) step 1).

   ```
   POST /v3/content_types/<ct>/entries/<entry_uid>/publish
   { "entry": { "locales": ["en-us"], "environments": ["<env>"] } }
   ```

7. **Verify.** For each seeded entry: `GET https://<cdn-host>/v3/content_types/<ct>/entries/<uid>?environment=<env>` returns 200 with all file-field references resolved to asset URLs.

## Acceptance

- [ ] All required global fields exist (`GET /v3/global_fields/<uid>` → 200).
- [ ] All required page CTs exist with the expected schema; `options.is_page` set correctly per CT.
- [ ] Every CT includes a `source_uid` (text, non-mandatory, indexed) field so downstream `import-content` runs are idempotent. Field UID must NOT begin with `_`.
- [ ] Asset dedupe map (`.asset-map.json` or equivalent) persists across runs — re-running provision does NOT upload duplicates.
- [ ] Each asset is published to the target environment (`GET /v3/assets/<uid>` shows `publish_details` entry for the env).
- [ ] Each entry's file fields hold asset uid(s), not URLs or filenames.
- [ ] Each entry's reference fields hold `{ uid, _content_type_uid }` objects, with uids resolved from the seed-uid map.
- [ ] Each entry is published; CDA `GET /v3/content_types/<ct>/entries/<uid>?environment=<env>` returns 200.
- [ ] JSON-RTE embeds carry `attrs.locale` matching the entry's locale.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Creating a CT that references a GF before the GF exists | CMA rejects POST `/v3/content_types` with "global field not found" | Create / update all global fields BEFORE page CTs |
| Re-uploading the same asset every provision run | Stack accumulates duplicate assets; entry references go stale on re-create | Dedupe via `GET /v3/assets?query={"title":"…"}` + persist `.asset-map.json` |
| File-field value set to the asset URL or filename instead of uid | CMA accepts the POST but the field reads as broken in CDA | Pass `<asset_uid>` (string) for single-file, `[<uid>, ...]` for multi-file |
| Forgetting `_content_type_uid` on reference field entries | CDA can't resolve the reference; field reads as empty | Each reference entry is `{ uid, _content_type_uid }` |
| JSON-RTE embed missing `attrs.locale` | Embed renders as a placeholder / blank | Set `attrs.locale` on every embedded entry / asset node (matches entry locale) |
| Asset published, entry referencing it NOT published | Entry 404s on CDA; canvas blank | Publish entries AFTER assets, BEFORE testing canvas |
| Entry published, asset NOT published | Image fields surface broken URLs on the live site | Publish assets first |
| `options.is_page: true` set on a non-URL CT (e.g. `author`) | Studio surfaces the CT in URL-resolution probes; spurious template matches | Set `is_page` only on URL-addressable CTs |
| Seed-uid map (`.entry-map.json`) deleted between runs | Cross-entry references break on subsequent runs (seed-uids no longer translate to server-uids) | Commit the map OR rebuild it from `GET /entries?query={"title":"..."}` lookups |
| Wrong region CMA host | 401 / 404 on every call | Use region-specific host (`eu-api.contentstack.com`, `azure-na-api.contentstack.com`, etc.) |

## See also

- [`provision-studio-project`](../provision-studio-project/SKILL.md) — stack-wide setup, compositions CT, Studio project registration.
- [`author-composition-via-api`](../author-composition-via-api/SKILL.md) — composition entries that bind to the CTs created here.
- [`build-connected-template`](../build-connected-template/SKILL.md) — Template authoring against these page CTs.
- `reference_studio_provisioning_api` — host map and auth headers.
