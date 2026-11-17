#!/usr/bin/env python3
"""
cda_read — simulate the connector's delivery-time fetch (Phase 4b render pre-check).

Uses the DELIVERY token against the Content Delivery API to fetch a page by its `url` slug
with slot references resolved (`include[]=<slot field>`) — exactly what the connector's
ContentstackClientService.getPageBySlug does. Confirms the published content is readable by
a storefront and that slot references hydrate to real component entries.

Read-only. Env: CS_API_KEY, CS_DELIVERY_TOKEN, CS_CDA_BASE (default https://cdn.contentstack.io),
CS_ENVIRONMENT (default development).

Usage: python3 cda_read.py --content-type landing_page --url / [--preview]
"""
import argparse, json, os, sys, urllib.parse, urllib.request

CDA = os.environ.get("CS_CDA_BASE", "https://cdn.contentstack.io").rstrip("/")
KEY = os.environ.get("CS_API_KEY")
DELIVERY = os.environ.get("CS_DELIVERY_TOKEN")
ENV = os.environ.get("CS_ENVIRONMENT", "development")

SLOT_FIELDS = ["section1", "section2", "section2_a", "section2_b", "section2_c",
               "section3", "section4", "section5", "body_content", "side_content",
               "summary", "up_selling", "cross_selling", "tabs", "placeholder_content_slot",
               "product_left_refinements", "product_list_slot", "product_grid_slot",
               "search_results_list_slot", "search_results_grid_slot",
               "top_content", "bottom_content", "header", "footer"]


def cda(path):
    req = urllib.request.Request(f"{CDA}/v3{path}")
    req.add_header("api_key", KEY)
    req.add_header("access_token", DELIVERY)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content-type", default="landing_page")
    ap.add_argument("--url", default="/")
    a = ap.parse_args()
    if not (KEY and DELIVERY):
        sys.exit("set CS_API_KEY and CS_DELIVERY_TOKEN")

    params = [("environment", ENV), ("query", json.dumps({"url": a.url}))]
    for f in SLOT_FIELDS:
        params.append(("include[]", f))
    qs = urllib.parse.urlencode(params)
    r = cda(f"/content_types/{a.content_type}/entries?{qs}")
    entries = r.get("entries") or []
    print(f"[cda_read] {a.content_type} url={a.url} @ {CDA} env={ENV}")
    if not entries:
        print("  no entry found (published? correct env/token?)"); sys.exit(1)
    e = entries[0]
    print(f"  title: {e.get('title')}  template: {e.get('template')}  page_type: {e.get('page_type')}")
    total_refs = 0
    for f in SLOT_FIELDS:
        v = e.get(f)
        if isinstance(v, list) and v:
            resolved = [x for x in v if isinstance(x, dict) and x.get("uid")]
            total_refs += len(resolved)
            types = sorted({x.get("_content_type_uid") or "?" for x in resolved})
            sample = resolved[0].get("title") if resolved else ""
            print(f"    {f:14s}: {len(resolved)} component(s) {types}  e.g. \"{sample}\"")
    print(f"  RESULT: {'PASS — page reads with ' + str(total_refs) + ' resolved components' if total_refs else 'entry found but no references resolved (publish components too?)'}")
    sys.exit(0 if total_refs else 1)


if __name__ == "__main__":
    main()
