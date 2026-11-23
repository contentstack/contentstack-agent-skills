#!/usr/bin/env python3
"""
stack_info — read-only: name the target stack and say what's in it, so gate 2 can tell the
user which stack will be written and published, and whether it's empty (the skill
recommends a new, dedicated stack: the publish step publishes everything in it).

Prints one line, never the API key:
  target stack: 'SAP demo' — empty (0 content types, 0 assets; locales en-us; no environments)

Usage: python3 stack_info.py      (CS_API_KEY + CS_MANAGEMENT_TOKEN or a csdx login)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cma_seed as low   # cma()


def count(path, key):
    st, r = low.cma("GET", f"{path}?include_count=true&limit=1")
    return r.get("count", len(r.get(key) or [])) if st == 200 else None


def main():
    if not (low.KEY and low.TOKEN):
        print("target stack: unknown (set CS_API_KEY, and CS_MANAGEMENT_TOKEN or a csdx login)")
        return
    st, r = low.cma("GET", "/stacks")
    if st != 200:
        print(f"target stack: couldn't read it (HTTP {st}) — check CS_API_KEY and the login")
        sys.exit(1)
    name = (r.get("stack") or {}).get("name", "?")
    n_ct, n_assets = count("/content_types", "content_types"), count("/assets", "assets")
    st_l, rl = low.cma("GET", "/locales")
    locales = [l["code"] for l in (rl.get("locales") or [])] if st_l == 200 else []
    st_e, re_ = low.cma("GET", "/environments")
    envs = [e["name"] for e in (re_.get("environments") or [])] if st_e == 200 else []
    empty = not n_ct and not n_assets
    print(f"target stack: '{name}' — {'empty' if empty else 'NOT empty'} "
          f"({n_ct} content types, {n_assets} assets; locales {', '.join(locales) or 'none'}; "
          f"environments {', '.join(envs) or 'none'})")


if __name__ == "__main__":
    main()
