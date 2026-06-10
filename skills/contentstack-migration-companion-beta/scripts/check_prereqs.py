#!/usr/bin/env python3
"""
check_prereqs.py  —  silent prerequisite evaluator for the CF→CS migration.

Runs all checks in one pass, auto-installs missing CLIs (csdx, contentful),
and emits a single JSON summary to stdout.

Exit codes:
  0  — all hard requirements met (some items may still need auth, flagged in JSON)
  1  — Node.js missing or too old (migration cannot proceed at all)
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, env=None):
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env if env is not None else os.environ,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return 1, "", f"{cmd[0]}: command not found"


def npm_install(pkg):
    """Silently install a global npm package. Errors surfaced via the JSON result."""
    subprocess.run(
        ["npm", "install", "-g", pkg],
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

out = {}

# ── Node.js ─────────────────────────────────────────────────────────────────
rc, ver, _ = run(["node", "--version"])
if rc != 0:
    out["node"] = {"ok": False, "error": "not_installed"}
    print(json.dumps(out, indent=2))
    sys.exit(1)

m = re.match(r"v(\d+)", ver)
major = int(m.group(1)) if m else 0
out["node"] = {"ok": major >= 20, "version": ver, "major": major}
if major < 20:
    # Hard blocker — emit result and exit 1 so the step file can surface the error
    print(json.dumps(out, indent=2))
    sys.exit(1)

# ── Contentstack CLI (csdx) ──────────────────────────────────────────────────
rc, ver, _ = run(["csdx", "--version"])
if rc != 0:
    print("Installing @contentstack/cli …", file=sys.stderr)
    npm_install("@contentstack/cli")
    rc, ver, _ = run(["csdx", "--version"])
out["csdx"] = {"ok": rc == 0, "version": ver if rc == 0 else None}

# ── Contentstack region ──────────────────────────────────────────────────────
rc, region_raw, _ = run(["csdx", "config:get:region"])
region = region_raw.strip() if rc == 0 else "UNKNOWN"
out["cs_region"] = {"region": region}

# ── Contentstack login + org UID ─────────────────────────────────────────────
rc, whoami, _ = run(["csdx", "auth:whoami"])
logged_in_cs = rc == 0 and whoami and "No user" not in whoami and "not logged" not in whoami.lower()

if logged_in_cs:
    # Ensure cli-utilities is available, then read the oauth org UID
    npm_install("@contentstack/cli-utilities")
    rc2, npm_root, _ = run(["npm", "root", "-g"])
    node_env = {**os.environ, "NODE_PATH": npm_root.strip()}
    uid_script = (
        "const {configHandler}=require('@contentstack/cli-utilities');"
        "const t=configHandler.get('authorisationType');"
        "const o=configHandler.get('oauthOrgUid');"
        "const e=configHandler.get('email')||'';"
        "if(t!=='OAUTH'||!o){process.exit(1);}"
        "console.log(JSON.stringify({orgUid:o,email:e}));"
    )
    rc3, uid_out, _ = run(["node", "-e", uid_script], env=node_env)
    if rc3 == 0:
        try:
            uid_data = json.loads(uid_out)
            out["cs_login"] = {
                "ok": True,
                "email": uid_data.get("email") or whoami,
                "org_uid": uid_data.get("orgUid"),
            }
        except Exception:
            out["cs_login"] = {"ok": True, "email": whoami, "org_uid": None}
    else:
        # Logged in but not via OAuth (or UID missing) — flag for re-auth
        out["cs_login"] = {
            "ok": True,
            "email": whoami,
            "org_uid": None,
            "needs_oauth_reauth": True,
        }
else:
    out["cs_login"] = {"ok": False, "needs_login": True}

# ── Contentful CLI ───────────────────────────────────────────────────────────
rc, ver, _ = run(["contentful", "--version"])
if rc != 0:
    print("Installing contentful-cli …", file=sys.stderr)
    npm_install("contentful-cli")
    rc, ver, _ = run(["contentful", "--version"])
out["contentful_cli"] = {"ok": rc == 0, "version": ver if rc == 0 else None}

# ── Contentful login + spaces ────────────────────────────────────────────────
rc, spaces_raw, spaces_err = run(["contentful", "space", "list"])
auth_error = "You have to be logged in" in spaces_raw or "You have to be logged in" in spaces_err
logged_in_cf = rc == 0 and not auth_error

if logged_in_cf:
    identity = {"ok": True}

    # Resolve account identity from the stored management token
    for p in ["~/.contentfulrc.json", "~/.config/contentful/config.json"]:
        f = pathlib.Path(p).expanduser()
        if not f.exists():
            continue
        try:
            d = json.loads(f.read_text())
            tok = (
                d.get("managementToken")
                or d.get("cmaToken")
                or d.get("management_token")
            )
            if not tok:
                continue
            req = urllib.request.Request(
                "https://api.contentful.com/users/me",
                headers={
                    "Authorization": f"Bearer {tok}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                user = json.loads(resp.read())
                identity["name"] = (
                    f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                )
                identity["email"] = user.get("email", "")
            break
        except Exception:
            pass

    out["contentful_login"] = identity

    # Parse spaces from the table output
    spaces = []
    for line in spaces_raw.split("\n"):
        if "│" in line:
            cols = [c.strip() for c in re.split(r"│", line) if c.strip()]
            if len(cols) >= 2 and cols[0] not in ("Space name", ""):
                name = re.sub(r"\s*\[.*?\]", "", cols[0]).strip()
                sid = cols[1]
                if name and sid:
                    spaces.append({"name": name, "id": sid})
    out["contentful_spaces"] = spaces
else:
    out["contentful_login"] = {"ok": False, "needs_login": True}
    out["contentful_spaces"] = []

# ── Done ─────────────────────────────────────────────────────────────────────
print(json.dumps(out, indent=2))
sys.exit(0)
