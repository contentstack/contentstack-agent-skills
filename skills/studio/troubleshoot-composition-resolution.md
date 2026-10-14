---
name: troubleshoot-composition-resolution
---

## When to use

Symptom-mapped diagnostic for "the URL I expected to render a composition renders the wrong one, or none." Covers URL pattern matching, `{{entry.url}}` lookup, specificity ties, and unified-URL-resolution semantics.

Use when a LIVE-site URL resolves to the wrong composition, none, or non-deterministically. Phrases: "URL renders the homepage", "two templates match the same pattern", "/blog/post-1 404s", "wildcard stopped matching". If the symptom is ambiguous, route via `troubleshoot` first. Do NOT use for canvas-only issues (use `troubleshoot-canvas`) or when the host app lacks a catch-all route. That's setup.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Troubleshoot composition URL resolution

## Arrived here from "SDK Not Initialized"?

If Sections render but the Template shows "SDK Not Initialized," you're in the right skill. The SDK is fine. The connected template's URL match failed, so `useCompositionData` never resolves, `<StudioComponent />` never mounts, and Studio's handshake times out. See `troubleshoot-canvas` § Run this SECOND: the section-test pre-flight to confirm Sections pass before continuing here.

## Context

When a request URL lands on a route that mounts `<StudioComponent>`, the SDK resolves it to a composition in three stages:

1. **Pattern match**: every composition's `url` pattern is compiled into a regex. The request URL is matched against all of them. Wildcards / placeholders (`{{entry.url}}`, `*`) capture segments. Literals must appear verbatim.
2. **Candidate ranking**: surviving patterns are ranked by **literal-character specificity** (how many non-placeholder characters they have). The most specific tier wins. Ties go to the next stage.
3. **Entry lookup**: for patterns containing `{{entry.<field>}}` or `*`, the SDK queries the linked content type for an entry whose field matches the captured segment. If only one tied candidate has a matching entry, it wins. If multiple do, the first by `composable_uid` order wins (deterministic but arbitrary).

Most production bugs in this area are caused by:
- **Authoring confusion** between "literal prefix in the pattern" vs "prefix stored on the entry's `url` field". When an entry's `url` field stores the full path (e.g. `/blog/post-1`) but the pattern's captured segment is just the slug (`post-1`), the entry lookup misses. Recent SDK versions handle this via a full-path `$or` branch in the entry query (see § Symptom-to-stage matrix below).
- **Specificity ties** between `/{{entry.url}}` and `/{{entry.slug}}` patterns linked to different content types.
- **Wildcard `*` handling** in older SDK versions where `*` was regex-escaped and only matched the literal star.

The SDK addresses several of these via a full-path `$or` branch in the template query. When the pattern contains `{{entry.url}}`, the CDA query becomes `{ $or: [<per-field>, { url: <full request path> }] }`, resolving whether the stored `url` is the captured slug OR the full path.

This skill maps the user-visible symptom to the failing stage and proposes the fix.

## Diagnostic tooling: inspecting a stored composition's `ui`

URL-resolution debugging needs the actual `url_metadata` (e.g. `url_source`, `url_queries`) on the stored composition. Fetch via the Studio API. The **`ui`** field is **`zlib:<base64>`**, literal `zlib:` prefix + base64-encoded zlib-deflated JSON. Decode for read-only inspection:

```js
// Node 18+. Save as inspect-ui.mjs (ES module)
import zlib from "node:zlib";

function decodeUi(ui) {
  if (!ui.startsWith("zlib:")) return JSON.parse(ui);  // legacy plain-JSON fallback
  const bytes = Buffer.from(ui.slice("zlib:".length), "base64");
  return JSON.parse(zlib.inflateSync(bytes).toString("utf8"));
}

const composition = JSON.parse(await new Response(process.stdin).text());
console.log(JSON.stringify(decodeUi(composition.ui), null, 2));
```

**Read-only, for debugging.** Do not modify a composition via the API. The UI-only `url_queries` metadata the Edit-URL modal generates is exactly what gets lost when you try, which is why an API-set `user_specified_pattern` reverts. Use Studio's Edit-URL modal to author URL patterns.

## Task

1. **Capture the SDK version** in the host app: `grep '"@contentstack/studio-client"' package.json` (or whichever SDK package the app uses). Note the version. Some fixes referenced below only exist in recent SDK versions. Confirm via the SDK CHANGELOG before promising a fix is available.
2. **Open DevTools, then the Network tab** in the host app and reload the misbehaving URL. Filter to `cdn.contentstack.io` (or the configured CDA host). You should see at least one composition-fetch query and (usually) an entry-fetch query.
3. **Match the symptom** to the matrix below, pick the closest one.
4. **Run "Check first."** If positive, apply the fix. If negative, run the secondary check.
5. **Report:** the symptom, which stage failed, the check you ran, and the fix. Cap at two checks. Escalate to engineering if both come back negative (paste the request URL, the candidate patterns from Studio, and the CDA call from DevTools).

### Symptom-to-stage matrix

| Symptom | Likely stage that failed | Check first | Fix |
|---|---|---|---|
| **404 / "No composition matched"** for a URL you DO have a pattern for | Pattern match | In Studio, open Compositions and confirm the pattern. Is it `/blog/{{entry.url}}` or `/blog/*`? Does it have an unintended trailing slash? Is there a Stack-level URL prefix the dev app should strip? | If the pattern uses `*` (e.g. `/blog/*`): confirm the SDK version contains the wildcard restoration fix. Older SDKs escape `*` and the pattern only matches the literal URL `/blog/*`. Upgrade the SDK or rewrite as `/blog/{{entry.url}}`. If the pattern uses `{{entry.url}}` and the entry's `url` field is empty / not the slug you expect: fix the entry's `url` field. |
| **Wrong composition wins** when two patterns tie on specificity (e.g. `/blog/{{entry.url}}` and `/article/{{entry.url}}` both exist, request is `/blog/post-1` and the article template renders) | Candidate ranking: specificity tie | Candidates are ranked by how many literal (non-placeholder) characters the pattern has. Ties at the top tier all enter entry lookup. In a host app, log `ranking.topTierMatches.length` from the SDK if exposed. Otherwise reason about it from the patterns. | When the request URL belongs unambiguously to one CT, the entry-lookup stage should drop tied candidates whose CT has no matching entry. Confirm your SDK version includes the entry-existence tie-break (check the SDK CHANGELOG). Otherwise: disambiguate by adding more literal prefix (e.g. `/blog/post/{{entry.url}}` vs `/article/{{entry.url}}`). |
| **Right composition matches but wrong entry renders** (e.g. `/blog/post-1` matches `/blog/{{entry.url}}` but renders post-2) | Entry lookup: `entry.url` field mismatch | Check DevTools Network: the CDA entry query body. Does it have `{ $or: [<per-field>, { url: <full path> }] }`? If yes, the full-path branch should resolve entries stored with the prefix. | If the captured segment is `post-1` but the entry's `url` field stores `/blog/post-1`: the full-path `$or` branch handles this. Confirm your SDK version includes that fix. Otherwise: pick ONE convention across the CT's entries (slug-only OR full path) and apply consistently. |
| **The same URL renders different compositions on different reloads / different machines** | Candidate ranking: tied with no disambiguator | Reload 10× with cache disabled. If the result varies: multiple top-tier candidates tied and the SDK is returning the first hit non-deterministically. | Recent SDK versions drop tied candidates with no matching entry, which makes ties deterministic when only one tied CT owns a matching entry. Confirm SDK version. Backstop: rewrite patterns so only one is top-tier for any given URL (add literal prefix). |
| **`*` wildcard pattern (e.g. `/blog/*`) doesn't match anything but `/blog/*` literally** | Pattern match: legacy wildcard | Older SDK versions escape `*` instead of treating it as a placeholder, so the pattern only matches the literal star. | Upgrade to an SDK version whose CHANGELOG lists wildcard support, OR rewrite the pattern as `/blog/{{entry.url}}`. |
| **Bare `/{{entry.url}}` pattern catches everything, including URLs you wanted other compositions to handle** | Specificity (working as designed, but unintended) | In Studio, open Compositions: which compositions have bare placeholders at the root (`/{{entry.url}}`, `/{{entry.slug}}`)? | Add literal prefixes to disambiguate (e.g. `/article/{{entry.url}}`). The entry-lookup stage's CT filter only helps when patterns tie on specificity, not when one bare pattern is uniquely the most specific match. |
| **`/blog/post-1` resolves to the homepage** (`/` or `/home`) | Catch-all routing in the host app, NOT SDK resolution | `grep -r "StudioComponent" src/` in the host app. Does the catch-all route exist? Or does a specific `/blog/*` route mount something else? | Add the catch-all route. See `embed-composition` skill. This isn't a Studio bug. |
| **An API-authored template renders fine on the live route, but Studio's Edit-URL panel shows the pattern as hand-typed**: no sign it derives from the connected CT. Editing anything in the modal loses the CT link | Not a resolution failure. The composition was written with `url` but **no `url_metadata`**, so Studio has no derivation to read and treats it as `legacy_url`. Delivery still resolves off the `url` pattern, which is why it looks healthy | Fetch the composition entry via the CMA. Is `url_metadata` absent, or is `url_metadata.url_source` unset? Then: does the compositions CT even model `url_metadata` as a group with `url_source` + `url_queries`? (A missing CT field makes the CMA drop the object silently on write.) | Fix the CT field first if missing (`provision-studio-project`), then re-write the composition with the matched pair: `url_source: "content_type_url_pattern"` for Connected on a page-type CT, `default_url_pattern` / `user_specified_pattern` for Freeform, `url_queries` as a JSON string. Read the entry back and confirm it persisted. See [`author-composition-entry` § `url` + `url_metadata`, a matched pair](author-composition-entry.md#url-metadata-matched-pair). |
| **Some compositions never appear in the candidate set even though they should** | Workspace scale: SDK fetches `url_metadata.$exists: true` and ranks client-side. Very large composition counts can exhaust the response payload | In Studio, open Compositions: how many compositions total? If >500, scale is plausible. Inspect the CDA composition-fetch response size and compare to the count. | Engineering escalation. There is no shipped client-side workaround. Reduce composition count or use more specific patterns as an interim measure. |
| **The pattern looks right but evaluates with `{{entry.title}}` rendering capitalized + `%20`-encoded** | The pattern uses `{{entry.title}}` instead of a slug field | In Studio, open the composition, then URL pattern. Does it reference `entry.title`? | Replace with `{{entry.url}}` or `{{entry.slug}}`. `title` is human-readable text and breaks on rename. |
| **CT `url_pattern: "/:slug"` saves but entries' `url` comes back literally `/:slug`** (not substituted) and the canvas URL stays `/:slug`, every entry of this CT looks like it has the same URL | Contentstack's **CMS-side** CT URL-pattern compiler (separate from the Studio SDK pattern compiler) recognizes `:title` as a substitution token. `:slug` is treated as a **literal**. The pattern stores correctly but nothing gets slugified into `entry.url` on save, so the SDK's lookup (which queries by `entry.url`) finds no per-entry URL to match against. | In Studio, open the content type, then URL pattern. Is the placeholder `:slug` or `:title`? | Switch the CT `url_pattern` to `:title` (CMS slugifies the title field: that's the working substitution token). Re-save + republish every entry so `entry.url` recomputes. In the composition, use `{{entry.title}}` for the placeholder. `:slug` is a footgun. Remove it from CT patterns. |
| **A multi-entry connected template 404s for every URL** (`/<route>/<slug>` returns "No composition for /…"), but a single-entry connected template (literal URL like `/home`) resolves fine on the same project | The multi-entry template's composition `url` is a literal pattern (e.g. `"/blog/:slug"`). The SDK can't match a literal `:slug` against any entry URL. Single-entry templates are fine with literal URLs because they only resolve one path. Multi-entry templates need a placeholder pattern + CT `url_pattern` that produces real per-entry URLs. | In Studio, open Compositions, select the multi-entry template, and read its URL pattern. Is it literal (`/blog/:slug`) or placeholder (`/blog/{{entry.title}}`)? Then check the CT's URL pattern. Is it `:slug` (broken) or `:title` (working)? Then pick any entry: does its `url` field show a real slug like `/blog/welcome-to-studio` or the literal `/:slug`? | The proven shape: CT `url_pattern: "/:title"` + `url_prefix: "/<route>/"` (e.g. `/blog/`). Composition `url: "/<route>/{{entry.title}}"` with `url_metadata.url_source: "content_type_url_pattern"` and `url_queries: ""`. Re-save + republish entries after the CT pattern change. CT pattern and composition URL must be **consistent by construction**. See [`build-connected-template § Single-entry vs multi-entry URL pattern rule`](build-connected-template.md#single-entry-vs-multi-entry-url-pattern-rule). |

### Runtime error taxonomy: what the SDK actually throws

The three-stage model above describes where resolution fails. This is what that failure looks like from the calling code, and it's the part most route wiring gets wrong.

**`sdk.fetchCompositionData` throws on a miss. It does not resolve with `hasSpec: false`.** So the standard guard `if (!specOptions.hasSpec) notFound()` is unreachable on exactly the path it was written for: the `await` throws, the framework's error boundary catches it, and the visitor gets a **500 where a 404 belongs**. A "my 404 page never shows / unmatched URLs return 500" report is this, not a routing bug.

It throws a `ComposableStudioError` carrying a **`code`** and an **`errorClass`**. For the 404 decision read neither: call `isCompositionNotFound(err)`, true for exactly the codes below and for any added after your build shipped.

| `code` (class `NOT_FOUND`) | Stage that failed | Typical cause |
|---|---|---|
| `COMPOSITION_UID_NOT_FOUND` | Lookup by identifier | Wrong or deleted uid: what embeds and Freeform fetches get |
| `NO_COMPOSITION_FOR_URL` | 1: pattern match | Unclaimed URL, or a literal pattern where a placeholder belongs |
| `URL_MATCHED_NO_ENTRY` | 3: entry lookup | Bad slug under a connected template, or the entry's `url` is empty or unpublished |
| `CONNECTED_ENTRY_NOT_FOUND` | 3: entry lookup | No entry authored, or none published to this environment |

Every other class is real breakage and **never a 404**: `SETUP_INVALID` (a wrong connection value), `SERVER_ERROR`, `NETWORK_ERROR`. That split is the point. All three used to arrive under one name reading "composition not found", so a route branching on it returned **404 on pages that exist**.

**Read `err.causes` first.** The SDK attaches `{ cause, fix }` pairs generated for that specific failure, ordered most likely first. It's the fastest diagnosis available and most people never look at it.

**`content_type_url_pattern` relocates the failure. This is the trap.** With `url_metadata.url_source: "content_type_url_pattern"`, the composition's pattern covers a whole URL family (`/blog/{{entry.title}}` matches any `/blog/*`). A mistyped slug therefore **passes** stage 1 and dies at stage 3: `URL_MATCHED_NO_ENTRY`, not `NO_COMPOSITION_FOR_URL`. Both are `NOT_FOUND`, so the predicate covers both — but route code that hand-rolls a list of names and only knows the first 404s correctly for `/nonsense` and 500s for `/blog/nonsense`. Test both.

Classify with the predicate:

```ts
import { isCompositionNotFound } from "@contentstack/studio-client";

if (isCompositionNotFound(err)) { /* 404 */ } else { throw err; /* 500 */ }
```

`useCompositionData` doesn't throw, it stores the same error object in `error`, so `isCompositionNotFound(error)` classifies identically.

The wrapper that turns this into correct 404-vs-500 behavior lives in [`configure-csr-vs-ssr` § `fetchCompositionData` does not return "not found"](configure-csr-vs-ssr.md#resolve-composition-helper), one canonical `resolveComposition` helper. Don't hand-roll a second one, and never blanket-catch: a bare `catch { notFound() }` converts CDA outages and expired tokens into silent 404s.

<a id="editor-vs-ssr-url-derivation"></a>

### Editor vs SSR: URL derivation is not the same code path

The symptom matrix above is about **live-site** resolution. The Studio **editor** resolves URLs differently, and a composition can pass one while failing the other. Reported as "the page works but the template won't open in Studio" (or the reverse).

| | Live site / SSR | Studio editor |
|---|---|---|
| What it resolves | The request path becomes a composition, via the compiled `url` pattern + a CDA entry query | A **preview entry** for the open template, via the editor's own preview-entry query |
| Needs `url_metadata`? | No, resolves off `url` alone | **Yes.** With no `url_metadata` you get `no-fetch` with reason `no-composition`, so there is nothing to derive a preview URL from and the template won't open |
| Honours `url_source`? | For query construction | **Decisively**: see the table below |

Editor query shape by `url_source`, and the error each raises when nothing matches:

| `url_source` | Editor query | Substitutes `{{entry.x}}`? | Error |
|---|---|---|---|
| `content_type_url_pattern` | Fixed `url`-field existence (`requiredVariables: ["url"]`) | **No** | `MISSING_CT_PATTERN_URL_FIELD`, shown as "No entry has a URL field populated yet" |
| `legacy_url` | Same fixed `url`-existence query | **No** | `MISSING_LINKED_URL_FIELD` |
| `user_specified_pattern` | Matches on the fields extracted from the pattern | **Yes** | `NO_ENTRY_WITH_ALL_VARIABLES` |

**The mismatch that produces this most often:** `url_source: "content_type_url_pattern"` on a CT where **no entry has a non-empty `url` field**. That source ignores your pattern and queries for `url` existence, so it doesn't matter what `{{entry.x}}` you wrote. Typical on a **singleton** CT (`options.singleton: true`, no `url_pattern`). Nothing auto-generates `url`, and if nobody set it by hand the editor shows "No entry has a URL field populated yet" while SSR renders fine off the literal `url`.

**Two valid fixes, pick by where the URL comes from:**
- If the URL is a fixed path (`/rewards`), keep `content_type_url_pattern` and **set `url` on the entry by hand**. Cheapest, and it's what a singleton expects.
- If the URL derives from some other field (`{{entry.slug}}`, a reference), switch to `user_specified_pattern`, the only source that substitutes pattern variables.

See [`author-composition-entry` § Which `url_source` to write](author-composition-entry.md).

**Check, in order:** (1) does the composition have `url_metadata` at all? (2) does `url_source` match how the URL is really derived? (3) for `content_type_url_pattern` / `legacy_url`, does at least one entry of the CT have a non-empty `url` starting with `/`? A "yes, yes, no" is the classic case.

### When to escalate

If both checks for a symptom come back negative, gather and send to engineering:

1. The request URL (exact, with query string).
2. Every candidate composition's `url` pattern from Studio.
3. The CDA calls from DevTools Network (request URL + response).
4. The SDK package version.
5. Whether `<StudioComponent>` is mounted on a catch-all route, and the route file path.
6. If available, output from any composition-resolution diagnostic surfaced in your app (the SDK exposes `CompositionResolutionDiagnosticEventData` and Studio's diagnostic-inspector module instruments this. Whether it's user-visible depends on the host app and Studio version).

Without those six pieces, engineering can't reproduce. Don't open a ticket until you have all six.

## Why this is a separate skill from `troubleshoot-canvas`

`troubleshoot-canvas` covers the **authoring iframe** (Studio's canvas, what the author sees while building). This skill covers the **live site** (what the visitor sees at the public URL). They share zero failure modes:

- Canvas issues are about communication between Studio and the canvas app (Live Preview, Delivery Token, route mounting).
- Resolution issues are about the matching logic between the SDK and the CDA on the live site.

If unsure which surface is failing: is the issue visible to authors only (inside Studio's iframe), or to visitors only (on the live URL)? That tells you which skill to use.

## What this skill is NOT

- Not a guide to authoring URL patterns from scratch. Use `build-connected-template` for that.
- Not a guide to debugging Studio's editor (use `troubleshoot-canvas`).
- Not a replacement for reading the SDK CHANGELOG. Version-specific fixes referenced here may not exist in older SDKs.
- Not a routing-setup guide. If the catch-all route is missing, use `embed-composition`.
