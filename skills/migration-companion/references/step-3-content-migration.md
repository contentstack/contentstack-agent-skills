# Step 3 — Content Migration (detailed procedure)

> **When to read:** Before running Step 3. Contains sub-steps 3.0–3.4 (token retrieval, confirmation, the migrate:create command and expected output, log parsing, progress summary) and token-expiry recovery. This file is part of the [migration-companion skill](../SKILL.md); `{SKILL_DIR}` / `$SKILL_DIR` refer to that skill's install directory.

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
| `EXPORT_JSON`   | `Stored space data to json file at: <path>`               | Step 3 Eval in SKILL.md |
| `BUNDLE_DIR`    | `Bundle: <path> (N types, N entries)`                     | Derived paths      |
| `STACK_NAME`    | `Stack name : …` (last occurrence — final summary box)    | Step 5 recap       |
| `STACK_KEY`     | `Stack key  : blt…` (last occurrence — final summary box) | Step 5 recap       |
| `REGION`        | `Region     : …` (last occurrence — final summary box)    | Step 4 env vars    |
| `LOG_DIR`       | `SUCCESS: The log has been stored at: <path>`             | Step 3 Eval in SKILL.md |
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

