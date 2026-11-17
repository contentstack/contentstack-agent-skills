"""
cs_auth — the Management API auth header for every pipeline call.

Two modes (CS_AUTH = token | csdx | auto, default auto):
  token  CS_MANAGEMENT_TOKEN, sent as `authorization: <token>` (stack-scoped, as before)
  csdx   the user's own Contentstack CLI session (`csdx auth:login --oauth`), via csdx_auth.cjs;
         OAuth tokens are refreshed by csdx, and once more after a 401
  auto   the management token when CS_MANAGEMENT_TOKEN is set, else the csdx session

With the csdx session, writes run as the logged-in user (the stack's audit log shows them).
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
MANAGEMENT_TOKEN = os.environ.get("CS_MANAGEMENT_TOKEN")
_MODE = os.environ.get("CS_AUTH", "auto").lower()
_cache = {}


def mode():
    if _MODE == "token" or (_MODE == "auto" and MANAGEMENT_TOKEN):
        return "token"
    return "csdx"


def available():
    """True when some credential is configured (the csdx session is checked on first use)."""
    return bool(MANAGEMENT_TOKEN) if mode() == "token" else True


def headers(refresh=False):
    if mode() == "token":
        return {"authorization": MANAGEMENT_TOKEN}
    if refresh or "h" not in _cache:
        args = ["node", os.path.join(HERE, "csdx_auth.cjs")] + (["--refresh"] if refresh else [])
        # When csdx refreshes an expired OAuth token, the helper can exit before printing;
        # the refreshed token is saved, so a second call returns it.
        for _ in range(3):
            p = subprocess.run(args, capture_output=True, text=True)
            if p.returncode:
                raise SystemExit((p.stderr or "csdx_auth failed").strip())
            # csdx can print progress lines (e.g. "Forcing token refresh...") on stdout
            # before the helper's JSON, so read only the JSON line.
            line = next((l for l in reversed(p.stdout.splitlines()) if l.strip().startswith("{")), "")
            if line:
                _cache["h"] = json.loads(line)
                break
            args = args[:2]
        else:
            raise SystemExit("[cs_auth] csdx returned no session — run `csdx auth:login --oauth`")
    return dict(_cache["h"])


def describe():
    return "management token" if mode() == "token" else "csdx login (CS_AUTH=csdx)"
