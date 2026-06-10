#!/usr/bin/env python3
"""
check_prereqs.py  —  silent prerequisite evaluator for the CF→CS migration.

Runs all checks in one pass, auto-installs missing CLIs (csdx, contentful),
and emits a single JSON summary to stdout.

Exit codes:
  0  — all hard requirements met (some items may still need auth, flagged in JSON)
  1  — Node.js missing or too old (migration cannot proceed at all)
"""
import glob
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
#
# All CLI subprocesses (node, npm, csdx, contentful) run under CLI_ENV. It
# starts as the inherited environment, but once we resolve the best available
# Node (see "Node.js" below) we prepend that Node's bin dir to PATH so every
# downstream tool uses it — even when an older /usr/local/bin/node would
# otherwise win in a non-interactive shell.
CLI_ENV = dict(os.environ)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, env=None):
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env if env is not None else CLI_ENV,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return 1, "", f"{cmd[0]}: command not found"


def npm_install(pkg):
    """Silently install a global npm package. Errors surfaced via the JSON result."""
    subprocess.run(
        ["npm", "install", "-g", pkg],
        capture_output=True,
        env=CLI_ENV,
    )


def extract_version(s):
    """Pull the first semver-looking token out of a `--version` output."""
    m = re.search(r"(\d+\.\d+\.\d+[^\s]*)", s or "")
    return m.group(1) if m else None


def npm_latest(pkg):
    """Latest published version of a package on npm (None if npm is unreachable)."""
    rc, ver, _ = run(["npm", "view", pkg, "version"])
    return ver.strip() if rc == 0 and ver.strip() else None


def node_version_tuple(node_bin):
    """(major, minor, patch) version tuple for a node binary, or None if it won't run."""
    rc, ver, _ = run([node_bin, "--version"])
    if rc != 0:
        return None, None
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", ver)
    if not m:
        return None, ver
    return tuple(int(x) for x in m.groups()), ver


def discover_node_bins():
    """Every node binary we can find: PATH entries, nvm-installed versions, and
    common system/homebrew locations. De-duplicated by real path."""
    candidates = []

    # All `node` on PATH (handles shims and multiple managers).
    rc, paths, _ = run(["which", "-a", "node"])
    if rc == 0:
        candidates += [p for p in paths.splitlines() if p.strip()]

    # Every nvm-installed version (the default shell may not expose these).
    nvm_dir = os.environ.get("NVM_DIR", os.path.expanduser("~/.nvm"))
    candidates += glob.glob(os.path.join(nvm_dir, "versions", "node", "*", "bin", "node"))

    # Common fixed locations.
    candidates += [
        "/opt/homebrew/bin/node",
        "/usr/local/bin/node",
        "/usr/bin/node",
    ]

    seen, uniq = set(), []
    for c in candidates:
        if not c or not os.path.exists(c):
            continue
        rp = os.path.realpath(c)
        if rp in seen:
            continue
        seen.add(rp)
        uniq.append(c)
    return uniq


def pick_best_node():
    """Highest-version node binary available. Returns (version_tuple, version_str,
    bin_path) or None if no node is found at all."""
    best = None
    for b in discover_node_bins():
        tup, ver = node_version_tuple(b)
        if tup is None:
            continue
        if best is None or tup > best[0]:
            best = (tup, ver, b)
    return best


def ensure_latest_cli(cmd_name, pkg):
    """Ensure a global CLI is installed AND on the latest npm version.

    Installs when missing, upgrades when an older version is present. Returns a
    dict suitable for the JSON summary: {ok, version, installed, latest, updated}.
    """
    rc, raw, _ = run([cmd_name, "--version"])
    installed = extract_version(raw) if rc == 0 else None
    latest = npm_latest(pkg)
    updated = False

    if rc != 0:
        # Not installed — install latest.
        print(f"Installing {pkg} …", file=sys.stderr)
        npm_install(f"{pkg}@latest")
        rc, raw, _ = run([cmd_name, "--version"])
        installed = extract_version(raw) if rc == 0 else None
        updated = rc == 0
    elif latest and installed and installed != latest:
        # Installed but outdated — upgrade to latest.
        print(f"Updating {pkg} {installed} → {latest} …", file=sys.stderr)
        npm_install(f"{pkg}@latest")
        rc, raw, _ = run([cmd_name, "--version"])
        installed = extract_version(raw) if rc == 0 else None
        updated = rc == 0
    # else: latest is unknown (offline) or already current — leave as-is.

    return {
        "ok": rc == 0,
        "version": raw if rc == 0 else None,
        "installed": installed,
        "latest": latest,
        "updated": updated,
    }


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

out = {}

# ── Node.js ─────────────────────────────────────────────────────────────────
# Pick the highest node available across PATH + nvm, not just whatever the
# non-interactive shell resolves first (which may be an old /usr/local/bin/node).
best = pick_best_node()
if best is None:
    out["node"] = {"ok": False, "error": "not_installed"}
    print(json.dumps(out, indent=2))
    sys.exit(1)

node_tuple, ver, node_bin = best
major = node_tuple[0]
node_dir = os.path.dirname(node_bin)
out["node"] = {
    "ok": major >= 20,
    "version": ver,
    "major": major,
    "path": node_bin,
    "bin_dir": node_dir,
}

if major < 20:
    # Hard blocker — emit result and exit 1 so the step file can surface the error.
    # `path`/`version` reflect the BEST node we found, so the message is accurate.
    print(json.dumps(out, indent=2))
    sys.exit(1)

# Pin every downstream CLI (npm, csdx, contentful, node -e) to this node's bin
# dir so they don't fall back to an older node earlier on PATH.
CLI_ENV["PATH"] = node_dir + os.pathsep + CLI_ENV.get("PATH", "")

# ── Contentstack CLI (csdx) — install if missing, upgrade if outdated ─────────
out["csdx"] = ensure_latest_cli("csdx", "@contentstack/cli")

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
    node_env = {**CLI_ENV, "NODE_PATH": npm_root.strip()}
    uid_script = (
        "const {configHandler}=require('@contentstack/cli-utilities');"
        "const t=configHandler.get('authorisationType');"
        "const o=configHandler.get('oauthOrgUid');"
        "const e=configHandler.get('email')||'';"
        "if(t!=='OAUTH'||!o){process.exit(1);}"
        "console.log(JSON.stringify({orgUid:o,email:e}));"
    )
    rc3, uid_out, _ = run([node_bin, "-e", uid_script], env=node_env)
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

# ── Contentful CLI — install if missing, upgrade if outdated ──────────────────
out["contentful_cli"] = ensure_latest_cli("contentful", "contentful-cli")

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
