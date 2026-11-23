#!/usr/bin/env python3
"""
cma_seed_connector — live seeder for the CONNECTOR reference-field profile (Phase 4b).

Imports the connector's shipped starter-pack content types into the stack, then applies a
connector-plan.json (from model_connector) idempotently:
  content types (starter pack, +sap_uid idempotency field on components)
  -> assets -> component entries (by sap_uid) -> global_slots (by title) -> pages (by url).

Reuses low-level CMA helpers from cma_seed.py. Creds from env (CS_API_KEY,
CS_MANAGEMENT_TOKEN, CS_REGION_BASE). English/master locale only.

Usage:
  python3 cma_seed_connector.py --plan <dir>/connector-plan.json \
      --starter-pack <connector>/import-export/starter-pack/content_types \
      --stages types,assets,entries
"""
import argparse, json, os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "marketplace-app"))
import cma_seed as low   # reuse cma(), asset_lookup(), upsert_asset(), download_occ, multipart
from sap_products import SapProductResolver, is_placeholder

PAGE_TYPES = {"landing_page", "content_page", "product_page", "category_page"}
GLOBAL_TYPE = "global_slots"

SAP_UID_FIELD = {"display_name": "SAP UID", "uid": "sap_uid", "data_type": "text",
                 "mandatory": False, "unique": True, "multiple": False,
                 "field_metadata": {"instruction": "Seed idempotency key = SAP component uid."}}


def sap_products_field(extension_uid):
    """The SAP Commerce Cloud app's product picker, as a carousel field. The extension uid is
    per stack (from sap_app.py), so it is injected at import time, not shipped in the pack."""
    return {"display_name": "SAP Products", "uid": "sap_products", "data_type": "json",
            "extension_uid": extension_uid, "config": {},
            "field_metadata": {"extension": True, "description":
                               "Pick products from SAP Commerce Cloud. The storefront reads the product codes from here."},
            "mandatory": False, "unique": False, "multiple": False, "non_localizable": False}


def load_starter_types(dir_):
    out = {}
    for fn in os.listdir(dir_):
        if fn.endswith(".json"):
            ct = json.load(open(os.path.join(dir_, fn)))
            out[ct["uid"]] = ct
    return out


def topo_types(starter):
    """Order all starter content types so every reference target precedes its user."""
    ordered, seen = [], set()
    def deps(ct):
        d = set()
        for f in ct.get("schema", []):
            if f.get("data_type") == "reference":
                for t in (f.get("reference_to") or []):
                    if t in starter and t != ct["uid"]:
                        d.add(t)
        return d
    def visit(uid, stack):
        if uid in seen or uid in stack:
            return
        stack.add(uid)
        for d in deps(starter[uid]):
            visit(d, stack)
        stack.discard(uid); seen.add(uid); ordered.append(uid)
    for uid in starter:
        visit(uid, set())
    return ordered


def import_content_types(needed, starter, sap_ext=None, verbose=True):
    """Returns the number of content types that failed to import."""
    # Import the FULL shipped model (topo-ordered) so every reference_to resolves,
    # even for types whose entries we defer (nav). Inject sap_uid on component types,
    # and the SAP app's product picker on the carousel when the app is set up.
    order = topo_types(starter)
    errors = 0
    for uid in order:
        ct = json.loads(json.dumps(starter[uid]))
        is_component = uid not in PAGE_TYPES and uid != GLOBAL_TYPE
        if is_component and not any(f.get("uid") == "sap_uid" for f in ct["schema"]):
            ct["schema"].append(dict(SAP_UID_FIELD))
        if uid == "product_carousel_component" and sap_ext:
            ct["schema"] = [f for f in ct["schema"] if f.get("uid") != "sap_products"]
            at = next((i + 1 for i, f in enumerate(ct["schema"]) if f.get("uid") == "products"),
                      len(ct["schema"]))
            ct["schema"].insert(at, sap_products_field(sap_ext))
        st, _ = low.cma("GET", f"/content_types/{uid}")
        body = {"content_type": ct}
        if st == 200:
            st2, r = low.cma("PUT", f"/content_types/{uid}", body)
            res = "updated" if st2 == 200 else f"ERR {st2}:{json.dumps(r)[:200]}"
        else:
            st2, r = low.cma("POST", "/content_types", body)
            res = "created" if st2 in (200, 201) else f"ERR {st2}:{json.dumps(r)[:200]}"
        if verbose or res.startswith("ERR"):
            print(f"  {uid}: {res}")
        errors += res.startswith("ERR")
    return errors


def resolve(v, uid_map, asset_cache, sap=None):
    if isinstance(v, dict):
        if v.get("_asset"):
            return asset_cache.get(v["code"])
        if v.get("_ref"):
            uid = uid_map.get(v["value"])
            return [{"uid": uid, "_content_type_uid": v["content_type"]}] if uid else None
        if is_placeholder(v):
            return sap.resolve(v)
        return {k: resolve(x, uid_map, asset_cache, sap) for k, x in v.items()}
    if isinstance(v, list):
        out = []
        for x in v:
            rv = resolve(x, uid_map, asset_cache, sap)
            if isinstance(x, dict) and x.get("_ref"):
                if rv:
                    out.extend(rv)
            else:
                out.append(rv)
        return out
    return v


def entry_body(e, uid_map, asset_cache, sap=None):
    return {"entry": {k: resolve(v, uid_map, asset_cache, sap)
                      for k, v in e.items() if not k.startswith("_")}}


def find_uid(ct, field, value):
    q = urllib.parse.quote(json.dumps({field: value}))
    st, r = low.cma("GET", f"/content_types/{ct}/entries?query={q}&limit=1")
    return (r.get("entries") or [{}])[0].get("uid") if st == 200 else None


def upsert_entry(e, uid_map, asset_cache, sap=None):
    ct = e["_content_type"]; kf, kv = e["_key"]["field"], e["_key"]["value"]
    body = entry_body(e, uid_map, asset_cache, sap)
    existing = find_uid(ct, kf, kv)
    if existing:
        st, r = low.cma("PUT", f"/content_types/{ct}/entries/{existing}", body)
        uid, res = existing, ("updated" if st == 200 else f"ERR {st}:{json.dumps(r)[:160]}")
    else:
        st, r = low.cma("POST", f"/content_types/{ct}/entries", body)
        uid, res = r.get("entry", {}).get("uid"), ("created" if st in (200, 201) else f"ERR {st}:{json.dumps(r)[:160]}")
    if uid and kf == "sap_uid":
        uid_map[kv] = uid
    return res, uid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--starter-pack", required=True)
    ap.add_argument("--stages", default="types,assets,entries")
    ap.add_argument("--sap-app", help="sap-app.json from marketplace-app/sap_app.py "
                                      "(required when the plan seeds carousels into sap_products)")
    a = ap.parse_args()
    if not (low.KEY and low.TOKEN):
        low.die("CS_API_KEY and CS_MANAGEMENT_TOKEN must be set")
    stages = set(s.strip() for s in a.stages.split(","))
    plan = json.load(open(a.plan))
    uid_map, asset_cache = {}, {}
    failures = 0   # per-item errors; exit 3 at the end so the orchestrator reports the stage as warn
    sap_ext, sap = None, None
    if plan.get("carousel_field") == "sap_products":
        if not a.sap_app:
            low.die("plan seeds carousels into sap_products — pass --sap-app <sap-app.json>")
        sap_ext = json.load(open(a.sap_app))["product_extension_uid"]
        sap = SapProductResolver(site=plan.get("site"))

    if "types" in stages:
        print("[content types] (starter pack, +sap_uid on components"
              f"{', +sap_products on carousel' if sap_ext else ''})")
        failures += import_content_types(plan["content_types_needed"], load_starter_types(a.starter_pack), sap_ext)

    if "assets" in stages:
        print(f"[assets] {len(plan['assets'])}")
        ok = err = 0
        for asset in plan["assets"]:
            r = low.upsert_asset(asset, asset_cache)
            ok += 1 if not r.startswith("ERR") else 0
            err += 1 if r.startswith("ERR") else 0
            if r.startswith("ERR"):
                print(f"  {asset['code']}: {r}")
        print(f"  assets: {ok} ok, {err} err")
        failures += err

    if "entries" in stages:
        if not asset_cache:                       # resolve existing assets for banner refs
            for asset in plan["assets"]:
                u = low.asset_lookup(asset["code"])
                if u:
                    asset_cache[asset["code"]] = u
        comps = plan["entries"]["components"]
        print(f"[components] {len(comps)}")
        ok = err = 0
        for e in comps:
            res, _ = upsert_entry(e, uid_map, asset_cache, sap)
            ok += 1 if not res.startswith("ERR") else 0
            if res.startswith("ERR"):
                err += 1
                if err <= 6:
                    print(f"  {e['_key']['value']}: {res}")
        print(f"  components: {ok} ok, {err} err")
        failures += err
        if sap:
            print(f"  sap_products: {len(sap.cache) - len(sap.missing)} products resolved on the app's SAP server"
                  + (f", NOT FOUND (left out): {[c for c, _ in sap.missing]}" if sap.missing else ""))
        gs = plan["entries"].get("global_slots")
        if gs:
            res, _ = upsert_entry(gs, uid_map, asset_cache, sap)
            print(f"[global_slots] {res}")
            failures += res.startswith("ERR")
        pages = plan["entries"]["pages"]
        print(f"[pages] {len(pages)}")
        ok = err = 0
        for e in pages:
            res, _ = upsert_entry(e, uid_map, asset_cache, sap)
            ok += 1 if not res.startswith("ERR") else 0
            if res.startswith("ERR"):
                err += 1; print(f"  {e['_key']['value']}: {res}")
        print(f"  pages: {ok} ok, {err} err")
        failures += err
    if failures:
        print(f"[seed] {failures} item(s) failed — see the ERR lines above; re-running is safe")
        sys.exit(3)


if __name__ == "__main__":
    main()
