# configure-studio


## When to use

Configure a Studio project's Environment, Language, and Canvas URL in one guided pass — replacing manual clicking through the Studio settings panels.

Use right after `seed-studio-project` (or manual project creation) to go from "empty Studio project" to "ready to author". Phrases — "configure Studio project", "set canvas URL", "change environment". Do NOT use to register components (use `register-component`) or wire preview routes (use `setup-template-preview-routes`).

# Configure a Studio project

## Context

Every Studio project has three configuration knobs that must be set before authoring is useful:

1. **Environment** — which Contentstack environment the project's compositions resolve content against (the `?environment=` on every CDA call).
2. **Language** — default locale code (e.g. `en-us`). Studio's UI calls this "Language"; the API and SDKs call it "locale" — same thing.
3. **Canvas URL** — the **path** on your site that mounts `<StudioCanvas />` (e.g. `/canvas`, `/studio-canvas`). Studio builds the iframe address as **Base URL + Canvas URL**, where the Base URL (the origin) is resolved from the Environment + Language above. This field holds **only the path**, never the origin.

Each lives in Studio → Project → Settings → Configuration. They can be edited individually any time, but a new project starts with all three blank and the user can't author until they're set.

### Where the "compositions content type UID" comes from

Studio installs a content type into your stack the first time a project is provisioned — that content type is where every composition lives as an entry. Its UID defaults to `compositions` but can be any UID the provisioning step chose.

To find the exact UID for THIS project:

- **Studio web app:** Project → Settings → Configuration → "Composition Content Type" field (shows the UID).
- **Contentstack web app:** Content Models → look for a content type with the description "Studio compositions" (or similar). The UID column is what you want.
- **API:** `GET /v3/content_types?query={"_metadata.studio_managed":true}` returns the compositions content type; its `uid` is the value.

Pass this UID to `studioSdk.init({ contentTypeUid: "<uid>" })` in your app's `lib/contentstack.ts` (the `install-studio` skill writes it from the `studioContentTypeUid` input). **This is the SDK-init `contentTypeUid` — NOT `templateContentTypeUid`, which identifies a composition's CONNECTED content type at fetch time.** See `<StudioComponent />` reference for the full distinction.

Reference: `docs/10-setup/studio-project/configure-environment-language-and-canvas-url.md`, `docs/30-composition/canvas-url.md`.

## Task

1. **Open Studio at the supplied `projectName`** → Settings → Configuration. Verify the settings panel is visible (Environment / Language / Canvas URL).

2. **Set Environment.** Dropdown shows every environment from the stack. Pick the value matching `environment`. If not present, the environment doesn't exist in the stack — stop and tell the user to create the environment in Stack → Settings → Environments first.

3. **Set Language.** Dropdown shows every locale enabled on the stack. Pick `defaultLanguage`. If not present, enable the locale in Stack → Settings → Languages.

4. **Set Canvas URL** to `canvasUrl`. This is the **path** Studio appends to the Base URL when loading its iframe — enter the path only, not a full origin. Common values:
   - Any environment: `/canvas` or `/studio-canvas` — must match the route in the app that mounts `<StudioCanvas />`. The same value works for local dev and deployed; the origin differs but comes from the Base URL, not this field.
   - Studio-hosted playground: leave blank to fall back to Playground Canvas (no canvas-app needed; deploy is disabled in this mode — see `docs/10-setup/studio-project/try-studio-in-the-playground-canvas-without-an-app.md`)

5. **Save.** Studio's Save button greys out post-save; that's the confirmation.

6. **Read back the settings** via the Studio UI to confirm the writes. The Configuration panel should show the three values exactly as set.

## Inputs needed from the user

In order:

1. `projectName` — locate the project. If the user has only one project, default to it but confirm.
2. `environment` — must match an existing stack environment; reject if not.
3. `defaultLanguage` — must match an existing stack locale; reject if not.
4. `canvasUrl` — the path that mounts `<StudioCanvas />` (e.g. `/canvas`). Confirm it matches the canvas route in the app; reject full origins like `http://localhost:5173/studio-canvas` and strip them to the path. A separate `verify-setup` call confirms the canvas actually loads.
Do NOT assume defaults silently for Environment / Language — these are stack-specific and wrong defaults strand the user.

## Acceptance

This skill succeeds only when ALL of the following are true.

- [ ] Environment is set to `environment` and the value matches a stack environment.
- [ ] Language is set to `defaultLanguage` and the value matches a stack locale.
- [ ] Canvas URL is set to `canvasUrl` (or explicitly left blank for Playground Canvas).
- [ ] All three values are read back from the Studio UI to verify the write took.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Setting Environment to a value that doesn't exist on the stack | CDA calls return 422; canvas renders empty | Verify the environment in Stack → Settings → Environments before configuring |
| Empty per-locale Base URL on the targeted environment | Studio can't compose the canvas iframe address (origin + path); it blocks the Canvas URL save and the canvas stays blank | Set the targeted environment's per-locale URL first at Stack → Settings → Environments → `<env>` → URL for `<locale>` (= your dev origin for local dev). See `setup-section-preview`. |
| Pasting a full origin into Canvas URL (e.g. `http://localhost:5173/studio-canvas` or `https://yoursite.com`) | Canvas URL is the **path only**; Studio prepends the Base URL (origin) itself. A full URL here produces a broken iframe address (origin duplicated or wrong path). | Enter just the path — `/canvas` or `/studio-canvas`. The origin comes from Environment + Language (the Base URL), not this field. |
| Saying "Language" everywhere when the codebase says "locale" | User searches for "Language" in SDK / API docs and finds nothing | Note explicitly: UI label is "Language"; SDK + API call it "locale". Same field. |
| Setting a Canvas URL that points to a host that isn't running | Canvas loads forever; spinner never resolves | Pair with `verify-setup` after configuring; if Layer 4 fails on a freshly set Canvas URL, the host isn't running |
| **Running two Studio projects on the same stack against different local apps** — switching to project A breaks preview for project B (and vice versa) | The env Base URL is a **stack-level** resource (set on the environment via `urls: [{ locale, url }]` — see `provision.ts`), not a per-project setting. Multiple Studio projects on one stack **share that single Base URL**. Project A pointing at `http://localhost:5192` and project B at `http://localhost:3000` cannot coexist on the same environment — only one can be the active iframe origin at a time. Connected-template canvas preview loads at this shared URL, so whichever project was last configured wins. | Pick ONE of: (a) **separate environment per project** (Stack → Settings → Environments → create `<project>_preview` for each project, point each at its own port; set each Studio project's Environment to its dedicated env in `configure-studio` step 2); (b) **separate stack per project** (cleanest isolation, but more provisioning overhead); (c) **manual Base URL swap** when switching projects (edit the env's per-locale URL in Stack settings each time — only viable if you switch infrequently). Option (a) is the recommended default. |

## See also

- `docs/10-setup/studio-project/configure-environment-language-and-canvas-url.md` — the canonical reference
- `docs/30-composition/canvas-url.md` — what Canvas URL is for
- `docs/10-setup/studio-project/try-studio-in-the-playground-canvas-without-an-app.md` — Studio-hosted canvas (no canvas-app needed; deploy disabled)
- `verify-setup` — run after this skill to confirm canvas loads
- `setup-template-preview-routes` — wire `/blog/:slug` style routes (separate from Canvas URL)
