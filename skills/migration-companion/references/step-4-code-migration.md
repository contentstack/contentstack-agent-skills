# Step 4 — Code Migration (detailed procedure)

> **When to read:** Before running Step 4. Contains sub-steps 4.1–4.4: input collection (repoPath, mapper, metadata credentials), logging, the SDK reference pointer, and the detect → plan → migrate → verify procedure. This file is part of the [migration-companion skill](../SKILL.md); `<SKILL_DIR>` refers to that skill's install directory.

### 4.1 — Collect inputs

**`repoPath`** — local file system path to the application to migrate.
Ask the user:

> "What is the local path to the codebase you want to migrate? (e.g. `/Users/you/projects/my-app`)"
> If it's a remote git repo, clone it first:
>
> ```bash
> cd "<SESSION_DIR>" && git clone <REPO_URL>
> ```
>
> Then use the cloned directory as `repoPath`.

**`mapperPath`** — the field-mapping JSON produced by Step 3 (the `MAPPER_PATH` recorded there). Confirm it exists:

```bash
ls -lh "<MAPPER_PATH>"
```

If the file is at a different path (e.g. the user used a custom workspace), ask them to confirm
the exact path.

Read `mapperPath` with the Read tool and extract the `fieldMapping` arrays from each content type
to build the Contentful-field-UID → Contentstack-field-UID table. Present the extracted table to
the user for confirmation before proceeding.

**`metadataPath`** — the credentials JSON written by Step 3's import (the `METADATA_PATH` recorded there). Confirm it exists and read it:

```bash
ls -lh "<METADATA_PATH>"
```

Read `metadataPath` with the Read tool. It supplies the new stack's Delivery SDK credentials so
you **do not have to ask the user for them**:

| metadata.json key | Use as              | Notes                                               |
| ----------------- | ------------------- | --------------------------------------------------- |
| `stack_api_key`   | `CS_API_KEY`        | the `blt…` **Stack API Key** — **not** `stack_id`   |
| `delivery_token`  | `CS_DELIVERY_TOKEN` | for the published-content SDK                       |
| `preview_token`   | `CS_PREVIEW_TOKEN`  | only if the app uses Live Preview (§18)             |
| `environment`     | `CS_ENVIRONMENT`    | e.g. `production`                                   |
| `stack_id`        | (stack UID)         | identifier only — do **not** use as the SDK api key |

`CS_REGION` (e.g. `AWS-NA`) is the `REGION` recorded from the final summary box in Step 3. Treat
the tokens as secrets — never echo them back or write them into files in this workspace; only set
them in the migrated app's local `.env` (which should be gitignored). If `metadata.json` is
missing, do not ask the user to paste credentials into the chat: ask them to put `CS_API_KEY`,
`CS_DELIVERY_TOKEN` and `CS_ENVIRONMENT` into the app's gitignored `.env` themselves and confirm
when done. Never ask for, echo or log the values.

### 4.2 — Logging

Resolve `<SKILL_DIR>` (see the "Bundled scripts & references" operating principle) — the
directory this skill is installed in — and write it as a literal into every command below, like
the other placeholders.

From the first action in this step, record everything to the session log by running
`SESSION_DIR="<SESSION_DIR>" bash "<SKILL_DIR>/scripts/log.sh" …` (shown below as `log.sh`):

- `log.sh <target> user-input "<what the user asked/answered>"` — every user input/communication.
- `log.sh <target> decision "<detection results, choices, assumptions, guessed UIDs>"`.
- `log.sh <target> ai-action "<files/queries you changed>"` and `communication "<what you told the user>"`.
- `log.sh <target> exception "<any error, blocker, or uncertainty you hit>"` — log all exceptions.
- Run shell commands through it so output + exit codes are captured and failures auto-log as
  exceptions: `log.sh <target> run "typecheck" -- npx --no-install tsc --noEmit`.

End with `log.sh <target> summary`. With `SESSION_DIR` set, the log lands in
`<SESSION_DIR>/migration-log/` (`session.log` + `session.jsonl` + per-command output), outside the
user's repo. Without it, `log.sh` falls back to `<target>/.migration/`; in that case confirm with
the user and add `.migration/` to the app's `.gitignore` so the log is never committed. See `"<SKILL_DIR>/scripts/README.md"`.

### 4.3 — Reference (read first)

The complete, source-verified mapping for every API, response shape, query operator, rich-text
renderer, asset transform, GraphQL query, and Live Preview API lives in:

**`<SKILL_DIR>/references/CONTENTFUL_TO_CONTENTSTACK_MIGRATION_CONTEXT.md`** (read it with the
Read tool from this skill's install dir — see the `<SKILL_DIR>` operating principle)

Read it in full before doing anything. It is the single source of truth — follow it; do not rely
on prior knowledge where the doc is specific. Key map:

- §0.1 — detect the data-access approach (decision table)
- §1–§16 — REST Delivery SDK (`@contentstack/delivery-sdk`) mapping
- §17 — GraphQL Content API migration
- §18 — Live Preview / draft mode migration
- §19 — raw REST / `fetch` and framework source plugins
- §13 gotchas, §15 checklist

### 4.4 — Procedure

1. **DETECT (doc §0.1).** Determine the app's language, framework, and which data-access
   approach(es) it uses, plus whether it implements Live Preview / draft mode. Migrate in the SAME
   language and framework, preserving the SAME approach (REST→REST, GraphQL→GraphQL, preview→preview).
   Report findings and PAUSE for confirmation.

2. **PREREQUISITES.** Confirm the target Contentstack stack already has the matching content model
   and published content, and confirm the Contentful-field-ID → Contentstack-field-UID map from
   step 4.1. If any UIDs are unknown, infer from a sample Contentstack entry and FLAG every guess.
   Confirm env vars (`CS_API_KEY`, `CS_DELIVERY_TOKEN`, `CS_ENVIRONMENT`, + `CS_REGION`/branch, +
   preview token if Live Preview) — these come from `metadataPath` (step 4.1), not the user
   (use `stack_api_key`, NOT `stack_id`, for `CS_API_KEY`). If the content model or entries do
   not yet exist in Contentstack,
   STOP — code migration requires content to be imported first (Steps 1–3).

3. **PLAN.** Produce a table: file:line → source call → Contentstack equivalent (cite the doc
   section) → field-UID dependencies → risk notes. Show it and PAUSE before editing any file.

4. **MIGRATE** per the doc, following the section matching each detected approach:

   - REST Delivery SDK: §1–§16. GraphQL: §17. Raw REST / framework plugins: §19.
   - Rich text / assets / locales / pagination: §9–§12.
     Make minimal, mechanical edits that match surrounding code style and the framework's existing
     data-fetching idioms. Preserve function/component contracts.

5. **LIVE PREVIEW.** If step 1 found preview/draft-mode, reimplement it per §18, matching the
   source's scope (routes, components, SSR vs client, click-to-edit vs read-only), and preserve
   existing preview gating/routing. Delivery tokens are safe in the browser. Preview tokens read
   unpublished content: expose them client-side only on preview deployments (CSR preview needs
   them), never in production builds. Management tokens never reach the browser.

6. **VERIFY — run the eval suite (this is mandatory, not optional).**
   Install deps first so the build eval is meaningful, then run the bundled evals in parallel:
   ```bash
   SESSION_DIR="<SESSION_DIR>" bash "<SKILL_DIR>/scripts/run-all.sh" "<repoPath>"
   ```
   For maximum parallelism you may instead spawn one agent per `"<SKILL_DIR>/scripts/"`NN\_\*.sh.
   See `"<SKILL_DIR>/scripts/README.md"` for what each check catches and exit-code semantics.
   - **Hard-gate FAIL/ERROR (residue, field-access, sdk-init, build, secrets) ⇒ the migration is NOT
     done.** Fix and re-run until they pass.
   - **Triage every review-eval finding** at its `file:line` — static greps flag _suspects_, not
     proven bugs. Fix the true positives; state explicitly why any remaining ones are safe. Never
     dismiss findings silently.
   - A green build is necessary but **not sufficient** — it cannot catch reference-array bugs, wrong
     field UIDs, or RTE output. Still smoke-test live queries against the real Contentstack stack.
   - For anything the doc marks "verify against current docs" (GraphQL hosts/headers, Live Preview
     front-end API), confirm before finalizing rather than guessing.

