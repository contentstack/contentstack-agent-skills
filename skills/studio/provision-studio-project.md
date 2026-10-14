---
name: provision-studio-project
---

## When to use

Bootstrap a Studio project via API: create the compositions CT with the schema Studio's editor + runtime require, plus the publish + delivery-token setup.

Use when standing up a brand-new Studio project headlessly (no UI), seeding an environment for tests/demos, or onboarding a new stack with no compositions CT yet. Signals: "create compositions CT via API", "seed a Studio project", "bootstrap a stack for Studio". Do NOT use for composition entries (`author-composition-via-api`) or stack assets/CTs outside compositions (`provision-studio-stack`).

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Provision Studio Project (API-first)

## Context

Provisioning a Studio project touches **two API surfaces**:

1. **Contentstack CMA** (`api.contentstack.io` and regional variants). Creates the stack, the compositions content type, the environment, the delivery + preview token, and enables Live Preview on the stack.
2. **Studio API** (`composable-studio-api.contentstack.com` and regional variants). Creates the Studio project itself via `/v1/projects`, binds it to the stack (`connectedStackApiKey`) and the compositions CT (`contentTypeUid`), and configures environment + locale + Freeform.

Skip either surface and Studio cannot resolve compositions:

- Without a compositions CT there is nothing to author against.
- Without a Studio project the canvas iframe has no project to load.
- Without Live Preview enabled on the stack the canvas iframe hangs forever on "Loading composition…" because the canvas-app's `rest-preview.contentstack.*` calls fail CORS preflight.

The CT must carry an exact set of fields. If any are missing, mistyped, or wrong cardinality, the editor's `?include[]=linked_sections` fails, the runtime's `composable_uid` lookup misses, or the canvas cannot persist the composition.

Once the project exists, composition entries are created via [`author-composition-via-api`](author-composition-via-api.md). Stack content outside the compositions CT (assets, page CTs the compositions reference) belongs in [`provision-studio-stack`](provision-studio-stack.md).

Regional hosts: see Step 10 below (Studio API hosts mirror the CMA region prefixes).

## Task

1. **Confirm prerequisites.** You have a resolved CMA credential, **OAuth Bearer by default**, session `authtoken` only as the last rung ([`authenticate-cma`](authenticate-cma.md)), AND `api_key` for the target stack. Both Studio API and CMA expect these two headers together. Know the region (regional Studio API hosts are listed in Step 10). NA defaults: CMA `api.contentstack.io`, Studio API `composable-studio-api.contentstack.com`. **Custom / private data center (hosts supplied by Contentstack): set every host explicitly.** There is no `region` shortcut. See [`install-studio`](install-studio.md) § Custom / private data center. Establish which data center you're on first via [`analyze-project-fit`](analyze-project-fit.md) § 2b: Determine the data center. Getting this wrong here provisions a CT, tokens and a Studio project **in the wrong data center**, with no error. The calls succeed against the default region.

   > **MCP-first execution.** Discover tools and verify the target with a read call per [`install-contentstack-mcp`](install-contentstack-mcp.md). When supported tools are callable, the **CMA** steps here run as MCP tool calls with no pasted `authtoken`: step 8 CT-create (POST then PUT) becomes `create_a_content_type` plus `update_content_type`, step 4 environment-create becomes `create_an_environment`, and verify becomes `get_a_single_content_type`. The MCP does **not** cover the Studio API or tokens: steps **5 (enable Live Preview), 6 (delivery+preview token), 10 (`/v1/projects` register)**, and stack-create stay raw HTTP, authenticated with the same OAuth credential (`-H "$CS_AUTH"`), not a pasted session token. **Step 10 (`/v1/projects`) has no MCP tool, but use the OAuth token there (`Authorization: Bearer`). A session authtoken is the last rung only, per step 10's callout.** Org comes from the login. Read the stack `api_key` from the MCP registration ([`understand-contentstack-mcp`](understand-contentstack-mcp.md)) and confirm before asking. A missing readiness flag requires discovery; use HTTP only for unavailable operations or a recorded connection limitation.

2. **FIRST: does a Studio project already exist? List, then ASK. Never create blind.**

   This skill creates a project. Run it after an OAuth login without looking and you get a **duplicate project against the same stack**. Nothing errors, and from then on half the tooling points at one project and half at the other. The stack step below already reuses-or-creates. The project needs the same treatment, plus an explicit question, because "reuse" vs "new" is the user's call and not inferable.

   ```bash
   curl -s "https://<studio-api-host>/v1/projects" \
     -H "Authorization: Bearer <oauth-access-token>" \
     -H "organization_uid: <org-uid>" | jq -r \
     '.projects[] | "\(.uid)  \(.name)  stack=\(.connectedStackApiKey)  ct=\(.contentTypeUid)"'
   ```

   (Auth ladder + host map: step 10's callout. `organization_uid`, **not** a stack `api_key`. Projects are org-scoped.)

   | Result | What to do |
   |---|---|
   | **A project's `connectedStackApiKey` matches the target stack** | **Almost certainly the one they want.** Say so and default to reusing it: "Project `<name>` (`<uid>`) is already connected to this stack with `contentTypeUid: <ct>`. Reuse it, or create a second project against the same stack?" A second project on one stack is legal but rarely intended. It splits compositions across two projects |
   | **Projects exist, none on this stack** | Present the numbered list below and **ask**: reuse one (repointing it, see the warning at the end) or create new. Don't assume new just because the stack differs |
   | **No projects at all** | Proceed to create, and say that's what you're doing |
   | **`GET` fails** (401/422) | **Stop.** An auth failure is not evidence that no project exists. Resolve auth per step 10's ladder, then re-check |

   ### Present the list as a numbered choice: never ask for a project id

   **You already fetched every project in the org, uid included. Do not ask the user to find or paste a project id.** Show a numbered list and accept a number (or the name). You map the choice back to the `uid` yourself:

   ```
   Found 3 Studio projects in your organization:

     1. Visual Experience Showcase   ← already connected to this stack (compositions)
     2. Marketing Site               stack=blt9f3…  ct=compositions
     3. Docs Playground              stack=blt21c…  ct=doc_compositions

     4. Create a NEW project instead

   Reply with a number (1–4).
   ```

   Rules for the prompt: mark the one already connected to the target stack, always offer **"create new"** as an explicit numbered option so reuse is never the only path, and show `stack=` / `ct=` so the choice is informed. Accept a name if they type one instead of a number. Only ask for a raw uid if the `GET` itself failed and they're supplying it from the UI.

   ### If the user picks an existing project: what actually happens next

   Reusing changes the rest of this skill. It does not simply skip to the end.

   | Step | On reuse |
   |---|---|
   | **10: register the project** | **Skipped entirely.** The project exists. Do not POST `/v1/projects` |
   | **7: pick the compositions CT uid** | **No longer a free choice.** Adopt the project's existing `contentTypeUid` from the listing. Inventing a new uid here creates a second compositions CT that the project doesn't point at. The canvas then loads nothing while the CT sits there looking correct |
   | **8 / 9: create + verify the CT** | Verify first (step 9's `GET /v3/content_types/<uid>`). If it exists with the right field shape, skip the create. If it's missing or mis-shaped, fix it against the **adopted** uid |
   | **3 to 6: stack, Live Preview, environment, tokens** | Still run, still reuse-or-create. An existing project does **not** imply Live Preview is enabled or that a preview token exists. Those are stack-level and are the most common thing missing on a project someone created in the UI |
   | **11 to 12: publish + record metadata** | Unchanged |

   **Then hand the chosen `uid` + `contentTypeUid` to [`configure-studio`](configure-studio.md)**, which reads back Environment / Language / Canvas URL rather than assuming a UI-created project has them set. Record the decision so a later agent doesn't re-ask.

   **Don't repoint an existing project at a different stack casually.** If the user picks a project whose `connectedStackApiKey` is some other stack, say so and confirm before changing it. Every composition already authored there resolves against the old stack's content.

3. **Ensure the stack exists** (CMA). Either reuse via `GET /v3/stacks?organization_uid=<org>&query={"name":"…"}` or create via `POST /v3/stacks` (body: `{ stack: { name, description, master_locale: "en-us" } }`, plus header `organization_uid`). Capture `api_key`.

4. **Create the environment** (CMA) if it doesn't exist: `POST /v3/environments` with `{ environment: { name: "preview", urls: [{ locale: "en-us", url: "<canvas-app-url>" }] } }`. The environment URL must match where the host app renders (the canvas-app or visitor app). Save `environment.uid`. Studio's `/v1/projects` configuration takes the **uid, not the name**.

5. **Enable Live Preview on the stack** (CMA, critical, easy to miss). Read-modify-write: siblings like `visual_builder` must survive the write.
   ```
   GET  /v3/stacks/settings     (headers: api_key, $CS_AUTH)
   POST /v3/stacks/settings     (headers: api_key, $CS_AUTH)
   { "stack_settings": { ...existing,
       "live_preview": { ...existing.live_preview,
         "enabled": true, "default-env": "<environment uid>", "default-url": "<canvas-app-url>" } } }
   ```
   **Not `PUT /v3/stacks`.** It answers `200 Stack updated successfully` and silently discards the payload: wrong endpoint, wrong envelope, `enable` not `enabled`. Live Preview stays off, silently. Saving Visual Experience in the Contentstack UI issues this same `POST /v3/stacks/settings`, measured at `201`.

   `enabled: true` alone is rejected `422 error_code 150`, asking for a default URL and environment. That is why step 4 comes first: its uid goes in `default-env`.

   A `200` is not proof. Re-read and assert `live_preview.enabled`. Without it the canvas iframe hangs on "Loading composition…" because the canvas-app's calls to `rest-preview.contentstack.*` fail CORS preflight.

6. **Create the delivery token, then the preview token** (CMA). Two calls. `?create_with_preview_token=true` returns `token.preview_token` on the same call, measured at `201` with a 26-char `cs…` value. Query param only: in the body it is accepted and the token is silently absent. Either route works; assert the token is non-empty, because an empty one 401s every Preview call silently. Use the dedicated endpoint below:
   ```
   POST /v3/stacks/delivery_tokens
   { "token": { "name": "...", "scope": [
       { "module": "environment", "environments": ["<env-name>"], "acl": { "read": true } },
       { "module": "branch",      "branches":     ["main"],       "acl": { "read": true } }
   ] } }
   ```
   Then create the preview token from its own endpoint. Live Preview must already be enabled on the
   stack, or this call fails:
   ```
   POST /v3/stacks/delivery_tokens/<uid>/preview_token
   ```
   It returns `token.preview_token` (a `cs…` string). Capture both. If it comes back empty, stop rather
   than continue: an empty preview token 401s every Preview API call and the canvas fails with
   "Component Loading Error / API error (0)".

7. **Pick the compositions CT uid.** Convention: `<project>_compositions` (lowercase, underscored). Studio resolves the compositions CT by this uid.

8. **Create the compositions CT: two calls, not one.** CMA validates reference targets at creation time, so **`linked_sections`** (a self-reference) must be added on a follow-up PUT. In the initial POST it returns `error_code 115: linked_sections.reference_to: content type does not exist`. The CT can't reference itself before it exists.

   ```
   POST /v3/content_types    (body = every field in the table below EXCEPT linked_sections)
   PUT  /v3/content_types/<uid>    (body = every field including linked_sections)
   ```

   Every field is **required by the editor or runtime**. Do not drop, rename, or change cardinality.

### Compositions CT: required fields

| uid | data_type | mandatory | multiple | Required by | Purpose |
|---|---|---|---|---|---|
| `title` | text | yes | no | CMS UX | Author-visible title. Unique recommended. |
| `url` | text | no | no | Runtime | Composition URL pattern (e.g. `/products/{{entry.url}}`). Empty for freeform. |
| `composable_uid` | text | yes | no | Runtime + editor | Contract key: runtime queries compositions by `composable_uid`, NOT entry uid. Must be unique. |
| `ui_preview` | file | no | no | Editor | Thumbnail shown in Studio's composition list. |
| `connected_content_type` | text | no | no | Editor + runtime | The page CT uid this composition is connected to (Connected Template). Empty for Freeform. |
| `ui` | text (multiline) | no | no | Editor + runtime | `zlib:<base64>`-encoded composition node tree. Written by Studio canvas. Written by [`author-composition-via-api`](author-composition-via-api.md) for headless authoring. |
| `data_sources` | text (multiline) | no | no | Runtime | JSON object holding `resolvedReferences` etc. for reference resolution at render. |
| `static_value` | group | no | no | Editor | Static-value sub-bindings. See § static_value sub-schema below. Required as-is for the picker to enumerate static-value types. |
| `schema_version` | text | no | no | Editor | Composition schema version stamp written by Studio, a semver-shaped string like `"1.0.0"` (also seen: `""`, `"1"`, `"2"`). |
| `place_composition_as` | text | no | no | Editor | `"page"` for top-level template compositions (both Connected and Freeform). `"section"` for section compositions. `"template"` is legal but not what Studio writes for the top-level entry. |
| `linked_schemas` | **group, multiple=true** | no | yes | Editor | Per-section template-binding override. One entry per content type the section accepts. **Must be `group` with `multiple: true`**. The editor expects an array. Sub-fields on the group: `content_type_uid` (text, **required**), `selected_field` (text, **optional**, set when the section restricts to one field), `display_name` (text, **optional**) and `cardinality` (text, **optional**, `single` or `collection`). Runtime stored shape: `[{ "content_type_uid": "blog_post", "_metadata": { "uid": "<system-generated>" } }, …]`. If this is a single `group` (multiple=false) or a flat text field, editor crashes during section-context build. |
| `url_metadata` | group | no | no | Editor | `url_source` (text), `url_queries` (text). Drives the URL pattern editor. **Both sub-fields must exist.** If the group (or either sub-field) is missing, the CMA silently drops `url_metadata` on every composition write: 201 returned, field reads back absent, and every template composition falls back to `legacy_url` semantics with no error anywhere. See [`author-composition-via-api` § `url` + `url_metadata`, a matched pair](author-composition-entry.md#url-metadata-matched-pair). |
| `linked_sections` | **reference, multiple=true, reference_to: <same CT uid>** | no | yes | Editor | Self-reference to other composition entries that are templates this composition links. **Must be a reference field**. The editor's CDA call uses `?include[]=linked_sections`, which only works on reference fields. If modeled as text/group, the editor's Template Did Not Load error appears. |

### `static_value` sub-schema

Add a `group` field named `static_value` (multiple=false) with **13 sub-groups (each multiple=true)**, one per scalar binding type the picker offers. Each sub-group has a uniform `{ key: text, value: text }` shape, EXCEPT `boolean` (`value: boolean`) and `choice` (`value: text` but **`multiple: true`**: exposed choice props write an array like `["center"]`. A single-value `choice.value` rejects the write with "should be a single value instead of multiple"):

```
static_value (group)
├─ text        (group[]) { key: text, value: text (multiline) }
├─ html_rte    (group[]) { key: text, value: text (multiline) }
├─ array       (group[]) { key: text, value: text (multiline) }
├─ object      (group[]) { key: text, value: text (multiline) }
├─ number      (group[]) { key: text, value: text (multiline) }
├─ href        (group[]) { key: text, value: text (multiline) }
├─ textarea    (group[]) { key: text, value: text (multiline) }
├─ any         (group[]) { key: text, value: text (multiline) }
├─ json_rte    (group[]) { key: text, value: text (multiline) }
├─ datestring  (group[]) { key: text, value: text (multiline) }
├─ boolean     (group[]) { key: text, value: boolean }
├─ imageurl    (group[]) { key: text, value: text (multiline) }
└─ choice      (group[]) { key: text, value: text (multiline, **multiple: true**) }
```

The picker's "Static Value" branch enumerates these sub-groups by uid. Missing sub-groups produce missing options in the picker.

9. **Verify the CT exists.** `GET /v3/content_types/<uid>` and confirm the field list matches the table above. Catch shape errors early. Fixing a wrong cardinality after entries exist requires deleting and re-creating the CT.

10. **Register the Studio project** (Studio API). Two calls.

   > **Auth for `/v1/projects`: try OAuth FIRST. A session authtoken is the last resort.** Work down this ladder and stop at the first that succeeds:
   >
   > 1. **`Authorization: Bearer <oauth-access-token>`**, from `install-contentstack-mcp`'s `--auth`, or `csdx --oauth`. **Runtime-confirmed:** `GET /v1/projects` with this token plus an `organization_uid` header returns **200** and the project list. **Always attempt this before asking for anything else**. Pair it with `organization_uid`, not a stack `api_key`, because projects are org-scoped.
   > 2. **Create the project in the Studio UI**, no token at all, and it onboards the stack in the same action.
   > 3. **Session authtoken**, only after `Authorization: Bearer <oauth>` with the `organization_uid` header still fails with a **freshly refreshed** token, and only after explaining the risk below. A 401 `error_code 105` from sending OAuth in the `authtoken:` header, or a 422 `error_code 21` "Stack not found" (wrong scope header), is a request bug: fix the request, don't escalate. (A management token as `authtoken:` returns **401 "not logged in"**, never the right credential here.)
   >
   > **A session authtoken is a full user-session credential**: every org, every stack, every permission that user holds, valid until the session ends. Pasting it leaves copies in shell history, logs and process lists. Don't request one speculatively: attempt OAuth, read the response, and only then escalate. If you do use one, scope it to this single call and discard it. Don't write it to `.env`.
   >
   > Sending the OAuth token in the wrong header is itself a 401 (`error_code 105`): OAuth goes in `Authorization: Bearer`, `authtoken:` is for session tokens only. Branch on the response rather than assuming. See `install-contentstack-mcp` § What it does, and does NOT do.

   ```
   POST  https://<studio-api-host>/v1/projects     (headers: organization_uid, $CS_AUTH — OAuth Bearer)
   {
     "name": "<Project Name>",
     "description": "...",
     "connectedStackApiKey": "<stack api_key from step 3>",
     "contentTypeUid":       "<compositions CT uid from step 7>",
     "canvasUrl":            "/canvas"   // route on the canvas-app that mounts <StudioCanvas/>
   }
   ```

   Then configure it (this is where environment + locale + Freeform attach):

   ```
   PUT https://<studio-api-host>/v1/projects/<projectUid>
   {
     "name": "<Project Name>",
     "canvasUrl": "/canvas",
     "connectedStackApiKey": "<api_key>",
     "contentTypeUid":       "<compositions CT uid>",
     "settings": {
       "configuration": { "environment": "<env UID from step 4>", "locale": "en-us" },
       "isFreeformEnabled": true
     }
   }
   ```

   The `environment` value MUST be the env **uid** (looked up via `GET /v3/environments`), not the name. The Studio API regional hosts mirror the CMA: `eu-composable-studio-api.contentstack.com`, `azure-na-composable-studio-api.contentstack.com`, `azure-eu-composable-studio-api.contentstack.com`.

11. **Publish at least one composition entry** to the chosen environment before testing rendering. Unpublished compositions return 404 from the CDA, presenting as a blank canvas or "Composition Not Found." See [`author-composition-via-api`](author-composition-via-api.md) § Publish for the publish call.

12. **Record the project metadata** so [`install-studio`](install-studio.md) can wire the host app consistently. `.env.example` gets the variable **names** with placeholder values only (e.g. `CONTENTSTACK_PREVIEW_TOKEN=<preview-token>`), never real values. The real values (CT uid, environment, delivery token, preview token, Studio project uid, branch) go only in the gitignored `.env` / `.env.local`. Don't print the tokens.

## Acceptance

- [ ] Live Preview enabled: `GET /v3/stacks/settings` returns `stack_settings.live_preview.enabled === true`.
- [ ] Environment exists. Delivery token + preview token captured.
- [ ] `GET /v1/projects` lists the project with `connectedStackApiKey === <stack api_key>` and the right `contentTypeUid`.
- [ ] `GET /v3/content_types/<uid>` returns all 13 fields from the table with exact `data_type`, `mandatory`, `multiple`.
- [ ] `linked_schemas` is `group` with `multiple: true`. (Single-group is the most common provisioning bug, re-check.)
- [ ] `linked_sections` is `reference` with `multiple: true` and `reference_to: [<this CT uid>]`.
- [ ] `composable_uid` is mandatory + unique.
- [ ] `static_value` group contains all 13 sub-groups with correct shape.
- [ ] One composition entry exists and is published. CDA `GET /v3/content_types/<uid>/entries?query={"composable_uid":"<your-uid>"}&environment=<env>` returns it.
- [ ] Preview token is set on the environment. `?live_preview=<hash>` flows through `sdk.fetchCompositionData`.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Naming a group sub-field `uid` | The CMA rejects the whole `PUT` with `422 schema.N.schema.0.uid: "has a restricted value 'uid', which is not allowed"`. Easy to hit on `linked_schemas`, where the natural guess for the content-type key is `uid` | The sub-field is **`content_type_uid`**, never `uid`. See the `linked_schemas` row above. `uid` is reserved by the CMA inside groups |
| `linked_schemas` modelled as `group` with `multiple: false` | Editor expects an array. Section-context build crashes on `.map` of a single object | Re-create CT with `multiple: true`. Or PATCH the CT field if no entries exist yet |
| `linked_sections` modelled as text/group instead of reference | Editor's `?include[]=linked_sections` returns nothing. Template Did Not Load on canvas open | Must be `reference` field with `reference_to: [<same CT uid>]`. See [`troubleshoot-canvas`](troubleshoot-canvas.md) Template-Did-Not-Load row |
| `composable_uid` left non-unique | Runtime lookup picks an arbitrary entry. One composition renders for many URLs | Mark mandatory + unique at CT creation time |
| Forgetting `static_value` sub-groups | Picker's Static Value root shows fewer (or zero) type options | Add the 13 sub-groups exactly as schema'd above |
| Composition entry not published | CDA returns 404. Canvas blank | Publish to the environment after entry create |
| Preview token missing / set to literal `"undefined"` | Canvas iframe gets HTTP 401 with no CORS headers, "Component Loading Error" | See [`troubleshoot-canvas`](troubleshoot-canvas.md) preview-token row |
| JSON-RTE static values fail to embed correctly | JSON-RTE embeds carry `attrs.locale`, missing in API-authored payloads | Set `attrs.locale` on every embedded entry/asset in `static_value.json_rte[*].value` |
| Wrong region host | CT creation 404s | Use the region-specific CMA and Studio API hosts (Step 10) |
| Live Preview not enabled on stack | Canvas iframe hangs on "Loading composition…". Rest-preview CORS preflight fails | `POST /v3/stacks/settings` with `live_preview.enabled`, `default-env` and `default-url` (step 5). `PUT /v3/stacks` answers `200` and changes nothing |
| Studio project configured with environment **name** instead of **uid** | Studio API accepts the PUT but environment binding silently misses. Compositions never resolve | Look up env uid via `GET /v3/environments`, pass `settings.configuration.environment = <uid>` |
| Re-using a Studio project across stacks (name match, stale `connectedStackApiKey`) | Project surfaces last stack's compositions. Current stack invisible in canvas | On every provision, `GET` the project and compare its `connectedStackApiKey` with the current stack. If it differs, show the user the before/after and get approval, then PUT to re-bind |
| Mixed CMA + Studio API hosts (e.g. NA Studio API with EU CMA) | 401/404s with no clear error | Pick a region and use BOTH region-matched hosts |
| Including `linked_sections` in the initial `POST /v3/content_types` | `error_code 115: linked_sections.reference_to: content type does not exist`. CMA validates reference targets at create time. A CT can't self-reference before it exists | Two-step: POST without `linked_sections`, then PUT with the full schema (step 8) |
| Delivery-token scope trimmed to environment-only (branch scope dropped) | `"Delivery Token creation failed. Please try again."` (no HTTP error code, no field diagnostic) a natural "simplification" of the step 6 body silently fails | Both scope entries are REQUIRED: `{ module: "environment", ... }` AND `{ module: "branch", branches: ["main"], acl: { read: true } }`. Keep the two-entry body from step 6 verbatim |
| `PUT /v3/environments/<uid>` to update an environment (using the UID in the path) | `error_code 248: could not find environment`. This CMA endpoint keys on env **name** in the path, not UID | Use the env name: `PUT /v3/environments/preview`. Studio `/v1/projects` config (step 10) instead takes the env UID from step 4 |
| Creating the stack (`POST /v3/stacks`) in an org where the user lacks stack-create rights | **HTTP 403, `error_code 316`, `"You don't have the permission to do this operation."`** (verified), a bare 403, no field diagnostic | Don't crash. Tell the user: get stack-create rights in the org, OR switch to an org where they can (re-auth if using the MCP: there's no org-picker, switch the active org first), OR reuse an existing stack. `--auth` captures the active org, so switching active org before login targets the right one |

## See also

- [`author-composition-via-api`](author-composition-via-api.md): create composition entries against this CT.
- [`provision-studio-stack`](provision-studio-stack.md): assets + page CTs the compositions reference.
- [`install-studio`](install-studio.md): host-app wiring + env vars.
- [`troubleshoot-canvas`](troubleshoot-canvas.md): preview token, linked_sections, blank canvas symptoms.
