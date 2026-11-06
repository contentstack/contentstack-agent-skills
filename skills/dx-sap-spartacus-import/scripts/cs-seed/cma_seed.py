#!/usr/bin/env python3
"""
cma_seed — live Contentstack Management API executor for the seed plan.

Applies a content-model output (content-types.json + entry-plan.json) to a real stack,
idempotently and in dependency order. English (master locale) only unless --locales given.

Reads credentials from env: CS_API_KEY, CS_MANAGEMENT_TOKEN, CS_REGION_BASE
(default https://api.contentstack.io). Never logs the token.

Stages (comma list, default all): globals,content_types,assets,entries
  python3 cma_seed.py --model-dir DIR --site electronics-spa --stages globals,content_types
  python3 cma_seed.py --model-dir DIR --site electronics-spa            # full run

Idempotent: content types & global fields by uid; assets by a `sap_code:<code>` tag;
entries by their unique key field. Re-running updates in place.
"""
import argparse, json, mimetypes, os, ssl, sys, time, urllib.parse, urllib.request

API = os.environ.get("CS_REGION_BASE", "https://api.contentstack.io").rstrip("/")
KEY = os.environ.get("CS_API_KEY")
TOKEN = os.environ.get("CS_MANAGEMENT_TOKEN")
MASTER = os.environ.get("CS_MASTER_LOCALE", "en-us")
OCC_HOST = (os.environ.get("OCC_BASE_URL") or "").split("/occ/")[0]


def occ_ssl_context():
    """TLS context for OCC calls. Verified by default; set OCC_INSECURE_TLS=1 only for a
    dev backend with a self-signed certificate you trust."""
    ctx = ssl.create_default_context()
    if os.environ.get("OCC_INSECURE_TLS") == "1":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


OCC_CTX = occ_ssl_context()


def die(msg):
    sys.exit(f"[cma_seed] ERROR: {msg}")


def cma(method, path, body=None, raw=None, content_type=None, retry=3):
    url = f"{API}/v3{path}"
    data, ct = None, None
    if raw is not None:
        data, ct = raw, content_type
    elif body is not None:
        data, ct = json.dumps(body).encode(), "application/json"
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("api_key", KEY)
    req.add_header("authorization", TOKEN)
    if ct:
        req.add_header("Content-Type", ct)
    for attempt in range(retry):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            payload = e.read().decode()
            if e.code == 429 and attempt < retry - 1:      # rate limited
                time.sleep(1.5 * (attempt + 1)); continue
            try:
                return e.code, json.loads(payload)
            except Exception:
                return e.code, {"_raw": payload}
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(1); continue
            return 0, {"_error": str(e)}
    return 0, {"_error": "unreachable"}


# ---------------- schema normalization ----------------
def ensure_title(ct):
    """Contentstack requires a text field with uid 'title'. Inject one if absent and
    point options.title at it. Other fields (page_label, slot_id, sap_name...) stay."""
    fields = ct.setdefault("schema", [])
    if not any(f.get("uid") == "title" for f in fields):
        fields.insert(0, {"display_name": "Title", "uid": "title", "data_type": "text",
                          "mandatory": True, "unique": False,
                          "field_metadata": {"_default": True}, "multiple": False})
    ct.setdefault("options", {})
    ct["options"]["title"] = "title"
    ct["options"].setdefault("singleton", False)
    # scrub any leftover _default on non-title fields (only title may be default)
    for f in fields:
        if f.get("uid") != "title":
            fm = f.get("field_metadata") or {}
            fm.pop("_default", None)
    return ct


def html_rte_field(uid, display):
    return {"display_name": display, "uid": uid, "data_type": "text",
            "field_metadata": {"allow_rich_text": True, "rich_text_type": "advanced",
                               "description": "", "multiline": False, "version": 3},
            "multiple": False, "mandatory": False, "unique": False}


def normalize_content_type(ct):
    """Make the registry-derived schema CMA-safe."""
    ct = json.loads(json.dumps(ct))  # deep copy
    # rich_text.content -> HTML-based advanced RTE (stores HTML directly; round-trips clean)
    if ct["uid"] == "rich_text":
        ct["schema"] = [f for f in ct["schema"] if f.get("uid") != "content"]
        ct["schema"].append(html_rte_field("content", "Content"))
    # passthrough config: CS has no generic JSON field -> store JSON as multiline text
    if ct["uid"] == "passthrough_component":
        for f in ct["schema"]:
            if f.get("uid") == "config":
                f["data_type"] = "text"
                f["field_metadata"] = {"description": "JSON-encoded verbatim OCC fields",
                                       "multiline": True}
                f.pop("enum", None)
    for f in ct["schema"]:
        if f.get("data_type") in ("reference", "global_field"):
            f.setdefault("field_metadata", {})
        if f.get("data_type") == "reference":
            f["field_metadata"].setdefault("ref_multiple", bool(f.get("field_metadata", {}).get("ref_multiple")))
        # CS select fields (enum) require a display_type
        if f.get("enum"):
            f["display_type"] = "dropdown"
            f.setdefault("field_metadata", {})
    return ensure_title(ct)


# ---------------- idempotent upserts ----------------
def upsert_global_field(gf):
    uid = gf["uid"]
    st, _ = cma("GET", f"/global_fields/{uid}")
    body = {"global_field": gf}
    if st == 200:
        st2, r = cma("PUT", f"/global_fields/{uid}", body)
        return "updated" if st2 == 200 else f"ERR {st2}:{r}"
    st2, r = cma("POST", "/global_fields", body)
    return "created" if st2 in (200, 201) else f"ERR {st2}:{json.dumps(r)[:300]}"


def upsert_content_type(ct):
    uid = ct["uid"]
    st, _ = cma("GET", f"/content_types/{uid}")
    body = {"content_type": ct}
    if st == 200:
        st2, r = cma("PUT", f"/content_types/{uid}", body)
        return "updated" if st2 == 200 else f"ERR {st2}:{json.dumps(r)[:400]}"
    st2, r = cma("POST", "/content_types", body)
    return "created" if st2 in (200, 201) else f"ERR {st2}:{json.dumps(r)[:400]}"


def download_occ(url):
    full = url if url.startswith("http") else OCC_HOST + url
    with urllib.request.urlopen(urllib.request.Request(full), context=OCC_CTX, timeout=60) as r:
        return r.read()


def multipart(fields, filename, filedata, mime):
    boundary = "----csseed" + str(len(filedata))
    out = []
    for k, v in fields.items():
        out.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    out.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"asset[upload]\"; "
                f"filename=\"{filename}\"\r\nContent-Type: {mime}\r\n\r\n").encode())
    out.append(filedata)
    out.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def asset_lookup(code):
    """Idempotency key = asset title (= the media code; no length limit, unlike tags)."""
    q = urllib.parse.quote(json.dumps({"title": code}))
    st, r = cma("GET", f"/assets?query={q}&limit=1")
    if st == 200 and r.get("assets"):
        return r["assets"][0]["uid"]
    return None


def upsert_asset(a, cache):
    code = a["code"]
    existing = asset_lookup(code)
    if existing:
        cache[code] = existing
        return "exists"
    try:
        data = download_occ(a["url"])
    except Exception as e:
        return f"ERR download:{e}"
    fname = code.split("/")[-1].split("?")[0] or "asset"
    mime = a.get("mime") or mimetypes.guess_type(fname)[0] or "application/octet-stream"
    short_tag = "sapmedia_" + str(abs(hash(code)) % 10**10)   # <=50 chars, stable within run
    raw, ct = multipart({"asset[title]": code, "asset[tags]": short_tag}, fname, data, mime)
    st2, r2 = cma("POST", "/assets", raw=raw, content_type=ct)
    if st2 in (200, 201):
        cache[code] = r2["asset"]["uid"]
        return "created"
    return f"ERR {st2}:{json.dumps(r2)[:200]}"


def resolve_value(v, key2uid, asset_cache):
    """Turn plan placeholders (_ref/_asset/_rte_from_html) into CMA entry values."""
    if isinstance(v, dict):
        if v.get("_asset"):
            return asset_cache.get(v["code"])
        if v.get("_ref"):
            uid = key2uid.get((v["content_type"], v["value"]))
            return [{"uid": uid, "_content_type_uid": v["content_type"]}] if uid else None
        if "_rte_from_html" in v:
            return v["_rte_from_html"] or ""
        return {k: resolve_value(x, key2uid, asset_cache) for k, x in v.items()}
    if isinstance(v, list):
        out = []
        for x in v:
            rv = resolve_value(x, key2uid, asset_cache)
            if isinstance(x, dict) and x.get("_ref"):
                if rv:
                    out.extend(rv)               # flatten single-ref arrays into the list
            else:
                out.append(rv)
        return out
    return v


def entry_payload(e, key2uid, asset_cache):
    skip = {"_content_type", "_key", "_localized"}
    body = {}
    for k, v in e.items():
        if k in skip:
            continue
        body[k] = resolve_value(v, key2uid, asset_cache)
    # passthrough config is a multiline-text field holding JSON
    if e.get("_content_type") == "passthrough_component" and isinstance(body.get("config"), (dict, list)):
        body["config"] = json.dumps(body["config"], ensure_ascii=False)
    return {"entry": body}


def find_entry_uid(ct, key_field, key_value):
    q = urllib.parse.quote(json.dumps({key_field: key_value}))
    st, r = cma("GET", f"/content_types/{ct}/entries?query={q}&limit=1")
    if st == 200 and r.get("entries"):
        return r["entries"][0]["uid"]
    return None


def upsert_entry(e, key2uid, asset_cache):
    ct = e["_content_type"]
    kf, kv = e["_key"]["field"], e["_key"]["value"]
    body = entry_payload(e, key2uid, asset_cache)
    existing = find_entry_uid(ct, kf, kv)
    if existing:
        st, r = cma("PUT", f"/content_types/{ct}/entries/{existing}", body)
        uid = existing
        status = "updated" if st == 200 else f"ERR {st}:{json.dumps(r)[:200]}"
    else:
        st, r = cma("POST", f"/content_types/{ct}/entries", body)
        uid = r.get("entry", {}).get("uid")
        status = "created" if st in (200, 201) else f"ERR {st}:{json.dumps(r)[:200]}"
    if uid:
        key2uid[(ct, kv)] = uid
    return status


# ---------------- driver ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--site", required=True)
    ap.add_argument("--stages", default="globals,content_types,assets,entries")
    ap.add_argument("--limit-entries", type=int, default=0, help="cap entries per group (smoke test)")
    a = ap.parse_args()
    if not (KEY and TOKEN):
        die("CS_API_KEY and CS_MANAGEMENT_TOKEN must be set in the environment")
    stages = set(s.strip() for s in a.stages.split(","))

    ct_doc = json.load(open(os.path.join(a.model_dir, "content-types.json")))
    ep = json.load(open(os.path.join(a.model_dir, "entry-plan.json")))

    # topo order for content types (reuse seed.py logic)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import seed
    order = seed.topo_content_types(ct_doc["content_types"])
    by_uid = {c["uid"]: c for c in ct_doc["content_types"]}

    key2uid, asset_cache = {}, {}

    if "globals" in stages:
        print("[globals]")
        for gf in ct_doc.get("global_fields", []):
            print(f"  {gf['uid']}: {upsert_global_field(gf)}")

    if "content_types" in stages:
        print("[content_types] (dependency order)")
        for uid in order:
            ct = normalize_content_type(by_uid[uid])
            print(f"  {uid}: {upsert_content_type(ct)}")

    if "assets" in stages:
        print(f"[assets] {len(ep['assets'])}")
        ok = err = 0
        for asset in ep["assets"]:
            r = upsert_asset(asset, asset_cache)
            if r.startswith("ERR"):
                err += 1; print(f"  {asset['code']}: {r}")
            else:
                ok += 1
        print(f"  assets: {ok} ok, {err} err, {len(asset_cache)} in cache")

    if "entries" in stages:
        # assets must be resolvable for banner refs even if we skipped the stage this run
        if not asset_cache and "assets" not in stages:
            for asset in ep["assets"]:
                uid = asset_lookup(asset["code"])
                if uid:
                    asset_cache[asset["code"]] = uid
        # Nav components hold an all_nodes pool of nav_node_flat entries, which in
        # turn reference `link` leaves (ordinary components). Refs resolve only
        # against entries already created this run (key2uid), so seed in this
        # order: non-nav components (incl. link leaves) -> nav_nodes -> nav
        # components -> slots -> pages.
        NAV_CTS = {"category_navigation_flat", "footer_navigation_flat"}
        comps = ep["entries"].get("components", [])
        seed_groups = [
            ("components", [e for e in comps if e["_content_type"] not in NAV_CTS]),
            ("nav_nodes", ep["entries"].get("nav_nodes", [])),
            ("nav_components", [e for e in comps if e["_content_type"] in NAV_CTS]),
            ("slots", ep["entries"]["slots"]),
            ("pages", ep["entries"]["pages"]),
        ]
        for group, items in seed_groups:
            if a.limit_entries:
                items = items[:a.limit_entries]
            print(f"[entries:{group}] {len(items)}")
            ok = err = 0
            for e in items:
                r = upsert_entry(e, key2uid, asset_cache)
                if r.startswith("ERR"):
                    err += 1
                    if err <= 5:
                        print(f"  {e['_key']['value']}: {r}")
                else:
                    ok += 1
            print(f"  {group}: {ok} ok, {err} err")


if __name__ == "__main__":
    main()
