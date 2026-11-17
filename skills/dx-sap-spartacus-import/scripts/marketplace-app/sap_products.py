#!/usr/bin/env python3
"""
sap_products — build the value of a `sap_products` field (the SAP Commerce Cloud marketplace
app's product picker) from plain SKU codes, exactly as the picker itself saves it.

The picker stores, per entry:

    {"type": "sapcommercecloud_product",
     "data": [{"code": "300938", "name": "Photosmart E317 Digital Camera",
               "cs_metadata": {"multiConfigName": "hti", "isConfigDeleted": false}}, ...]}

with only the keys the app's "Keys to Save" setting allows (this skill configures the app to
save `code` + `name`, see sap_app.cjs). Names are looked up on the SAP server the APP is
configured for (SAP_APP_* env), not the storefront's OCC, because that is what the picker
reads; product codes are the same on both.

Contentstack caps a JSON field at 20 KB, so build() refuses a value over that limit.

Used by cma_seed_connector.py (master locale) and localize.py (other locales): the model step
emits a `{"_sap_products": true, "codes": [...]}` placeholder and the seeders call resolve().

Env:
  SAP_APP_API_BASE_URL   host of the app's SAP OCC (no scheme), e.g. api.<...>.commerce.ondemand.com
  SAP_APP_API_ROUTE      default /occ/v2/
  SAP_APP_BASE_SITE      e.g. electronics
  SAP_APP_CONFIG_NAME    the app configuration name stored in cs_metadata, default hti
Falls back to OCC_BASE_URL + the run's site when SAP_APP_API_BASE_URL is unset.
"""
import json, os, ssl, urllib.parse, urllib.request

FIELD_TYPE = "sapcommercecloud_product"
MAX_BYTES = 20 * 1024

def _occ_ctx():
    """TLS for the storefront's OCC fallback: verified unless OCC_INSECURE_TLS=1 (a trusted
    self-signed dev backend). The app's own SAP server is always verified."""
    ctx = ssl.create_default_context()
    if os.environ.get("OCC_INSECURE_TLS") == "1":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def occ_product_base(site=None):
    """OCC products URL prefix the picker reads from (ends with '/products/')."""
    host = (os.environ.get("SAP_APP_API_BASE_URL") or "").strip().rstrip("/")
    if host:
        if not host.startswith("http"):
            host = "https://" + host
        route = "/" + (os.environ.get("SAP_APP_API_ROUTE") or "/occ/v2/").strip("/") + "/"
        base_site = os.environ.get("SAP_APP_BASE_SITE") or site
        return f"{host}{route}{base_site}/products/", True
    occ = (os.environ.get("OCC_BASE_URL") or "").rstrip("/")
    if not occ:
        raise SystemExit("[sap_products] set SAP_APP_API_BASE_URL (or OCC_BASE_URL) to look up product names")
    return f"{occ}/{site}/products/", False


class SapProductResolver:
    def __init__(self, site=None, lang="en"):
        self.base, self.verified_tls = occ_product_base(site)
        self.lang = lang
        self.config_name = os.environ.get("SAP_APP_CONFIG_NAME", "hti")
        self.cache = {}
        self.missing = []

    def item(self, code):
        if code not in self.cache:
            url = f"{self.base}{urllib.parse.quote(code)}?fields=code,name&lang={self.lang}"
            ctx = None if self.verified_tls else _occ_ctx()
            try:
                with urllib.request.urlopen(url, context=ctx, timeout=30) as r:
                    p = json.loads(r.read().decode())
                self.cache[code] = {"code": p["code"], "name": p.get("name") or p["code"],
                                    "cs_metadata": {"multiConfigName": self.config_name,
                                                    "isConfigDeleted": False}}
            except Exception as e:           # unknown code on the app's server -> skip it
                self.cache[code] = None
                self.missing.append((code, str(e)[:80]))
        return self.cache[code]

    def build(self, codes):
        data = [i for i in (self.item(c) for c in codes) if i]
        value = {"data": data, "type": FIELD_TYPE}
        size = len(json.dumps(value, separators=(",", ":")).encode())
        if size > MAX_BYTES:
            raise ValueError(f"sap_products value is {size} B (> 20 KB JSON field limit); "
                             f"save fewer keys in the app or split the carousel")
        return value

    def resolve(self, v):
        """Turn a model placeholder {"_sap_products": true, "codes": [...]} into the field value."""
        return self.build(v.get("codes") or [])


def is_placeholder(v):
    return isinstance(v, dict) and v.get("_sap_products") is True


def placeholder(codes):
    return {"_sap_products": True, "codes": list(codes)}


if __name__ == "__main__":
    import sys
    r = SapProductResolver(site=os.environ.get("SAP_APP_BASE_SITE"))
    print(json.dumps(r.build(sys.argv[1:]), indent=1))
    if r.missing:
        print("missing:", r.missing, file=sys.stderr)
