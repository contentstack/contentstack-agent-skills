#!/usr/bin/env python3
"""
orchestrate — the content-modeling AGENT: one governed command that runs the whole
pipeline for a storefront, with two human gates.

  extract ──▶ nav-resolve ──▶ model ──▶ [GATE 1: model approval]
          ──▶ [GATE 2: pre-publish] ──▶ SAP app ──▶ seed ──▶ publish ──▶ verify

The SAP app stage runs only when carousels are seeded into `sap_products` (the default when
the SAP_APP_* configuration is exported; --carousel-field overrides): it installs + configures
the SAP Commerce Cloud marketplace app on the stack using the user's csdx login, so editors
pick carousel products from SAP instead of typing SKUs. Otherwise carousels keep the plain
`products` SKU list.

It sequences the skills (each a standalone, tested script), enforces the gates, and
handles the one judgment call the skills don't: an UNKNOWN typeCode (Gate 1). Everything
is idempotent — re-running updates in place — and resumable via the run directory.

GATES (fail-closed): the pipeline STOPS at each gate unless the matching approval flag is
passed, so nothing is created or published without an explicit human go.
  Gate 1  model approval   -> pass --approve-model    (only blocks if unknown typeCodes found)
  Gate 2  pre-publish      -> pass --approve-publish   (always blocks before any write; with the
                              SAP picker on, also stops with exit 4 if the picker's SAP server
                              fails the preflight in marketplace-app/sap_preflight.py)

Default (no approval flags) = a full DRY RUN: extract→model + both gate reports, no writes.

Usage (from the Spartacus project root, after `ng add @contentstack/contentstack-spartacus-connector`):
  # dry run (safe): see the plan + gate reports, write nothing
  python3 orchestrate.py --site electronics-spa

  # full governed run (requires CS_* env for seed/publish/verify)
  python3 orchestrate.py --site electronics-spa --approve-model --approve-publish --env development

Written by Vaishnavi Kedar (spartacus-content-modelling-agent); packaged as the
dx-sap-spartacus-import skill.
"""
import argparse, json, os, subprocess, sys, datetime, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS = ROOT
PROFILE = os.path.join(ROOT, "registry", "connector.registry.json")
# The connector's shipped starter-pack content types are the model of record. Default: the
# copy `ng add` installed in the current project; override with --starter-pack or
# CONNECTOR_STARTER_PACK (e.g. a connector checkout).
_INSTALLED = os.path.join(os.getcwd(), "node_modules", "@contentstack", "contentstack-spartacus-connector",
                          "import-export", "starter-pack", "content_types")
DEFAULT_STARTER = os.environ.get("CONNECTOR_STARTER_PACK", _INSTALLED)
DEFAULT_OCC = os.environ.get("OCC_BASE_URL")
# The SAP Commerce Cloud marketplace app configuration (the SAP server its product picker
# searches). With all three set, `--carousel-field auto` seeds carousels into the picker field
# `sap_products`; without them, carousels keep the plain `products` SKU list.
SAP_APP_ENV = ("SAP_APP_API_BASE_URL", "SAP_APP_BASE_SITE", "SAP_APP_BACKOFFICE_URL")

C = {"h": "\033[1m", "ok": "\033[32m", "warn": "\033[33m", "err": "\033[31m",
     "gate": "\033[35m", "z": "\033[0m"}


def banner(txt, color="h"):
    line = "─" * (len(txt) + 2)
    print(f"{C[color]}┌{line}┐\n│ {txt} │\n└{line}┘{C['z']}")


def step(txt):
    print(f"{C['h']}▶ {txt}{C['z']}")


OCC_BASE = None   # set in main(); exported to every stage so asset downloads hit the same OCC


def run(script, args, env=None):
    """Run a skill script; stream nothing, return (rc, output)."""
    env = dict(env or os.environ)
    if OCC_BASE:
        env["OCC_BASE_URL"] = OCC_BASE
    p = subprocess.run([sys.executable, os.path.join(SKILLS, script), *args],
                       capture_output=True, text=True, env=env)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def known_typecodes(profile):
    comp = {k for k in profile["component_map"] if not k.startswith("_")}
    occ = set(profile["occ_only_types"]["types"])
    return comp | occ


def load_pack(dir_):
    """uid -> content type JSON for every type in the starter pack (schema.json skipped)."""
    pack = {}
    for f in sorted(os.listdir(dir_)):
        if f.endswith(".json") and f != "schema.json":
            ct = json.load(open(os.path.join(dir_, f)))
            if isinstance(ct, dict) and ct.get("uid"):
                pack[ct["uid"]] = ct
    return pack


def connector_reads_sap_products(starter_pack):
    """(version, reads) for the connector the starter pack came from. reads is True when its
    code reads the picker field `sap_products`, False when it doesn't (npm 0.1.0 reads only
    `products`), None when no code was found next to the starter pack.

    The version can't decide it: a build from the connector repo's main branch also says
    0.1.0. So look at the code: the installed package's bundle (node_modules, a `file:` tgz or
    an npm link), else a repo checkout's build (dist/) or its source (src/, specs excluded)."""
    root = os.path.abspath(os.path.join(starter_pack, "..", "..", ".."))
    version = None
    try:
        version = json.load(open(os.path.join(root, "package.json"))).get("version")
    except Exception:
        pass
    found_code = False
    for d in ("fesm2022", "fesm2020", "fesm2015", "bundles", os.path.join("dist", "fesm2022"), "dist"):
        folder = os.path.join(root, d)
        if not os.path.isdir(folder):
            continue
        for f in os.listdir(folder):
            if f.endswith((".mjs", ".js")):
                found_code = True
                if "sap_products" in open(os.path.join(folder, f), errors="ignore").read():
                    return version, True
    src = os.path.join(root, "src")
    if not found_code and os.path.isdir(src):
        for dirpath, _, files in os.walk(src):
            for f in files:
                if f.endswith(".ts") and not f.endswith(".spec.ts"):
                    found_code = True
                    if "sap_products" in open(os.path.join(dirpath, f), errors="ignore").read():
                        return version, True
    return version, (False if found_code else None)


def pack_mismatches(plan, pack):
    """Every content type and field the plan writes must exist in the starter pack, or the
    seed fails half-way. sap_uid is allowed: the seeder adds it when the pack lacks it."""
    problems = []
    for ct in plan.get("content_types_needed", []):
        if ct not in pack:
            problems.append(f"content type '{ct}' is not in the starter pack")
    entries = plan.get("entries", {})
    groups = [entries.get("components", []), entries.get("pages", []), entries.get("nav", [])]
    if entries.get("global_slots"):
        groups.append([entries["global_slots"]])
    for group in groups:
        for e in group:
            ct = e.get("_content_type")
            if ct not in pack:
                continue
            fields = {f["uid"] for f in pack[ct].get("schema", [])} | {"sap_uid", "title"}
            if ct == "product_carousel_component":
                fields.add("sap_products")   # the seeder adds the SAP app picker field per stack
            for k in e:
                if not k.startswith("_") and k not in fields:
                    problems.append(f"{ct}.{k} is not a field in the starter pack")
    return sorted(set(problems))


def main():
    global OCC_BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--inventory", default="", help="reuse a saved inventory.json instead of extracting")
    ap.add_argument("--base", default=DEFAULT_OCC, help="OCC v2 base URL, e.g. https://HOST/occ/v2 (or set OCC_BASE_URL)")
    ap.add_argument("--starter-pack", default=DEFAULT_STARTER, help="connector starter-pack content_types dir")
    ap.add_argument("--env", default="development")
    ap.add_argument("--approve-model", action="store_true", help="pass Gate 1")
    ap.add_argument("--approve-publish", action="store_true", help="pass Gate 2 (enables writes)")
    ap.add_argument("--locales", default="", help="optional i18n: sapIso=csLocale,... e.g. de=de-de,ja=ja-jp,zh=zh-cn")
    ap.add_argument("--carousel-field", choices=["auto", "products", "sap_products"], default="auto",
                    help="where carousel SKUs go; auto = sap_products when SAP_APP_API_BASE_URL, "
                         "SAP_APP_BASE_SITE and SAP_APP_BACKOFFICE_URL are set (any site, B2C or B2B) AND "
                         "the installed connector reads sap_products; products otherwise")
    ap.add_argument("--skip-app-install", action="store_true",
                    help="SAP app already installed + configured: only discover its field extension")
    ap.add_argument("--reinstall-app", action="store_true",
                    help="uninstall + reinstall the SAP app and configure it once (repairs a broken install)")
    ap.add_argument("--run-dir", default="")
    a = ap.parse_args()
    if not a.base and (not a.inventory or a.locales or a.approve_publish):
        # --inventory alone can re-plan offline; asset uploads and localized extracts need OCC.
        sys.exit("Set OCC_BASE_URL (or pass --base https://HOST/occ/v2).")
    OCC_BASE = a.base
    if not os.path.isdir(a.starter_pack):
        sys.exit(f"Starter pack not found at {a.starter_pack}. Run from the Spartacus project root after "
                 "`ng add @contentstack/contentstack-spartacus-connector`, or set CONNECTOR_STARTER_PACK.")
    locale_map = dict(p.split("=", 1) for p in a.locales.split(",") if "=" in p) if a.locales else {}
    carousel_field = a.carousel_field
    picker_configured = all(os.environ.get(k) for k in SAP_APP_ENV)
    conn_ver, conn_reads = connector_reads_sap_products(a.starter_pack)
    carousel_reason = ""
    if carousel_field == "auto":
        if picker_configured and conn_reads:
            carousel_field = "sap_products"
            carousel_reason = "SAP_APP_* set and the connector reads sap_products"
        else:
            carousel_field = "products"
            if not picker_configured:
                carousel_reason = "SAP_APP_* not set"
            elif conn_reads is False:
                carousel_reason = f"the installed connector ({conn_ver or 'unknown version'}) reads only `products`"
            else:
                carousel_reason = "couldn't find the connector's code to check whether it reads sap_products"

    run_dir = a.run_dir or os.path.join(tempfile.gettempdir(), f"sap-spartacus-import-{a.site}")
    os.makedirs(run_dir, exist_ok=True)
    inv_path = os.path.join(run_dir, "inventory.json")
    profile = json.load(open(PROFILE))
    manifest = {"site": a.site, "started": datetime.datetime.now().isoformat(timespec="seconds"),
                "stages": {}}

    def record(stage, status, note=""):
        manifest["stages"][stage] = {"status": status, "note": note}
        json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=2)

    banner(f"CONTENT-MODELING AGENT · {a.site} · profile connector-reference-fields")
    print(f"  run dir: {run_dir}   env: {a.env}   starter pack: {a.starter_pack}")
    print(f"  carousel SKUs -> {carousel_field}{' (' + carousel_reason + ')' if carousel_reason else ''}")
    print(f"  occ: {a.base}   region: {os.environ.get('CS_REGION_BASE', 'https://api.contentstack.io')}")
    print(f"  approvals: model={'YES' if a.approve_model else 'no'} "
          f"publish={'YES' if a.approve_publish else 'no'}"
          f"{'   (DRY RUN — no writes)' if not a.approve_publish else ''}\n")

    # 1. EXTRACT (or load fixture)
    step("1/8 extract")
    if a.inventory:
        json.dump(json.load(open(a.inventory)), open(inv_path, "w"))
        print(f"   reused inventory {a.inventory} -> {inv_path}")
    else:
        rc, out = run("storefront-extract/extract.py",
                      ["--site", a.site, "--base", a.base, "--out", inv_path, "--quiet"])
        print("   " + out.strip().splitlines()[-1] if out.strip() else "")
        if rc:
            record("extract", "error", out[-300:]); sys.exit("extract failed")
    record("extract", "ok")

    # 2. NAV RESOLVE
    step("2/8 nav-resolve")
    if a.base:
        rc, out = run("storefront-extract/nav_resolve.py", ["--inventory", inv_path, "--site", a.site, "--base", a.base])
        print("   " + (out.strip().splitlines()[-1] if out.strip() else ""))
        record("nav-resolve", "ok" if not rc else "warn")
    else:   # reused inventory, no OCC: keep the navigation it already resolved
        has_nav = "navigationLinks" in json.load(open(inv_path))
        print(f"   skipped (no OCC base){'; the inventory already has resolved navigation' if has_nav else ''}")
        record("nav-resolve", "skipped" if has_nav else "warn", "" if has_nav else "no OCC base, navigation unresolved")

    # 3. MODEL
    step("3/8 model")
    rc, out = run("content-model/model_connector.py",
                  ["--inventory", inv_path, "--profile", PROFILE, "--out", run_dir,
                   "--starter-pack", a.starter_pack, "--carousel-field", carousel_field])
    print("   " + "\n   ".join(out.strip().splitlines()))
    if rc:
        record("model", "error", out[-300:]); sys.exit("model failed")
    record("model", "ok")
    plan = json.load(open(os.path.join(run_dir, "connector-plan.json")))

    # 4. GATE 1 — model approval (unknown typeCodes)
    inv = json.load(open(inv_path))
    seen = set(inv.get("componentTypeInventory", {}))
    unknown = sorted(seen - known_typecodes(profile))
    print()
    banner("GATE 1 · MODEL APPROVAL", "gate")
    if unknown:
        print(f"  {C['warn']}UNKNOWN typeCodes (not in profile): {unknown}{C['z']}")
        print("  These need a human decision: add to component_map (authored) or occ_only_types (OCC).")
        if not a.approve_model:
            record("gate1", "blocked", f"unknown: {unknown}")
            print(f"\n  {C['err']}STOP{C['z']} — resolve the mapping, then re-run with --approve-model.")
            sys.exit(2)
        print(f"  {C['ok']}approved (--approve-model){C['z']} — proceeding.")
    else:
        print(f"  {C['ok']}no unknown typeCodes — all {len(seen)} classified.{C['z']}")
    record("gate1", "passed", f"unknown={unknown}")

    # 5. GATE 2 — pre-publish summary
    n_comp = len(plan["entries"]["components"])
    n_pages = len(plan["entries"]["pages"])
    print()
    banner("GATE 2 · PRE-PUBLISH", "gate")
    if os.environ.get("CS_API_KEY"):
        _, out_si = run("cs-seed/stack_info.py", [])
        print("  " + (out_si.strip().splitlines() or ["target stack: unknown"])[-1])
    else:
        print("  target stack: not set yet (export CS_API_KEY before the write)")
    pack = load_pack(a.starter_pack)
    try:
        report = json.load(open(os.path.join(run_dir, "connector-report.json")))
        n_nav = sum((report.get("nav_entries") or {}).values())
    except Exception:
        n_nav = 0
    print(f"  will UPSERT to that stack + publish to '{a.env}':")
    print(f"    content types : {len(pack)} (the connector's full starter pack; this site's entries "
          f"use {len(plan['content_types_needed'])}). Existing types with these uids are replaced.")
    print(f"    assets        : {len(plan['assets'])}")
    print(f"    entries       : {n_comp - n_nav} components, {n_nav} navigation, {n_pages} pages, "
          f"{'1' if plan['entries'].get('global_slots') else '0'} global_slots")
    print(f"    pages: {[p['_key']['value'] for p in plan['entries']['pages']]}")
    if locale_map:
        print(f"    + localize into: {list(locale_map.values())} "
              f"(fully-localized OCC extract per language, incl. per-locale images)")
    mismatches = pack_mismatches(plan, pack)
    if mismatches:
        print(f"  {C['err']}starter pack mismatch ({len(mismatches)}){C['z']} — the plan writes types/fields the pack lacks:")
        for m in mismatches[:25]:
            print(f"    - {m}")
        print("  Update the connector (npm i @contentstack/contentstack-spartacus-connector@latest) or the "
              "mapping profile before writing.")
        record("gate2", "blocked", f"pack mismatch: {len(mismatches)}")
        sys.exit(3)
    print(f"  {C['ok']}starter pack check: every planned type and field exists{C['z']}")
    print(f"    carousel SKUs -> {carousel_field}")
    if carousel_field == "sap_products" and conn_reads is False:
        # only when forced with --carousel-field sap_products
        print(f"    {C['warn']}the installed connector ({conn_ver or 'unknown version'}) reads only `products`:{C['z']} "
              f"carousels seeded into sap_products render empty on the storefront until you update to "
              f"the connector release that reads sap_products (or use --carousel-field products).")
        record("connector", "warn", f"{conn_ver} reads only products; picker forced")
    elif carousel_field == "products" and picker_configured and a.carousel_field == "auto":
        print(f"    {C['warn']}SAP product picker not set up:{C['z']} {carousel_reason}. The carousels get the plain "
              f"`products` list, which this connector renders. Update to a connector that reads sap_products "
              f"(the release, or a build of the connector repo's main branch) and re-run to use the picker, "
              f"or force it with --carousel-field sap_products.")
        record("connector", "warn", carousel_reason)
    auth = os.environ.get("CS_AUTH", "auto").lower()
    uses_token = auth == "token" or (auth == "auto" and os.environ.get("CS_MANAGEMENT_TOKEN"))
    print(f"    writes as: {'management token' if uses_token else 'your csdx login (csdx auth:login --oauth)'}")
    if carousel_field == "sap_products":
        if a.skip_app_install:
            print("    SAP Commerce Cloud app: already set up (--skip-app-install) — only find its Product field")
        else:
            print(f"    SAP Commerce Cloud app: install if missing + config "
                  f"'{os.environ.get('SAP_APP_CONFIG_NAME', 'hti')}': server SAP_APP_API_BASE_URL"
                  f"{os.environ.get('SAP_APP_API_ROUTE', '/occ/v2/')}, base site "
                  f"{os.environ.get('SAP_APP_BASE_SITE', '<SAP_APP_BASE_SITE unset>')}"
                  f", keys code+name (uses your csdx login)")
            missing = [k for k in SAP_APP_ENV if not os.environ.get(k)]
            if missing:
                print(f"    {C['warn']}missing env for the SAP app: {missing}{C['z']}")
    # The picker's SAP server must serve this site to an anonymous caller over trusted TLS,
    # with a built search index and the carousels' product codes (B2C and B2B sites alike).
    # Checked here so the dry run shows it, and so a failing server stops the run before
    # the app is installed or anything is written.
    preflight_failed = False
    if carousel_field == "sap_products" and all(os.environ.get(k) for k in SAP_APP_ENV[:2]):
        rc_pf, out_pf = run("marketplace-app/sap_preflight.py",
                            ["--plan", os.path.join(run_dir, "connector-plan.json")])
        print("    SAP picker preflight:")
        print("\n".join("  " + line for line in out_pf.rstrip().splitlines()))
        record("picker-preflight", "pass" if not rc_pf else "fail",
               " | ".join(l.strip() for l in out_pf.splitlines()
                          if l.strip().startswith(("ok", "warn", "FAIL")))[:300])
        preflight_failed = bool(rc_pf)
    if not a.approve_publish:
        record("gate2", "dry-run")
        if preflight_failed:
            print(f"\n  {C['err']}The SAP picker preflight failed{C['z']} — a write would stop before "
                  f"the app is installed. Fix the SAP server, or use --carousel-field products.")
        print(f"\n  {C['warn']}DRY RUN complete{C['z']} — nothing written. "
              f"Re-run with --approve-publish (and CS_* env) to seed + publish.")
        sys.exit(0)
    if preflight_failed:
        record("gate2", "blocked", "SAP picker preflight failed")
        print(f"  {C['err']}stopped: the SAP picker preflight failed{C['z']} — nothing installed or written. "
              f"Fix the SAP server, or re-run with --carousel-field products.")
        sys.exit(4)
    if not os.environ.get("CS_API_KEY"):
        record("gate2", "error", "no creds")
        sys.exit(f"{C['err']}--approve-publish set but CS_API_KEY missing.{C['z']}")
    if os.environ.get("CS_AUTH", "auto").lower() == "token" and not os.environ.get("CS_MANAGEMENT_TOKEN"):
        record("gate2", "error", "no creds")
        sys.exit(f"{C['err']}CS_AUTH=token but CS_MANAGEMENT_TOKEN missing.{C['z']}")
    print(f"  {C['ok']}approved (--approve-publish){C['z']} — writing.")
    record("gate2", "passed")

    plan_path = os.path.join(run_dir, "connector-plan.json")
    # 6. SAP APP — install/configure the marketplace app + find its Product field extension
    sap_app_path = os.path.join(run_dir, "sap-app.json")
    seed_args = ["--plan", plan_path, "--starter-pack", a.starter_pack, "--stages", "types,assets,entries"]
    step("4/8 SAP Commerce Cloud app")
    if carousel_field == "sap_products":
        missing = [k for k in SAP_APP_ENV if not os.environ.get(k)]
        if missing and not a.skip_app_install:
            record("sap-app", "error", f"missing env {missing}")
            sys.exit(f"{C['err']}SAP app env missing: {missing} — export them, or pass "
                     f"--carousel-field products.{C['z']}")
        rc, out = run("marketplace-app/sap_app.py",
                      ["--out", sap_app_path] + (["--skip-install"] if a.skip_app_install else [])
                      + (["--reinstall"] if a.reinstall_app else []))
        print("   " + "\n   ".join(out.strip().splitlines()[-4:]))
        record("sap-app", "ok" if not rc else "error", out[-300:])
        if rc:
            sys.exit("SAP app stage failed")
        seed_args += ["--sap-app", sap_app_path]
    else:
        print("   skipped (carousels use the plain products SKU list)")
        record("sap-app", "skipped")

    # 7. SEED
    step("5/8 seed (types + assets + entries)")
    rc, out = run("cs-seed/cma_seed_connector.py", seed_args)
    tail = "\n   ".join(out.strip().splitlines()[-6:])
    print("   " + tail)
    # exit 3 = some items failed (their ERR lines are in the output); the rest was written
    record("seed", "ok" if not rc else "warn" if rc == 3 else "error", out[-300:])
    if rc and rc != 3:
        sys.exit("seed failed")
    if rc == 3:
        print(f"   {C['warn']}some items failed (ERR lines above); re-running is safe{C['z']}")

    # 7. PUBLISH
    step("6/8 publish")
    master = os.environ.get("CS_MASTER_LOCALE", "en-us")
    rc, out = run("cs-seed/publish.py", ["--env", a.env, "--locale", master])
    print("   " + "\n   ".join(out.strip().splitlines()[-4:]))
    record("publish", "ok" if not rc else "warn" if rc == 3 else "error", out.strip().splitlines()[-1] if out.strip() else "")

    # 8. VERIFY
    step("7/8 verify — round-trip")
    rc, out = run("verify/verify_connector.py", ["--inventory", inv_path, "--plan", plan_path])
    print("   " + "\n   ".join(out.strip().splitlines()[-3:]))
    rt_ok = rc == 0
    record("verify-roundtrip", "pass" if rt_ok else "check")

    step("8/8 verify — delivery read (landing page)")
    venv = os.environ.copy(); venv["CS_ENVIRONMENT"] = a.env
    rc, out = run("verify/cda_read.py", ["--content-type", "landing_page", "--url", "/"], env=venv)
    print("   " + "\n   ".join(out.strip().splitlines()[-2:]))
    # exit 5 = no delivery token yet (expected on a fresh stack): re-run cda_read.py after creating one
    record("verify-cda", "pass" if rc == 0 else "check",
           "no CS_DELIVERY_TOKEN yet: create one for the environment, then re-run verify/cda_read.py"
           if rc == 5 else out.strip().splitlines()[-1] if out.strip() else "")

    # 9. LOCALIZE (optional) — full localized OCC extract per language, then localize+publish.
    for sap_iso, cs_loc in locale_map.items():
        print()
        banner(f"LOCALIZE · {sap_iso} → {cs_loc}", "gate")
        linv = os.path.join(run_dir, f"inventory-{sap_iso}.json")
        lmodel = os.path.join(run_dir, f"model-{sap_iso}")
        # localized inventory (always live — i18n needs the localized OCC responses)
        rc, out = run("storefront-extract/extract.py",
                      ["--site", a.site, "--base", a.base, "--langs", sap_iso, "--primary-only", "--out", linv, "--quiet"])
        if rc:
            record(f"localize:{cs_loc}", "error", "extract failed"); continue
        run("storefront-extract/nav_resolve.py", ["--inventory", linv, "--site", a.site, "--base", a.base, "--lang", sap_iso])
        rc, out = run("content-model/model_connector.py", ["--inventory", linv, "--profile", PROFILE, "--out", lmodel,
                                                           "--starter-pack", a.starter_pack,
                                                           "--carousel-field", carousel_field])
        if rc:
            record(f"localize:{cs_loc}", "error", "model failed"); continue
        rc, out = run("cs-seed/localize.py",
                      ["--locale", cs_loc, "--plan", os.path.join(lmodel, "connector-plan.json"), "--env", a.env])
        print("   " + "\n   ".join(out.strip().splitlines()[-4:]))
        # localize.py exits 3 when some entries or assets failed after a retry (re-running is safe)
        record(f"localize:{cs_loc}", "ok" if not rc else "warn" if rc == 3 else "error", out[-200:])

    print()
    loc_ok = [l for l in locale_map.values() if manifest["stages"].get(f"localize:{l}", {}).get("status") == "ok"]
    loc_failed = [l for l in locale_map.values() if l not in loc_ok]
    banner(f"DONE · {a.site} · round-trip {'PASS' if rt_ok else 'CHECK'}"
           f"{' · +' + str(len(loc_ok)) + ' locales' if loc_ok else ''}"
           f"{' · locales with errors (re-run is safe): ' + ', '.join(loc_failed) if loc_failed else ''}",
           "ok" if rt_ok and not loc_failed else "warn")
    print(f"  manifest: {run_dir}/manifest.json")
    stages = manifest["stages"]
    for name in ("seed", "publish"):
        if stages.get(name, {}).get("status") == "warn":
            print(f"  {C['warn']}{name}: some items failed{C['z']} — see the ERR lines above; re-running is safe")
    if stages.get("verify-cda", {}).get("status") == "check":
        print(f"  delivery check: {stages['verify-cda'].get('note') or 'see the output above'}")
    if carousel_field == "sap_products":
        print(f"\n  {C['gate']}NEXT · verify the SAP product picker in the browser{C['z']} — "
              f"references/sap-commerce-app.md › 'Verify, retry, then ask'. Without a browser, ask the "
              f"user to open a carousel entry and check that the SAP Products field lists products.\n"
              f"  Repair (max 2): python3 {os.path.join(SKILLS, 'marketplace-app', 'sap_app.py')} "
              f"--reinstall --out {sap_app_path}\n"
              f"  Fallback (user's choice): python3 {os.path.join(SKILLS, 'marketplace-app', 'use_products.py')} "
              f"--plan {plan_path} --env {a.env} --starter-pack {a.starter_pack}")


if __name__ == "__main__":
    main()
