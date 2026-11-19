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


def ensure_environment(name, locales=("en-us",), url="http://localhost:4200"):
    """Create the target environment if missing (fresh-stack support) and give it a base URL
    for every locale. Live Preview is locale-based: a locale without a URL shows "Unable to
    load the preview". Existing URLs are kept; only missing locales are added."""
    st, r = low.cma("GET", "/environments")
    env = next((e for e in (r.get("environments") or []) if e["name"] == name), None)
    if not env:
        st2, r2 = low.cma("POST", "/environments", {"environment": {
            "name": name, "urls": [{"locale": l, "url": url} for l in locales]}})
        return "created" if st2 in (200, 201) else f"ERR {st2}:{json.dumps(r2)[:160]}"
    urls = {u["locale"]: u.get("url") for u in env.get("urls") or []}
    missing = [l for l in locales if not urls.get(l)]
    if not missing:
        return "exists"
    urls.update({l: url for l in missing})
    st2, r2 = low.cma("PUT", f"/environments/{name}", {"environment": {
        "name": name, "urls": [{"locale": l, "url": u} for l, u in urls.items()]}})
    return f"exists, added URL for {missing}" if st2 == 200 else f"ERR {st2}:{json.dumps(r2)[:160]}"


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
    ap.add_argument("--locale", default=os.environ.get("CS_MASTER_LOCALE", "en-us"))
    ap.add_argument("--preview-locales", default="",
                    help="comma list of extra locales that need a Live Preview URL, e.g. de-de,ja-jp")
    ap.add_argument("--preview-url", default=os.environ.get("CS_PREVIEW_URL", "http://localhost:4200"),
                    help="storefront base URL for Live Preview (default $CS_PREVIEW_URL or localhost:4200)")
    a = ap.parse_args()
    if not (low.KEY and low.TOKEN):
        low.die("CS_API_KEY and CS_MANAGEMENT_TOKEN must be set")

    envs, loc = [a.env], [a.locale]
    preview_locales = [a.locale] + [l for l in a.preview_locales.split(",") if l and l != a.locale]
    print(f"[environment '{a.env}'] {ensure_environment(a.env, preview_locales, a.preview_url)}")
    # assets first, then entries (components/shell) then pages last
    assets = list_all("/assets", "assets")
    print(f"[publish assets] {len(assets)}")
    ok = err = 0
    for x in assets:
        st, r = low.cma("POST", f"/assets/{x['uid']}/publish",
                        {"asset": {"environments": envs, "locales": loc}})
        ok += st in (200, 201); err += st not in (200, 201)
    print(f"  assets: {ok} ok, {err} err")
    totals = {"assets": ok, "entries": 0, "errors": err}

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
        totals["entries"] += ok; totals["errors"] += err
    # one summary line last, so a caller that shows only the tail still sees the totals
    print(f"[publish] {totals['assets']} assets and {totals['entries']} entries published to "
          f"'{a.env}' ({a.locale}), {totals['errors']} errors")
    if totals["errors"]:
        sys.exit(3)


if __name__ == "__main__":
    main()
