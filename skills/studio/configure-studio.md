---
name: configure-studio
---

## When to use

Configure a Studio project's Environment, Language, and Canvas URL in one guided pass, replacing manual clicking through the Studio settings panels.

Use right after `provision-studio-project` (or manual project creation) to go from "empty Studio project" to "ready to author". Phrases: "configure Studio project", "set canvas URL", "change environment". Do NOT use to register components (use `register-component`) or wire preview routes (use `setup-template-preview-routes`).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Configure a Studio project

## Context

Every Studio project has three configuration knobs that must be set before authoring is useful:

1. **Environment**: which Contentstack environment the project's compositions resolve content against (the `?environment=` on every CDA call).
2. **Language**: default locale code (e.g. `en-us`). Studio's UI calls this "Language". The API and SDKs call it "locale", same thing.
3. **Canvas URL**: the **path** on your site that mounts `<StudioCanvas />` (e.g. `/canvas`, `/studio-canvas`). Studio builds the iframe address as **Base URL + Canvas URL**, where the Base URL (the origin) is resolved from the Environment + Language above. This field holds **only the path**, never the origin.

To reach all three in Studio, open your project, go to Settings, and open Configuration. They can be edited individually any time, but a new project starts with all three blank and the user can't author until they're set.

### Where the "compositions content type UID" comes from

Studio installs a content type into your stack the first time a project is provisioned. That content type is where every composition lives as an entry. Its UID defaults to `compositions` but can be any UID the provisioning step chose.

To find the exact UID for THIS project:

- **Studio web app:** open the project, go to Settings, then Configuration, and read the "Composition Content Type" field (it shows the UID).
- **Contentstack web app:** open Content Models and look for a content type with the description "Studio compositions" (or similar). The UID column is what you want.
- **API:** `GET /v3/content_types?query={"_metadata.studio_managed":true}` returns the compositions content type. Its `uid` is the value.

Pass this UID to `studioSdk.init({ contentTypeUid: "<uid>" })` in your app's `lib/contentstack.ts` (the `install-studio` skill writes it from the `studioContentTypeUid` input). **This is the SDK-init `contentTypeUid`, NOT `templateContentTypeUid`, which identifies a composition's CONNECTED content type at fetch time.**

## Task

<a id="select-the-studio-project"></a>

0. **Select the Studio project first: list them, never assume.** An org routinely has several, and picking the wrong one is silent: the compositions list and Sections panel come up **empty** with no error, which reads as a broken install rather than a wrong project. This step is also what supplies `studioProjectId` to every downstream skill (`setup-section-preview`, `migrate-page-to-studio`, `troubleshoot-canvas`, `figma-generate-components`).

   **List the projects** (OAuth first, see [`provision-studio-project`](provision-studio-project.md) step 10 for the auth ladder):

   ```bash
   curl -s "https://<studio-api-host>/v1/projects" \
     -H "Authorization: Bearer <oauth-access-token>" \
     -H "organization_uid: <org-uid>" | jq -r \
     '.projects[] | "\(.uid)  \(.name)  stack=\(.connectedStackApiKey)  ct=\(.contentTypeUid)"'
   ```

   `<studio-api-host>` is `composable-studio-api.contentstack.com` (+ regional variants). Custom / private data center (hosts supplied by Contentstack): set every host explicitly; see [`install-studio`](install-studio.md) § Custom / private data center.

   **Two token-free alternatives (prefer these over asking for a credential):**

   > **OAuth Bearer is confirmed working for the Studio API on prod.** Runtime-verified: `GET /v1/projects` on `composable-studio-api.contentstack.com` with `Authorization: Bearer <oauth-access-token>` + `organization_uid` returned **200** with the project list, using a token minted by the Contentstack MCP's `--auth` flow. The ladder in [`provision-studio-project`](provision-studio-project.md) step 10 therefore resolves at its **first** rung on prod, no session authtoken needed.

   - **`csdx` (Studio plugin): use `project:set`, not `project:get`.** Source-verified in `@contentstack/studio` 0.0.3, and the two commands are not equivalent:

     | Command | Hits the API? | Use it for |
     |---|---|---|
     | `studio:project:get` | **No.** Reads the cached `projectId`. `projectDetails` is hardcoded `null` behind a "Fetching project information..." spinner | Seeing what this machine last selected, nothing more. It cannot tell you the project still exists or belongs to the right stack |
     | `studio:project:set --project-id=<id>` | **Yes**: `fetchProjects()` calls `GET {base}/projects`, then `projects.find(p => p.uid === id)` | **Validating** a project id against your org, and switching to it |

     **Enumeration trick: `project:set` prints the list when the id is wrong.** On a miss it reports `Project with ID '<id>' not found in your organization`, then prints every available project as `• <name> (<uid>)`. So a deliberately-invalid id lists them without any manual token handling:

     ```bash
     csdx studio:project:set --project-id=list-them-please   # invalid on purpose
     ```

     **Both require OAuth**, not a session login: the plugin reads `oauthAccessToken` and `oauthOrgUid` from CLI config and sends `Authorization: Bearer <token>` + `organization_uid`. Absent those, it can't fetch. Run `csdx auth:login --oauth` first. (This is also independent corroboration for the auth ladder in [`provision-studio-project`](provision-studio-project.md) step 10. The shipped plugin authenticates the Studio API with an OAuth Bearer token, and scopes by **org**, not by stack api_key.)

     **Do not take `project:get` as confirmation of anything.** It succeeds on a machine with no OAuth token at all, because it never authenticates, which is exactly how a stale or wrong cached id survives unnoticed.

     **Runtime-verified, and worse than it sounds: the cached id survives a region switch.** On a machine moved from one data center to another (here, to NA), `project:get` kept reporting a project id belonging to the **old data center**, while the org's live list (`GET /v1/projects`, 200) held a completely different single project. Nothing warned. The id simply looked plausible. **A cached id can point at a project in another DC entirely**, which is why the cross-check below compares against the live list, not against what the CLI remembers.

     **The plugin needs a region name the CLI core does not store.** Both of its lookups (`getComposableApiUrl()` and `getComposableApiBase()`) do `configHandler.get("region").name.toUpperCase()` against maps keyed with an **`AWS-` prefix**. The CLI core stores the short names, which aren't keys, so the plugin throws a **"Region not configured"** error naming `csdx config:set:region` even though `csdx config:get:region` reports the region correctly. <!-- style-lint: allow -->

     | `csdx config:set:region` stores | Plugin needs | Works by default? |
     |---|---|---|
     | `NA` | **`AWS-NA`** | **No**, set the prefixed name |
     | `EU` | **`AWS-EU`** | **No**, set the prefixed name |
     | `AU` | **`AWS-AU`** | **No**, set the prefixed name |
     | `AZURE-NA` / `AZURE-EU` | same | Yes |
     | `GCP-NA` / `GCP-EU` | same | Yes |
     | a custom region name | that name, uppercased | Yes |

     Runtime-verified on prod: `config:set:region NA` makes the plugin fail. `config:set:region AWS-NA` makes it return the project. Only the three AWS short names need translating.

     **The two failures are distinguishable. Use them to tell which layer is broken.** Runtime-verified on prod:

     | Symptom from `studio:project:set` | Means |
     |---|---|
     | `Region not configured…` | Region **name** is wrong (a short name like `NA`). No request was sent |
     | `You are not logged in…` followed by `Failed to fetch projects: Unauthorized` | Region name is **correct**. The host resolved and the request went out. Missing OAuth token. Run `csdx auth:login --oauth` |

     Reaching `Unauthorized` is therefore progress, not a regression: it proves the region maps to a real Studio API host.

     **Two traps that make this hard to diagnose:**
     - Re-running `config:set:region` with the same short name cannot fix it. The message asks for the exact action that just failed.
     - `config:set:region` prints a correct `Studio URL:` line, which looks like proof the Studio host is configured. The plugin never reads that value. It re-derives from its own map. A correct-looking Studio URL and a broken plugin coexist happily.
   - **Studio UI**: the top-bar project switcher lists everything the user can reach.

   **Branch on the count:**

   | Projects found | What to do |
   |---|---|
   | **0** | Nothing to configure. Run [`provision-studio-project`](provision-studio-project.md) to create one, then return here. It re-checks and asks before creating, so it won't duplicate if a project appears in the meantime |
   | **1** | Use it, but **state which one** ("Using project `<name>` (`<uid>`), stack `<api_key>`"). Don't switch silently |
   | **2 or more** | **STOP and ask.** Print a numbered list with name, uid, connected stack and compositions CT, and let the user pick **by number**. You already have every uid from the listing, so never make them find or paste one. Never guess from a name resembling the repo |

   **Flag any mismatch before proceeding.** Compare the chosen project's `connectedStackApiKey` against the stack the app actually initializes (from `.env` or `.env.local`). If they differ, say so and stop. That mismatch is the cause of the "empty compositions list" and **HTTP 412** symptoms in [`troubleshoot-canvas`](troubleshoot-canvas.md), and configuring the wrong project just moves the problem. Same for `contentTypeUid`: it must match the compositions CT the app reads.

   **Record the chosen `uid`** and reuse it for the rest of the session rather than re-asking.

**By API instead:** `GET /v1/projects/<uid>` first, show the user the current settings next to the ones you will write, and get approval; then `PUT /v1/projects/<uid>` (PATCH returns 404) with `settings.configuration.environment` set to the environment's **uid** from `GET /v3/environments`, never its name. A name saves, but Studio shows no environment and the canvas falls back to Studio's default host.

1. **Open Studio at the selected project**, then go to Settings, then Configuration. Verify the settings panel is visible (Environment / Language / Canvas URL).

2. **Set Environment.** Dropdown shows every environment from the stack. Pick the value matching `environment`. If not present, the environment doesn't exist in the stack. Stop and tell the user to create the environment first, in the stack under Settings, then Environments.

3. **Set Language.** Dropdown shows every locale enabled on the stack. Pick `defaultLanguage`. If not present, enable the locale in the stack, under Settings, then Languages.

4. **Set Canvas URL** to `canvasUrl`. This is the **path** Studio appends to the Base URL when loading its iframe. Enter the path only, not a full origin. Common values:
   - Any environment: `/canvas` or `/studio-canvas`, must match the route in the app that mounts `<StudioCanvas />`. The same value works for local dev and deployed. The origin differs but comes from the Base URL, not this field.
   - Studio-hosted playground: leave blank to fall back to Playground Canvas (no canvas-app needed. Deploy is disabled in this mode)

5. **Save.** Studio's Save button grays out post-save. That's the confirmation.

6. **Read back the settings** via the Studio UI to confirm the writes. The Configuration panel should show the three values exactly as set.

7. **By API, the body shape:** after showing the before/after values and getting the user's approval, send it flat, `{ canvasUrl, settings: { configuration: { environment, locale } } }`. A `{ "project": … }` wrapper returns 200 and saves nothing. Read the project back to confirm.

## Inputs needed from the user

In order:

1. `studioProjectId` / `projectName`: **resolved by Step 0, not asked for blind.** List the org's projects: with one, confirm which. With two or more, the user picks. With none, provision one first.
2. `environment`: must match an existing stack environment. Reject if not.
3. `defaultLanguage`: must match an existing stack locale. Reject if not.
4. `canvasUrl`: the path that mounts `<StudioCanvas />` (e.g. `/canvas`). Confirm it matches the canvas route in the app. Reject full origins like `http://localhost:5173/studio-canvas` and strip them to the path. A separate `verify-setup` call confirms the canvas actually loads.
Do NOT assume defaults silently for Environment / Language. These are stack-specific and wrong defaults strand the user.

## Acceptance

- [ ] **The project was selected from an actual list, and the choice was stated back.** With 2+ projects the user picked. With exactly 1 it was named rather than silently assumed. The chosen project's `connectedStackApiKey` matches the stack the app initializes, and its `contentTypeUid` matches the compositions CT the app reads. A mismatch was surfaced, not configured around.

This skill succeeds only when ALL of the following are true.

- [ ] Environment is set to `environment` and the value matches a stack environment.
- [ ] Language is set to `defaultLanguage` and the value matches a stack locale.
- [ ] Canvas URL is set to `canvasUrl` (or explicitly left blank for Playground Canvas).
- [ ] All three values are read back from the Studio UI to verify the write took.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Setting Environment to a value that doesn't exist on the stack | CDA calls return 422. Canvas renders empty | Verify the environment in the stack, under Settings, then Environments, before configuring |
| Empty per-locale Base URL on the targeted environment | Studio can't compose the canvas iframe address (origin + path). It blocks the Canvas URL save and the canvas stays blank | Set the targeted environment's per-locale URL first: in the stack, open Settings, then Environments, then `<env>`, and set the URL for `<locale>` (your dev origin for local dev). See `setup-section-preview`. |
| Only the default locale has a Base URL on a localized project | Language here is one value, but authors switch locale in the canvas. Every locale without a Base URL goes blank the moment they do, with an error pointing at the Studio project | Set a Base URL for **every** locale the app serves (with the app's prefix if it uses one). [`convert-project-to-studio`](convert-project-to-studio.md) § Step 3 maps and writes them. |
| Pasting a full origin into Canvas URL (e.g. `http://localhost:5173/studio-canvas` or `https://yoursite.com`) | Canvas URL is the **path only**. Studio prepends the Base URL (origin) itself. A full URL here produces a broken iframe address (origin duplicated or wrong path). | Enter just the path: `/canvas` or `/studio-canvas`. The origin comes from Environment + Language (the Base URL), not this field. |
| Saying "Language" everywhere when the codebase says "locale" | User searches for "Language" in SDK / API docs and finds nothing | Note explicitly: UI label is "Language". SDK + API call it "locale". Same field. |
| Setting a Canvas URL that points to a host that isn't running | Canvas loads forever. Spinner never resolves | Pair with `verify-setup` after configuring. If Layer 4 fails on a freshly set Canvas URL, the host isn't running |
| **Running two Studio projects on the same stack against different local apps**: switching to project A breaks preview for project B (and vice versa) | The env Base URL is a **stack-level** resource (set on the environment via `urls: [{ locale, url }]`, see [`provision-studio-project`](provision-studio-project.md) step 4), not a per-project setting. Multiple Studio projects on one stack **share that single Base URL**. Project A pointing at `http://localhost:5192` and project B at `http://localhost:3000` cannot coexist on the same environment. Only one can be the active iframe origin at a time. Connected-template canvas preview loads at this shared URL, so whichever project was last configured wins. | Pick ONE of: (a) **separate environment per project** (in the stack, open Settings, then Environments, and create `<project>_preview` for each project, pointing each at its own port. Set each Studio project's Environment to its dedicated env in `configure-studio` step 2), (b) **separate stack per project** (cleanest isolation, but more provisioning overhead), (c) **manual Base URL swap** when switching projects (edit the env's per-locale URL in Stack settings each time, only viable if you switch infrequently). Option (a) is the recommended default. |

## See also

- `verify-setup`: run after this skill to confirm canvas loads
- `setup-template-preview-routes`: wire `/blog/:slug` style routes (separate from Canvas URL)
