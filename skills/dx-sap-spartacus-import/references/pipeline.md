# Pipeline: stages, gates and run directory

`scripts/orchestrate.py` runs each stage as its own script and stops at two gates. Every stage writes to the run directory (default `$TMPDIR/sap-spartacus-import-<site>/`), so a failed run can be inspected and re-run.

```
extract ─▶ nav-resolve ─▶ model ─▶ [gate 1] ─▶ [gate 2 + pack check] ─▶ sap-app ─▶ seed ─▶ publish ─▶ verify ─▶ [localize per locale]
```

## Stages

| # | Stage | Script | What it does |
|---|---|---|---|
| 1 | extract | `storefront-extract/extract.py` | Crawls the baseSite over OCC: content pages found by following seed labels and internal links, one product and one category layout, slots with their components (`fields=FULL`), navigation, and a manifest of every image. Writes `inventory.json` (schema: `storefront-extract/inventory.schema.json`). |
| 2 | nav-resolve | `storefront-extract/nav_resolve.py` | Resolves navigation link entries into full link detail and finds the navigation roots. Adds `navigationLinks` and `navigationRoots` to the inventory. Skipped when `--inventory` is reused without an OCC base. |
| 3 | model | `content-model/model_connector.py` | Maps the inventory onto the connector model with `registry/connector.registry.json`. Writes `connector-plan.json` (entries, assets, content types needed) and `connector-report.json`. Drops page slots the target content type lacks in the starter pack. With `--carousel-field sap_products`, carousel SKUs become a `sap_products` placeholder the seed resolves. |
| – | gate 1 | orchestrator | Blocks when the site uses a component typeCode the profile doesn't know. Pass with `--approve-model` once it's mapped. |
| – | gate 2 | orchestrator | Names the target stack and says whether it's empty (`cs-seed/stack_info.py`, read-only), then prints what will be written: the connector's full starter pack of content types, assets, and components, navigation entries and pages separately. Checks that every content type and field the plan writes exists in the starter pack, and exits with code 3 if not. With carousels in `sap_products`, also runs the SAP picker preflight (`marketplace-app/sap_preflight.py`) and, on `--approve-publish`, exits with code 4 before any write if it fails. Without `--approve-publish` the run ends here as a dry run. |
| 4 | sap-app | `marketplace-app/sap_app.py` (+ `sap_app.cjs`) | Only when carousels use `sap_products`: installs and configures the SAP Commerce Cloud app on the user's csdx login, finds its Product field extension, writes `sap-app.json`. See [sap-commerce-app.md](sap-commerce-app.md). |
| 5 | seed | `cs-seed/cma_seed_connector.py` | Imports the starter-pack content types (adds a `sap_uid` field where the pack lacks one, and the `sap_products` picker field on the carousel when the app is set up), uploads images, then upserts component entries, the `global_slots` shell entry and page entries in reference order. Exits 3 when items failed (recorded as `warn`; the rest is written). |
| 6 | publish | `cs-seed/publish.py` | Creates the environment when missing (with a Live Preview URL per locale) and publishes every entry and asset in the stack to it in the master locale (`CS_MASTER_LOCALE`, default `en-us`). Ends with a totals line; exits 3 when some publishes failed (recorded as `warn`). |
| 7 | verify, round trip | `verify/verify_connector.py` | Reads the seeded entries back and compares each with its original OCC component, including the rebuilt navigation tree. |
| 8 | verify, delivery | `verify/cda_read.py` | Reads the home page (`landing_page`, url `/`) through the Delivery API with `CS_DELIVERY_TOKEN`. Without a token (always the case on a fresh stack) it exits 5 and the stage is `check` with a note: create a token for the environment, then re-run this script. |
| 9 | localize | `cs-seed/localize.py` | Per `--locales` pair: a localized extract and model, the locale's images, a localized version of every entry, and a publish in that locale. A failed entry update is retried once; if anything still fails the locale is recorded as `warn` and named in the final banner. Re-running it is safe. |

`cs-seed/cma_seed.py` holds the shared Content Management API helpers the seed, publish and localize stages import. `cs-seed/cs_auth.py` picks the auth header: `CS_MANAGEMENT_TOKEN`, or the user's csdx session through `cs-seed/csdx_auth.cjs` (refreshed once after a 401). `marketplace-app/use_products.py` is the user-chosen fallback from the picker back to `products`.

## Flags

| Flag | Default | Notes |
|---|---|---|
| `--site` | required | SAP baseSite uid. |
| `--base` | `$OCC_BASE_URL` | OCC v2 base URL. |
| `--inventory` | none | Reuse a saved `inventory.json` and skip the OCC extract. |
| `--starter-pack` | `$CONNECTOR_STARTER_PACK`, else `./node_modules/@contentstack/contentstack-spartacus-connector/import-export/starter-pack/content_types` | The connector's content types. |
| `--env` | `development` | Target environment for publishing. |
| `--approve-model` | off | Pass gate 1. |
| `--approve-publish` | off | Pass gate 2 and write. |
| `--carousel-field` | `auto` | `sap_products` when the `SAP_APP_*` configuration is exported, else `products`. |
| `--skip-app-install` | off | The SAP app is already set up: only discover its field extension. |
| `--reinstall-app` | off | Uninstall, reinstall and configure the SAP app once (repairs a broken install). |
| `--locales` | none | `sapIso=csLocale` pairs, for example `de=de-de,ja=ja-jp,zh=zh-cn`. |
| `--run-dir` | `$TMPDIR/sap-spartacus-import-<site>` | Where every stage writes. |

## Run directory

- `inventory.json`, `inventory-<iso>.json`: extracted content.
- `connector-plan.json`, `connector-report.json`: the plan and its summary; `model-<iso>/` per locale.
- `sap-app.json`: the app installation and its field extension uids, when the picker is used.
- `manifest.json`: status per stage (`ok`, `warn`, `error`, `blocked`, `dry-run`, `pass`, `check`).

## Exit codes

- `0`: done, or dry run complete.
- `2`: gate 1 blocked on unknown typeCodes.
- `3`: gate 2 blocked on a starter-pack mismatch.
- `4`: gate 2 blocked because the SAP picker preflight failed (nothing installed or written).
- Per-stage `warn` (seed, publish, a locale) doesn't stop the run: some items failed and are listed as ERR lines; re-running is safe.
- Anything else: a stage failed. Its output is printed and recorded in `manifest.json`.

## Common problems

- **`CERTIFICATE_VERIFY_FAILED`**: the SAP backend uses a self-signed certificate. Fix the certificate, or set `OCC_INSECURE_TLS=1` for a dev backend you trust.
- **Starter pack not found**: run from the Spartacus project root after `ng add @contentstack/contentstack-spartacus-connector`, or set `CONNECTOR_STARTER_PACK`.
- **Gate 2 pack mismatch**: the installed connector is older than the mapping profile expects. Update the connector package.
- **`csdx not found` or `not logged in`**: the run has no management token, or reached the SAP app stage. Install `@contentstack/cli` and run `csdx auth:login --oauth`, or export `CS_MANAGEMENT_TOKEN` and pass `--carousel-field products`.
- **SAP picker preflight fails** (exit `4`): the server in `SAP_APP_API_BASE_URL` can't serve the picker. The line marked `FAIL` names the cause: an untrusted certificate, a missing base site, an empty search index, product search behind a login, or a catalog without the carousel codes. See "Before install: preflight" in [sap-commerce-app.md](sap-commerce-app.md).
- **A locale ends as `warn`**: an entry update in that locale failed twice (the Management API can answer a transient 422). Re-run with the same `--locales`; it updates in place.
- **SAP Products field errors or HTTP 414**: see "Verify, retry, then ask" in [sap-commerce-app.md](sap-commerce-app.md).
- **Empty carousels on the storefront**: the connector is older than the `sap_products` release (gate 2 warns about this). Update it, or re-run with `--carousel-field products`.
- **Blank storefront after import**: check the app's `cmsPageContentType` is `landing_page`, the `localeMapping` covers the imported locales, and the environment name matches `CS_ENVIRONMENT`.
