# troubleshoot-composition-resolution


## When to use

Symptom-mapped diagnostic for "the URL I expected to render a composition renders the wrong one — or none." Covers URL pattern matching, `{{entry.url}}` lookup, specificity ties, and unified-URL-resolution semantics.

Use when a LIVE-site URL resolves to the wrong composition, none, or non-deterministically. Phrases — "URL renders the homepage", "two templates match the same pattern", "/blog/post-1 404s", "wildcard stopped matching". If the symptom is ambiguous, route via `troubleshoot` first. Do NOT use for canvas-only issues (use `troubleshoot-canvas`) or when the host app lacks a catch-all route — that's setup.

# Troubleshoot composition URL resolution

## ⚡ Arrived here from "SDK Not Initialized"?

If Sections render but the Template shows "SDK Not Initialized," you're in the right skill — the SDK is fine; the connected template's URL match failed, so `useCompositionData` never resolves, `<StudioComponent />` never mounts, and Studio's handshake times out. See `troubleshoot-canvas` § *Run this FIRST — the section-test pre-flight* to confirm Sections pass before continuing here.

## Context

When a request URL lands on a route that mounts `<StudioComponent>`, the SDK resolves it to a composition in three stages:

1. **Pattern match** — every composition's `url` pattern is compiled into a regex. The request URL is matched against all of them. Wildcards / placeholders (`{{entry.url}}`, `*`) capture segments; literals must appear verbatim.
2. **Candidate ranking** — surviving patterns are ranked by **literal-character specificity** (how many non-placeholder characters they have). The most specific tier wins. Ties go to the next stage.
3. **Entry lookup** — for patterns containing `{{entry.<field>}}` or `*`, the SDK queries the linked content type for an entry whose field matches the captured segment. If only one tied candidate has a matching entry, it wins. If multiple do, the first by `composable_uid` order wins (deterministic but arbitrary).

Most production bugs in this area are caused by:
- **Authoring confusion** between "literal prefix in the pattern" vs "prefix stored on the entry's `url` field" — when an entry's `url` field stores the full path (e.g. `/blog/post-1`) but the pattern's captured segment is just the slug (`post-1`), the entry lookup misses. Recent SDK versions handle this via a full-path `$or` branch in the entry query (see § *Symptom matrix* below).
- **Specificity ties** between `/{{entry.url}}` and `/{{entry.slug}}` patterns linked to different content types.
- **Wildcard `*` handling** in older SDK versions where `*` was regex-escaped and only matched the literal star.

The SDK addresses several of these via a full-path `$or` branch in the template query — when the pattern contains `{{entry.url}}`, the CDA query becomes `{ $or: [<per-field>, { url: <full request path> }] }`, resolving whether the stored `url` is the captured slug OR the full path.

This skill maps the user-visible symptom to the failing stage and proposes the fix.

## Diagnostic tooling — inspecting a stored composition's `ui`

URL-resolution debugging needs the actual `url_metadata` (e.g. `url_source`, `url_queries`) on the stored composition. Fetch via the Studio API; the **`ui`** field is **`zlib:<base64>`** — literal `zlib:` prefix + base64-encoded zlib-deflated JSON. Decode for read-only inspection:

```js
// Node 18+. Save as inspect-ui.js
import zlib from "node:zlib";

function decodeUi(ui) {
  if (!ui.startsWith("zlib:")) return JSON.parse(ui);  // legacy plain-JSON fallback
  const bytes = Buffer.from(ui.slice("zlib:".length), "base64");
  return JSON.parse(zlib.inflateSync(bytes).toString("utf8"));
}

const composition = JSON.parse(await new Response(process.stdin).text());
console.log(JSON.stringify(decodeUi(composition.ui), null, 2));
```

**Read-only — for debugging.** Do not modify a composition via the API; the UI-only `url_queries` metadata the Edit-URL modal generates is exactly what gets lost when you try, which is the root cause of finding #9 (API-set `user_specified_pattern` reverts). Use Studio's Edit-URL modal to author URL patterns.

## Task

1. **Capture the SDK version** in the host app: `grep '"@contentstack/studio-client"' package.json` (or whichever SDK package the app uses). Note the version. Fixes referenced below land in SDK alpha after the unified-URL-resolution ADR — confirm via the SDK CHANGELOG before promising a fix is available.
2. **Open DevTools → Network tab** in the host app and reload the misbehaving URL. Filter to `cdn.contentstack.io` (or the configured CDA host). You should see at least one composition-fetch query and (usually) an entry-fetch query.
3. **Match the symptom** to the matrix below — pick the closest one.
4. **Run "Check first."** If positive, apply the fix. If negative, run the secondary check.
5. **Report:** symptom → which stage failed → check → fix. Cap at two checks; escalate to engineering if both come back negative (paste the request URL, the candidate patterns from Studio, and the CDA call from DevTools).

### Symptom → stage matrix

| Symptom | Likely stage that failed | Check first | Fix |
|---|---|---|---|
| **404 / "No composition matched"** for a URL you DO have a pattern for | Pattern match | Studio → Compositions → confirm the pattern. Is it `/blog/{{entry.url}}` or `/blog/*`? Does it have an unintended trailing slash? Is there a Stack-level URL prefix the dev app should strip? | If the pattern uses `*` (e.g. `/blog/*`): confirm the SDK version contains the wildcard restoration fix. Older SDKs escape `*` and the pattern only matches the literal URL `/blog/*`. Upgrade the SDK or rewrite as `/blog/{{entry.url}}`. If the pattern uses `{{entry.url}}` and the entry's `url` field is empty / not the slug you expect: fix the entry's `url` field. |
| **Wrong composition wins** when two patterns tie on specificity (e.g. `/blog/{{entry.url}}` and `/article/{{entry.url}}` both exist, request is `/blog/post-1` and the article template renders) | Candidate ranking — specificity tie | Inspect the candidates via `rank-url-matches.ts` logic: each match carries a `literalCharCount`. Ties at the top tier all enter entry lookup. In a host app, log `ranking.topTierMatches.length` from the SDK if exposed; otherwise reason about it from the patterns. | When the request URL belongs unambiguously to one CT, the entry-lookup stage should drop tied candidates whose CT has no matching entry. Confirm SDK version contains the unified-URL-resolution ADR work. Otherwise: disambiguate by adding more literal prefix (e.g. `/blog/post/{{entry.url}}` vs `/article/{{entry.url}}`). |
| **Right composition matches but wrong entry renders** (e.g. `/blog/post-1` matches `/blog/{{entry.url}}` but renders post-2) | Entry lookup — `entry.url` field mismatch | Check DevTools Network: the CDA entry query body. Does it have `{ $or: [<per-field>, { url: <full path> }] }`? If yes, the full-path branch should resolve entries stored with the prefix. | If the captured segment is `post-1` but the entry's `url` field stores `/blog/post-1`: the full-path `$or` branch handles this — confirm your SDK version includes that fix. Otherwise: pick ONE convention across the CT's entries (slug-only OR full path) and apply consistently. |
| **The same URL renders different compositions on different reloads / different machines** | Candidate ranking — tied with no disambiguator | Reload 10× with cache disabled. If the result varies: multiple top-tier candidates tied and the SDK is returning the first hit non-deterministically. | The entry-existence drop in the unified-URL-resolution work makes ties deterministic when only one tied CT owns a matching entry. Confirm SDK version. Backstop: rewrite patterns so only one is top-tier for any given URL (add literal prefix). |
| **`*` wildcard pattern (e.g. `/blog/*`) doesn't match anything but `/blog/*` literally** | Pattern match — legacy wildcard | Inspect `url-pattern-matcher.ts` in your SDK version: does `compileUrlPattern` treat `*` as a placeholder, or does `escapeRegExp` escape it? If the latter, the pattern only matches the literal star. | Upgrade SDK to a version where `*` is compiled as a placeholder (check `url-pattern-matcher.spec.ts` for wildcard test cases), OR rewrite the pattern as `/blog/{{entry.url}}`. |
| **Bare `/{{entry.url}}` pattern catches everything, including URLs you wanted other compositions to handle** | Specificity (working as designed, but unintended) | Studio → Compositions → which compositions have bare placeholders at the root (`/{{entry.url}}`, `/{{entry.slug}}`)? | Add literal prefixes to disambiguate (e.g. `/article/{{entry.url}}`); the entry-lookup stage's CT filter only helps when patterns tie on specificity, not when one bare pattern is uniquely the most specific match. |
| **`/blog/post-1` resolves to the homepage** (`/` or `/home`) | Catch-all routing in the host app, NOT SDK resolution | `grep -r "StudioComponent" src/` in the host app. Does the catch-all route exist? Or does a specific `/blog/*` route mount something else? | Add the catch-all route. See `embed-composition` skill. This isn't a Studio bug. |
| **Some compositions never appear in the candidate set even though they should** | Workspace scale — SDK fetches `url_metadata.$exists: true` and ranks client-side; very large composition counts can exhaust the response payload | Studio → Compositions → how many compositions total? If >500, scale is plausible. Inspect the CDA composition-fetch response size and compare to the count. | Engineering escalation — there is no shipped client-side workaround. Reduce composition count or use more specific patterns as an interim measure. |
| **The pattern looks right but evaluates with `{{entry.title}}` rendering capitalised + `%20`-encoded** | The pattern uses `{{entry.title}}` instead of a slug field | Studio → Composition → URL pattern. Does it reference `entry.title`? | Replace with `{{entry.url}}` or `{{entry.slug}}`. `title` is human-readable text and breaks on rename. |
| **CT `url_pattern: "/:slug"` saves but entries' `url` comes back literally `/:slug`** (not substituted) and the canvas URL stays `/:slug` — every entry of this CT looks like it has the same URL | Contentstack's **CMS-side** CT URL-pattern compiler (separate from the Studio SDK pattern compiler) recognises `:title` as a substitution token; `:slug` is treated as a **literal**. The pattern stores correctly but nothing gets slugified into `entry.url` on save, so the SDK's lookup (which queries by `entry.url`) finds no per-entry URL to match against. | Studio → Content type → URL pattern. Is the placeholder `:slug` or `:title`? | Switch the CT `url_pattern` to `:title` (CMS slugifies the title field — that's the working substitution token). Re-save + republish every entry so `entry.url` recomputes. In the composition, use `{{entry.title}}` for the placeholder. `:slug` is a footgun; remove it from CT patterns. |
| **A multi-entry connected template 404s for every URL** (`/<route>/<slug>` returns "No composition for /…"), but a single-entry connected template (literal URL like `/home`) resolves fine on the same project | The multi-entry template's composition `url` is a literal pattern (e.g. `"/blog/:slug"`) — the SDK can't match a literal `:slug` against any entry URL. Single-entry templates are fine with literal URLs because they only resolve one path; multi-entry templates need a placeholder pattern + CT `url_pattern` that produces real per-entry URLs. | Studio → Compositions → multi-entry template → URL pattern. Is it literal (`/blog/:slug`) or placeholder (`/blog/{{entry.title}}`)? Then: CT → URL pattern. Is it `:slug` (broken) or `:title` (working)? Then: pick any entry → does its `url` field show a real slug like `/blog/welcome-to-studio` or the literal `/:slug`? | The proven shape: CT `url_pattern: "/:title"` + `url_prefix: "/<route>/"` (e.g. `/blog/`); composition `url: "/<route>/{{entry.title}}"` with `url_metadata.url_source: "content_type_url_pattern"` and `url_queries: ""`. Re-save + republish entries after the CT pattern change. CT pattern and composition URL must be **consistent by construction**. See [`build-connected-template § Single-entry vs multi-entry URL pattern rule`](../build-connected-template/SKILL.md#single-entry-vs-multi-entry-url-pattern-rule). |

### When to escalate

If both checks for a symptom come back negative, gather and send to engineering:

1. The request URL (exact, with query string).
2. Every candidate composition's `url` pattern from Studio.
3. The CDA calls from DevTools Network (request URL + response).
4. The SDK package version.
5. Whether `<StudioComponent>` is mounted on a catch-all route, and the route file path.
6. If available, output from any composition-resolution diagnostic surfaced in your app (the SDK exposes `CompositionResolutionDiagnosticEventData` and Studio's diagnostic-inspector module instruments this; whether it's user-visible depends on the host app and Studio version).

Without those six pieces, engineering can't reproduce. Don't open a ticket until you have all six.

## Why this is a separate skill from `troubleshoot-canvas`

`troubleshoot-canvas` covers the **authoring iframe** (Studio's canvas — what the author sees while building). This skill covers the **live site** (what the visitor sees at the public URL). They share zero failure modes:

- Canvas issues are about Studio ↔ canvas-app communication (Live Preview, Delivery Token, route mounting).
- Resolution issues are about SDK ↔ CDA matching logic on the live site.

If unsure which surface is failing: is the issue visible to authors only (inside Studio's iframe), or to visitors only (on the live URL)? That tells you which skill to use.

## What this skill is NOT

- Not a guide to authoring URL patterns from scratch — use `build-connected-template` for that.
- Not a guide to debugging Studio's editor (use `troubleshoot-canvas`).
- Not a replacement for reading the SDK CHANGELOG — version-specific fixes referenced here may not exist in older SDKs.
- Not a routing-setup guide — if the catch-all route is missing, use `embed-composition`.
