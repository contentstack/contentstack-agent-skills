#!/usr/bin/env python3
"""
verify_connector — round-trip verification for the CONNECTOR profile (Phase 4b).

Reads the seeded connector-model entries back from the stack, reverse-maps each authored
component to its original OCC shape, and diffs against the original inventory. Only the
AUTHORED components (those the connector profile seeds) are checked — functional components
are intentionally left to OCC and not in Contentstack.

Read-only. Creds from env: CS_API_KEY, CS_MANAGEMENT_TOKEN, CS_REGION_BASE.

Usage: python3 verify_connector.py --inventory <fixture.json> --plan <connector-plan.json> [--verbose]
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request
from collections import defaultdict

API = os.environ.get("CS_REGION_BASE", "https://api.contentstack.io").rstrip("/")
KEY, TOKEN = os.environ.get("CS_API_KEY"), os.environ.get("CS_MANAGEMENT_TOKEN")

# connector content type -> OCC typeCode (subset we author)
CT_TO_TYPECODE = {
    "simple_responsive_banner_component": "SimpleResponsiveBannerComponent",
    "simple_banner_component": "SimpleBannerComponent",
    "product_carousel_component": "ProductCarouselComponent",
    "cms_paragraph_component": "CMSParagraphComponent",
    "cms_link_component": "CMSLinkComponent",
    "cms_flex_component": "CMSFlexComponent",
}


def cma(path):
    req = urllib.request.Request(f"{API}/v3{path}")
    req.add_header("api_key", KEY); req.add_header("authorization", TOKEN)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())


def all_entries(ct):
    out, skip = [], 0
    while True:
        r = cma(f"/content_types/{ct}/entries?limit=100&skip={skip}&include_count=true")
        es = r.get("entries") or []
        out += es; skip += len(es)
        if len(es) < 100 or skip >= (r.get("count") or 0):
            break
    return out


def asset_titles():
    out, skip = {}, 0
    while True:
        r = cma(f"/assets?limit=100&skip={skip}&include_count=true")
        a = r.get("assets") or []
        for x in a:
            out[x["uid"]] = x.get("title")
        skip += len(a)
        if len(a) < 100 or skip >= (r.get("count") or 0):
            break
    return out


def norm_html(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def as_target(v):
    return "true" if str(v).strip().lower() == "true" else "false"


def _uid(v):
    if isinstance(v, list) and v:
        return v[0] if isinstance(v[0], str) else v[0].get("uid")
    return v if isinstance(v, str) else (v.get("uid") if isinstance(v, dict) else None)


def orig_proj(c):
    tc = c["typeCode"]
    m = c.get("media") or {}
    if tc == "SimpleResponsiveBannerComponent":
        codes = sorted(m[b]["code"] for b in ("mobile", "tablet", "desktop", "widescreen")
                       if isinstance(m.get(b), dict) and m[b].get("code"))
        return {"media": codes, "url_link": c.get("urlLink") or ""}
    if tc == "SimpleBannerComponent":
        return {"media": [m["code"]] if m.get("code") else [], "url_link": c.get("urlLink") or ""}
    if tc == "ProductCarouselComponent":
        return {"title": c.get("title") or "", "products": sorted((c.get("productCodes") or "").split())}
    if tc == "CMSParagraphComponent":
        return {"content": norm_html(c.get("content"))}
    if tc == "CMSLinkComponent":
        return {"link_name": c.get("linkName") or "", "url": c.get("url") or "",
                "target": as_target(c.get("target"))}
    if tc == "CMSFlexComponent":
        return {"flex_type": c.get("flexType") or ""}
    return {}


def cs_proj(e, ct, assets):
    if ct == "simple_responsive_banner_component":
        codes = sorted(assets.get(_uid(e.get(f))) for f in
                       ("media_mobile", "media_tablet", "media_desktop", "media_widescreen") if e.get(f))
        return {"media": [c for c in codes if c], "url_link": e.get("url_link") or ""}
    if ct == "simple_banner_component":
        c = assets.get(_uid(e.get("media")))
        return {"media": [c] if c else [], "url_link": e.get("url_link") or ""}
    if ct == "product_carousel_component":
        return {"title": e.get("title") or "", "products": sorted(e.get("products") or [])}
    if ct == "cms_paragraph_component":
        return {"content": norm_html(e.get("content"))}
    if ct == "cms_link_component":
        return {"link_name": e.get("link_name") or "", "url": e.get("url") or "",
                "target": as_target(e.get("target"))}
    if ct == "cms_flex_component":
        return {"flex_type": e.get("flex_type") or ""}
    return {}


def flatten_source_tree(root):
    """Flatten a source OCC navigationNode tree into
    {node_uid: (parent_uid, order, link_itemId)}. The root node is a pure
    container, so its children are the top level (parent '')."""
    flat = {}
    def walk(node, parent, order):
        uid = node.get("uid")
        if not uid:
            return
        entries = [e.get("itemId") for e in (node.get("entries") or [])
                   if e.get("itemType") == "CMSLinkComponent" and e.get("itemId")]
        flat[uid] = (parent, order, entries[0] if entries else None)
        for i, ch in enumerate(node.get("children") or [], start=1):
            walk(ch, uid, i)
    for i, ch in enumerate(root.get("children") or [], start=1):
        walk(ch, "", i)
    return flat


def verify_nav(inv, nav_orig, verbose):
    """Read the seeded FLAT nav back and diff each menu against its source tree.

    For every CategoryNavigation/FooterNavigation component: fetch the flat
    component, walk its all_nodes pool into nav_node_flat entries, reassemble the
    tree from node_id/parent_id, and diff each node's (parent, sort_order, link)
    against the original OCC navigationNode tree. Proves the flat model faithfully
    represents the source hierarchy — the same reassembly the connector does at
    runtime. Returns (checked, ok, issues)."""
    FLAT_CT = ("category_navigation_flat", "footer_navigation_flat")
    comps = {}
    for ct in FLAT_CT:
        for e in all_entries(ct):
            if e.get("sap_uid"):
                comps[e["sap_uid"]] = e
    nodes_by_csuid = {e["uid"]: e for e in all_entries("nav_node_flat")}
    link_sap_by_csuid = {e["uid"]: e.get("sap_uid") for e in all_entries("cms_link_component")}

    def node_link_sap(n):
        u = _uid(n.get("links")) if n.get("links") else None
        return link_sap_by_csuid.get(u) if u else None

    checked = ok = 0
    issues = []
    for cuid, c in nav_orig.items():
        checked += 1
        root = c.get("navigationNode") or {}
        if not root.get("children"):
            root = (inv.get("navigation") or {}).get(root.get("uid"), root)
        src = flatten_source_tree(root)
        cs = comps.get(cuid)
        if not cs:
            issues.append((cuid, ["flat component missing in stack"])); continue
        got = {}
        for r in cs.get("all_nodes") or []:
            n = nodes_by_csuid.get(r.get("uid") if isinstance(r, dict) else r)
            if n and n.get("node_id"):
                got[n["node_id"]] = (n.get("parent_id") or "", n.get("sort_order"), node_link_sap(n))
        diffs = []
        for nid, (p, o, lk) in src.items():
            if nid not in got:
                diffs.append(f"missing node {nid}"); continue
            gp, go, glk = got[nid]
            if gp != p:
                diffs.append(f"{nid}: parent {gp!r}!={p!r}")
            if go != o:
                diffs.append(f"{nid}: sort {go}!={o}")
            if glk != lk:
                diffs.append(f"{nid}: link {glk}!={lk}")
        extra = sorted(set(got) - set(src))
        if extra:
            diffs.append(f"extra nodes {extra}")
        if not diffs:
            ok += 1
        else:
            issues.append((cuid, diffs))
        if verbose:
            print(f"    nav {cuid}: source {len(src)} nodes, stack {len(got)} "
                  f"-> {'OK' if not diffs else diffs[:4]}")
    return checked, ok, issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    if not (KEY and TOKEN):
        sys.exit("set CS_API_KEY and CS_MANAGEMENT_TOKEN")
    inv = json.load(open(a.inventory))
    plan = json.load(open(a.plan))

    # original components by uid
    orig = {}
    for p in inv["contentPages"].values():
        for s in p["slots"]:
            for c in s["components"]:
                if c.get("uid"):
                    orig.setdefault(c["uid"], c)

    # which uids we actually seeded (from the plan)
    seeded_uids = {e["_key"]["value"] for e in plan["entries"]["components"]}

    assets = asset_titles()
    # fetch seeded component entries by content type, index by sap_uid
    cs_by_uid, cs_ct = {}, {}
    for ct in CT_TO_TYPECODE:
        for e in all_entries(ct):
            u = e.get("sap_uid")
            if u:
                cs_by_uid[u] = e; cs_ct[u] = ct

    per = defaultdict(lambda: {"n": 0, "match": 0})
    mismatches, missing = [], []
    NAV_TYPES = {"CategoryNavigationComponent", "FooterNavigationComponent"}
    for uid in seeded_uids:
        c = orig.get(uid)
        if not c:
            continue
        tc = c["typeCode"]
        if tc in NAV_TYPES:            # nav components verified separately (nav tree read), not here
            continue
        cs = cs_by_uid.get(uid)
        if not cs:
            missing.append(uid); continue
        want, got = orig_proj(c), cs_proj(cs, cs_ct[uid], assets)
        per[tc]["n"] += 1
        if want == got:
            per[tc]["match"] += 1
        else:
            mismatches.append((tc, uid, {k: (want.get(k), got.get(k))
                                         for k in set(want) | set(got) if want.get(k) != got.get(k)}))

    total = sum(r["n"] for r in per.values())
    matched = sum(r["match"] for r in per.values())
    print(f"[verify_connector] {inv['site']} @ {API}")
    print(f"  authored components checked: {total}  matched: {matched}  "
          f"mismatched: {total - matched}  missing-in-stack: {len(missing)}")
    for tc in sorted(per):
        print(f"    {tc:34s} {per[tc]['match']}/{per[tc]['n']}")
    if missing:
        print("  MISSING:", missing[:10])
    if mismatches and a.verbose:
        for tc, uid, d in mismatches[:15]:
            print(f"  {tc} {uid}: {json.dumps(d)[:200]}")

    # flat navigation: reassemble the seeded nav_node_flat pool and diff the tree
    # against the source (skipped in the per-component loop above).
    nav_orig = {uid: c for uid, c in orig.items() if c["typeCode"] in NAV_TYPES}
    nav_checked, nav_ok, nav_issues = verify_nav(inv, nav_orig, a.verbose)
    if nav_checked:
        print(f"  nav menus (flat) checked: {nav_checked}  trees match: {nav_ok}")
        for cuid, diffs in nav_issues:
            print(f"    NAV MISMATCH {cuid}: {diffs[:6]}")

    comp_ok = (matched == total and not missing and total > 0)
    nav_pass = (nav_ok == nav_checked)
    ok = comp_ok and nav_pass
    print("  RESULT:", "PASS — connector model round-trips (components + nav)" if ok
          else f"{total-matched} comp mismatch / {len(missing)} missing / "
               f"{nav_checked-nav_ok} nav mismatch")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
