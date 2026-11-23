#!/usr/bin/env python3
"""
use_products — fallback when the SAP Commerce Cloud product picker can't be made to work:
switch a seeded stack's product carousels back to the plain `products` SKU list, as they were
before the picker was introduced.

Only run this after the user has chosen the fallback (see SKILL.md › Verify, retry, then ask).

What it does, for product_carousel_component:
  1. re-imports the content type from the starter pack WITHOUT `sap_products`
     (this removes the picker field and the picker data stored in it),
  2. writes each carousel's SKUs into `products`, in the same order, in every locale the
     entry exists in,
  3. publishes each of those locale versions to the environment.

The storefront renders the same products either way — the connector reads `sap_products`
first and falls back to `products` — editors just type/paste SKU codes instead of picking.
The SAP app itself stays installed; uninstall it from Marketplace if it isn't wanted.

Usage:
  python3 use_products.py --plan <run>/connector-plan.json --env development
"""
import argparse, json, os, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cs-seed"))
import cma_seed as low
import cma_seed_connector as seeder
from sap_products import is_placeholder

CT = "product_carousel_component"
# Same default as orchestrate.py: the starter pack `ng add` installed in the current project.
DEFAULT_STARTER = os.environ.get("CONNECTOR_STARTER_PACK", os.path.join(
    os.getcwd(), "node_modules", "@contentstack", "contentstack-spartacus-connector",
    "import-export", "starter-pack", "content_types"))


def carousel_codes(plan):
    out = {}
    for e in plan["entries"]["components"]:
        if e["_content_type"] != CT:
            continue
        v = e.get("sap_products")
        out[e["_key"]["value"]] = list(v["codes"]) if is_placeholder(v) else list(e.get("products") or [])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="connector-plan.json of the run (master locale)")
    ap.add_argument("--env", default="development")
    ap.add_argument("--starter-pack", default=DEFAULT_STARTER)
    a = ap.parse_args()
    if not (low.KEY and low.TOKEN):
        low.die("CS_API_KEY and CS_MANAGEMENT_TOKEN (or a csdx login) must be set")

    codes = carousel_codes(json.load(open(a.plan)))
    if not codes:
        low.die("the plan has no product carousels")

    print(f"[{CT}] re-import without sap_products")
    starter = seeder.load_starter_types(a.starter_pack)
    seeder.import_content_types([CT], {CT: starter[CT]}, sap_ext=None)

    st, r = low.cma("GET", "/locales")
    locales = [l["code"] for l in (r.get("locales") or [])] or [low.MASTER]
    for sap_uid, skus in codes.items():
        q = urllib.parse.quote(json.dumps({"sap_uid": sap_uid}))
        st, r = low.cma("GET", f"/content_types/{CT}/entries?query={q}&locale={low.MASTER}&limit=1")
        found = r.get("entries") or []
        if not found:
            print(f"  {sap_uid}: not found on the stack, skipped"); continue
        uid = found[0]["uid"]
        done = []
        for loc in locales:
            st, r = low.cma("GET", f"/content_types/{CT}/entries/{uid}?locale={loc}")
            e = r.get("entry") or {}
            if e.get("locale") != loc:          # not localized in this locale: inherits master
                continue
            st, r = low.cma("PUT", f"/content_types/{CT}/entries/{uid}?locale={loc}",
                            {"entry": {"products": skus}})
            if st != 200:
                print(f"  {sap_uid} [{loc}]: PUT {st} {json.dumps(r)[:120]}"); continue
            ver = r["entry"]["_version"]
            st, r = low.cma("POST", f"/content_types/{CT}/entries/{uid}/publish?locale={loc}",
                            {"entry": {"environments": [a.env], "locales": [loc]},
                             "locale": loc, "version": ver})
            done.append(loc if st in (200, 201) else f"{loc}(publish {st})")
        print(f"  {sap_uid}: {len(skus)} SKUs in products -> {done}")


if __name__ == "__main__":
    main()
