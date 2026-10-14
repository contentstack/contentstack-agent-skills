# Step 1 — Prerequisites & inputs (detailed procedure)

> **When to read:** Before running Step 1. Contains sub-steps 1.0–1.6: session workspace, Python detection, the prereq checker, login recovery, the summary/confirm table, region picker, and Contentful space selection. This file is part of the [migration-companion skill](../SKILL.md); `<SKILL_DIR>` refers to that skill's install directory.

### 1.0 — Create session workspace

Before doing anything else, create the unique session directory for this migration run:

```bash
SESSION_DIR=$(mktemp -d "${TMPDIR:-/tmp}/migrate-to-cs-$(date +%Y%m%d-%H%M%S)-XXXXXX") && echo "SESSION_DIR=$SESSION_DIR"
```

**Record the printed `SESSION_DIR` path exactly** (e.g. `/tmp/migrate-to-cs-20260608-143022-a1B2c3`).
Substitute this concrete value wherever these instructions write `<SESSION_DIR>`.
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

**Record `PYTHON_CMD` exactly as printed.** Substitute it for `<PYTHON_CMD>` wherever these instructions
show a Python invocation — do not hardcode `python3` or `python`.

If `PYTHON_CMD` is empty, stop immediately and tell the user:

> "Python 3 is required but not found. Install it from python.org or via your package manager
> (e.g. `brew install python3` on macOS, `sudo apt install python3` on Ubuntu,
> or download the installer from python.org on Windows), then try again."

Do not proceed past this point until Python 3 is detected.

### 1.2 — Run the prerequisite checker

Run this single script. It evaluates Node.js, installs any missing CLIs (`csdx`, `contentful`)
and upgrades outdated ones, checks the Contentstack region and login, and checks the Contentful
login and spaces — all in one pass. It outputs a JSON summary.

**Tell the user before running it** that it may install or upgrade the global npm packages
`@contentstack/cli`, `contentful-cli` and `@contentstack/cli-utilities`.

```bash
<PYTHON_CMD> "<SKILL_DIR>/scripts/check_prereqs.py"
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
PATH="<NODE_BIN_DIR>:$PATH" csdx auth:login --oauth
```

Tell the user: _"A browser window is opening — complete the Contentstack login there, then come
back here."_ Wait for the command to return (it blocks until the browser flow finishes), then
**re-run the prereq checker** (same command as 1.2) to capture the updated email and org UID.

Once `cs_login.org_uid` is non-null (whether this sub-step ran or not), record it as the
literal `ORG_UID`; Step 3 passes it to `migrate:create` as `--org "<ORG_UID>"`.

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
| Python 3                | ✅ `<output of PYTHON_CMD --version>`                 |                               |
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
| "region"                             | Present the region menu (see below), wait for selection, run `PATH="<NODE_BIN_DIR>:$PATH" csdx config:set:region <REGION>`, re-run the prereq checker, re-display the summary |
| "contentstack login"                 | Run `PATH="<NODE_BIN_DIR>:$PATH" csdx auth:login --oauth`, wait for browser login, re-run the prereq checker, re-display the summary                                          |
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
PATH="<NODE_BIN_DIR>:$PATH" csdx config:set:region <REGION>   # e.g. <REGION> = AWS-EU
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
PATH="<NODE_BIN_DIR>:$PATH" contentful space use --space-id <SPACE_ID>
```

If this fails, the token likely lacks access to that space — tell the user and ask them to
re-check the selection or switch to a Contentful account that has the right access.

