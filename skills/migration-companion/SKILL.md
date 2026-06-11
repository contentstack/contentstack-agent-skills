---
name: contentstack-migration-companion
description: Migration companion for moving to Contentstack from another CMS. Guides content and application migration through a structured, step-by-step workflow. Currently supports migrations from Contentful, with additional source platforms planned. Use when users want to migrate, move, switch, port, or re-platform to Contentstack, including content models, content, assets, locales, application integrations, or website code. Trigger on requests such as "migrate to Contentstack", "move to Contentstack", "switch to Contentstack", "migrate from Contentful", "move my Contentful space", "port my CMS", or similar migration-related requests. The skill validates prerequisites, guides the migration process, provides progress checkpoints, and delivers a completion summary. Prefer this skill whenever a Contentstack migration is requested.
---

# contentstack-migration-companion

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
  SESSION_ID=$(date +%Y%m%d-%H%M%S) && SESSION_DIR="/tmp/migrate-to-cs/$SESSION_ID" && mkdir -p "$SESSION_DIR" && echo "SESSION_DIR=$SESSION_DIR"
  ```
  Record the printed `SESSION_DIR` value (e.g. `/tmp/migrate-to-cs/20260608-143022`) and
  **carry it as a concrete literal** through every shell command in this migration — do not
  regenerate it. This keeps each migration run isolated so concurrent sessions and re-runs
  never collide. If the user points you to a different workspace, use their path instead.
- **Bundled scripts & references live next to this skill — resolve them via `{SKILL_DIR}`.**
  This skill ships helper scripts (a `scripts/` folder) and reference docs (a `references/`
  folder) **alongside this `SKILL.md` file**. Wherever these instructions write `{SKILL_DIR}`,
  substitute the absolute path of the directory this `SKILL.md` was loaded from — i.e. the
  skill's own install directory. **Do not assume a fixed path.** The location differs by AI
  assistant, by OS, and by whether the skill was installed per-project or per-user — for example
  it may be `<project>/.claude/skills/contentstack-migration-companion`,
  `~/.claude/skills/contentstack-migration-companion`, or a Windows path like
  `%USERPROFILE%\.claude\skills\contentstack-migration-companion`. Determine the real path once
  (it is the folder you read this `SKILL.md` from; if unsure, search the workspace and home
  directory for `*/contentstack-migration-companion/SKILL.md`), and for shell commands set it as
  a variable up front (`SKILL_DIR="<that absolute path>"`) so bundled scripts can be invoked as
  `"$SKILL_DIR/scripts/<name>"`. The bundled scripts self-locate their own siblings, so once you
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
  sees tool calls in the tool panel — repeating code in chat is noise.

## The migration at a glance

| # | Step | Command (core) | Produces |
|---|------|----------------|----------|
| 1 | Prerequisites & inputs | prereq check script | verified env + gathered inputs |
| 2 | Install migrate plugin | `csdx plugins:link .` (or `plugins:add`) | `csdx migrate:*` available |
| 3 | Content Migration | `csdx migrate:create` | populated stack + bundle + credentials |
| 4 | Code Migration | detect → plan → rewrite → eval (13 checks) | rewritten data layer |
| 5 | Welcome to Contentstack 🎉 | — | celebration + next steps |

Work through them in order. The sections below give the exact commands, what to show the
user, and what to carry forward.

> **Self-contained skill.** Everything Step 4 needs — the full code-migration procedure, the
> Contentful → Contentstack SDK reference (`references/`), and the eval scripts (`scripts/`) —
> ships inside this one skill. There is no separate code-migration skill to install; resolve the
> bundled files via `{SKILL_DIR}` as described above.

---

## Step 1 — Prerequisites & inputs

> **[PROGRESS]** Output the migration progress block:
> Step 1 → `"in_progress"`, Steps 2–4 → `"pending"`.

### 1.0 — Create session workspace

Before doing anything else, create the unique session directory for this migration run:

```bash
SESSION_ID=$(date +%Y%m%d-%H%M%S) && SESSION_DIR="/tmp/migrate-to-cs/$SESSION_ID" && mkdir -p "$SESSION_DIR" && echo "SESSION_DIR=$SESSION_DIR"
```

**Record the printed `SESSION_DIR` path exactly** (e.g. `/tmp/migrate-to-cs/20260608-143022`).
Substitute this concrete value wherever these instructions reference `$SESSION_DIR`.
Do not regenerate it — every step in this migration must use the same directory so artifacts
chain correctly.

Tell the user: "Session workspace created at `<SESSION_DIR>`."

### 1.1 — Detect the Python 3 command

Run this to find the correct Python 3 command for this environment:

```bash
if python3 --version 2>&1 | grep -q "Python 3"; then
  PYTHON_CMD=python3
elif python --version 2>&1 | grep -q "Python 3"; then
  PYTHON_CMD=python
else
  PYTHON_CMD=""
fi
echo "PYTHON_CMD=$PYTHON_CMD"
```

**Record `PYTHON_CMD` exactly as printed.** Substitute `$PYTHON_CMD` wherever these instructions
show a Python invocation — do not hardcode `python3` or `python`.

If `PYTHON_CMD` is empty, stop immediately and tell the user:

> "Python 3 is required but not found. Install it from python.org or via your package manager
> (e.g. `brew install python3` on macOS, `sudo apt install python3` on Ubuntu,
> or download the installer from python.org on Windows), then try again."

Do not proceed past this point until Python 3 is detected.

### 1.2 — Run the prerequisite checker

Run this single script. It silently evaluates Node.js, installs any missing CLIs (`csdx`,
`contentful`), checks the Contentstack region and login, and checks the Contentful login and
spaces — all in one pass. It outputs a JSON summary:

```bash
$PYTHON_CMD "{SKILL_DIR}/scripts/check_prereqs.py"
```

Parse the JSON result and carry every field forward as session state.

**Record the Node bin directory.** Capture `node.bin_dir` from the JSON as the concrete literal
`NODE_BIN_DIR`. Per the "Pin the Node version" principle in the overview, prefix every later
`csdx`, `npm`, and `contentful` command with `PATH="<NODE_BIN_DIR>:$PATH"` so the whole migration
runs on the Node the checker validated — not whatever an unconfigured non-interactive shell would
resolve first (the checker already picks the **highest installed Node ≥ 20**, scanning PATH and
all nvm installs). If `node.bin_dir` is missing, fall back to the plain command.

**Hard blocker:** If the script exits with code 1, Node.js is missing or too old. The reported
`node.version`/`node.path` reflect the *best* Node found anywhere on the machine, so the message is
accurate even when a newer Node exists but isn't on the default PATH. Stop immediately and tell the
user the exact problem:

- `node.error == "not_installed"` → "Node.js is not installed. Install it via `nvm install 22`
  or from nodejs.org, then try again."
- `node.ok == false` (e.g. `node.version == "v18.x"`) → "The newest Node I can find is
  `<version>`, but Node 20+ is required. Install a newer one with `nvm install 22 && nvm use 22`
  (or upgrade your system Node), then try again."

Do not continue past this point until Node 20+ is confirmed.

### 1.3 — Handle missing Contentstack login (if needed)

Skip this sub-step if `cs_login.ok` is true in the JSON.

If `cs_login.ok` is false (needs_login) or `cs_login.org_uid` is null (needs_oauth_reauth),
trigger a fresh OAuth login:

```bash
csdx auth:login --oauth
```

Tell the user: _"A browser window is opening — complete the Contentstack login there, then come
back here."_ Wait for the command to return (it blocks until the browser flow finishes), then
**re-run the prereq checker** (same command as 1.2) to capture the updated email and org UID.

If the org UID is still missing after the retry, tell the user:

> "OAuth login did not store an org UID. Please re-run `csdx auth:login --oauth` manually, then
> let me know when done so I can retry."

### 1.4 — Handle missing Contentful login (if needed)

Skip this sub-step if `contentful_login.ok` is true in the JSON.

`contentful login` is interactive (it needs the user to press Y and paste a token) — you cannot
run it as a Bash command. Instruct the user to run it themselves:

> "Please run this command in your terminal:
>
> ```
> contentful login
> ```
>
> It will ask **'Continue login on the browser? (Y/n)'** — press **Y**.
> A browser window will open — sign in there.
> When the browser login completes, the terminal will show **'Paste your token here:'** —
> copy your Management Token from the browser page and paste it, then press Enter.
> Come back here once the login confirms success."

**Wait for the user to confirm they have completed the login**, then re-run the prereq checker
to pick up the new session.

> The Management Token is a secret: do not ask the user to share it with you, do not echo it
> back in your summaries, and do not write it into any file in this workspace.

### 1.5 — Show the prerequisites summary and confirm

Once `cs_login.ok` and `contentful_login.ok` are both true, display a summary table from the
JSON result. Use ✅ for items that look good and ⚠️ for anything that may need attention:

| Check                   | Status                                                | Detail                        |
| ----------------------- | ----------------------------------------------------- | ----------------------------- |
| Python 3                | ✅ `<$PYTHON_CMD --version output>`                   |                               |
| Node.js                 | ✅ `<node.version>`                                   |                               |
| Contentstack CLI (csdx) | ✅ `<csdx.version>`                                   |                               |
| Contentstack region     | ⚙️ `<cs_region.region>`                               |                               |
| Contentstack login      | ✅ `<cs_login.email>`                                 | Org UID: `<cs_login.org_uid>` |
| Contentful CLI          | ✅ `<contentful_cli.version>`                         |                               |
| Contentful login        | ✅ `<contentful_login.name> <contentful_login.email>` |                               |

Then ask this single question:

> "Everything looks good — ready to proceed? Or would you like to change anything before
> we start?
>
> - **proceed** — start the migration
> - **region** — switch the Contentstack region
> - **contentstack login** — switch the Contentstack account
> - **contentful login** — switch the Contentful account"

**Wait for the user's answer before continuing.**

| Answer                               | Action                                                                                                                                            |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| "proceed" / "yes" / any confirmation | Skip to 1.6                                                                                                                                       |
| "region"                             | Present the region menu (see below), wait for selection, run `csdx config:set:region <REGION>`, re-run the prereq checker, re-display the summary |
| "contentstack login"                 | Run `csdx auth:login --oauth`, wait for browser login, re-run the prereq checker, re-display the summary                                          |
| "contentful login"                   | Instruct the user to run `contentful login` themselves (same as 1.4), wait for confirmation, re-run the prereq checker, re-display the summary    |

**Region picker** — when the user asks to change the region, show this menu and wait for their
choice before running the command:

> "Which region is your destination stack in?
>
> 1. AWS-NA — AWS North America
> 2. AWS-EU — AWS Europe
> 3. AWS-AU — AWS Australia
> 4. AZURE-NA — Azure North America
> 5. AZURE-EU — Azure Europe
> 6. GCP-NA — Google Cloud North America
> 7. GCP-EU — Google Cloud Europe"

Map the number to its region code and run:

```bash
csdx config:set:region <REGION>   # e.g. csdx config:set:region AWS-EU
```

Repeat the summary + question until the user confirms they are ready to proceed.

### 1.6 — Contentful Space ID (select from list)

The `contentful_spaces` array in the prereq JSON already holds all accessible spaces (populated
from the `contentful space list` call run inside the checker).

**If there is exactly one space in the list**, select it automatically — do not ask the user.
Announce the selection:

> "Found one Contentful space: **My Marketing Site** (`abc123`). Using it automatically."

Capture its ID as `SPACE_ID` and continue.

**If there are two or more spaces**, present them as a numbered menu
— **do not ask the user to type or paste a Space ID**:

```
1. My Marketing Site  (abc123)
2. Developer Sandbox  (def456)
…
```

Ask:

> "Which space do you want to migrate? Enter the number."

**Wait for the answer.** Map the number back to the Space ID and capture it as `SPACE_ID`.

If the list is empty (no spaces parsed), fall back to asking:

> "I couldn't list your Contentful spaces. Please enter the Space ID directly."

Then confirm the token can reach the selected space:

```bash
contentful space use --space-id <SPACE_ID>
```

If this fails, the token likely lacks access to that space — tell the user and ask them to
re-check the selection or switch to a Contentful account that has the right access.

### Eval — Verify Step 1 before proceeding

```bash
# Use the Node the checker validated (NODE_BIN_DIR from the prereq JSON).
export PATH="<NODE_BIN_DIR>:$PATH"
$PYTHON_CMD --version   # must print Python 3.x
node --version          # must print v20.x or higher
csdx --version          # must print a version number
csdx auth:whoami        # must print a logged-in email
contentful --version    # must print a version number
contentful space list   # must return a list of spaces — not "You have to be logged in"
```

(`export` only affects this one Eval block — shell state does not persist across commands, so
later steps must still prefix `PATH="<NODE_BIN_DIR>:$PATH"` per the overview principle.)

**Pass criteria:**

- `$PYTHON_CMD` detected and exits 0 with `Python 3.x`
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

The `csdx migrate:*` commands come from `@contentstack/cli-external-migrate`. Run this block to
install or update it automatically — it is intentionally silent unless something changes or fails:

```bash
PLUGIN_NAME="@contentstack/cli-external-migrate"

# Version currently installed (empty string if not installed)
INSTALLED=$(csdx plugins 2>/dev/null \
  | grep -F "$PLUGIN_NAME" \
  | grep -oE '[0-9]+\.[0-9]+\.[0-9]+[^ ]*' \
  | head -1)

# Latest version on npm
LATEST=$(npm view "$PLUGIN_NAME" version 2>/dev/null)

if [ -z "$LATEST" ]; then
  echo "PLUGIN_NPM_UNAVAILABLE"
elif [ -z "$INSTALLED" ]; then
  csdx plugins:install "$PLUGIN_NAME" && echo "PLUGIN_INSTALLED:$LATEST" || echo "PLUGIN_INSTALL_FAILED"
elif [ "$INSTALLED" = "$LATEST" ]; then
  echo "PLUGIN_UP_TO_DATE:$INSTALLED"
else
  csdx plugins:uninstall "$PLUGIN_NAME" \
    && csdx plugins:install "$PLUGIN_NAME" \
    && echo "PLUGIN_UPDATED:$INSTALLED→$LATEST" \
    || echo "PLUGIN_UPDATE_FAILED:$INSTALLED→$LATEST"
fi
```

Interpret the last line:

- **`PLUGIN_UP_TO_DATE:<version>`** → already on the latest version; proceed to the Eval. (Stay
  silent — don't report "already up to date" to the user.)
- **`PLUGIN_INSTALLED:<version>`** → freshly installed. Briefly tell the user, then proceed.
- **`PLUGIN_UPDATED:<old>→<new>`** → uninstalled old version and installed latest. Briefly tell
  the user the plugin was updated, then proceed.
- **`PLUGIN_INSTALL_FAILED`** / **`PLUGIN_UPDATE_FAILED:<old>→<new>`** → the install or
  reinstall errored. Show the user the error output, then display this message and wait:

  > The automatic plugin install failed. Please run the following command manually in your
  > terminal, then click **Continue** when done:
  >
  > ```
  > csdx plugins:install @contentstack/cli-external-migrate
  > ```

  After the user clicks Continue, skip straight to the **Eval** below to verify the plugin is
  working before proceeding.

- **`PLUGIN_NPM_UNAVAILABLE`** → `npm view` returned nothing (network issue or package not yet
  published). Show the user this message and wait:

  > Could not reach npm to check the plugin version. Please run the following command manually
  > in your terminal, then click **Continue** when done:
  >
  > ```
  > csdx plugins:install @contentstack/cli-external-migrate
  > ```

  After the user clicks Continue, proceed to the **Eval** below.

### Eval — Verify Step 2 before proceeding

```bash
csdx migrate --help
```

**Pass criteria:**

- Output includes `migrate:create` (the one-shot command used in Step 3)

If `migrate:create` is present, update the migration checklist to set cf-step2="completed" and cf-step3="in_progress", then proceed to Step 3. If the command errors or `migrate:create` is missing, re-run the install block above and re-verify.

---

## Step 3 — Content Migration

> **[PROGRESS]** Output the migration progress block:
> Steps 1–2 → `"completed"`, Step 3 → `"in_progress"`, Step 4 → `"pending"`.

This single command exports the Contentful space, converts the content to a Contentstack
bundle, and imports it into a brand-new stack — all in one shot. The master locale is
auto-detected from the export's default locale.

### 3.0 — Retrieve the stored Management Token

The Contentful CLI stores the token from the login in `~/.contentfulrc.json`. Read it now
so `migrate:create` can use it without prompting:

```bash
$PYTHON_CMD -c "
import json, sys, pathlib
for p in ['~/.contentfulrc.json', '~/.config/contentful/config.json']:
    f = pathlib.Path(p).expanduser()
    if f.exists():
        d = json.loads(f.read_text())
        tok = d.get('managementToken') or d.get('cmaToken') or d.get('management_token')
        if tok:
            print(tok)
            sys.exit(0)
print('NOT_FOUND', file=sys.stderr)
sys.exit(1)
"
```

Capture the printed value as `CONTENTFUL_MANAGEMENT_TOKEN`. **Do not display it to the user
or write it to any file.**

If the token is NOT found (exits 1), tell the user the token could not be resolved. Ask them
to run `contentful login` again, then retry.

### 3.1 — Confirm before running

Tell the user:

> "Ready to start the content migration. This will export your Contentful space, convert
> the content, and import it into a new stack under your org. Shall I proceed?"

**Wait for confirmation before running the command.**

### 3.2 — Run migrate:create (output captured to log file)

Run from `$SESSION_DIR` so that the import `logs/` directory and `_backup_*/` are written
there, keeping the user's project directory clean. Pipe through `tee` so output streams live
and is also saved for parsing:

```bash
cd "$SESSION_DIR" && \
csdx migrate:create --source contentful \
  --space-id "$SPACE_ID" \
  --source-token "$CONTENTFUL_MANAGEMENT_TOKEN" \
  --org "$ORG_UID" \
  --download-assets \
  --output "$SESSION_DIR" \
  --workspace "$SESSION_DIR" \
  -y \
  2>&1 | tee "$SESSION_DIR/migrate-create.log"
```

Flag notes:

- `--space-id` / `--source-token` — Contentful source (token resolved in 3.0)
- `--org` — the org UID captured in Step 1; a new stack is created here
- `--source contentful` — declares Contentful as the migration source
- `--download-assets` — include asset binaries in the migration
- `--output "$SESSION_DIR"` — bundle written to `$SESSION_DIR/bundle/`
- `--workspace "$SESSION_DIR"` — export JSON saved to `$SESSION_DIR/export.json`
- `-y` — skip internal confirmation prompts (we already confirmed above)
- `cd "$SESSION_DIR"` — ensures `logs/` and `_backup_*/` land in the session dir, not CWD

The command runs three phases and prints this progression:

**Phase 1 — Export** (streams fetch progress, ends with the entity-count table):

```
┌────────────────────────┐
│ Exported entities      │
├───────────────────┬────┤
│ Content Types     │ 16 │
│ Entries           │ 53 │
│ Assets            │ 21 │
│ Locales           │ 2  │
│ …                 │ …  │
└───────────────────┴────┘
Stored space data to json file at: <SESSION_DIR>/export.json
```

**Phase 2 — Convert** (transforms export into Contentstack bundle):

```
  validate   ✓  export.json
  extract    ✓  2 locales · 16 types
  transform  ✓  53 entries · 13 types  →  <SESSION_DIR>/bundle
  Bundle: <SESSION_DIR>/bundle (16 types, 53 entries)
```

**Phase 3 — Import** (creates stack, imports content, ends with the summary box):

```
✓ Stack created · via cma
──────────────────────────────────────
  Stack name : Contentful Migration 2026-06-08
  Stack key  : blt3e69b8da307655a7
  Region     : AWS-NA
──────────────────────────────────────
… (import progress) …
SUCCESS: Successfully imported the content to the stack named … with the API key blt… .
SUCCESS: The log has been stored at: <SESSION_DIR>/logs
✓ Bundle metadata written: <SESSION_DIR>/bundle/metadata.json
✓ Migration complete
──────────────────────────────────────
  Stack name : Contentful Migration 2026-06-08
  Stack key  : blt3e69b8da307655a7
  Region     : AWS-NA
──────────────────────────────────────
```

### 3.3 — Parse the output and extract session variables

Once the command returns, parse the captured log with exact patterns matching the real output:

```bash
$PYTHON_CMD - <<'PYEOF'
import re, pathlib, os

raw = pathlib.Path(os.environ["SESSION_DIR"] + "/migrate-create.log").read_text()
# Strip ANSI escape codes — the import phase wraps paths in color sequences
log = re.sub(r'\x1b\[[0-9;]*m', '', raw)

# Patterns matched against real command output
export_json = re.search(r'Stored space data to json file at:\s+(\S+)',  log)
bundle_dir  = re.search(r'Bundle:\s+(\S+)',                             log)
stack_name  = re.findall(r'Stack name\s*:\s*(.+)',                      log)
stack_key   = re.findall(r'Stack key\s*:\s*(blt\w+)',                   log)
region      = re.findall(r'Region\s*:\s*(\S+)',                         log)
log_dir     = re.search(r'SUCCESS: The log has been stored at:\s+(\S+)',log)
metadata    = re.search(r'Bundle metadata written:\s+(\S+)',            log)

session_dir = os.environ["SESSION_DIR"]
# Use last match for stack fields — the final summary box is authoritative
print("EXPORT_JSON="   + (export_json.group(1).strip() if export_json else session_dir + "/export.json"))
print("BUNDLE_DIR="    + (bundle_dir.group(1).strip()  if bundle_dir  else session_dir + "/bundle"))
print("STACK_NAME="    + (stack_name[-1].strip()       if stack_name  else "UNKNOWN"))
print("STACK_KEY="     + (stack_key[-1].strip()        if stack_key   else "UNKNOWN"))
print("REGION="        + (region[-1].strip()           if region      else "UNKNOWN"))
print("LOG_DIR="       + (log_dir.group(1).strip()     if log_dir     else "UNKNOWN"))
print("METADATA_PATH=" + (metadata.group(1).strip()    if metadata    else session_dir + "/bundle/metadata.json"))
PYEOF
```

Capture each printed `KEY=value` as a session variable:

| Variable        | Exact source line in the log                              | Used in            |
| --------------- | --------------------------------------------------------- | ------------------ |
| `EXPORT_JSON`   | `Stored space data to json file at: <path>`               | Eval below         |
| `BUNDLE_DIR`    | `Bundle: <path> (N types, N entries)`                     | Derived paths      |
| `STACK_NAME`    | `Stack name : …` (last occurrence — final summary box)    | Step 5 recap       |
| `STACK_KEY`     | `Stack key  : blt…` (last occurrence — final summary box) | Step 5 recap       |
| `REGION`        | `Region     : …` (last occurrence — final summary box)    | Step 4 env vars    |
| `LOG_DIR`       | `SUCCESS: The log has been stored at: <path>`             | Eval below         |
| `METADATA_PATH` | `✓ Bundle metadata written: <path>`                       | Step 4 credentials |

Also set the mapper path (always `$BUNDLE_DIR/mapper.json`):

```bash
MAPPER_PATH="$BUNDLE_DIR/mapper.json"
```

If any value is `UNKNOWN`, check `$SESSION_DIR/migrate-create.log` directly for the line and
set it manually before continuing.

### 3.4 — Show the user a progress summary

Show the entity-count table and the final stack summary, both taken from the captured log:

```bash
# Entity count table from Phase 1 (export)
grep -A 18 'Exported entities' "$SESSION_DIR/migrate-create.log" | head -20

# Final stack summary box from Phase 3 (last occurrence)
grep -A 4 'Stack name' "$SESSION_DIR/migrate-create.log" | tail -6
```

Report in plain prose:

> "Content migration complete — stack **`$STACK_NAME`** (`$STACK_KEY`, `$REGION`) is ready."

### Handle token expiry mid-run

The Contentstack OAuth token can expire during a long import. The symptom in the log is:

```
stack creation failed.
  CMA:  401 The provided access token is invalid or expired or revoked
```

Re-authenticate and re-run from step 3.1:

```bash
csdx auth:login --oauth
```

The command is safe to re-run — it creates a fresh stack each time.

### Eval — Verify Step 3 before proceeding

Confirm the key artifacts exist:

```bash
ls -lh "$METADATA_PATH"
ls -lh "$MAPPER_PATH"
```

Run the bundled import summary parser to verify entity counts match what was exported:

```bash
$PYTHON_CMD "$SKILL_DIR/scripts/parse_import_summary.py" "$LOG_DIR" --export "$EXPORT_JSON"
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

If all pass, update the migration checklist to set cf-step3="completed" and cf-step4="in_progress", then
proceed to Step 4. If counts diverge or artifacts are missing, surface the discrepancy and
point the user at `$LOG_DIR` — do not proceed until resolved.

### Session variables carried into Step 4

| Variable        | Value                                  | Purpose                                                  |
| --------------- | -------------------------------------- | -------------------------------------------------------- |
| `BUNDLE_DIR`    | from log (or `$SESSION_DIR/bundle`)    | Root of the import bundle                                |
| `METADATA_PATH` | from `✓ Bundle metadata written:` line | Stack credentials — API key, delivery token, environment |
| `MAPPER_PATH`   | `$BUNDLE_DIR/mapper.json`              | Contentful → Contentstack field-UID mapping              |
| `STACK_NAME`    | from final summary box                 | Step 5 recap                                             |
| `STACK_KEY`     | from final summary box                 | Step 5 recap                                             |
| `REGION`        | from final summary box                 | `.env` setup in Step 4                                   |

---

## Step 4 — Code Migration

> **[PROGRESS]** Output the migration progress block:
> Steps 1–3 → `"completed"`, Step 4 → `"in_progress"`.

With the content now in Contentstack, migrate the **application code** that reads from the CMS.
This step runs a full detect → plan → rewrite → eval cycle with 13 post-migration checks.

### 4.1 — Collect inputs

**`repoPath`** — local file system path to the application to migrate.
Ask the user:

> "What is the local path to the codebase you want to migrate? (e.g. `/Users/you/projects/my-app`)"
> If it's a remote git repo, clone it first:
>
> ```bash
> cd "$SESSION_DIR" && git clone <REPO_URL>
> ```
>
> Then use the cloned directory as `repoPath`.

**`mapperPath`** — the field-mapping JSON produced by Step 3. Confirm it exists:

```bash
ls -lh "$SESSION_DIR/bundle/mapper.json"
```

If the file is at a different path (e.g. the user used a custom workspace), ask them to confirm
the exact path.

Read `mapperPath` with the Read tool and extract the `fieldMapping` arrays from each content type
to build the Contentful-field-UID → Contentstack-field-UID table. Present the extracted table to
the user for confirmation before proceeding.

**`metadataPath`** — the credentials JSON written by Step 3's import. Confirm it exists and read it:

```bash
ls -lh "$SESSION_DIR/bundle/metadata.json"
```

Read `metadataPath` with the Read tool. It supplies the new stack's Delivery SDK credentials so
you **do not have to ask the user for them**:

| metadata.json key | Use as              | Notes                                               |
| ----------------- | ------------------- | --------------------------------------------------- |
| `stack_api_key`   | `CS_API_KEY`        | the `blt…` **Stack API Key** — **not** `stack_id`   |
| `delivery_token`  | `CS_DELIVERY_TOKEN` | for the published-content SDK                       |
| `preview_token`   | `CS_PREVIEW_TOKEN`  | only if the app uses Live Preview (§18)             |
| `environment`     | `CS_ENVIRONMENT`    | e.g. `master`                                       |
| `stack_id`        | (stack UID)         | identifier only — do **not** use as the SDK api key |

The region (e.g. `AWS-NA`) comes from `csdx config:get:region`. Treat the tokens as secrets —
never echo them back or write them into files in this workspace; only set them in the migrated
app's local `.env` (which should be gitignored). If `metadata.json` is missing, fall back to
asking the user for `CS_API_KEY`, `CS_DELIVERY_TOKEN`, and `CS_ENVIRONMENT`.

### 4.2 — Logging

First resolve `{SKILL_DIR}` (see the "Bundled scripts & references" operating principle) — the
directory this skill is installed in — and set it as a shell variable so every command below can
reach the bundled scripts portably, on any OS or assistant:

```bash
SKILL_DIR="<absolute path to this skill's install dir>"   # the folder holding this SKILL.md
```

From the first action in this step, record everything to the session log using
`"$SKILL_DIR/scripts/log.sh"`:

- `log.sh <target> user-input "<what the user asked/answered>"` — every user input/communication.
- `log.sh <target> decision "<detection results, choices, assumptions, guessed UIDs>"`.
- `log.sh <target> ai-action "<files/queries you changed>"` and `communication "<what you told the user>"`.
- `log.sh <target> exception "<any error, blocker, or uncertainty you hit>"` — log all exceptions.
- Run shell commands through it so output + exit codes are captured and failures auto-log as
  exceptions: `log.sh <target> run "typecheck" -- npx tsc --noEmit`.

End with `log.sh <target> summary`. The log lands in `<target>/.migration/` (`session.log` +
`session.jsonl` + per-command output). See `"$SKILL_DIR/scripts/README.md"`.

### 4.3 — Reference (read first)

The complete, source-verified mapping for every API, response shape, query operator, rich-text
renderer, asset transform, GraphQL query, and Live Preview API lives in:

**`{SKILL_DIR}/references/CONTENTFUL_TO_CONTENTSTACK_MIGRATION_CONTEXT.md`** (read it with the
Read tool from this skill's install dir — see the `{SKILL_DIR}` operating principle)

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
   Confirm env vars (`CS_API_KEY`, `CS_DELIVERY_TOKEN`, `CS_ENVIRONMENT`, + region/branch, +
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
   source's scope (routes, components, SSR vs client, click-to-edit vs read-only). Keep preview
   tokens server-side and preserve existing preview gating/routing.

6. **VERIFY — run the eval suite (this is mandatory, not optional).**
   Install deps first so the build eval is meaningful, then run the bundled evals in parallel:
   ```bash
   bash "$SKILL_DIR/scripts/run-all.sh" <path-to-migrated-app>
   ```
   For maximum parallelism you may instead spawn one agent per `"$SKILL_DIR/scripts/"`NN\_\*.sh.
   See `"$SKILL_DIR/scripts/README.md"` for what each check catches and exit-code semantics.
   - **Hard-gate FAIL/ERROR (residue, field-access, sdk-init, build, secrets) ⇒ the migration is NOT
     done.** Fix and re-run until they pass.
   - **Triage every review-eval finding** at its `file:line` — static greps flag _suspects_, not
     proven bugs. Fix the true positives; state explicitly why any remaining ones are safe. Never
     dismiss findings silently.
   - A green build is necessary but **not sufficient** — it cannot catch reference-array bugs, wrong
     field UIDs, or RTE output. Still smoke-test live queries against the real Contentstack stack.
   - For anything the doc marks "verify against current docs" (GraphQL hosts/headers, Live Preview
     front-end API), confirm before finalizing rather than guessing.

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
- **Next steps:** set the `CS_*` env vars in the app's local `.env` from `metadata.json`
  (`CS_API_KEY` = `stack_api_key`, `CS_DELIVERY_TOKEN` = `delivery_token`, `CS_ENVIRONMENT` =
  `environment`, plus `CS_PREVIEW_TOKEN` = `preview_token` if Live Preview, and the region from
  `csdx config:get:region`), run the app against Contentstack, and verify pages render.

---

## Step 5 — Welcome to Contentstack 🎉

The migration is complete. Display the following message to the user — render it exactly as shown, preserving the section headings, icons, and line breaks:

---

![Contentstack](https://images.contentstack.io/v3/assets/blt77d44a06c81b1730/blt2e24a315fedaeaf7/68bc10f25f14881bc908b6c2/CS_OnlyLogo.webp)

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚀  Welcome to Contentstack!                                   ║
║                                                                  ║
║   The Agentic Experience Platform                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

> *"The world's best digital experiences run on Contentstack."*

**🎊 Your migration is complete.**

Your content, content types, assets, and website code have all successfully moved from Contentful to Contentstack. Here's a quick recap of what just happened:

| ✅ | What was migrated |
|---|---|
| 📦 | Content types & field definitions |
| 🖼️ | Assets & media |
| 📝 | Entries & localized content |
| 💻 | Website data-layer code |

### 📂 Where to find your migrated files

Using the exact paths captured during this session, fill in and display this table:

| Artifact | Location |
|---|---|
| 🗂️ **Contentful export** | The `export.json` path in `$SESSION_DIR` (from Step 3) |
| 📦 **Contentstack import bundle** | `$SESSION_DIR/bundle/` (from Step 3) |
| 🔑 **Stack credentials** | `$SESSION_DIR/bundle/metadata.json` (from Step 3) |
| 📋 **Import logs** | The log directory printed by `migrate:create` (Step 3) |
| 💻 **Migrated website code** | The `repoPath` the user provided in Step 4 |
| 🔍 **Code migration log** | `<repoPath>/.migration/session.log` |

Do not use default or guessed paths — substitute only the real paths you captured from each step's command output.

---

### 🌟 You're now on the platform trusted by the world's top brands

Contentstack powers digital experiences for enterprises across retail, media, finance, and beyond — delivering content at scale, across every channel, without compromise.

Here's what you've unlocked:

| Capability | What it means for you |
|---|---|
| ⚡ **Composable architecture** | Mix and match best-of-breed tools — your stack, your way |
| 🌍 **Multi-region delivery** | Content served fast, anywhere on the globe |
| 🔄 **Omnichannel publishing** | Web, mobile, IoT, voice — one content hub for all |
| 🛡️ **Enterprise-grade security** | SOC 2 Type II, GDPR, HIPAA-ready |
| 🤝 **Dedicated support** | Real humans, not just docs — onboarding, migrations, and beyond |
| 🧩 **Marketplace & integrations** | 100+ pre-built connectors — plug in what you already use |

---

### 🚦 Recommended next steps

1. **Verify your live site** — start your app with the new `CS_*` env vars and confirm pages render against Contentstack.
2. **Explore the Contentstack dashboard** — invite your team, set up roles, and configure publishing workflows.
3. **Set up webhooks & automation** — trigger deploys, Slack alerts, or custom workflows on publish events.
4. **Review the Contentstack Docs** — [contentstack.com/docs](https://www.contentstack.com/docs) is your go-to for Delivery SDK, GraphQL, and Live Preview guides.
5. **Talk to your account team** — let them know you're live; they can unlock additional features and walk you through advanced capabilities.

---

> 💡 **Tip:** Bookmark the [Contentstack Developer Hub](https://www.contentstack.com/developers) — it has SDK references, starter apps, and video tutorials to help you get the most out of your new platform.

---

*Congratulations on completing your migration.  
You've made the right call — the world's best digital experiences are built on Contentstack, and now yours will be too.* 🚀
