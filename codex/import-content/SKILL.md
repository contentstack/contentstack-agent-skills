# import-content


## When to use

Populate Contentstack Content Type entries from a customer-owned source — a JSON API, an internal JSON export, a CSV of records, an existing Contentstack stack, or a folder of Markdown files. Uses the Contentstack Management API (CMA) with idempotency + resumability so re-runs pick up where a failed run left off. Handles asset uploads for images referenced in the source.

Use when Sections + Templates exist but need real content to render. Phrases — "populate entries from CSV", "seed content from JSON", "import content from our API", "ingest content into this CT", "backfill CMS content", "import Markdown blog posts". Do NOT use for schema provisioning (`provision-studio-stack`), fixture / dummy-data seeding (also `provision-studio-stack`), or one-off manual entry authoring (Contentstack UI is faster). **Migration from other CMS platforms (WordPress, Contentful, Sitecore, AEM, etc.) is out of scope** — Contentstack ships a dedicated CLI (`@contentstack/cli-cm-import`) with per-source connectors; use that. This skill covers customer-owned data sources only.

# Import content into Contentstack CTs — idempotent, resumable, asset-aware

> ## Verification status
>
> This skill's mechanics are **runtime-verified end-to-end** against a live Contentstack stack. Reproducers committed under `scripts/verify-import-*.ts`.
>
> - ✅ `@contentstack/json-rte-serializer` (v3.1.0) confirmed real on npm; use this package for HTML→JSON-RTE conversion.
> - ✅ CMA endpoints (`/v3/assets`, `/v3/content_types/<ct>/entries`, `/v3/content_types/<ct>/entries/publish`) match those used by [`provision-studio-stack`](../provision-studio-stack/SKILL.md) and [`author-composition-via-api`](../author-composition-via-api/SKILL.md).
> - ✅ Retry + rate-limit pattern matches `scripts/upload-to-digital-concierge.ts` — production-tested against Contentstack's Digital Concierge API.
> - ✅ **Preview mode (Step 1a) runtime-verified** — the bundled sample JSON parses to exactly 3 posts / 2 unique authors / 2 embedded assets, and `@contentstack/json-rte-serializer` + `jsdom` produce a valid JSON RTE doc (with h2 heading, list, and inline `<img>` preserved) that round-trips back to HTML. Reproduce with `npx ts-node scripts/verify-import-preview.ts`.
> - ✅ **End-to-end run verified against a live stack** — provisions an isolated CT with a `source_uid` field, uploads an asset (`/v3/assets` multipart), POSTs 3 entries with JSON-RTE bodies, re-runs the same import and confirms **0 duplicates created** + same entry UIDs returned, then cleans up. 8/8 structural claims pass. Reproduce with `npx ts-node scripts/verify-import-e2e.ts` (requires `CS_API_KEY` + `CS_AUTH_TOKEN` in `.env`).
> - ✅ **`source_uid` field convention** works as documented. **Important:** the field UID MUST NOT start with an underscore — Contentstack rejects CTs whose field UIDs begin with `_` (error 115 "The UID must begin with a letter"). Use `source_uid`, not `_source_uid`.
>
> Rate limits (~10 uploads/sec, ~15 entries/sec) are documented defaults; tune via `Retry-After` observation on your own plan. If you find a specific claim broken in practice, file a docs issue — the skill converges on the truth via real usage.

## Context

After [`decompose-design`](../decompose-design/SKILL.md) or [`decompose-site`](../decompose-site/SKILL.md) provisions schema and authors Sections + Templates, the CTs are empty. For a fresh brand launch that's fine — marketers author entries manually. For **bulk ingest** (an existing JSON feed, a CSV export from another system, a Markdown blog folder), a scripted import is table stakes.

This skill handles the general case. Sources vary widely; the mechanics are the same: read source → map fields → upload assets → POST entries → track what succeeded → resume on failure.

## Task

### Step 1 — Get the source content from the user

Ask the user *exactly one* of the following, in this priority order:

1. **File path** — "Where's your source file?" (accepts `.json`, `.csv`, or a folder of `.md` files). Preferred — no copy-paste, full fidelity.
2. **Inline content** — "Paste the source content here if it's small." Useful for CSVs of ≤50 rows or a Markdown file. Not for anything with binary assets — you can't paste an image.
3. **API endpoint + auth** — "Which URL should I fetch from, and what auth?" For JSON APIs or an existing Contentstack stack.
4. **Preview mode** — "No file yet? Type `preview` to run the pipeline against a small bundled sample." Uses the fixture at the bottom of this skill to prove the transform + POST + idempotency chain end-to-end before you commit to a real import.

If none of the above is supplied, do NOT infer — ask again explicitly. Silent invention of source data is the single most common failure mode of import scripts. Also collect:

- **Target CT** — the Content Type UID to import into (from the site plan, from `provision-studio-stack`'s output, or explicit from the user).
- **Field mapping** — how source fields map to target CT fields. Propose a mapping from the source's field names; confirm before proceeding. Never mutate without a confirmed mapping.

### Step 1a — Preview mode (dry-run against a bundled sample)

If the user chose `preview`, or explicitly asked "test this on a sample first," use the fixture below **without hitting any real Contentstack stack** and print each transform stage's output so the user sees what a real run would produce. This is the safety valve — verify the transform chain works before pointing it at production data.

**Bundled sample JSON (3 posts, 2 authors, 2 assets):**

```json
{
  "posts": [
    {
      "id": "post-101",
      "title": "Welcome to Studio",
      "slug": "welcome-to-studio",
      "excerpt": "A quick tour of Studio's role in modern content workflows.",
      "body_html": "<h2>Composable content</h2><p>Studio lets marketers build pages from your registered components.</p><ul><li>Engineering registers components.</li><li>Marketers compose without a PR.</li></ul><p><img src=\"https://picsum.photos/id/1/800/400\" alt=\"Composable hero\" /></p>",
      "author": "Alice Kim",
      "published_at": "2026-02-03T12:00:00.000Z",
      "status": "published",
      "tags": ["product-news", "composable"]
    },
    {
      "id": "post-102",
      "title": "Two-step content ingest",
      "slug": "two-step-content-ingest",
      "excerpt": "A hands-on look at bulk-loading content into Contentstack.",
      "body_html": "<h2>Two-step ingest</h2><p>Export from your source, transform, POST to Contentstack.</p><p><img src=\"https://picsum.photos/id/2/800/400\" alt=\"Ingest steps\" /></p>",
      "author": "Bob Rivera",
      "published_at": "2026-02-12T09:00:00.000Z",
      "status": "published",
      "tags": ["how-to"]
    },
    {
      "id": "post-103",
      "title": "Design tokens in Studio",
      "slug": "design-tokens-in-studio",
      "excerpt": "How Studio exposes your design tokens to marketers.",
      "body_html": "<h2>Brand-consistent authoring</h2><p>Design tokens flow from your Tailwind config to Studio's design panel.</p>",
      "author": "Alice Kim",
      "published_at": "2026-02-24T14:00:00.000Z",
      "status": "draft",
      "tags": []
    }
  ]
}
```

**Preview mode output — what to print without touching any stack:**

```
PREVIEW MODE — no writes to Contentstack

Parsed 3 posts, 2 authors, 2 assets from sample JSON.

Field mapping preview (against target CT `blog_post`):
| Source (JSON) | Target field | Sample from post-101 |
|---|---|---|
| title         | title       | "Welcome to Studio" |
| body_html     | body (JSON RTE) | { doc: [{ type: "h2", children: […]}, …] } |
| excerpt       | excerpt     | "A quick tour of Studio's role…" |
| published_at  | publish_date (ISO) | "2026-02-03T12:00:00.000Z" |
| author        | author (ref) | → author "Alice Kim" (created if missing) |
| slug          | url         | "/blog/welcome-to-studio" |
| tags          | tags        | ["product-news", "composable"] |
| id            | source_uid | "post-101" |
| <img src>     | body inline asset | download picsum.photos/id/1 → upload → attach |

Preview asset list (would download + upload, not doing either):
  - https://picsum.photos/id/1/800/400 (referenced by post-101)
  - https://picsum.photos/id/2/800/400 (referenced by post-102)

Preview author resolution:
  - "Alice Kim" — 2 posts (post-101, post-103). Would create author entry if not found.
  - "Bob Rivera" — 1 post (post-102). Would create author entry if not found.

Idempotency preview:
  Second run over the same JSON:
    - post-101 already imported → skip.
    - post-102 already imported → skip.
    - post-103 was a draft; already imported → skip. (Publish state ignored on re-run.)

Ready to run for real? Provide:
  1. Path to your real source file, OR paste the export inline.
  2. Target stack UID + management token (env var CS_MANAGEMENT_TOKEN).
  3. Confirm the field mapping above matches your CT `blog_post` (or say what to change).
```

If the user confirms, proceed to Step 2 with their real file. If the user just wanted to see what the skill *would* do, the preview alone is enough — no writes have happened.

**Real-file workflow:** everything from Step 2 onward runs on the user's actual file. Preview mode reuses every downstream step's logic so what you see in preview is what the real run does — no divergence.

### Step 2 — Emit an import plan

Before any CMA writes, output a plan:

```
IMPORT PLAN
Source: blog-export.json — 342 posts
Target: Contentstack CT `blog_post` on stack `blt3f2a9d7…`

Field mapping:
| Source | Target field | Transform |
|---|---|---|
| title | title | text as-is |
| body_html | body | html → json_rte (see conversion notes) |
| excerpt | excerpt | text as-is |
| featured_image_url | cover_image | download → upload asset → reference |
| slug | url | prepend "/blog/" |
| author | author | look up author entry by name, create if missing |
| tags | tags | flat list; drop taxonomy hierarchy |

Assets: 342 featured images to upload (avg 180 KB, total ~62 MB).

Resumable state file: docs/_import-state/blog_post-import-state.json
```

Wait for user approval before writing to the target stack. **Never write without an explicit go-ahead.**

### Step 3 — Idempotency setup

Every import produces a state file at `docs/_import-state/<ct_uid>-import-state.json`:

```json
{
  "source": "blog-export.json",
  "target_ct": "blog_post",
  "target_stack": "blt3f2a9d7...",
  "started_at": "2026-...",
  "records": {
    "post-42": { "status": "imported", "entry_uid": "blt5a8...", "assets": ["blt6c1..."] },
    "post-43": { "status": "asset-upload-failed", "error": "...", "retried": 2 },
    "post-44": { "status": "pending" }
  }
}
```

Every source record has a stable ID (JSON `id` field, CSV row number, Markdown filename). The state file maps ID → status. On re-run:

- `status: imported` → **skip**.
- `status: pending` → attempt.
- `status: <error>` → retry (up to N times, configurable).

**Idempotency check before every entry POST:** query CMA for an existing entry with the same source-ID stashed in a `source_uid` field (or a per-run configured key). If found, update instead of create. Never create duplicates.

### Step 4 — Asset upload with retry

For every source asset (image, PDF, video):

1. Check state file — already uploaded? Reuse the recorded `asset_uid`.
2. Not uploaded: download from source (if URL) or read from disk, POST to Contentstack CMA `/v3/assets`. Attach a `source_url` metadata field on the asset so re-runs match by that key.
3. Record `asset_uid` in the state file immediately after successful upload — before proceeding to the next asset. Never batch state writes; a crash mid-batch strands assets in an unrecorded state.

Rate limit: CMA `/v3/assets` accepts ~10 uploads/sec. Concurrency of 2-3 is safe; anything higher trips rate-limit-retry loops. Retry-after honoured on 429.

### Step 5 — Entry POST with idempotency

For every source record:

1. Check state file — already imported? **Skip.**
2. Transform source fields per the mapping. Apply source-format-specific converters:
   - **HTML** (from any source that stores rich content as HTML strings) → JSON RTE via [`@contentstack/json-rte-serializer`](https://www.npmjs.com/package/@contentstack/json-rte-serializer) (v3.1.0 as of writing). Contentstack also ships a CLI plugin — [`@contentstack/cli-cm-migrate-rte`](https://www.npmjs.com/package/@contentstack/cli-cm-migrate-rte) — for bulk HTML→JSON-RTE migration on existing entries. Preserve heading levels, links, embedded images.
   - **CSV** — text fields as-is; boolean coercion for known columns; date parsing.
   - **Markdown** — parse via `remark` → JSON RTE. Preserve frontmatter as top-level fields.
3. Resolve references. `author` string → look up existing `author` entry by name; if not found and the plan allows, POST a new one and stash its UID.
4. Substitute asset UIDs from Step 4 into image-referencing fields.
5. POST to CMA `/v3/content_types/<ct_uid>/entries`. Include `source_uid` in the entry payload for idempotency.
6. Record `entry_uid` in state file. Rate-limit: 15 entries/sec safe; concurrency 2-3.

### Step 6 — Publish

By default, imported entries are drafts. To go live:

- Batch-publish all imported entries via CMA `/v3/content_types/<ct>/entries/publish` with the entry UIDs from the state file.
- Publish to the target environments (typically `preview` first, then `production` after human review).

Ask before publishing to production — the confirmation step catches wrong-target-CT bugs before they hit customers.

### Step 7 — Emit a report

At the end (or on cancel), print:

```
IMPORT COMPLETE
Source: blog-export.json — 342 records
Target: blog_post on blt3f2a9d7...
  ✓ 338 imported (335 new, 3 updated from prior runs)
  ✗ 4 failed:
    - post-87: asset download 404 (source URL broken)
    - post-134: json_rte conversion failed (malformed HTML)
    - post-201: reference to unknown author "Guest Contributor"
    - post-289: exceeded content-length limit

  → Failures preserved in docs/_import-state/blog_post-import-state.json.
  → Re-run this skill to retry only failed records.
```

## Inputs needed from the user

1. **Source** — exactly one of:
   - **File path** (`.json`, `.csv`, or a folder of `.md`). **Preferred** — no copy-paste, full fidelity, handles binary refs.
   - **Inline content pasted into chat** — for small imports (≤50 rows CSV, one Markdown file). Cannot handle binary assets — you can't paste an image.
   - **API endpoint + auth** — for JSON APIs or an existing Contentstack stack (URL + bearer token / API key).
   - **`preview` mode** — no file yet; run against the bundled sample JSON to verify the transform + POST + idempotency chain works before you commit to a real import.
2. Target CT UID + target stack management token (from env or explicit).
3. Field mapping (skill proposes from the source; user confirms before any CMA write).
4. Any transformation rules the source needs (e.g. `strip HTML → keep only text`, `only import posts published after 2020-01-01`).
5. Whether to publish immediately or leave as drafts. Publishing to production requires an explicit confirm.

**If none of the source options in #1 is supplied, ask again explicitly. Do NOT invent a source or silently proceed.** Silent invention of source content is the single most common failure mode of import scripts.

## Acceptance

- [ ] Source was supplied by the user (file path / inline content / API endpoint / `preview` mode). Skill did NOT invent a source silently.
- [ ] If `preview` mode: no CMA writes happened; skill printed the parsed sample + proposed field mapping + asset list + idempotency preview. Verified before continuing to real data.
- [ ] An import plan is emitted + approved before any CMA writes.
- [ ] State file exists under `docs/_import-state/<ct_uid>-import-state.json` and is updated **before** each record's next step (asset then entry then publish).
- [ ] Every source record ends in one of four states: `imported`, `updated`, `skipped-existing`, `failed-with-reason`. No records disappear.
- [ ] Re-running the skill with the same inputs is idempotent: no duplicates created, no already-imported records touched, only pending / failed records attempted.
- [ ] Rate-limit retries honour `Retry-After` headers.
- [ ] Publishing to production requires an explicit confirmation prompt.
- [ ] Final report accounts for every source record.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| No state file, no idempotency | A crash halfway through 500 entries creates 250 real entries + 250 orphans. Re-run creates 500 duplicates. | State file mandatory. Update after every step, not at end. |
| Batching state writes | Crash between batches strands writes in unrecorded state. | Serial state writes, one per record. Concurrency in CMA calls, not in state persistence. |
| HTML → JSON RTE via naive string parsing | Loses formatting, breaks embedded images, mangles nested lists | Use `@contentstack/json-rte-serializer`. Never write your own. |
| Not attaching `source_uid` to imported entries | Second run can't detect duplicates → creates copies | Every CT that receives imports must have a `source_uid` (single-line text) field. Add it to the CT during `provision-studio-stack` if it isn't already. |
| Skipping the "publish to production" confirmation | Draft entries silently land on the live site on the wrong environment | Explicit prompt required before ProdPublish. |
| Ignoring rate limits | CMA 429s → auto-retry storm → longer 429 → cascading failure | Concurrency 2-3, honour `Retry-After`, exponential backoff on unresolved 429. Match the DC uploader's approach — see `upload-to-digital-concierge.ts` for the reference implementation. |

## Handling per-source specifics

| Source | Key considerations |
|---|---|
| **JSON export / API** | Paginate carefully; some APIs limit to 100 records/page. Auth: bearer token or API key. Rate limits are source-specific. HTML string fields → JSON RTE via `@contentstack/json-rte-serializer`. |
| **CSV** | Every column becomes one field; type coercion needed (dates, booleans, references). No native references; use ID columns + a two-pass import (entries first, then references). |
| **Existing Contentstack stack** | Bulk-fetch entries via Delivery API (fast) or CMA (respects draft state). If CTs mismatch between source and target, this becomes a schema migration — see [`migrate-ct-schema`](../migrate-ct-schema/SKILL.md). |
| **Markdown folder** | Frontmatter as top-level fields; body via `remark` → JSON RTE. Filename → slug. Handle image references (``) — download local paths, upload as assets. |
| **Any other CMS (WordPress, Contentful, Sitecore, AEM, Drupal…)** | Out of scope. Use Contentstack's dedicated CLI: [`@contentstack/cli-cm-import`](https://www.npmjs.com/package/@contentstack/cli-cm-import) with the appropriate connector. |

## See also

- [`provision-studio-stack`](../provision-studio-stack/SKILL.md) — creates the target CTs this skill populates. Run first.
- [`decompose-design`](../decompose-design/SKILL.md) / [`decompose-site`](../decompose-site/SKILL.md) — plan the schema this skill fills.
- [`migrate-ct-schema`](../migrate-ct-schema/SKILL.md) — if source and target schemas diverge, run this alongside to align.
- `agent-idempotency` — the state-file + resume pattern this skill uses is documented as the canonical convention for every skill making CMA writes.
- `scripts/upload-to-digital-concierge.ts` in this repo — reference implementation of the retry + state + concurrency pattern.
