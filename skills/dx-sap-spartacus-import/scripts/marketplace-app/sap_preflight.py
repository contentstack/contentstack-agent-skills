#!/usr/bin/env python3
"""
sap_preflight — check, before anything is installed or written, that the SAP server the SAP
Commerce Cloud app's product picker will search can actually serve the carousels.

The picker never talks to SAP from the browser: the app's own backend calls the server in
SAP_APP_API_BASE_URL. So that server has to work for an anonymous caller over HTTPS with a
publicly trusted certificate, for the base site in SAP_APP_BASE_SITE. This holds for a B2C
site (electronics) and a B2B site (powertools-spa) alike; B2B sites are the ones that most
often fail it (site not imported, search index not built, or search behind a login).

Checks, all with TLS verified (OCC_INSECURE_TLS does not apply: the app's backend verifies):
  1. tls     — the server's certificate is trusted
  2. site    — SAP_APP_BASE_SITE is one of the server's base sites
  3. search  — product search on that site returns products (needs a built Solr index and
               anonymous access; a 401/403 means the site requires a login)
  4. codes   — the carousel product codes in the plan exist on that server (the picker saves
               codes the storefront looks up on its own OCC; both must carry the same catalog)

Exit 0 = pass (missing codes are a warning: they are left out of the picker value and
reported), 4 = fail: nothing should be installed or written. The orchestrator runs this at
gate 2 and stops before any write when it fails.

Usage:
  python3 sap_preflight.py [--plan <run-dir>/connector-plan.json]
"""
import argparse, json, os, ssl, sys, urllib.error, urllib.parse, urllib.request

FAIL = 4


def server():
    host = (os.environ.get("SAP_APP_API_BASE_URL") or "").strip().rstrip("/")
    if not host:
        return None, None, None
    if not host.startswith("http"):
        host = "https://" + host
    route = "/" + (os.environ.get("SAP_APP_API_ROUTE") or "/occ/v2/").strip("/") + "/"
    return host, route, os.environ.get("SAP_APP_BASE_SITE")


def get(url):
    """GET with TLS verified. Returns (status, json-or-None, error-kind, detail)."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}),
                                    context=ssl.create_default_context(), timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}"), None, ""
    except urllib.error.HTTPError as e:
        return e.code, None, "http", e.read().decode(errors="replace")[:200]
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(e.reason):
            return 0, None, "tls", str(e.reason)[:200]
        return 0, None, "net", str(e.reason)[:200]
    except Exception as e:  # timeouts, bad JSON
        return 0, None, "net", str(e)[:200]


def carousel_codes(plan):
    codes = []
    for e in plan.get("entries", {}).get("components", []):
        if e.get("_content_type") != "product_carousel_component":
            continue
        sp = e.get("sap_products")
        if isinstance(sp, dict) and sp.get("_sap_products"):
            codes += sp.get("codes") or []
        elif isinstance(e.get("products"), list):
            codes += [c for c in e["products"] if isinstance(c, str)]
    return list(dict.fromkeys(codes))


def run(plan_path=None):
    """Returns (ok, lines)."""
    lines, ok = [], True
    host, route, site = server()
    if not host or not site:
        return False, ["SAP_APP_API_BASE_URL and SAP_APP_BASE_SITE must be set for the picker"]
    base = f"{host}{route}"
    lines.append(f"picker server: {base} · base site {site}")

    st, body, kind, detail = get(f"{base}basesites?fields=baseSites(uid)")
    if kind == "tls":
        return False, lines + [
            "FAIL tls: the server's certificate isn't publicly trusted. The app's backend rejects it "
            "(SAP's default development certificate, CN=hybris, is the usual cause). Give the server "
            "a trusted certificate (for example Let's Encrypt behind a reverse proxy) and re-run.",
            f"     {detail}"]
    if kind:
        return False, lines + [f"FAIL server: {base}basesites answered {st or kind} — {detail}"]
    lines.append("ok   tls: certificate trusted")
    sites = [s.get("uid") for s in (body or {}).get("baseSites", [])]
    if site not in sites:
        return False, lines + [
            f"FAIL site: '{site}' isn't a base site on this server (it has: {', '.join(sites) or 'none'}).",
            "     On SAP Commerce Cloud the -spa sites come from the spartacussampledata extension; "
            "a store's sample data (for example powertoolsstore) has to be imported for its site to exist."]
    lines.append(f"ok   site: {site} exists")

    st, body, kind, detail = get(f"{base}{site}/products/search?pageSize=1&fields=pagination(totalResults)")
    total = ((body or {}).get("pagination") or {}).get("totalResults", 0) if not kind else 0
    if kind == "http" and st in (401, 403):
        return False, lines + [
            f"FAIL search: product search on {site} needs a login (HTTP {st}). The picker searches "
            "anonymously; allow anonymous product search on this B2B site, or point the app at one that does."]
    if kind:
        return False, lines + [f"FAIL search: {st or kind} — {detail}"]
    if not total:
        return False, lines + [
            f"FAIL search: product search on {site} returns 0 products, so the picker would list nothing.",
            "     Run a full Solr index for the site's catalog (for example full-powertoolsIndex-cronJob) and re-run."]
    lines.append(f"ok   search: {total} products")

    if plan_path:
        codes = carousel_codes(json.load(open(plan_path)))
        missing = []
        for c in codes:
            st, _, kind, _ = get(f"{base}{site}/products/{urllib.parse.quote(c)}?fields=code")
            if st != 200:
                missing.append(c)
        if codes and len(missing) == len(codes):
            return False, lines + [
                f"FAIL codes: none of the {len(codes)} carousel product codes exist on this server. "
                "It doesn't carry the storefront's catalog; point the app at a server that does."]
        if missing:
            lines.append(f"warn codes: {len(codes) - len(missing)}/{len(codes)} found; missing {missing} "
                         "will be left out of the picker value")
        else:
            lines.append(f"ok   codes: {len(codes)}/{len(codes)} carousel product codes found")
    return ok, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", help="connector-plan.json, to check the carousel product codes")
    a = ap.parse_args()
    ok, lines = run(a.plan)
    for l in lines:
        print(f"  {l}")
    sys.exit(0 if ok else FAIL)


if __name__ == "__main__":
    main()
