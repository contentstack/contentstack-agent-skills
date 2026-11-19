# SAP Commerce Cloud app: carousel product picker

The optional `sap-app` stage runs between gate 2 and the seed. It sets up the **SAP Commerce Cloud** marketplace app on the target stack, so carousel products come from the app's product picker (`sap_products`) instead of a hand-typed SKU list (`products`). Editors then add, remove and reorder products visually, and Live Preview's Edit on a carousel opens the picker.

The stage runs when carousels are seeded into `sap_products`: by default when `SAP_APP_API_BASE_URL`, `SAP_APP_BASE_SITE` and `SAP_APP_BACKOFFICE_URL` are all exported, or always with `--carousel-field sap_products`. With `--carousel-field products`, or without that configuration, it's skipped and carousels keep the `products` list.

The storefront must run a connector release that reads `sap_products` (it falls back to `products`). Connector 0.1.0 reads only `products` and would render these carousels empty. On a re-run into a stack seeded earlier with `products`, both fields stay filled, so an older connector keeps showing the earlier `products` list.

## Which SAP server and base site

The picker doesn't call SAP from the browser: the app's own backend calls the server in `SAP_APP_API_BASE_URL`. Point it at a server that carries the **same catalog as the storefront's OCC**: the picker saves product codes, and the storefront looks those codes up on its own server.

| Storefront site | `SAP_APP_BASE_SITE` | Notes |
| --- | --- | --- |
| `electronics-spa` (B2C) | `electronics` or `electronics-spa` | The electronics sample catalog. |
| `powertools-spa` (B2B) | `powertools-spa` | Created by `spartacussampledata` once the Powertools sample data (`powertoolsstore`) is imported. Product search must work without a login. |
| Your own site | that site's uid | Any site that passes the preflight below. |

Each stack gets its own app configuration, so an electronics stack and a powertools stack can point at the same SAP server with different base sites.

## Before install: preflight

At gate 2, with carousels going into `sap_products`, the orchestrator runs `scripts/marketplace-app/sap_preflight.py` against that server, with TLS verified (`OCC_INSECURE_TLS` doesn't apply: the app's backend verifies). The dry run prints the result; a write stops with exit code `4` before the app is installed or anything is written if a check fails.

| Check | Fails when | Fix |
| --- | --- | --- |
| tls | The certificate isn't publicly trusted. SAP's default development certificate (`CN=hybris`) is the usual cause. | Give the server a trusted certificate, for example Let's Encrypt behind a reverse proxy. |
| site | `SAP_APP_BASE_SITE` isn't one of the server's base sites. | Import the store's sample data and `spartacussampledata` on that server, or fix the uid. |
| search | Product search returns 0 products, or answers 401/403. | Run a full Solr index for the site (for example `full-powertoolsIndex-cronJob`), or allow anonymous product search on the B2B site. |
| codes | None of the carousels' product codes exist there. Some missing is only a warning; those codes are left out of the picker value. | Point the app at a server with the storefront's catalog. |

Run it on its own with the `SAP_APP_*` variables exported: `python3 "<SKILL_DIR>/scripts/marketplace-app/sap_preflight.py" --plan <run-dir>/connector-plan.json`.

## What it does

1. **Install** the app on the stack if it isn't there yet.
2. **Configure** it, on a fresh install only: one configuration named `SAP_APP_CONFIG_NAME` (default `hti`), set as default, with Custom URL `SAP_APP_API_BASE_URL` + `SAP_APP_API_ROUTE`, base site `SAP_APP_BASE_SITE`, Backoffice `SAP_APP_BACKOFFICE_URL`, and **Keys to Save** = Custom Fields `code` + `name`. Other configurations already on the stack are kept.
3. **Discover** the app's `SAP Commerce Cloud - Product` field extension (it only shows with `?include_marketplace_extensions=true`) and write it to `<run-dir>/sap-app.json`.

The seed step then adds `sap_products` (JSON, that extension) to `product_carousel_component` right after `products`, and fills it per carousel with exactly what the picker saves:

```json
{"type": "sapcommercecloud_product",
 "data": [{"code": "300938", "name": "Photosmart E317 Digital Camera",
           "cs_metadata": {"multiConfigName": "hti", "isConfigDeleted": false}}]}
```

Names come from the app's SAP server (`scripts/marketplace-app/sap_products.py`); codes that server doesn't have are left out and reported. A value over the 20 KB JSON-field limit is refused, which is why the app saves only `code` + `name` (images would make each product about 3 KB). `localize.py` writes the same value to every locale: the picker stores the app's language, not the locale's.

## Auth

A **management token can't install or configure marketplace apps.** Steps 1 and 2 run on the user's own Contentstack CLI session, through csdx's bundled `@contentstack/cli-utilities`, so they need Node.js and `@contentstack/cli` on `PATH`:

```bash
csdx auth:login --oauth      # once; orgs with SSO reject a basic email/password login
```

Step 3 and all seeding use `CS_MANAGEMENT_TOKEN` when it's set, or the same csdx session when it isn't (`CS_AUTH=auto`).

## Run it on its own

```bash
python3 "<SKILL_DIR>/scripts/marketplace-app/sap_app.py" --status                       # read-only: installation + config
python3 "<SKILL_DIR>/scripts/marketplace-app/sap_app.py" --out <run-dir>/sap-app.json    # install/configure once + discover
python3 "<SKILL_DIR>/scripts/marketplace-app/sap_app.py" --out <run-dir>/sap-app.json --skip-install   # already set up: discover only
python3 "<SKILL_DIR>/scripts/marketplace-app/sap_app.py" --out <run-dir>/sap-app.json --reinstall      # repair a broken install
python3 "<SKILL_DIR>/scripts/marketplace-app/use_products.py" --plan <run-dir>/connector-plan.json --env <env>   # fallback to products
```

## Verify, retry, then ask

The pipeline can't tell on its own whether the picker works: the app only talks to its server with a token Contentstack issues inside the browser. So after every `sap_products` run the agent checks it in the browser (or asks the user to), repairs it at most twice, and then hands the decision to the user. Don't keep retrying or ask open-ended questions.

**Check (one attempt):**

1. Open a seeded carousel entry: `https://app.contentstack.com/#!/stack/<api_key>/content-type/product_carousel_component/en-us/entries` (use the region's app host outside North America). The demo sites have two: "Our Bestselling Products" and "What's New" (electronics), "Our Bestselling Products" and "WHAT'S NEW" (powertools).
2. Wait about 20 seconds. **Pass** if the SAP Products field shows "N Products" with names. **Fail** if it shows "Something went wrong while fetching data".
3. Click **Add Product(s)**. **Pass** if the picker lists products. To read the app server's status code, run this in the picker tab with a product code from the carousel:
   ```js
   const tk = new URLSearchParams(location.hash.split('?')[1]||'').get('authToken');
   const q = new URLSearchParams({query:'product','id:in':'[]',isOldUser:'false',configKey:'{"hti":{}}'});
   (await fetch('https://sapcc.contentstackmarket.com/api-auth?'+q,{method:'POST',
     headers:{'Content-Type':'application/json',authToken:tk},
     body:JSON.stringify({config:{},ids:{hti:['<product code>']}})})).status   // 200 ok, 414 = broken install
   ```
   Replace `hti` with `SAP_APP_CONFIG_NAME` if it was changed. Close the picker without adding anything.

**Attempts:**

- Attempt 1: the check right after the run. If it fails, wait a minute and reload once (a fresh install can need a short warm-up). That's still attempt 1.
- Attempts 2 and 3: repair with `sap_app.py --reinstall --out <run-dir>/sap-app.json`, wait a minute, check again. The repair uninstalls the app, installs it, configures it once, and points the carousel's `sap_products` field at the new extension. Entry data is kept.

**After three failed attempts, stop and ask the user.** Say briefly what failed (field or picker error, the status code) and what you tried; recommend installing and configuring the app once from Marketplace in the UI, or raising it with the SAP Commerce Cloud app team with the installation uid from `sap_app.py --status`; and offer the choice: **keep trying to fix the picker**, or **use the `products` field instead**.

Explain the fallback in a sentence or two: the storefront shows the same products either way, because the connector reads `sap_products` first and falls back to `products`. With `products`, editors type or paste SAP product codes into a list instead of searching and picking them, and the entry shows codes rather than names.

**If the user picks `products`**, run `use_products.py --plan <run-dir>/connector-plan.json --env <env>`. It re-imports the carousel content type without `sap_products`, writes each carousel's SKUs into `products` (same order, every locale the entry exists in) and publishes them. Later runs for that stack: `--carousel-field products`. The app stays installed; the user can uninstall it from Marketplace.

## Limits

- **Warm-up:** for about a minute after a fresh install, the field can show "Something went wrong while fetching data". Reload the entry.
- **The configuration is written exactly once, on a fresh install.** Writing it again to an install that already has it, even with identical values, breaks that install on the app's server: the field and picker then fail with HTTP 414 from `sapcc.contentstackmarket.com/api-auth`, and it doesn't recover. So re-runs only check an existing install, and stop if its settings differ. To change settings, use the app's Configuration page; to repair a broken install, run with `--reinstall-app` (or `sap_app.py --reinstall`).
- The first install of an app in an org can need a one-time consent in the UI. If the API install is refused, the stage stops and says so: install it once from Marketplace, then re-run.
