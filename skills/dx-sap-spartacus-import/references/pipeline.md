# Pipeline: stages, gates and run directory

`scripts/orchestrate.py` runs each stage as its own script and stops at two gates. Every stage writes to the run directory (default `$TMPDIR/sap-spartacus-import-<site>/`), so a failed run can be inspected and re-run.

```
extract ─▶ nav-resolve ─▶ model ─▶ [gate 1] ─▶ [gate 2 + pack check] ─▶ seed ─▶ publish ─▶ verify ─▶ [localize per locale]
```

## Stages

| # | Stage | Script | What it does |
|---|---|---|---|
| 1 | extract | `storefront-extract/extract.py` | Crawls the baseSite over OCC: content pages found by following seed labels and internal links, one product and one category layout, slots with their components (`fields=FULL`), navigation, and a manifest of every image. Writes `inventory.json` (schema: `storefront-extract/inventory.schema.json`). |
| 2 | nav-resolve | `storefront-extract/nav_resolve.py` | Resolves navigation link entries into full link detail and finds the navigation roots. Adds `navigationLinks` and `navigationRoots` to the inventory. |
| 3 | model | `content-model/model_connector.py` | Maps the inventory onto the connector model with `registry/connector.registry.json`. Writes `connector-plan.json` (entries, assets, content types needed) and `connector-report.json`. Drops page slots the target content type lacks in the starter pack. |
| – | gate 1 | orchestrator | Blocks when the site uses a component typeCode the profile doesn't know. Pass with `--approve-model` once it's mapped. |
| – | gate 2 | orchestrator | Prints what will be written. Checks that every content type and field the plan writes exists in the starter pack, and exits with code 3 if not. Without `--approve-publish` the run ends here as a dry run. |
| 4 | seed | `cs-seed/cma_seed_connector.py` | Imports the starter-pack content types (adds a `sap_uid` field where the pack lacks one), uploads images, then upserts component entries, the `global_slots` shell entry and page entries in reference order. |
| 5 | publish | `cs-seed/publish.py` | Creates the environment when missing and publishes every entry and asset in the stack to it in the master locale. |
| 6 | verify, round trip | `verify/verify_connector.py` | Reads the seeded entries back and compares each with its original OCC component, including the rebuilt navigation tree. |
| 7 | verify, delivery | `verify/cda_read.py` | Reads the home page (`landing_page`, url `/`) through the Delivery API with `CS_DELIVERY_TOKEN`. |
| 8 | localize | `cs-seed/localize.py` | Per `--locales` pair: a localized extract and model, the locale's images, a localized version of every entry, and a publish in that locale. |

`cs-seed/cma_seed.py` holds the shared Content Management API helpers the seed, publish and localize stages import.

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
| `--locales` | none | `sapIso=csLocale` pairs, for example `de=de-de,ja=ja-jp,zh=zh-cn`. |
| `--run-dir` | `$TMPDIR/sap-spartacus-import-<site>` | Where every stage writes. |

## Run directory

- `inventory.json`, `inventory-<iso>.json`: extracted content.
- `connector-plan.json`, `connector-report.json`: the plan and its summary; `model-<iso>/` per locale.
- `manifest.json`: status per stage (`ok`, `warn`, `error`, `blocked`, `dry-run`, `pass`, `check`).

## Exit codes

- `0`: done, or dry run complete.
- `2`: gate 1 blocked on unknown typeCodes.
- `3`: gate 2 blocked on a starter-pack mismatch.
- Anything else: a stage failed. Its output is printed and recorded in `manifest.json`.

## Common problems

- **`CERTIFICATE_VERIFY_FAILED`**: the SAP backend uses a self-signed certificate. Fix the certificate, or set `OCC_INSECURE_TLS=1` for a dev backend you trust.
- **Starter pack not found**: run from the Spartacus project root after `ng add @contentstack/contentstack-spartacus-connector`, or set `CONNECTOR_STARTER_PACK`.
- **Gate 2 pack mismatch**: the installed connector is older than the mapping profile expects. Update the connector package.
- **Blank storefront after import**: check the app's `cmsPageContentType` is `landing_page`, the `localeMapping` covers the imported locales, and the environment name matches `CS_ENVIRONMENT`.
