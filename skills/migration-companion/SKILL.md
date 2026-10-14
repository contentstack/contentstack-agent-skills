---
name: migration-companion
description: 'Migration companion for moving to Contentstack from another CMS. Guides content and application migration through a structured, step-by-step workflow. Currently supports migrations from Contentful, with additional source platforms planned. Use when users want to migrate, move, switch, port, or re-platform to Contentstack, including content models, content, assets, locales, application integrations, or website code. Trigger on requests such as "migrate to Contentstack", "move to Contentstack", "switch to Contentstack", "migrate from Contentful", "move my Contentful space", "port my CMS", or similar migration-related requests. The skill validates prerequisites, guides the migration process, provides progress checkpoints, and delivers a completion summary. Prefer this skill whenever a migration from another CMS into Contentstack is requested; for upgrading Contentstack SDK code from JavaScript to TypeScript, use dx-migrate-js-to-ts-sdk.'
---

# Contentstack Migration Companion

Guide a user through migrating a project from **Contentful** to **Contentstack** —
first the **content** (content types, entries, assets, locales) via the Contentstack
CLI migrate plugin, then the **website code** that reads from the CMS.

This is a sequential workflow where **each step produces output that the next step
consumes** (the create command produces a populated stack and a bundle with credentials,
which feeds the code migration). Treat the artifact paths and counts that each command
prints as state you must capture and carry forward.

## Operating principles

Follow these throughout — they matter more than any single command:

- **Work in a unique session workspace.** At the very start of Step 1, create a
  session-scoped directory by running:
  ```bash
  SESSION_DIR=$(mktemp -d "${TMPDIR:-/tmp}/migrate-to-cs-$(date +%Y%m%d-%H%M%S)-XXXXXX") && echo "SESSION_DIR=$SESSION_DIR"
  ```
  Record the printed `SESSION_DIR` value (e.g. `/tmp/migrate-to-cs-20260608-143022-a1B2c3`) and
  **carry it as a concrete literal** through every shell command in this migration — do not
  regenerate it. This keeps each migration run isolated so concurrent sessions and re-runs
  never collide. If the user points you to a different workspace, use their path instead.
- **Bundled scripts & references live next to this skill — resolve them via `<SKILL_DIR>`.**
  This skill ships helper scripts (a `scripts/` folder) and reference docs (a `references/`
  folder) **alongside this `SKILL.md` file**. Wherever these instructions write `<SKILL_DIR>`,
  substitute the absolute path of the directory this `SKILL.md` was loaded from — i.e. the
  skill's own install directory. **Do not assume a fixed path.** The location differs by AI
  assistant, by OS, and by whether the skill was installed per-project or per-user — for example
  it may be `<project>/.claude/skills/migration-companion`,
  `~/.claude/skills/migration-companion`, or a Windows path like
  `%USERPROFILE%\.claude\skills\migration-companion`. Determine the real path once
  (it is the folder you read this `SKILL.md` from; if unsure, search the workspace and home
  directory for `*/migration-companion/SKILL.md`), record it, and write it into every shell
  command as a literal so bundled scripts are invoked as `"<SKILL_DIR>/scripts/<name>"`. The bundled scripts self-locate their own siblings, so once you
  invoke them by absolute path they work regardless of your current directory.
- **Pin the Node version for the whole session.** A machine often has several Node versions
  (system, Homebrew, multiple nvm installs) and a non-interactive shell may resolve an old one
  (e.g. `/usr/local/bin/node` v14) ahead of the user's nvm default. The Step 1 prereq checker
  finds the **highest installed Node ≥ 20** and reports its directory as `node.bin_dir` in the
  JSON. Record that value as a concrete literal `NODE_BIN_DIR` and **prefix every `csdx`, `npm`,
  and `contentful` command for the rest of the migration** with it, e.g.
  `PATH="<NODE_BIN_DIR>:$PATH" csdx migrate:create …`. This guarantees the CLI runs on the
  Node the prereq check validated, not whatever an unconfigured shell picks first. If
  `node.bin_dir` is absent (older check output), fall back to the plain command.
- **One step at a time, and show the result.** After each command, surface the meaningful
  output to the user — the summary tables, the counts, the artifact path — not a wall of
  raw logs. The user is watching this like a progress bar; give them a clean status, then
  the path/handle the next step needs.
- **Track migration progress with the checklist.** At each `[PROGRESS]` trigger below, output
  a progress block in your response using these emoji: `✅` = completed, `⏳` = currently running,
  `⬜` = not yet started. Example for Step 3 in progress:
  ```
  **Migration progress**
  - ✅ Step 1 — Prerequisites & inputs
  - ✅ Step 2 — Install migrate plugin
  - ⏳ Step 3 — Content Migration
  - ⬜ Step 4 — Code Migration
  ```
  Output it at two moments: (1) at the start of each step, and (2) when each step's eval passes.
  Only one step is `⏳` at a time. Step 4 stays `⏳` through all sub-steps 4.1–4.6.
  Step 5 (Welcome) is **not** tracked — it triggers automatically once Step 4 is ✅.
- **Gate the destructive or expensive steps.** Confirm before logging in, before creating a
  new stack, and before editing the user's code. These either touch live accounts or modify
  their repo, so a quick "ready to proceed?" prevents nasty surprises.
- **Capture the outputs explicitly.** When a command prints a bundle path, a log directory,
  or a stack API key, record the exact path/value and reuse it verbatim. Do not guess paths —
  read them back from the command output.
- **Placeholders are not shell variables.** Shell state does not persist between commands, so
  `<PYTHON_CMD>`, `<SKILL_DIR>`, `<NODE_BIN_DIR>`, `<SESSION_DIR>`, `<ORG_UID>`, `<SPACE_ID>`,
  `<EXPORT_JSON>`, `<BUNDLE_DIR>`, `<LOG_DIR>`, `<METADATA_PATH>` and `<MAPPER_PATH>` in these
  instructions are placeholders: replace each with the literal value you recorded before running
  the command (or set it at the top of that same command). Never rely on a variable set by an
  earlier command.
- **Browser-based login is normal here.** `csdx auth:login --oauth` opens the user's browser;
  the terminal then blocks and auto-detects when they finish. Run it, tell the user to complete
  login in the browser, and simply wait for the command to return — do not try to script the
  browser or kill the command.
- **Currently Contentful is the only supported source.** Do not ask the user which legacy
  platform they're on; assume Contentful. (The CLI flag is `--source contentful`.)
- **If a step fails, stop and diagnose** rather than barrelling ahead. Most failures here are
  recoverable (expired token → re-login, missing content model → inform the user), and the
  relevant recovery is described in the step that can fail.
- **Never display code in your text output.** Do not show shell commands, code snippets,
  scripts, or any fenced code blocks (``` blocks) in your chat messages at any point during
  the migration. Just run commands silently and report the result in plain prose. The user
  sees tool calls in the tool panel — repeating code in chat is noise. Two exceptions: a command
  the user must run themselves (for example `contentful login` or a manual plugin install), and
  a template these instructions tell you to render verbatim (such as the Step 5 welcome message).

## The migration at a glance

| # | Step | Command (core) | Produces |
|---|------|----------------|----------|
| 1 | Prerequisites & inputs | prereq check script | verified env + gathered inputs |
| 2 | Install migrate plugin | `csdx plugins:install @contentstack/cli-external-migrate` | `csdx migrate:*` available |
| 3 | Content Migration | `csdx migrate:create` | populated stack + bundle + credentials |
| 4 | Code Migration | detect → plan → rewrite → eval (13 checks) | rewritten data layer |
| 5 | Welcome to Contentstack 🎉 | — | celebration + next steps |

Work through them in order. Each step below gives a concise summary, its gates, and its eval;
the exact commands, expected output, and what to show the user live in a per-step reference
file under `references/`. **Read the step's reference file before running that step** — load
only the one you need, when you reach it.

| Step | Reference (read before running the step) |
|------|------------------------------------------|
| 1 | [references/step-1-prerequisites.md](references/step-1-prerequisites.md) |
| 2 | [references/step-2-plugin-install.md](references/step-2-plugin-install.md) |
| 3 | [references/step-3-content-migration.md](references/step-3-content-migration.md) |
| 4 | [references/step-4-code-migration.md](references/step-4-code-migration.md) + [references/CONTENTFUL_TO_CONTENTSTACK_MIGRATION_CONTEXT.md](references/CONTENTFUL_TO_CONTENTSTACK_MIGRATION_CONTEXT.md) |
| 5 | [references/step-5-welcome-message.md](references/step-5-welcome-message.md) |

> **Self-contained skill.** Everything Step 4 needs — the full code-migration procedure, the
> Contentful → Contentstack SDK reference (`references/`), and the eval scripts (`scripts/`) —
> ships inside this one skill. There is no separate code-migration skill to install; resolve the
> bundled files via `<SKILL_DIR>` as described above.

---

## Step 1 — Prerequisites & inputs

> **[PROGRESS]** Output the migration progress block:
> Step 1 → `"in_progress"`, Steps 2–4 → `"pending"`.

Read [references/step-1-prerequisites.md](references/step-1-prerequisites.md) before running this step.

Summary of sub-steps (full commands, messages, and tables are in the reference file):

- **1.0 — Create session workspace.** Create the session directory once and record it as the literal `SESSION_DIR`.
- **1.1 — Detect the Python 3 command.** Record `PYTHON_CMD`; if empty, stop — Python 3 is required.
- **1.2 — Run the prerequisite checker** (`<PYTHON_CMD> "<SKILL_DIR>/scripts/check_prereqs.py"`).
  Tell the user first that it may install or upgrade the global `@contentstack/cli` and
  `contentful-cli` npm packages. Record `NODE_BIN_DIR` from `node.bin_dir`. **Hard blocker:** exit code 1 means Node 20+ is
  missing — stop until it is fixed.
- **1.3 / 1.4 — Handle missing Contentstack / Contentful login.** `csdx auth:login --oauth` for
  Contentstack, then record `cs_login.org_uid` as the literal `ORG_UID`; the user runs `contentful login` themselves (it is interactive). Never ask for,
  echo, or write the Management Token.
- **1.5 — Show the prerequisites summary and confirm.** **Gate:** wait for the user to say
  proceed (or switch region / account) before continuing.
- **1.6 — Contentful Space ID.** Auto-select a single space; otherwise present a numbered menu
  and wait. Capture `SPACE_ID`.

### Eval — Verify Step 1 before proceeding

```bash
# Use the Node the checker validated (NODE_BIN_DIR from the prereq JSON).
export PATH="<NODE_BIN_DIR>:$PATH"
<PYTHON_CMD> --version  # must print Python 3.x
node --version          # must print v20.x or higher
csdx --version          # must print a version number
csdx auth:whoami        # must print a logged-in email
contentful --version    # must print a version number
contentful space list   # must return a list of spaces — not "You have to be logged in"
```

(`export` only affects this one Eval block — shell state does not persist across commands, so
later steps must still prefix `PATH="<NODE_BIN_DIR>:$PATH"` per the overview principle.)

**Pass criteria:**

- `PYTHON_CMD` detected and exits 0 with `Python 3.x`
- Node major version ≥ 20
- `csdx auth:whoami` returns an email (not "No user logged in")
- `cs_login.org_uid` is non-null (captured from prereq JSON in step 1.2 / 1.3)
- `contentful space list` returns rows without an auth error
- `SPACE_ID` captured from the user's selection in 1.6

> Note: `contentful whoami` is not available in all CLI versions — use `contentful space list`
> to verify authentication instead.

If every check passes:

> **[PROGRESS]** Output the migration progress block:
> Step 1 → `"completed"`, Step 2 → `"in_progress"`, Steps 3–4 → `"pending"`.

Then proceed to Step 2. If any check fails, fix the issue (re-run the relevant sub-step) and re-verify.

---

## Step 2 — Install the migrate CLI plugin

> **[PROGRESS]** Output the migration progress block:
> Step 1 → `"completed"`, Step 2 → `"in_progress"`, Steps 3–4 → `"pending"`.

Read [references/step-2-plugin-install.md](references/step-2-plugin-install.md) before running this step.

Summary: run the bundled install/update block, which installs or updates
`@contentstack/cli-external-migrate` and prints one result marker (`PLUGIN_UP_TO_DATE`,
`PLUGIN_INSTALLED`, `PLUGIN_UPDATED`, `PLUGIN_INSTALL_FAILED` / `PLUGIN_UPDATE_FAILED`, or
`PLUGIN_NPM_UNAVAILABLE`). On a failure marker, ask the user to install manually and wait for
them to continue, then run the Eval.

### Eval — Verify Step 2 before proceeding

```bash
PATH="<NODE_BIN_DIR>:$PATH" csdx migrate --help
```

**Pass criteria:**

- Output includes `migrate:create` (the one-shot command used in Step 3)

If `migrate:create` is present, proceed to Step 3 (its **[PROGRESS]** block marks Step 2 ✅ and Step 3 ⏳). If the command errors or `migrate:create` is missing, re-run the install block in [references/step-2-plugin-install.md](references/step-2-plugin-install.md) and re-verify.

---

## Step 3 — Content Migration

> **[PROGRESS]** Output the migration progress block:
> Steps 1–2 → `"completed"`, Step 3 → `"in_progress"`, Step 4 → `"pending"`.

This single command exports the Contentful space, converts the content to a Contentstack
bundle, and imports it into a brand-new stack — all in one shot. The master locale is
auto-detected from the export's default locale.

Read [references/step-3-content-migration.md](references/step-3-content-migration.md) before running this step.

Summary of sub-steps (full commands, expected output, and parsing script are in the reference file):

- **3.0 — Check the stored Management Token** with `scripts/read_cf_token.py --check`, which
  prints only `FOUND` / `NOT_FOUND`. Stop if it is not found. Never display the token or write it
  to a file; 3.2 resolves it inside the same command that runs `csdx`.
- **3.1 — Confirm before running.** **Gate:** this creates a new stack in the user's org — wait
  for confirmation.
- **3.2 — Run `csdx migrate:create`** from `<SESSION_DIR>`, teeing output to
  `<SESSION_DIR>/migrate-create.log`.
- **3.3 — Parse the output** into `EXPORT_JSON`, `BUNDLE_DIR`, `STACK_NAME`, `STACK_KEY`,
  `REGION`, `LOG_DIR`, `METADATA_PATH`, and `MAPPER_PATH`.
- **3.4 — Show the user a progress summary** (entity counts + final stack box).
- **Token expiry mid-run:** re-run `csdx auth:login --oauth` and restart from 3.1.

### Eval — Verify Step 3 before proceeding

Confirm the key artifacts exist:

```bash
ls -lh "<METADATA_PATH>"
ls -lh "<MAPPER_PATH>"
```

Run the bundled import summary parser to verify entity counts match what was exported:

```bash
<PYTHON_CMD> "<SKILL_DIR>/scripts/parse_import_summary.py" "<LOG_DIR>" --export "<EXPORT_JSON>"
```

**Pass criteria:**

- `STACK_KEY` starts with `blt` (a real stack was created)
- `METADATA_PATH` and `MAPPER_PATH` both exist
- `SUCCESS: Successfully imported…` line is present in the captured log
- Imported counts match exported counts; any divergence must be explained before proceeding

Present the counts table to the user:

```
Module          Imported   (Exported)
Locales         2          2
Content Types   16         16
Assets          21         21
Entries         53         53
✓ Imported into stack "<STACK_NAME>" (<STACK_KEY>)
```

If all pass, proceed to Step 4 (its **[PROGRESS]** block marks Step 3 ✅ and Step 4 ⏳). If counts diverge or artifacts are missing, surface the discrepancy and
point the user at `<LOG_DIR>` — do not proceed until resolved.

### Session variables carried into Step 4

| Variable        | Value                                  | Purpose                                                  |
| --------------- | -------------------------------------- | -------------------------------------------------------- |
| `BUNDLE_DIR`    | from log (or `<SESSION_DIR>/bundle`)   | Root of the import bundle                                |
| `METADATA_PATH` | from `✓ Bundle metadata written:` line | Stack credentials — API key, delivery token, environment |
| `MAPPER_PATH`   | `<BUNDLE_DIR>/mapper.json`             | Contentful → Contentstack field-UID mapping              |
| `STACK_NAME`    | from final summary box                 | Step 5 recap                                             |
| `STACK_KEY`     | from final summary box                 | Step 5 recap                                             |
| `REGION`        | from final summary box                 | `CS_REGION` in the app's `.env` (Step 4)                 |
| `LOG_DIR`       | from `SUCCESS: The log has been stored at:` | Step 3 Eval, Step 5 recap                           |
| `EXPORT_JSON`   | from `Stored space data to json file at:`  | Step 3 Eval, Step 5 recap                           |

---

## Step 4 — Code Migration

> **[PROGRESS]** Output the migration progress block:
> Steps 1–3 → `"completed"`, Step 4 → `"in_progress"`.

With the content now in Contentstack, migrate the **application code** that reads from the CMS.
This step runs a full detect → plan → rewrite → eval cycle with 13 post-migration checks.

Read [references/step-4-code-migration.md](references/step-4-code-migration.md) before running
this step, and read the full SDK reference it points to
([references/CONTENTFUL_TO_CONTENTSTACK_MIGRATION_CONTEXT.md](references/CONTENTFUL_TO_CONTENTSTACK_MIGRATION_CONTEXT.md))
before editing any code.

Summary of sub-steps (full detail in the reference file):

- **4.1 — Collect inputs:** `repoPath`, `mapperPath` (field-UID table, confirmed with the user),
  and `metadataPath` (stack credentials — use `stack_api_key`, not `stack_id`, for `CS_API_KEY`).
- **4.2 — Logging:** record every action through `SESSION_DIR="<SESSION_DIR>" bash "<SKILL_DIR>/scripts/log.sh"`
  (the log lands in `<SESSION_DIR>/migration-log/`, outside the user's repo).
- **4.3 — Reference:** read the SDK mapping doc in full; it is the single source of truth.
- **4.4 — Procedure:** DETECT (pause) → PREREQUISITES → PLAN (**gate:** pause before editing any
  file) → MIGRATE → LIVE PREVIEW → VERIFY with `bash "<SKILL_DIR>/scripts/run-all.sh" "<repoPath>"`. Hard-gate
  eval failures mean the migration is NOT done.

### 4.5 — Guardrails

- Do NOT modify content modeling or move/import entries — out of scope for this step.
- Convert every reference dereference to safe array access (`?.[0]`) and audit null safety
  (Contentstack resolves references to arrays, not single objects).
- When a UID or behavior is uncertain, leave a `// TODO(migration):` comment and list it — never
  guess silently.

### 4.6 — Wrap up

> **[PROGRESS]** Output the migration progress block:
> Steps 1–4 all → `"completed"`. Then immediately proceed to Step 5.

Give the user a final summary of the whole migration journey:

- **Content:** counts imported into the stack (from Step 3).
- **Code:** files changed, the rich-text rendering strategy chosen, guessed UIDs to verify, and
  any `TODO(migration)` call sites still needing attention.
- **Eval results:** whether all hard gates passed and which review findings remain to triage.
- **Detection summary:** language/framework/approach(es) detected; whether Live Preview was
  present and how it was reimplemented; every guessed UID; every TODO; and any call site not
  fully migrated (geo queries, `locale: '*'`, cross-space ResourceLinks, GraphQL features without
  an equivalent).
- **Next steps:** the user sets the `CS_*` env vars in the app's gitignored `.env` from
  `metadata.json` (`CS_API_KEY` = `stack_api_key`, `CS_DELIVERY_TOKEN` = `delivery_token`,
  `CS_ENVIRONMENT` = `environment`, plus `CS_PREVIEW_TOKEN` = `preview_token` if Live Preview, and
  `CS_REGION` = the `REGION` recorded in Step 3), runs the app against Contentstack, and verifies
  pages render.

---

## Step 5 — Welcome to Contentstack 🎉

The migration is complete. Read [references/step-5-welcome-message.md](references/step-5-welcome-message.md)
and display that message to the user — render it exactly as shown there, preserving the section
headings, icons, and line breaks, and filling the file-location table with the real paths
captured during this session.

## Security

### Defaults

- Logins use browser OAuth (`csdx auth:login --oauth`); never ask the user to paste passwords or tokens into chat.
- Delivery tokens are safe in the browser. Preview tokens read unpublished content: expose them client-side only on preview deployments (CSR preview needs them), never in production builds. Management tokens (Contentful or Contentstack) never reach the browser.

### Destructive Actions

Logging in, creating a stack and editing the user's code are gated behind confirmation (see § Operating principles). The Step 1 prerequisite checker installs or upgrades the global `@contentstack/cli` and `contentful-cli` npm packages (and `@contentstack/cli-utilities`) when they are missing or outdated: tell the user before running it. Never delete the source Contentful space, an existing Contentstack stack (including a partial one left by a failed run), or user files.

### Secrets

Never display, echo or write management tokens. Credentials the migrated app needs go only into its gitignored `.env`, with the user's confirmation; never into source, logs or the final report.

### Environment Variables

The migrated app reads `CS_API_KEY`, `CS_DELIVERY_TOKEN`, `CS_ENVIRONMENT`, `CS_REGION` and `CS_PREVIEW_TOKEN` (Live Preview only) from its `.env`. Ask the user to fill in the values themselves; never ask for or log them.
