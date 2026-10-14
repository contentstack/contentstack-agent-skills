#!/usr/bin/env python3
"""Resolve the Contentful management token stored by `contentful login`.

  read_cf_token.py --check   prints FOUND or NOT_FOUND (never the token); exit 0 / 1
  read_cf_token.py           prints only the token, for command substitution in the
                             same shell command that consumes it; exit 1 if not found

Never run it without --check in a way that shows its output to the user or a log.
"""
import json
import pathlib
import sys

PATHS = ["~/.contentfulrc.json", "~/.config/contentful/config.json"]
KEYS = ["managementToken", "cmaToken", "management_token"]


def find_token():
    for p in PATHS:
        f = pathlib.Path(p).expanduser()
        if not f.exists():
            continue
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict):
            continue
        for k in KEYS:
            if d.get(k):
                return d[k]
    return None


tok = find_token()
if "--check" in sys.argv[1:]:
    print("FOUND" if tok else "NOT_FOUND")
elif tok:
    print(tok)
sys.exit(0 if tok else 1)
