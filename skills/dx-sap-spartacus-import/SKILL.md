---
name: dx-sap-spartacus-import
description: "Import the CMS content of a running SAP Commerce Cloud (Spartacus / composable storefront) site into a Contentstack stack, in the model the Contentstack Spartacus connector reads. Extracts pages, slots, components, navigation and images over SAP OCC, maps them onto the connector starter-pack content types, seeds and publishes them, verifies the round trip, and can localize into more languages. Can also install the SAP Commerce Cloud marketplace app so carousels use its product picker. Use when a developer has added @contentstack/contentstack-spartacus-connector to a Spartacus app (ng add) and wants to bring the existing SAP storefront content into Contentstack, seed a demo stack from an SAP electronics or powertools site, re-run the import to update entries, add de/ja/zh locales, or have editors pick carousel products from SAP. For Contentful-to-Contentstack migrations, use migration-companion; for general csdx import or export, use dx-cli; for content model design, use cms-data-modeling-best-practices."
allowed-tools: Read Grep Glob Bash
---

# SAP Spartacus content import

Takes the content an SAP Commerce Cloud storefront serves over OCC and recreates it in Contentstack, shaped for `@contentstack/contentstack-spartacus-connector`. It follows the connector's hybrid model: Contentstack holds the authored slots (banners, paragraphs, carousels, links, navigation, logo, footer), while SAP keeps products, prices, search, cart, checkout and every functional component.

## When to use

- A Spartacus app has the connector (`ng add @contentstack/contentstack-spartacus-connector`) and the team wants the existing SAP storefront content in Contentstack.
- Seeding a demo or proof-of-concept stack from an SAP site such as `electronics-spa` or `powertools-spa`.
- Re-running the import after content changed in SAP (it updates entries in place).
- Adding locales (`de-de`, `ja-jp`, `zh-cn`, …) from SAP's localized content.

Use another skill for:

- Migrating from Contentful → `migration-companion`
- Plain `csdx` import, export, seed or bulk publish → `dx-cli`
- Designing a content model from scratch → `cms-data-modeling-best-practices`
- Live Preview or Visual Builder setup → `cms-live-preview-visual-editor-support-assistant`
- Other marketplace apps, or the SAP app's category picker and fields outside carousels → `marketplace-apps`

## Before you answer

Confirm, without asking for secret values:

1. The current directory is the Spartacus project root and `node_modules/@contentstack/contentstack-spartacus-connector/import-export/starter-pack/content_types` exists. If not, the connector isn't installed: run `ng add @contentstack/contentstack-spartacus-connector` first, or point `CONNECTOR_STARTER_PACK` at a connector checkout.
2. The SAP baseSite uid (for example `electronics-spa`) and the OCC v2 base URL (`https://HOST/occ/v2`). List baseSites with `curl -s "$OCC_BASE_URL/basesites"`.
3. The target stack is **new or dedicated to this import**. The publish step publishes every entry and asset in the stack.
4. `python3 --version` is 3.9 or later. The Python scripts use only the standard library.
5. How the run writes: with `CS_MANAGEMENT_TOKEN`, or, without one, as the user's own `csdx auth:login --oauth` session. The SAP Commerce Cloud app step always needs that csdx session (a management token can't install apps), plus Node.js and `@contentstack/cli` on `PATH`.
6. For the product picker: the SAP server the app will search (`SAP_APP_API_BASE_URL`, with a publicly trusted certificate), its base site (`SAP_APP_BASE_SITE`: `electronics` for the electronics demo, `powertools-spa` for the B2B powertools demo) and its Backoffice URL. It must carry the same catalog as the storefront's OCC. See [references/sap-commerce-app.md](references/sap-commerce-app.md).

## Instructions

1. Resolve `<SKILL_DIR>`: the folder this `SKILL.md` was loaded from. Run every script by absolute path, `python3 "<SKILL_DIR>/scripts/orchestrate.py"`, from the Spartacus project root.
2. Ask the user to export the variables under Environment Variables in their own shell. Never ask them to paste values into chat.
3. **Dry run** (writes nothing):
   ```bash
   python3 "<SKILL_DIR>/scripts/orchestrate.py" --site electronics-spa
   ```
   It extracts the site, builds the plan and prints both gate reports. Summarize them for the user: pages, component entries, assets, which slots stay with SAP, any unknown component types, where carousel SKUs go (`products` or `sap_products`), and whether writes run as the management token or the csdx login.
4. **Gate 1, model approval.** If the report lists unknown typeCodes, stop. Each one is either authored (add it to `component_map` in `scripts/registry/connector.registry.json` with its connector content type and field mapping) or functional (add it to `occ_only_types.types`). Re-run the dry run. Pass `--approve-model` only after the user agrees.
5. **Gate 2, pre-publish.** Show the counts and the target stack and environment. The run stops here if the plan writes a content type or field the installed starter pack lacks. The fix is a newer connector (`npm i @contentstack/contentstack-spartacus-connector@latest`), not editing the stack by hand.
6. With the user's explicit yes, run the write:
   ```bash
   python3 "<SKILL_DIR>/scripts/orchestrate.py" --site electronics-spa \
     --approve-model --approve-publish --env development
   ```
   This sets up the SAP Commerce Cloud app when carousels use the picker, imports the starter-pack content types, uploads images, upserts entries, creates the environment if needed, publishes, and runs the verify steps.
7. **Carousel products.** With `SAP_APP_API_BASE_URL`, `SAP_APP_BASE_SITE` and `SAP_APP_BACKOFFICE_URL` exported, carousels go into `sap_products`, the SAP Commerce Cloud app's product picker; otherwise into the plain `products` SKU list. Force either with `--carousel-field products|sap_products`. It works the same for B2C and B2B sites. Gate 2 runs a preflight on the picker's SAP server (trusted certificate, base site present, product search returns products without a login, carousel codes found); if it fails, the write stops with exit code 4 before the app is installed. Quote the `FAIL` line to the user with its fix. After a picker run, follow "Verify, retry, then ask" in [references/sap-commerce-app.md](references/sap-commerce-app.md): check the picker, repair at most twice, then let the user choose between fixing it and falling back to `products`.
8. For more languages, add `--locales de=de-de,ja=ja-jp,zh=zh-cn` (SAP isocode = Contentstack locale). Locales are created when missing, with the master locale as fallback.
9. Report the result from `manifest.json` in the run directory, then point the user at the app config: `cmsPageContentType: 'landing_page'`, a `localeMapping` that matches the locales imported, and `occFallback: true`.

### How the pipeline works

`extract → nav-resolve → model → gate 1 → gate 2 (+ SAP picker preflight) → sap-app → seed → publish → verify → localize`. Stage details, run-directory files and flags are in [references/pipeline.md](references/pipeline.md). The mapping rules (which SAP templates, slots and typeCodes become which content types) are in [references/mapping-profile.md](references/mapping-profile.md). The SAP Commerce Cloud app stage, its auth and its recovery steps are in [references/sap-commerce-app.md](references/sap-commerce-app.md).

### Rules

- **Idempotent.** Component entries upsert by `sap_uid`, pages by `url`, the shell entry by `title`, assets by a `sap_code` tag. Re-running updates in place; it never duplicates.
- **Starter pack is the model of record.** The skill never invents content types. It imports the connector's pack and drops any page slot the target page type lacks, leaving that slot to SAP.
- **Hybrid by design.** Login, account, cart, checkout, search and other functional pages get no Contentstack page. SiteContext and SiteLinks stay with SAP, so the language switcher and sign-in keep working.
- **Reuse an extract** with `--inventory <run-dir>/inventory.json` to re-plan without calling OCC again.
- **Self-signed SAP dev backends** fail TLS verification. Set `OCC_INSECURE_TLS=1` only for a backend the user owns and trusts; never for production.

## MCP tools

The import runs on the bundled Python scripts against the Content Management API; it doesn't need MCP. When the Contentstack MCP server is connected, its read tools are a way to check the result (local server group in brackets):

- Inspect: `get_all_content_types`, `get_single_entry`, `get_all_entries`, `get_all_assets`, `get_all_languages`, `get_all_environments` (`cma`)

Don't use MCP write or delete tools to patch imported content mid-run; fix the mapping and re-run instead.

## Output

After each run, give a short status: stage results from `manifest.json`, counts (pages, component entries, navigation entries, assets, locales), slots left to SAP, and the next command. On a failure, quote the failing stage and the last lines of its output, and say whether a re-run is safe (it always is: every step upserts).

## Security

### Defaults

- Dry run first, every time. Writes happen only with both `--approve-model` and `--approve-publish`, after the user has seen the gate reports.
- OCC TLS is verified. `OCC_INSECURE_TLS=1` is an explicit opt-in for a trusted dev backend.
- Reads from SAP only. The skill never writes to SAP Commerce Cloud.

### Destructive Actions

- The seed step creates or updates content types, entries and assets in the target stack, and changes existing content types to match the starter pack.
- The publish step publishes **every** entry and asset in the stack to the chosen environment, not just the imported ones.
- The `sap-app` stage installs and configures the SAP Commerce Cloud app on the stack. `--reinstall-app` (or `sap_app.py --reinstall`) uninstalls and reinstalls it; `use_products.py` removes the `sap_products` field and its data from the carousel type. Run those only on the user's explicit choice.

So before passing `--approve-publish`, name the stack (API key's stack name, not the key), the environment and the counts, warn that existing content in that stack will be published, and wait for a clear yes. Recommend a new, dedicated stack. Never delete entries, content types, assets or stacks.

### Secrets

Never print, echo, log or store the management token, delivery token, API key or csdx session token, and never write them into the project, the run directory or the final report. The user exports them in their own shell; refer to them by variable name only.

### Environment Variables

- `OCC_BASE_URL`: SAP OCC v2 base, `https://HOST/occ/v2` (or pass `--base`).
- `OCC_INSECURE_TLS`: `1` only for a trusted self-signed dev backend.
- `CS_API_KEY`, `CS_MANAGEMENT_TOKEN`: target stack and a management token with write access. Leave the token unset to write as the csdx login.
- `CS_AUTH`: `auto` (default: the token when set, else csdx), `token` or `csdx`.
- `CS_DELIVERY_TOKEN`, `CS_ENVIRONMENT`: used by the final delivery read check.
- `CS_REGION_BASE`, `CS_CDA_BASE`: management and delivery hosts outside North America, for example `https://eu-api.contentstack.com` and `https://eu-cdn.contentstack.com`.
- `CS_MASTER_LOCALE`: defaults to `en-us`.
- `CS_PREVIEW_URL`: storefront URL set on the environment for every locale, so Live Preview loads (default `http://localhost:4200`).
- `CONNECTOR_STARTER_PACK`: override the starter-pack path.
- `SAP_APP_API_BASE_URL` (host, no scheme), `SAP_APP_BASE_SITE` (for example `electronics` or `powertools-spa`), `SAP_APP_BACKOFFICE_URL`: the SAP server the app's picker searches. Setting all three turns on the picker.
- `SAP_APP_API_ROUTE` (default `/occ/v2/`), `SAP_APP_CONFIG_NAME` (default `hti`), and optionally `SAP_APP_UID`, `CS_ORG_UID`.

## References

- [references/pipeline.md](references/pipeline.md): stages, gates, run directory and flags.
- [references/mapping-profile.md](references/mapping-profile.md): how SAP templates, slots and typeCodes map to connector content types, and how to extend it.
- [references/sap-commerce-app.md](references/sap-commerce-app.md): the SAP Commerce Cloud app stage, the picker value, verify-repair-fallback.
- Connector package: https://www.npmjs.com/package/@contentstack/contentstack-spartacus-connector
- Connector docs: https://www.contentstack.com/docs/marketplace/spartacus-contentstack-connector
- Author: Vaishnavi Kedar (Contentstack Developer Ecosystem), from the Spartacus content-modelling agent.

## Examples

User: Import our SAP electronics storefront into my new stack.
Assistant: Runs the dry run, then reports: "6 pages (/, /faq, /contact, /sale, shared /product and /category layouts), 34 components, 79 navigation entries, 37 images. SearchBox, MiniCart, SiteContext and SiteLinks stay with SAP. No unknown component types. Gate 2 will write to stack 'SAP demo' and publish everything in it to 'development'. Shall I run it?" and waits.

User: Set up the SAP product picker on our powertools demo stack too.
Assistant: Asks for the SAP server and Backoffice URL the app should search (base site `powertools-spa`), runs the dry run with the `SAP_APP_*` variables exported, and reports the preflight: "powertools-spa exists, search returns 252 products, 14 of 14 carousel codes found." Then it asks before the write, which installs and configures the app once, fills both carousels' `sap_products`, and checks the picker in the browser.

User: Just publish it, skip the dry run.
Assistant: Explains that the write step only runs after the gate reports have been reviewed, runs the dry run (it writes nothing and takes about a minute), and asks for the go-ahead with the counts in front of the user.
