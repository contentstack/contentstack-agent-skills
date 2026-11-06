# Mapping profile: SAP OCC to the connector model

`scripts/registry/connector.registry.json` is a translation table from what SAP serves over OCC to the content types the Contentstack Spartacus connector ships in its starter pack. It defines no schemas: those come from the connector package, so the imported content always matches what the connector reads.

## The hybrid model

SAP renders the base of every page. Contentstack overrides only the slots that are authored. Functional components, slots nobody authors, and pages that aren't content pages stay with SAP and aren't imported. The slot is the unit of control.

## Sections of the profile

| Key | Maps | Notes |
|---|---|---|
| `page_types` | SAP page template → page content type | `LandingPage2Template` and `ContentPage1Template` → `landing_page`; `ProductDetailsPageTemplate` → `product_page` (shared slug `/product`); `ProductListPageTemplate` → `category_page` (shared slug `/category`). Any other template gets no Contentstack page. |
| `slot_field_map` | SAP slot position → page reference field | For example `Section1` → `section1`, `BodyContent` → `body_content`, `HomepageNavLink` → `homepage_nav_link`. A position missing here, or a field the target page type lacks, stays with SAP. |
| `global_slots` | Shell positions → fields on the single `global_slots` entry | `SiteLogo`, `NavigationBar` and `Footer` are authored. `SiteContext` and `SiteLinks` stay with SAP so the language switcher and sign-in keep working. |
| `component_map` | SAP typeCode → component content type and field mapping | Banners, product carousel (`products` holds the SKUs), paragraph, link, flex component. Image fields become uploaded assets. |
| `navigation` | Navigation trees | Seeded flat: `nav_node_flat` entries with `node_id`, `parent_id` and `sort_order`, plus a `category_navigation_flat` or `footer_navigation_flat` entry that references them through `all_nodes`. The connector rebuilds the tree. |
| `occ_only_types` | Functional typeCodes | Mini cart, search box, breadcrumb, product list, refinements, add to cart and similar. Never imported. |

## Keys used for re-runs

- Pages: `url` (home is `/`).
- Components and navigation entries: `sap_uid`, the SAP component or node uid.
- Shell entry: `title`, set to the baseSite uid.
- Assets: a `sap_code:<media code>` tag.

## Extending it

When gate 1 reports an unknown typeCode, decide with the user:

- **Editors should control it**: add it to `component_map` with the connector content type it maps to and a field mapping from OCC field to connector field. The content type must exist in the starter pack; gate 2 checks this.
- **SAP renders it**: add it to `occ_only_types.types`.

Re-run the dry run. The mapping then applies to every later run.
