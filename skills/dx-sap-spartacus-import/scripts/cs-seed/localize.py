#!/usr/bin/env python3
"""
localize — full per-locale localization from the FULLY LOCALIZED OCC response (i18n v2).

Unlike a field-diff, this drives off a complete localized inventory (extract.py run with
lang=de/ja/zh + nav_resolve --lang), so pages, components, nav AND per-locale media are all
localized. For one target locale it:
  1. uploads the locale's images (different per language, e.g. ...DE...) as CS assets,
  2. localizes EVERY authored entry (components + pages + global_slots + nav) by writing a
     locale variant (PUT ?locale) with localized scalar/text fields + localized asset refs;
     reference fields are left to inherit from master so they resolve to localized targets,
  3. publishes each localized entry to the environment in that locale (?locale=, required —
     else CS 141 "Localised entries can not be published from master locale").

The base (master en-us) entries must already be seeded. Matches entries by their key
(sap_uid / url / title). Idempotent. Creds from env (CS_API_KEY, CS_MANAGEMENT_TOKEN).

Usage:
  python3 localize.py --locale de-de --plan <localized-model>/connector-plan.json --env development
"""
import argparse, json, os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cma_seed as low   # cma(), upsert_asset(), asset_lookup(), download_occ


_LOCALE_NAMES = {"de-de": "German - Germany", "ja-jp": "Japanese - Japan",
                 "zh-cn": "Chinese - China", "fr-fr": "French - France",
                 "es-es": "Spanish - Spain", "it-it": "Italian - Italy"}


def ensure_locale(code, master):
    """Create the target locale (fallback = master) if the stack doesn't have it."""
    st, r = low.cma("GET", "/locales")
    if code in {l["code"] for l in (r.get("locales") or [])}:
        return "exists"
    st2, r2 = low.cma("POST", "/locales",
                      {"locale": {"code": code, "fallback_locale": master,
                                  "name": _LOCALE_NAMES.get(code, code)}})
    return "created" if st2 in (200, 201) else f"ERR {st2}:{json.dumps(r2)[:120]}"


def find_uid(ct, field, value, master):
    q = urllib.parse.quote(json.dumps({field: value}))
    st, r = low.cma("GET", f"/content_types/{ct}/entries?query={q}&locale={master}&limit=1")
    es = r.get("entries") or []
    return es[0]["uid"] if es else None


def loc_fields(e, asset_cache, ref_uid):
    """Full localized payload. IMPORTANT: a Contentstack localized entry is standalone —
    it does NOT per-field-inherit from master, so we must send EVERY field, including
    reference fields (resolved to the shared entry uids, which point to the localized
    versions at query time) and localized asset uids."""
    def resolve(v):
        if isinstance(v, dict):
            if v.get("_asset"):
                return asset_cache.get(v["code"])
            if v.get("_ref"):
                uid = ref_uid(v["content_type"], v["value"])
                return [{"uid": uid, "_content_type_uid": v["content_type"]}] if uid else None
            return {k: resolve(x) for k, x in v.items()}
        if isinstance(v, list):
            out = []
            for x in v:
                rv = resolve(x)
                if isinstance(x, dict) and x.get("_ref"):
                    if rv:
                        out.extend(rv)
                elif rv is not None:
                    out.append(rv)
            return out
        return v
    return {k: resolve(v) for k, v in e.items() if not k.startswith("_") and k != "sap_meta"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--locale", required=True, help="target CS locale, e.g. de-de")
    ap.add_argument("--plan", required=True, help="connector-plan.json from the LOCALIZED inventory")
    ap.add_argument("--env", default="development")
    ap.add_argument("--master", default="en-us")
    a = ap.parse_args()
    if not (low.KEY and low.TOKEN):
        low.die("CS_API_KEY and CS_MANAGEMENT_TOKEN must be set")
    loc = a.locale
    plan = json.load(open(a.plan))
    print(f"[{loc}] locale: {ensure_locale(loc, a.master)}")

    # 1) localized assets (different image per language) -> code->uid, then PUBLISH them
    # (unpublished assets are not delivered -> nested banner media resolves to null).
    asset_cache = {}
    ok = err = 0
    for asset in plan.get("assets", []):
        r = low.upsert_asset(asset, asset_cache)   # downloads localized bytes, uploads by title
        ok += 1 if not r.startswith("ERR") else 0
        err += 1 if r.startswith("ERR") else 0
    pub = 0
    for aid in set(asset_cache.values()):
        st, _ = low.cma("POST", f"/assets/{aid}/publish",
                        {"asset": {"environments": [a.env], "locales": [a.master, loc]}})
        pub += 1 if st in (200, 201) else 0
    print(f"[{loc}] assets: {ok} ok, {err} err, {len(asset_cache)} resolved, {pub} published")

    # resolve a reference target's entry uid by sap_uid (shared across locales), cached
    ref_cache = {}
    def ref_uid(ct, sap_uid):
        key = (ct, sap_uid)
        if key not in ref_cache:
            ref_cache[key] = find_uid(ct, "sap_uid", sap_uid, a.master)
        return ref_cache[key]

    def do(entries, label):
        put_ok = pub_ok = miss = e_err = 0
        for e in entries:
            ct = e["_content_type"]; kf = e["_key"]["field"]; kv = e["_key"]["value"]
            uid = find_uid(ct, kf, kv, a.master)
            if not uid:
                miss += 1; continue
            fields = loc_fields(e, asset_cache, ref_uid)
            st, r = low.cma("PUT", f"/content_types/{ct}/entries/{uid}?locale={loc}", {"entry": fields})
            if st not in (200, 201):
                e_err += 1
                if e_err <= 4:
                    print(f"    {loc} {ct}/{kv}: PUT {st} {json.dumps(r)[:120]}")
                continue
            put_ok += 1
            st2, _ = low.cma("POST", f"/content_types/{ct}/entries/{uid}/publish?locale={loc}",
                             {"entry": {"environments": [a.env], "locales": [loc]}})
            pub_ok += 1 if st2 in (200, 201) else 0
        print(f"  [{loc}] {label}: localized {put_ok}, published {pub_ok}, missing {miss}, err {e_err}")

    do(plan["entries"]["components"], "components+nav")
    if plan["entries"].get("global_slots"):
        do([plan["entries"]["global_slots"]], "global_slots")
    do(plan["entries"]["pages"], "pages")


if __name__ == "__main__":
    main()
