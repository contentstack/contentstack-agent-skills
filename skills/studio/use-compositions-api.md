---
name: use-compositions-api
---

## When to use

Create, read, list, update, or delete Studio compositions through the **managed Composable Studio API service**, the REST layer that validates the layout, compresses the `ui` spec, and forwards the caller's identity, so you don't hand-encode entries against the raw CMA.

Use when the project talks to the Composable Studio API service (`/v1/projects/:projectUid/compositions`) and you want guardrails: server-side Studio validation, automatic `ui` compression, `composable_uid` backfill, a referenced-guard on delete, and list/references endpoints. Phrases: "compositions REST API", "Studio API service", "create composition endpoint", "list compositions", "composition references API", "managed composition API". Do NOT use for: raw-CMA / seed-pipeline / migration authoring where you hold a management token and encode the `ui` yourself. That's `author-composition-via-api`. Do NOT use for interactive UI authoring. That's `build-section` / `build-connected-template`. The `ui`-tree shapes themselves are NOT redefined here. They live in `author-composition-via-api`.

> **Auth preflight: settle the credential before the first API call.** The service accepts OAuth Bearer. Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Use the Compositions API (managed Studio service)

## Context

The **Composable Studio API service** is a REST wrapper over the CMS. Instead of building a composition entry by hand, you `POST` the layout and the service does the mechanical work:

- **You send the `ui` tree uncompressed** (a JSON object). The service compresses it to `zlib:<base64>`. You never touch zlib.
- **The service validates** the tree against Studio's structural rules and returns all problems at once, field-anchored.
- **`composable_uid` is backfilled** with the entry uid when you omit it, and uniqueness is enforced content-type-wide.
- **Delete is guarded**: it refuses to orphan a referenced composition unless you force it.

This is the counterpart to `author-composition-via-api`, which drives the **raw CMA** (CMA credential per `authenticate-cma`, self-encoded `ui`). Same result (a composition entry) at a higher level. Pick this skill when you want the guardrails and are acting as a signed-in user. Pick `author-composition-via-api` for management-token automation and full low-level control.

> **Preview: not yet GA.** The service is rolling out. **Paths and response shapes may change**, and it may not be enabled on your region/tenant. If a call 404s at the host itself (not a composition-not-found body), the service isn't deployed for you. Fall back to `author-composition-via-api`. A stack-scoped **management-token** mode is not available yet. Management-token automation must use the raw-CMA path.

## Pre-flight checks

- A Studio **project** exists and is bound to a stack + a compositions content type. If not, run `provision-studio-project`.
- You have the **`projectUid`**, every route is nested under it.
- You have a resolved credential (**OAuth Bearer by default**, session `authtoken` only as the last rung, [`authenticate-cma`](authenticate-cma.md)) and the **`organization_uid`** that owns the project. Both styles are accepted. The service forwards whichever you send. `401 error_code 39` means **neither** arrived, not that Bearer was refused.
- You know the **base URL** for the region (see below). Confirm the service answers before scripting against it.

## The endpoints

All routes are prefixed with `/v1` and nested under the project. Base URL per region, e.g. AWS NA `https://composable-studio-api.contentstack.com/v1`. EU / Azure / GCP have their own hosts.

| Operation | Method + path |
|---|---|
| Create (placement in body) | `POST /v1/projects/{projectUid}/compositions` |
| Create a template | `POST …/compositions/templates` |
| Create a section | `POST …/compositions/sections` |
| List / query | `GET …/compositions` |
| Fetch one | `GET …/compositions/{uid}` |
| Fetch, assert template | `GET …/compositions/{uid}/template` |
| Fetch, assert section | `GET …/compositions/{uid}/section` |
| List references | `GET …/compositions/{uid}/references` |
| Update (partial merge) | `PUT …/compositions/{uid}` |
| Delete (guarded) | `DELETE …/compositions/{uid}` |

## Authentication

Send two headers on every request. The service acts **as the calling user**: it forwards your own credential to the CMA rather than holding a service credential of its own.

| Header | Value |
|---|---|
| `$CS_AUTH` | `authorization: Bearer <oauth>` by default. `authtoken: <session>` only as the last rung, [`authenticate-cma`](authenticate-cma.md). Send exactly one. `401` `39` means neither arrived |
| `organization_uid` | Org that owns the project |

Three checks, each with its own failure code: a **project access** denial gives `422`, **no credential** reaching the service gives `401`, and when Contentstack rejects the token the upstream **401/403** is preserved. Reads need read access to the project's stack. Writes need write access.

## Task

### Step 1: Build the `ui` tree (uncompressed)

Assemble the layout as a plain node object. **Do not compress it**. That's the service's job. The node anatomy, value sources, Repeater / Condition Block / Section Slot / Binding Override, and the closed prop/node-type sets are the single source of truth in `author-composition-via-api` (and the Building Blocks API reference). Reuse them. This skill does not restate them.

### Step 2: Create the composition

`POST` the uncompressed payload. Placement comes from the body on the generic route, or from the flavored routes (`/templates` maps to `page`, `/sections` to `section`).

```bash
# requires:
#   STUDIO_API  Studio API base URL for your region, e.g. https://<studio-api-host>
#   PROJECT     Studio project uid
#   ORG_UID     organization uid that owns the project
#   CS_AUTH     one auth header resolved per authenticate-cma, e.g. "authorization: Bearer $CS_OAUTH_ACCESS_TOKEN"
curl -X POST "$STUDIO_API/v1/projects/$PROJECT/compositions" \
  -H "$CS_AUTH" \
  -H "organization_uid: $ORG_UID" \
  -H 'Content-Type: application/json' \
  -d '{
        "title": "Blog Post",
        "place_composition_as": "page",
        "url": "/blog/{{entry.slug}}",
        "connected_content_type": "blog_post",
        "ui": { "uid": "root", "type": "page", "props": {}, "slots": {}, "metadata": {} },
        "data_sources": []
      }'
```

On success (`201`) the response is `{ notice, composition, warnings? }`. The returned `composition.ui` is the **compressed** string as stored. `composable_uid` equals the entry uid unless you supplied one. Non-blocking findings ride along in `warnings[]`.

### Step 3: Handle validation

Blocking problems return **`422` `composition_invalid`** with every failing path at once: `errors: { "<path>": ["<message>"] }`. Fix each path and resend. Warnings don't block, surface them but proceed.

### Step 4: Read, list, reference

- **Fetch one:** `GET …/{uid}` returns the entry with `ui` compressed by default. Add `?decompression=true` to get the node tree back (and `data_sources` parsed).
- **List:** `GET …/compositions` returns lightweight items (`ui` omitted). Filter with `place_composition_as`, `composable_uid`, `title`. Paginate with `limit` (1 to 100, default 50) / `skip`. Add `include_count=true` for the total. Add `include_ui=true` (+ `decompression=true`) to include the spec.
- **References:** `GET …/{uid}/references` lists what points at a composition. Check this before deleting a section.

### Step 5: Update and delete

- **Update** is a **partial merge**: `PUT …/{uid}` with only the fields you're changing. If you send `ui`, send it uncompressed. The service re-validates and re-compresses. `composable_uid` is **immutable** (`422` if you try to change it).
- **Delete**: `DELETE …/{uid}`. If other compositions reference it, you get **`409` `composition_referenced`**. `?force=true` deletes anyway and leaves those references dangling, so before using it: `GET …/{uid}/references`, show the user the referencing compositions, and get explicit approval for the forced delete. Send the DELETE **without** a JSON `Content-Type` on an empty body (Fastify rejects that combination with a `400`).

### Step 6: Attach a thumbnail when `place_composition_as: "section"`

A section created through this API has no `ui_preview`, so it lands as a blank tile in the Sections accordion and the Section Slot picker. Studio only captures one when an author opens the section and clicks **Save**. Browsing or reloading never repairs it.

Upload an image asset and set its uid as `ui_preview` on the entry. Routes (including generating a schematic from the entry's own `ui`), trade-offs and pitfalls: [`author-composition-thumbnails`](author-composition-thumbnails.md).

**This step is mandatory, not optional.** A create is not complete until `ui_preview` is set. If the thumbnail call fails, report it and retry, do not silently continue, and do not describe the section as created. "Cosmetic" means it cannot corrupt data. It does not mean skippable.

## Inputs needed from the user

- Region **base URL** (or confirm which cloud/region the project is in).
- **`projectUid`**, **`organization_uid`**, and a valid credential resolved per [`authenticate-cma`](authenticate-cma.md).
- The composition to create (or the `uid` to read/update/delete).

## Definition of done

A composition created through this API is not finished when the write returns `200`. Section compositions need `ui_preview`, the components they place need `thumbnailUrl` and CSLP tags, and the project needs Live Preview on, all six rows of [`complete-the-build`](complete-the-build.md). None of them affect rendering, so a green create call proves nothing about them.

## Acceptance

- Create returns `201` with a `composition.uid`. `composable_uid` is set (backfilled or yours).
- The `ui` you sent as an object comes back as a `zlib:`-prefixed string.
- A structurally invalid `ui` returns `422` with field-anchored `errors`, not a partial write.
- `GET …/{uid}?decompression=true` round-trips your tree.
- Deleting a referenced composition is blocked (`409`) unless `?force=true`, which is only sent after the user has seen the references and approved.
- For `place_composition_as: "section"`, `ui_preview` is set, **verified by re-reading the entry**, not assumed from a successful POST. A blank tile means the create is unfinished (Step 6).

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Sending `ui` pre-compressed | The service compresses for you. A `zlib:` string is treated as the tree and fails validation | Send the **uncompressed node object** |
| `data_sources` as a JSON string | The service stringifies it. A string double-encodes | Send a plain **array** |
| Blank `composable_uid` | A whitespace-only value is rejected, not backfilled | Omit it, or send a real slug. A blank value gives `422` |
| Duplicate `composable_uid` in another locale | Uniqueness is content-type-wide, not per-locale | Expect `409` at create. Pick a unique slug |
| Treating `422 stack_not_found` as "missing" | It's the **access-denied** code (Studio convention, not 403) | Check the caller's rights on the project's stack |
| `DELETE` with `Content-Type: application/json` + empty body | Fastify rejects it with `400` before the handler | Omit the header on a body-less DELETE |
| Host itself 404s | The service isn't deployed for your region/tenant yet | Fall back to `author-composition-via-api` (raw CMA) |

## See also

- `author-composition-via-api`: the raw-CMA path and the **canonical `ui`-tree / binding shapes** (CMA credential per `authenticate-cma`, self-encoded).
- `understand-authoring-headlessly`: the `ui` zlib tree + `data_sources` + the six binding types, conceptually.
- `embed-composition`: render one managed region inside a code-owned page once the composition exists.
- `provision-studio-project`: create the project + compositions content type this API targets.
