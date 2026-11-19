#!/usr/bin/env python3
"""
sap_app — pipeline stage: make sure the SAP Commerce Cloud marketplace app is installed and
configured on the target stack, then find its Product custom-field extension uid.

  1. install + configure the app (sap_app.cjs, on the user's csdx login — a management token
     cannot install or configure marketplace apps),
  2. look up the app's "SAP Commerce Cloud - Product" field extension with the management
     token. Marketplace extensions only appear with ?include_marketplace_extensions=true.

Writes {installation_uid, product_extension_uid, category_extension_uid, ...} to --out, which
cma_seed_connector.py reads to add the `sap_products` field to product_carousel_component.

Usage:
  python3 sap_app.py --out <run>/sap-app.json            # install/configure + discover
  python3 sap_app.py --out <run>/sap-app.json --skip-install   # discover only (app already set up)
  python3 sap_app.py --status                            # read-only summary
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cs-seed"))
import cma_seed as low   # cma()

HERE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.environ.get("SAP_APP_NAME", "SAP Commerce Cloud")


def node(cmd, *extra):
    # The stack API key goes to node through the environment (CS_API_KEY), not argv,
    # so it never shows in the process list.
    env = dict(os.environ, CS_API_KEY=low.KEY)
    p = subprocess.run(["node", os.path.join(HERE, "sap_app.cjs"), cmd, *extra],
                       capture_output=True, text=True, env=env)
    if p.returncode:
        low.die((p.stderr or p.stdout).strip())
    return json.loads(p.stdout)


def find_extensions():
    st, r = low.cma("GET", "/extensions?include_marketplace_extensions=true")
    if st != 200:
        low.die(f"could not list extensions ({st}): {json.dumps(r)[:160]}")
    out = {}
    for x in r.get("extensions") or []:
        title = " ".join((x.get("title") or "").split())       # app titles have a double space
        if not title.startswith(APP_NAME):
            continue
        if x.get("type") == "field" and title.endswith("Product"):
            out["product_extension_uid"] = x["uid"]
        elif x.get("type") == "field" and title.endswith("Category"):
            out["category_extension_uid"] = x["uid"]
        out.setdefault("app_installation_uid", x.get("app_installation_uid") or x.get("app_uid"))
    return out


def repoint_carousel_field(ext_uid, ct_uid="product_carousel_component"):
    """A reinstall creates a new Product field extension; point an existing `sap_products`
    field at it (entry data is kept). No-op when the type or field doesn't exist yet."""
    st, r = low.cma("GET", f"/content_types/{ct_uid}")
    if st != 200:
        return None
    ct = r["content_type"]
    field = next((f for f in ct["schema"] if f.get("uid") == "sap_products"), None)
    if not field or field.get("extension_uid") == ext_uid:
        return None
    field["extension_uid"] = ext_uid
    body = {"content_type": {k: ct[k] for k in ("title", "uid", "schema", "options", "description") if k in ct}}
    st, r = low.cma("PUT", f"/content_types/{ct_uid}", body)
    return ext_uid if st == 200 else low.die(f"could not re-point {ct_uid}.sap_products ({st}): {json.dumps(r)[:160]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write the result JSON here")
    ap.add_argument("--skip-install", action="store_true",
                    help="don't touch the app; only discover its extensions")
    ap.add_argument("--status", action="store_true", help="read-only summary")
    ap.add_argument("--reinstall", action="store_true",
                    help="uninstall the app on the stack, install it again and configure it once "
                         "(repairs an install whose picker fails with HTTP 414)")
    a = ap.parse_args()
    if not (low.KEY and low.TOKEN):
        low.die("CS_API_KEY and CS_MANAGEMENT_TOKEN must be set")

    if a.status:
        print(json.dumps({**node("status"), **find_extensions()}, indent=1))
        return
    result = {} if a.skip_install else node("ensure", *(["--reinstall"] if a.reinstall else []))
    if result:
        how = ("already set up — left unchanged" if result.get("unchanged")
               else "reinstalled + configured" if result.get("reinstalled")
               else "installed + configured")
        print(f"  app {how}: config '{result.get('configured')}', keys {result.get('keys')}")
    result.update(find_extensions())
    if not result.get("product_extension_uid"):
        low.die(f"'{APP_NAME} - Product' field extension not found on the stack — "
                f"is the app installed with its Custom Field location enabled?")
    print(f"  product field extension: {result['product_extension_uid']}")
    repointed = repoint_carousel_field(result["product_extension_uid"])
    if repointed:
        print(f"  carousel sap_products field -> {repointed}")
    if a.out:
        json.dump(result, open(a.out, "w"), indent=2)
        print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
