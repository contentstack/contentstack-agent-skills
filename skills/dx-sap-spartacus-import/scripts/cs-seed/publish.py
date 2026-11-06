#!/usr/bin/env python3
"""
publish — publish seeded entries + assets to a Contentstack environment (Phase 4b).

Publishing makes entries readable by a delivery token (a storefront/CDA). Publishes every
entry of every content type on the stack, plus every asset, to the given environment/locale.
Idempotent (re-publishing is safe). Creds from env (CS_API_KEY, CS_MANAGEMENT_TOKEN).

Usage: python3 publish.py --env development [--locale en-us]
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cma_seed as low


def ensure_environment(name):
    """Create the target environment if the stack doesn't have it yet (fresh-stack support)."""
    st, r = low.cma("GET", "/environments")
    existing = {e["name"] for e in (r.get("environments") or [])}
    if name in existing:
        return "exists"
    st2, r2 = low.cma("POST", "/environments",
                      {"environment": {"name": name, "urls": [{"locale": "en-us", "url": "http://localhost:4200"}]}})
    return "created" if st2 in (200, 201) else f"ERR {st2}:{json.dumps(r2)[:160]}"


def list_all(path, key):
    out, skip = [], 0
    while True:
        st, r = low.cma("GET", f"{path}{'&' if '?' in path else '?'}limit=100&skip={skip}&include_count=true")
        items = r.get(key) or []
        out += items; skip += len(items)
        if len(items) < 100 or skip >= (r.get("count") or 0):
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--locale", default="en-us")
    a = ap.parse_args()
    if not (low.KEY and low.TOKEN):
        low.die("CS_API_KEY and CS_MANAGEMENT_TOKEN must be set")

    envs, loc = [a.env], [a.locale]
    print(f"[environment '{a.env}'] {ensure_environment(a.env)}")
    # assets first, then entries (components/shell) then pages last
    assets = list_all("/assets", "assets")
    print(f"[publish assets] {len(assets)}")
    ok = err = 0
    for x in assets:
        st, r = low.cma("POST", f"/assets/{x['uid']}/publish",
                        {"asset": {"environments": envs, "locales": loc}})
        ok += st in (200, 201); err += st not in (200, 201)
    print(f"  assets: {ok} ok, {err} err")

    cts = [c["uid"] for c in list_all("/content_types", "content_types")]
    # order: components, then global_slots, then pages
    page_types = {"landing_page", "content_page", "product_page", "category_page"}
    order = ([c for c in cts if c not in page_types and c != "global_slots"]
             + [c for c in cts if c == "global_slots"]
             + [c for c in cts if c in page_types])
    for ct in order:
        entries = list_all(f"/content_types/{ct}/entries", "entries")
        if not entries:
            continue
        ok = err = 0
        for e in entries:
            st, r = low.cma("POST", f"/content_types/{ct}/entries/{e['uid']}/publish",
                            {"entry": {"environments": envs, "locales": loc}})
            ok += st in (200, 201); err += st not in (200, 201)
            if st not in (200, 201) and err <= 3:
                print(f"    {ct}/{e['uid']}: {st} {json.dumps(r)[:120]}")
        print(f"[publish {ct}] {ok} ok, {err} err")


if __name__ == "__main__":
    main()
