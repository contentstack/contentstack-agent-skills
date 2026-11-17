#!/usr/bin/env python3
"""
storefront-extract — Phase 2 of the SAP Spartacus -> Contentstack content-modeling agent.

Crawls one SAP Commerce baseSite over the OCC API and emits a normalized "content
inventory" JSON that conforms to inventory.schema.json. That inventory is the single
contract every downstream skill (content-model, cs-seed, verify) consumes.

Design facts this encodes (all validated live against the SAP backend):
  * OCC /cms/pages is PAGE-BY-LABEL, not a bulk list -> content pages are found by a
    guided BFS from known labels + internal urlLinks.
  * fields=FULL inlines each component's fields, media (responsive variants) AND the
    full navigationNode tree.
  * Product/Category page LAYOUTS are fetched with pageType + code= (not pageLabelOrId).
  * Media bytes download from host + media.url (the ?context= token is required).
  * Content is per content-catalog + version; we read the published Online version.

Deterministic: no wall-clock timestamps in the output, stable key order -> fixture-diffable.

Usage:
  python3 extract.py --site electronics-spa [--base URL] [--langs en,de] \
      [--out inventory.json] [--download-media DIR] [--quiet]
"""
import argparse, json, os, re, ssl, sys, urllib.parse, urllib.request
from collections import OrderedDict, deque

DEFAULT_BASE = os.environ.get("OCC_BASE_URL")


def occ_ssl_context():
    """TLS context for OCC calls. Verified by default; set OCC_INSECURE_TLS=1 only for a
    dev backend with a self-signed certificate you trust."""
    ctx = ssl.create_default_context()
    if os.environ.get("OCC_INSECURE_TLS") == "1":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx

# Standard Spartacus content-page labels used to seed BFS discovery.
SEED_LABELS = [
    "homepage", "login", "register", "cart", "checkout", "orderConfirmation",
    "search", "faq", "contact", "terms", "sale", "store-finder", "storefinder",
    "wishlist", "notFound", "myaccount", "address-book", "update-profile",
    "order-history", "my-coupons", "consents", "close-account", "payment-details",
]
# Component field names that carry localizable text (captured per language for i18n).
I18N_FIELDS = ("content", "title", "linkName", "name", "urlLink", "notice", "altText")
LABEL_RE = re.compile(r"^/([A-Za-z0-9\-_]+)/?$")


class Occ:
    """Thin OCC client (TLS per occ_ssl_context)."""
    def __init__(self, base, site):
        self.base, self.site = base.rstrip("/"), site
        self.host = base.split("/occ/")[0]
        self.ctx = occ_ssl_context()
        self.calls = 0

    def get(self, path, **params):
        self.calls += 1
        url = f"{self.base}/{self.site}/{path}?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, context=self.ctx, timeout=40) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            return {"__error__": str(e)}

    def download(self, media_url):
        self.calls += 1
        url = media_url if media_url.startswith("http") else self.host + media_url
        req = urllib.request.Request(url, headers={"Accept": "*/*"})
        with urllib.request.urlopen(req, context=self.ctx, timeout=60) as r:
            return r.read()

    def page(self, page_type, key_field, key, lang):
        return self.get("cms/pages", pageType=page_type, fields="FULL", lang=lang,
                        **{key_field: key})


def sorted_json(o):
    """Recursively order dict keys for deterministic, diff-stable output."""
    if isinstance(o, dict):
        return OrderedDict((k, sorted_json(o[k])) for k in sorted(o))
    if isinstance(o, list):
        return [sorted_json(v) for v in o]
    return o


class Extractor:
    def __init__(self, occ, langs, quiet=False):
        self.occ = occ
        self.langs = langs
        self.primary = langs[0]
        self.quiet = quiet
        self.components_by_type = {}   # typeCode -> [normalized component]
        self.media = OrderedDict()     # media code -> {url, mime, altText}
        self.slots = OrderedDict()     # slotId -> meta
        self.nav_nodes = OrderedDict() # nodeUid -> raw navigationNode tree
        self.warnings = []

    def log(self, *a):
        if not self.quiet:
            print(*a, file=sys.stderr)

    # ---- media & link scanning -------------------------------------------------
    def record_media(self, m):
        if not isinstance(m, dict):
            return
        if "code" in m and "url" in m:
            self.media.setdefault(m["code"], {
                "url": m.get("url"), "mime": m.get("mime"), "altText": m.get("altText")})
        else:
            for v in m.values():
                if isinstance(v, dict):
                    self.record_media(v)

    def scan_labels(self, obj, out):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("url", "urlLink", "linkTo") and isinstance(v, str):
                    mm = LABEL_RE.match(v.strip())
                    if mm:
                        out.add(mm.group(1))
                self.scan_labels(v, out)
        elif isinstance(obj, list):
            for v in obj:
                self.scan_labels(v, out)

    # ---- component normalization ----------------------------------------------
    DROP = ("uuid", "modifiedtime", "synchronizationBlocked")

    def normalize_component(self, c):
        tc = c.get("typeCode", "<unknown>")
        if "media" in c:
            self.record_media(c["media"])
        if "navigationNode" in c and isinstance(c["navigationNode"], dict):
            nn = c["navigationNode"]
            if nn.get("uid"):
                self.nav_nodes.setdefault(nn["uid"], self.clean(nn))
        keep = self.clean(c)
        self.components_by_type.setdefault(tc, []).append(keep)
        return keep

    def clean(self, o):
        if isinstance(o, dict):
            return {k: self.clean(v) for k, v in o.items() if k not in self.DROP}
        if isinstance(o, list):
            return [self.clean(v) for v in o]
        return o

    def normalize_page(self, label, raw):
        slots = []
        for s in (raw.get("contentSlots") or {}).get("contentSlot", []):
            sid = s.get("slotId")
            self.slots.setdefault(sid, {
                "position": s.get("position"), "shared": s.get("slotShared"),
                "name": s.get("name"), "firstSeenOn": label})
            comps = (s.get("components") or {}).get("component", [])
            slots.append({
                "slotId": sid, "position": s.get("position"),
                "shared": s.get("slotShared"),
                "components": [self.normalize_component(c) for c in comps]})
        return {
            "label": raw.get("label") or label, "uid": raw.get("uid"),
            "title": raw.get("title"), "template": raw.get("template"),
            "typeCode": raw.get("typeCode"), "robotTag": raw.get("robotTag"),
            "slots": slots}

    # ---- discovery -------------------------------------------------------------
    def discover_content_pages(self):
        pages, visited = OrderedDict(), set()
        frontier = deque(dict.fromkeys(SEED_LABELS))
        while frontier:
            label = frontier.popleft()
            if label in visited:
                continue
            visited.add(label)
            raw = self.occ.page("ContentPage", "pageLabelOrId", label, self.primary)
            if raw.get("__error__") or not raw.get("uid"):
                continue
            pages[label] = self.normalize_page(label, raw)
            found = set()
            self.scan_labels(raw, found)
            for f in found:
                if f not in visited:
                    frontier.append(f)
        self.log(f"  content pages: {len(pages)}")
        return pages

    def sample_layout_pages(self):
        out = OrderedDict()
        # product code from search
        s = self.occ.get("products/search", query="", pageSize="1",
                          fields="DEFAULT", lang=self.primary, curr="USD")
        if not s.get("products"):
            s = self.occ.get("products/search", query="a", pageSize="1",
                              fields="DEFAULT", lang=self.primary, curr="USD")
        code = (s.get("products") or [{}])[0].get("code")
        if code:
            pp = self.occ.page("ProductPage", "code", code, self.primary)
            if pp.get("uid"):
                out["ProductPage"] = self.normalize_page(f"product:{code}", pp)
        else:
            self.warnings.append("no product code resolved for ProductPage layout")
        # category code: try a handful
        for cat in ("575", "576", "1", "brands", "1358"):
            cp = self.occ.page("CategoryPage", "code", cat, self.primary)
            if cp.get("uid"):
                out[f"CategoryPage:{cat}"] = self.normalize_page(f"category:{cat}", cp)
                break
        else:
            self.warnings.append("no category code resolved for CategoryPage layout")
        self.log(f"  layout samples: {list(out)}")
        return out

    # ---- i18n ------------------------------------------------------------------
    def capture_i18n(self, page_labels):
        i18n = OrderedDict()
        for lang in self.langs[1:]:
            per = OrderedDict()
            for label in page_labels:
                raw = self.occ.page("ContentPage", "pageLabelOrId", label, lang)
                if raw.get("__error__"):
                    continue
                for s in (raw.get("contentSlots") or {}).get("contentSlot", []):
                    for c in (s.get("components") or {}).get("component", []):
                        uid = c.get("uid")
                        if not uid:
                            continue
                        vals = {f: c[f] for f in I18N_FIELDS
                                if isinstance(c.get(f), str) and c[f]}
                        if vals:
                            per.setdefault(uid, {}).update(vals)
            i18n[lang] = per
            self.log(f"  i18n[{lang}]: {len(per)} components")
        return i18n

    # ---- media download (optional) --------------------------------------------
    def download_media(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        ok = 0
        for code, m in self.media.items():
            if not m.get("url"):
                continue
            try:
                data = self.occ.download(m["url"])
                fname = re.sub(r"[^A-Za-z0-9._-]", "_", code)
                with open(os.path.join(out_dir, fname), "wb") as f:
                    f.write(data)
                m["bytes"] = len(data)
                ok += 1
            except Exception as e:
                self.warnings.append(f"media download failed {code}: {e}")
        self.log(f"  media downloaded: {ok}/{len(self.media)}")
        return ok

    # ---- assemble --------------------------------------------------------------
    def run(self, download_dir=None):
        self.log(f"[extract] {self.occ.site}  langs={self.langs}")
        pages = self.discover_content_pages()
        layouts = self.sample_layout_pages()
        i18n = self.capture_i18n(list(pages))
        if download_dir:
            self.download_media(download_dir)

        type_inventory = {
            tc: {"instances": len(v),
                 "fields": sorted({k for c in v for k in c.keys()})}
            for tc, v in sorted(self.components_by_type.items(),
                                key=lambda kv: -len(kv[1]))}
        inv = {
            "schemaVersion": "1.0",
            "site": self.occ.site,
            "source": self.occ.base,
            "catalogVersion": "Online",
            "primaryLanguage": self.primary,
            "languages": self.langs,
            "counts": {
                "contentPages": len(pages),
                "layoutSamples": len(layouts),
                "uniqueSlots": len(self.slots),
                "sharedSlots": sum(1 for s in self.slots.values()
                                   if s["shared"] in (True, "true")),
                "componentTypes": len(self.components_by_type),
                "componentInstances": sum(len(v) for v in self.components_by_type.values()),
                "navigationNodes": len(self.nav_nodes),
                "mediaAssets": len(self.media),
            },
            "componentTypeInventory": type_inventory,
            "slots": self.slots,
            "contentPages": pages,
            "layoutSamples": layouts,
            "navigation": self.nav_nodes,
            "i18n": i18n,
            "mediaManifest": self.media,
            "warnings": self.warnings,
        }
        return inv


def resolve_languages(occ, arg):
    if arg:
        return [x.strip() for x in arg.split(",") if x.strip()]
    d = occ.get("languages")
    langs = [l["isocode"] for l in d.get("languages", []) if l.get("isocode")]
    # put 'en' first if present for a stable primary
    if "en" in langs:
        langs = ["en"] + [l for l in langs if l != "en"]
    return langs or ["en"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--base", default=DEFAULT_BASE, required=DEFAULT_BASE is None,
                    help="OCC v2 base URL, e.g. https://HOST/occ/v2 (or set OCC_BASE_URL)")
    ap.add_argument("--langs", default="", help="comma list; default = site languages")
    ap.add_argument("--primary-only", action="store_true",
                    help="crawl only the primary language (skip i18n)")
    ap.add_argument("--out", default="inventory.json")
    ap.add_argument("--download-media", default="", help="dir to save media bytes")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    occ = Occ(a.base, a.site)
    langs = resolve_languages(occ, a.langs)
    if a.primary_only:
        langs = langs[:1]
    inv = Extractor(occ, langs, quiet=a.quiet).run(download_dir=a.download_media or None)

    with open(a.out, "w") as f:
        json.dump(sorted_json(inv), f, indent=2)

    c = inv["counts"]
    print(f"[extract] {a.site}: pages={c['contentPages']} layouts={c['layoutSamples']} "
          f"types={c['componentTypes']} instances={c['componentInstances']} "
          f"nav={c['navigationNodes']} media={c['mediaAssets']} "
          f"| {occ.calls} OCC calls -> {a.out}")
    if inv["warnings"]:
        print("  warnings: " + "; ".join(inv["warnings"]))


if __name__ == "__main__":
    main()
