#!/usr/bin/env python3
"""
nav_resolve — the deferred navigation resolve pass (enriches an inventory in place).

storefront-extract captures the navigationNode trees, but each link leaf is only a
reference ({itemId, itemType: CMSLinkComponent}). This pass batch-resolves those leaves
from OCC (/cms/components) into full link detail, so the connector model can seed a
nav_node tree with real cms_link_component leaves.

Adds two keys to the inventory:
  navigationLinks : { itemId -> {link_name, url, target, external, name} }
  navigationRoots : { componentUid -> rootNodeUid }   (from CategoryNavigation/FooterNavigation)

Usage: python3 nav_resolve.py --inventory <fixture.json> --site electronics-spa [--base URL]
"""
import argparse, json, os, ssl, sys, urllib.parse, urllib.request

DEFAULT_BASE = os.environ.get("OCC_BASE_URL")


def occ_ssl_context():
    """TLS context for OCC calls. Verified by default; set OCC_INSECURE_TLS=1 only for a
    dev backend with a self-signed certificate you trust."""
    ctx = ssl.create_default_context()
    if os.environ.get("OCC_INSECURE_TLS") == "1":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


CTX = occ_ssl_context()


def _get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, context=CTX, timeout=40) as r:
        return json.loads(r.read().decode())


def occ_components(base, site, ids, lang="en"):
    out = {}
    for i in range(0, len(ids), 10):
        chunk = ids[i:i + 10]
        url = f"{base}/{site}/cms/components?" + urllib.parse.urlencode(
            {"componentIds": ",".join(chunk), "lang": lang})
        try:
            d = _get(url)
            for c in (d.get("component") or d.get("components") or []):
                out[c.get("uid")] = c
        except Exception as e:
            print(f"  batch chunk failed: {e}", file=sys.stderr)
    # single-GET fallback for anything the batch didn't return
    missing = [i for i in ids if i not in out]
    for iid in missing:
        try:
            c = _get(f"{base}/{site}/cms/components/{iid}?lang={lang}")
            if c.get("uid"):
                out[c["uid"]] = c
        except Exception:
            pass
    return out


def collect_link_ids(node, ids):
    for e in (node.get("entries") or []):
        if isinstance(e, dict) and e.get("itemType") == "CMSLinkComponent" and e.get("itemId"):
            ids.add(e["itemId"])
    for ch in (node.get("children") or []):
        collect_link_ids(ch, ids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--site", required=True)
    ap.add_argument("--base", default=DEFAULT_BASE, required=DEFAULT_BASE is None,
                    help="OCC v2 base URL (or set OCC_BASE_URL)")
    ap.add_argument("--lang", default="en", help="OCC language for localized nav labels")
    a = ap.parse_args()
    inv = json.load(open(a.inventory))

    nav = inv.get("navigation", {})
    ids = set()
    for node in nav.values():
        collect_link_ids(node, ids)
    print(f"[nav_resolve] {a.site} (lang={a.lang}): {len(nav)} root nodes, {len(ids)} link leaves to resolve")

    resolved = occ_components(a.base, a.site, sorted(ids), lang=a.lang)
    links = {}
    for iid, c in resolved.items():
        links[iid] = {"link_name": c.get("linkName"), "url": c.get("url"),
                      "target": c.get("target"), "external": c.get("external"),
                      "name": c.get("name")}
    inv["navigationLinks"] = links

    # component uid -> root node uid, from the nav components in the inventory
    roots = {}
    for p in inv.get("contentPages", {}).values():
        for s in p.get("slots", []):
            for comp in s.get("components", []):
                if comp.get("typeCode") in ("CategoryNavigationComponent", "FooterNavigationComponent"):
                    nn = comp.get("navigationNode") or {}
                    if nn.get("uid"):
                        roots[comp["uid"]] = {"root": nn["uid"], "typeCode": comp["typeCode"],
                                              "position": s.get("position"),
                                              "wrapAfter": comp.get("wrapAfter")}
    inv["navigationRoots"] = roots

    json.dump(inv, open(a.inventory, "w"), indent=2)
    print(f"  resolved {len(links)}/{len(ids)} links; {len(roots)} nav components "
          f"-> {sorted((r['typeCode'], r['position']) for r in roots.values())}")
    print(f"  enriched -> {a.inventory}")


if __name__ == "__main__":
    main()
