#!/usr/bin/env python3
"""
model_connector — content-model for the CONNECTOR reference-field profile (Phase 4b).

Reads an inventory (from storefront-extract) + connector.registry.json and emits a
connector-shaped plan that conforms to the @contentstack/contentstack-spartacus-connector starter-pack model:
per-template page entries with named per-slot REFERENCE fields, authored component entries
only, and a single global_slots shell entry. Functional components + non-content pages are
left to OCC (hybrid islands model). Stack-agnostic — no API calls.

Output: connector-plan.json (+ prints a summary).

Usage:
  python3 model_connector.py --inventory <inv.json> --profile <connector.registry.json> --out <dir>
"""
import argparse, json, os
from collections import OrderedDict


def clean(d):
    return {k: v for k, v in d.items() if not k.startswith("_")}


def as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def as_target(v):  # OCC "true"/"false" -> normalized "true"/"false" string (connector reads strings)
    if isinstance(v, bool):
        return "true" if v else "false"
    return "true" if str(v).strip().lower() == "true" else "false"


def ref(content_type, uid):
    return {"_ref": True, "content_type": content_type, "by": "sap_uid", "value": uid}


def asset_ref(code):
    return {"_asset": True, "code": code} if code else None


class ConnectorModeler:
    def __init__(self, inv, prof, pack_fields=None):
        self.inv = inv
        # content type uid -> field uids in the connector's starter pack. When given, a page
        # slot is only authored if the target page type has that slot field; otherwise it is
        # left to OCC (e.g. HomepageNavLink exists on landing_page but not product_page).
        self.pack_fields = pack_fields
        self.page_types = clean(prof["page_types"])
        self.slot_map = clean(prof["slot_field_map"])
        self.global_pos = clean(prof["global_slots"]["positions"])
        self.global_ct = prof["global_slots"]["content_type"]
        self.cmap = {k: v for k, v in prof["component_map"].items() if not k.startswith("_")}
        self.occ_only = set(prof["occ_only_types"]["types"])
        self.components = OrderedDict()   # uid -> entry
        self.assets = OrderedDict()
        self.skipped_deferred = set()
        self.unmapped_slots = set()

    # ---- component field mapping ----
    def add_asset(self, code):
        if code and code not in self.assets:
            m = self.inv.get("mediaManifest", {}).get(code, {})
            self.assets[code] = {"code": code, "url": m.get("url"),
                                 "mime": m.get("mime"), "alt_text": m.get("altText")}

    def map_component(self, c):
        tc = c.get("typeCode")
        spec = self.cmap.get(tc)
        # Nav components are NOT regular slot components — build_nav() flattens
        # them into the nav_node_flat pool + a flat nav component and wires them
        # into the shell itself. Skip them here (both the legacy "deferred-nav"
        # and the profile's "nav-pass" status) so process_page never wires the
        # shell with a recursive nav type that build_nav then can't override.
        if not spec or spec.get("status") in ("deferred-nav", "nav-pass"):
            if spec:
                self.skipped_deferred.add(tc)
            return None                       # not authored (functional or nav)
        uid = c.get("uid")
        if not uid:
            return None
        if uid in self.components:
            return uid
        ct = spec["content_type"]
        m = c.get("media") or {}
        fields = {"sap_uid": uid}
        if tc == "SimpleResponsiveBannerComponent":
            for bp, fld in (("mobile", "media_mobile"), ("tablet", "media_tablet"),
                            ("desktop", "media_desktop"), ("widescreen", "media_widescreen")):
                d = m.get(bp)
                if isinstance(d, dict) and d.get("code"):
                    fields[fld] = asset_ref(d["code"]); self.add_asset(d["code"])
            d = m.get("desktop") if isinstance(m.get("desktop"), dict) else None
            if d and d.get("code"):
                fields["media"] = asset_ref(d["code"])
            fields["url_link"] = c.get("urlLink")
            fields["title"] = c.get("name") or uid
        elif tc == "SimpleBannerComponent":
            if m.get("code"):
                fields["media"] = asset_ref(m["code"]); self.add_asset(m["code"])
            fields["url_link"] = c.get("urlLink")
            fields["title"] = c.get("name") or uid
        elif tc == "ProductCarouselComponent":
            fields["title"] = c.get("title") or c.get("name") or uid   # rendered heading
            fields["products"] = [x for x in (c.get("productCodes") or "").split() if x]
        elif tc == "CMSParagraphComponent":
            fields["title"] = c.get("name") or uid
            fields["content"] = c.get("content")
        elif tc == "CMSLinkComponent":
            fields["title"] = c.get("name") or uid
            fields["link_name"] = c.get("linkName")
            fields["url"] = c.get("url")
            fields["target"] = as_target(c.get("target"))
        elif tc == "CMSFlexComponent":
            fields["title"] = c.get("name") or uid
            fields["flex_type"] = c.get("flexType")
        else:
            fields["title"] = c.get("name") or uid
        entry = {"_content_type": ct, "_key": {"field": "sap_uid", "value": uid}}
        entry.update({k: v for k, v in fields.items() if v is not None})
        self.components[uid] = entry
        return uid

    # ---- one page (content page or layout sample) ----
    SHARED_SLUG = {"product_page": "/product", "category_page": "/category"}

    def process_page(self, label, p, global_fields, url_override=None):
        tpl = p.get("template")
        pt = self.page_types.get(tpl)
        if not pt:
            return None                                     # non-content page -> OCC, no CS page
        slot_fields = {}
        for s in p.get("slots", []):
            pos = s.get("position")
            if pos not in self.global_pos and pos in self.slot_map and self.pack_fields is not None \
                    and self.slot_map[pos] not in self.pack_fields.get(pt["content_type"], set()):
                self.unmapped_slots.add(f"{pos} ({pt['content_type']} has no {self.slot_map[pos]})")
                continue                                    # target type lacks the slot -> OCC
            if pos not in self.global_pos and pos not in self.slot_map:
                self.unmapped_slots.add(pos)                # authored page, unknown slot -> OCC
                continue
            comp_uids = [u for u in (self.map_component(c) for c in s.get("components", [])) if u]
            if not comp_uids:
                continue
            if pos in self.global_pos:                      # shell -> global_slots (dedupe by uid)
                fld = self.global_pos[pos]
                bucket = global_fields.setdefault(fld, [])
                seen = {r["value"] for r in bucket}
                for u in comp_uids:
                    if u not in seen:
                        bucket.append(ref(self.components[u]["_content_type"], u)); seen.add(u)
            elif pos in self.slot_map:                      # page slot
                fld = self.slot_map[pos]
                slot_fields[fld] = [ref(self.components[u]["_content_type"], u) for u in comp_uids]
            else:
                self.unmapped_slots.add(pos)                # authored page, unknown slot -> OCC
        url = url_override or ("/" if label == "homepage" else "/" + label)
        page = {"_content_type": pt["content_type"], "_key": {"field": "url", "value": url},
                "title": p.get("title") or label, "url": url,
                "page_type": p.get("typeCode"), "template": tpl}
        page.update(slot_fields)
        return page

    # ---- navigation: link leaves -> FLAT nav_node_flat pool -> flat nav components ----
    def build_nav(self, global_fields):
        """Emit navigation as a FLAT adjacency list, not a recursive tree.

        Each menu becomes a pool of `nav_node_flat` entries — every node points at
        its parent by the plain-text `parent_id` (a node id, NOT a reference) and
        orders siblings via `sort_order` — plus a `category/footer_navigation_flat`
        component that references the whole pool through `all_nodes`. The connector
        rebuilds the tree in code, so the menu resolves in one shallow, constant
        include chain regardless of depth (no Delivery API include-depth cap).

        Every entry is keyed by `sap_uid` (the connector seeder only tracks
        sap_uid-keyed entries in its ref map); nav_node_flat also carries node_id ==
        sap_uid and parent_id == parent's sap_uid for the connector to read.
        Emission order (link leaves -> nodes -> component) keeps every _ref target
        created before its referrer.
        """
        roots = self.inv.get("navigationRoots", {})
        links = self.inv.get("navigationLinks", {})
        tree = self.inv.get("navigation", {})
        nav_entries = []
        if not roots:
            return nav_entries
        # 1. link leaves actually used by the nav trees
        used = set()
        def collect(node):
            for e in (node.get("entries") or []):
                if e.get("itemType") == "CMSLinkComponent" and e.get("itemId") in links:
                    used.add(e["itemId"])
            for ch in (node.get("children") or []):
                collect(ch)
        for r in roots.values():
            if tree.get(r["root"]):
                collect(tree[r["root"]])
        for lid in sorted(used):
            ld = links[lid]
            nav_entries.append({"_content_type": "cms_link_component",
                "_key": {"field": "sap_uid", "value": lid}, "sap_uid": lid,
                "title": ld.get("name") or ld.get("link_name") or lid,
                "link_name": ld.get("link_name"), "url": ld.get("url"),
                "target": as_target(ld.get("target"))})
        # 2. flatten a menu tree into nav_node_flat entries (parent_id text +
        #    sort_order); append in pre-order so parents precede children.
        def flatten(node, parent_uid, order, collected):
            uid = node.get("uid")
            if not uid:
                return
            node_links = [e["itemId"] for e in (node.get("entries") or [])
                          if e.get("itemType") == "CMSLinkComponent" and e.get("itemId") in links]
            # A SAP leaf node usually has NO title — its label lives on the linked
            # cms_link_component. Fall back to the link's name so the storefront
            # shows "Contact Us", not the node uid "ContactUsNavNode".
            leaf_label = links[node_links[0]].get("link_name") if node_links else None
            entry = {"_content_type": "nav_node_flat",
                     "_key": {"field": "sap_uid", "value": uid}, "sap_uid": uid,
                     "node_id": uid, "parent_id": parent_uid, "sort_order": order,
                     "title": node.get("title") or node.get("name") or leaf_label or uid}
            if node_links:
                entry["links"] = [ref("cms_link_component", lid) for lid in node_links]
            nav_entries.append(entry)
            collected.append(uid)
            for i, ch in enumerate(node.get("children") or [], start=1):
                flatten(ch, uid, i, collected)
        # 3. flat nav components -> placed into the shell (navigation_bar / footer)
        for cuid, r in roots.items():
            root_node = tree.get(r["root"])
            if not root_node:
                continue
            node_uids = []
            # the root is a pure container: its children are the top-level items
            for i, ch in enumerate(root_node.get("children") or [], start=1):
                flatten(ch, "", i, node_uids)
            ct = ("category_navigation_flat"
                  if r["typeCode"] == "CategoryNavigationComponent" else "footer_navigation_flat")
            nav_entries.append({"_content_type": ct, "_key": {"field": "sap_uid", "value": cuid},
                "sap_uid": cuid, "title": cuid, "wrap_after": as_int(r.get("wrapAfter")),
                "all_nodes": [ref("nav_node_flat", nid) for nid in node_uids]})
            fld = self.global_pos.get(r.get("position"))
            if fld:
                bucket = global_fields.setdefault(fld, [])
                if cuid not in {x["value"] for x in bucket}:
                    bucket.append(ref(ct, cuid))
        return nav_entries

    def run(self):
        pages, global_fields = [], {}
        for label, p in self.inv.get("contentPages", {}).items():
            pg = self.process_page(label, p, global_fields)
            if pg:
                pages.append(pg)
        for label, p in self.inv.get("layoutSamples", {}).items():   # product/category pages
            pt = self.page_types.get(p.get("template"))
            if not pt:
                continue
            pg = self.process_page(label, p, global_fields,
                                   url_override=self.SHARED_SLUG.get(pt["content_type"]))
            if pg:
                pages.append(pg)
        nav_entries = self.build_nav(global_fields)          # after pages so shell fields exist

        global_entry = None
        if global_fields:
            global_entry = {"_content_type": self.global_ct,
                            "_key": {"field": "title", "value": self.inv.get("site")},
                            "title": self.inv.get("site")}
            # Clear any shell field we no longer author (e.g. site_context/site_links now
            # left to OCC) so an update removes stale references instead of keeping them.
            ALL_SHELL = ["site_logo", "search_box", "mini_cart", "navigation_bar",
                         "site_context", "site_links", "header_links", "footer"]
            for fld in ALL_SHELL:
                global_entry.setdefault(fld, [])
            global_entry.update(global_fields)

        components_out = list(self.components.values()) + nav_entries   # nav ordered: links->nodes->components
        used_cts = sorted({e["_content_type"] for e in components_out} |
                          {p["_content_type"] for p in pages} |
                          ({self.global_ct} if global_entry else set()))
        from collections import Counter
        nav_by_ct = Counter(e["_content_type"] for e in nav_entries)
        plan = {
            "site": self.inv.get("site"), "profile": "connector-reference-fields",
            "content_types_needed": used_cts,
            "assets": list(self.assets.values()),
            "entries": {"components": components_out,
                        "global_slots": global_entry, "pages": pages},
        }
        report = {
            "site": self.inv.get("site"),
            "authored_pages": [(p["url"], p["_content_type"]) for p in pages],
            "component_entries": len(self.components),
            "nav_entries": dict(nav_by_ct),
            "assets": len(self.assets),
            "global_slots_fields": sorted(global_fields.keys()),
            "unmapped_slot_positions": sorted(self.unmapped_slots),
        }
        return plan, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--starter-pack", default="", help="connector starter-pack content_types dir (drops slots a page type lacks)")
    a = ap.parse_args()
    inv = json.load(open(a.inventory)); prof = json.load(open(a.profile))
    os.makedirs(a.out, exist_ok=True)
    pack_fields = None
    if a.starter_pack:
        pack_fields = {}
        for f in os.listdir(a.starter_pack):
            if f.endswith(".json") and f != "schema.json":
                ct = json.load(open(os.path.join(a.starter_pack, f)))
                if isinstance(ct, dict) and ct.get("uid"):
                    pack_fields[ct["uid"]] = {x["uid"] for x in ct.get("schema", [])}
    plan, report = ConnectorModeler(inv, prof, pack_fields).run()
    json.dump(plan, open(os.path.join(a.out, "connector-plan.json"), "w"), indent=2)
    json.dump(report, open(os.path.join(a.out, "connector-report.json"), "w"), indent=2)
    print(f"[model_connector] {report['site']} (profile: connector-reference-fields)")
    print(f"  authored pages: {len(report['authored_pages'])} -> {report['authored_pages']}")
    print(f"  component entries: {report['component_entries']}  assets: {report['assets']}")
    print(f"  content types needed: {plan['content_types_needed']}")
    print(f"  global_slots fields: {report['global_slots_fields']}")
    if report.get("nav_entries"):
        print(f"  nav entries: {report['nav_entries']}")
    if report["unmapped_slot_positions"]:
        print(f"  unmapped slots -> OCC: {report['unmapped_slot_positions']}")
    print(f"  -> {a.out}/connector-plan.json")


if __name__ == "__main__":
    main()
