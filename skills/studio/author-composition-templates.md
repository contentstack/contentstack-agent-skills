---
name: author-composition-templates
---

## When to use

Author a Template by API: populate `linked_sections` for every API-placed section, plus a complete worked Freeform composition body.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Authoring a Template: populate `linked_sections` for every API-placed section

Sibling concern to the section-side traps in [`author-composition-sections`](author-composition-sections.md). When a Template's `ui` tree contains `section-composition` nodes that were placed via API, the template's **`linked_sections` reference field** ALSO has to be populated, even though SSR walks the nodes directly. Same editor-vs-runtime asymmetry as the section-side `selectedField` trap, but at the template layer.

### The asymmetry

| Path | How it discovers placed sections |
|---|---|
| **Editor canvas** (template open in Studio web app) | Loads the template with `?include[]=linked_sections` (resolves the references inline), builds `spec.sectionCompositions` from the resolved `linked_sections` field. If empty, there are no section specs and you get **"Template Did Not Load"** |
| **SSR / runtime** (`sdk.fetchCompositionData`) | Walks the template's `ui` tree looking for `section-composition` nodes. Reads each node's `metadata.compositionUID`. Fetches each section composition separately |

So a template can render perfectly on the deployed site (SSR walks the nodes) yet refuse to open in the editor (`linked_sections` is empty, editor has no specs to resolve the nodes against). **"Template Did Not Load"** in the editor + a passing SSR render = empty `linked_sections`.

### Recipe: populate `linked_sections` when API-placing sections

When your composition-authoring script writes `section-composition` nodes into a template's `ui`, ALSO populate the template entry's `linked_sections` field with a reference per placed section's composition entry:

```jsonc
// Template composition entry (CMA write)
{
  "title": "Product Page",
  "url": "/products/{{entry.title}}",
  "url_metadata": {
    "url_source": "content_type_url_pattern",
    "url_queries": "{\"include\":[],\"only\":{},\"where\":{}}"
  },
  "composable_uid": "product_page_template",
  "connected_content_type": "product",
  "place_composition_as": "page",
  "ui": "zlib:<base64 of the ui tree containing section-composition nodes>",
  "linked_sections": [
    {
      "uid": "<section-A composition entry uid>",
      "_content_type_uid": "<compositions-CT-uid>"     // the project's compositions CT
    },
    {
      "uid": "<section-B composition entry uid>",
      "_content_type_uid": "<compositions-CT-uid>"
    }
    // …one reference per distinct placed section. Dedupe: a section placed
    // multiple times in the same template only needs one entry here.
  ]
}
```

The references can be bare `{uid, _content_type_uid}` stubs. The CMA stores them. The editor's `?include[]=` resolves them inline when loading. There's no UI-only metadata to mirror (unlike the section-side `selectedField`).

Then **publish the template entry**. The editor reads from the published entry. An unpublished update won't show up.

### Pre-flight check for an API-authored template

Before you mark a template as ready, verify both paths agree:

```bash
# 1. Editor path — does linked_sections resolve to actual sections?
curl -s "https://<cdn-host>/v3/content_types/<compositions-CT-uid>/entries/<template-entry-uid>?include[]=linked_sections" \
  -H "api_key: <stack-api-key>" -H "access_token: <delivery-token>" \
  | jq '.entry.linked_sections | length, .entry.linked_sections[0].uid'

# 2. SSR path — does fetchCompositionData find the same sections?
#    (Use verify-setup Layer 7's script and dump section_scoped_data; the key count
#     should equal the count of distinct section-composition nodes in the template's ui.)
```

Both must agree:
- If the editor path returns 0 sections but the SSR path returns N, `linked_sections` is not populated. Populate per the recipe above.
- If the editor returns N sections but SSR returns 0, `linked_sections` is set but the `ui` tree has no `section-composition` nodes (probably a separate authoring bug).
- If both return matching N, both paths are wired correctly.

## Complete example: a real Freeform composition body

Every field below is what Studio actually stores for a real Freeform composition. Use this shape verbatim when hand-authoring one. The tree is a single `page` root holding a `doc-hero` component, which holds a `doc-product-card` in the hero's `"Actions"` slot, all bound with `static_value` keys.

### The `ui` tree (inflated, before `zlib+base64`)

```json
{
  "uid": "mZfkYLfEsk28cuV",
  "type": "page",
  "attrs": {},
  "metadata": {},
  "styles": {},
  "props": {
    "children": { "type": "slot", "slot": "lW5KA7MYsHQxdHC" }
  },
  "slots": {
    "lW5KA7MYsHQxdHC": [
      {
        "uid": "mHjnXsgKbBlj_PZ",
        "type": "doc-hero",
        "attrs": {},
        "metadata": { "slotNames": { "7Opc3nDCi1wwpyy": "Actions" } },
        "styles": { "default": { "classes": [""], "responsiveStyles": { "default": {} } } },
        "props": {
          "headline": { "type": "string",   "binding": { "type": "static_value", "value": "mHjnXsgKbBlj_PZ-headline" } },
          "subhead":  { "type": "string",   "binding": { "type": "static_value", "value": "mHjnXsgKbBlj_PZ-subhead"  } },
          "cover":    { "type": "imageurl", "binding": { "type": "static_value", "value": "mHjnXsgKbBlj_PZ-cover"    } },
          "ctaLabel": { "type": "string",   "binding": { "type": "static_value", "value": "mHjnXsgKbBlj_PZ-ctaLabel" } },
          "ctaHref":  { "type": "href",     "binding": { "type": "static_value", "value": "mHjnXsgKbBlj_PZ-ctaHref"  } },
          "children": { "type": "slot", "slot": "7Opc3nDCi1wwpyy" }
        },
        "slots": {
          "7Opc3nDCi1wwpyy": [
            {
              "uid": "Wo-7Ly0xHXWsOXQ",
              "type": "doc-product-card",
              "attrs": {},
              "metadata": {},
              "styles": { "default": { "classes": [""], "responsiveStyles": { "default": {} } } },
              "props": {
                "title":   { "type": "string",   "binding": { "type": "static_value", "value": "Wo-7Ly0xHXWsOXQ-title"   } },
                "image":   { "type": "imageurl", "binding": { "type": "static_value", "value": "Wo-7Ly0xHXWsOXQ-image"   } },
                "price":   { "type": "number",   "binding": { "type": "static_value", "value": "Wo-7Ly0xHXWsOXQ-price"   } },
                "badge":   { "type": "choice",   "binding": { "type": "static_value", "value": "Wo-7Ly0xHXWsOXQ-badge"   } },
                "ctaHref": { "type": "href",     "binding": { "type": "static_value", "value": "Wo-7Ly0xHXWsOXQ-ctaHref" } }
              },
              "slots": {}
            }
          ]
        }
      }
    ]
  }
}
```

Notes on the tree that aren't in the recipe examples above:
- Every node carries `attrs`, `metadata`, `styles`, `props`, `slots`, even when empty (`{}`). Studio writes them. You should too.
- The root's `type` is `"page"`, the built-in Page system component. Freeform / Connected templates wrap their content in this root.
- `props.children.type: "slot"` + `props.children.slot: "<slot-uid>"`: declares that this node's children live in the matching key inside `slots`. Same pattern on nested slot-owning components.
- `metadata.slotNames.<slot-uid>: "<author-visible name>"`: components with named slots (like `doc-hero`'s `"Actions"` slot) register the label here so the canvas shows it.
- Each `props.<name>.type` (`"string"`, `"imageurl"`, `"number"`, `"href"`, `"choice"`) is the widget kind. It **must match** the sub-bucket of `entry.static_value` the resolver looks in (`string` → `text`; other types use the same name; see the two-level-lookup rule above).

### The full CMA POST body

The `ui` value on the wire is the tree above, JSON-stringified, `zlib.compress`ed, base64-encoded, and prefixed with `zlib:`. The rest of the entry:

```json
{
  "entry": {
    "title": "Spring 2026 Landing",
    "composable_uid": "spring_2026_landing",
    "connected_content_type": "",
    "url": "/campaigns/spring-2026",
    "url_metadata": {
      "url_source": "user_specified_pattern",
      "url_queries": "{\"include\":[],\"only\":{},\"where\":{}}"
    },
    "place_composition_as": "page",
    "schema_version": "1.0.0",
    "data_sources": "[]",
    "linked_schemas": [],
    "linked_sections": [],
    "static_value": {
      "text": [
        { "key": "mHjnXsgKbBlj_PZ-headline", "value": "Welcome to Studio" },
        { "key": "mHjnXsgKbBlj_PZ-ctaLabel", "value": "" },
        { "key": "Wo-7Ly0xHXWsOXQ-title",    "value": "Studio Pro" }
      ],
      "textarea": [
        { "key": "mHjnXsgKbBlj_PZ-subhead", "value": "Visual composition for content teams — using the React components your engineering already built." }
      ],
      "imageurl": [
        { "key": "mHjnXsgKbBlj_PZ-cover",  "value": "" },
        { "key": "Wo-7Ly0xHXWsOXQ-image", "value": "" }
      ],
      "href": [
        { "key": "mHjnXsgKbBlj_PZ-ctaHref", "value": "" },
        { "key": "Wo-7Ly0xHXWsOXQ-ctaHref", "value": "https://example.com" }
      ],
      "number": [
        { "key": "Wo-7Ly0xHXWsOXQ-price", "value": 49 }
      ],
      "choice": [
        { "key": "Wo-7Ly0xHXWsOXQ-badge", "value": [] }
      ],
      "array":     [],
      "boolean":   [],
      "any":       [],
      "datestring":[],
      "json_rte":  [],
      "html_rte":  [],
      "object":    [],
      "ui": "zlib:eNqtlFtvgjAUgP9L…"
    }
  }
}
```

Studio-generated `_metadata.uid` on each `static_value.*` entry is added by the CMA on write. Do not populate it yourself.

### Python builder: produces the exact body above

Save the tree from § "The ui tree" above as `ui.json`, paste this into `build_entry.py`, and run it with the output path as its argument:

```python
import base64, json, sys, zlib

with open("ui.json") as f:
    UI_TREE = json.load(f)

raw = json.dumps(UI_TREE, separators=(",", ":"))
assert raw.count('"children"') >= 2, "children key corrupted before compression"
compressed = "zlib:" + base64.b64encode(zlib.compress(raw.encode())).decode()

body = {
  "entry": {
    "title": "Spring 2026 Landing",
    "composable_uid": "spring_2026_landing",
    "connected_content_type": "",
    "url": "/campaigns/spring-2026",
    "url_metadata": {
      # Freeform + hand-chosen path → user_specified_pattern.
      # Connected template → "content_type_url_pattern". NEVER omit this block.
      "url_source": "user_specified_pattern",
      "url_queries": json.dumps({"include": [], "only": {}, "where": {}}),  # JSON STRING on the wire
    },
    "place_composition_as": "page",
    "schema_version": "1.0.0",
    "data_sources": "[]",
    "linked_schemas": [],
    "linked_sections": [],
    "static_value": {
      # One row per static_value binding in the tree (same rows as the JSON body above).
      "text": [
        {"key": "mHjnXsgKbBlj_PZ-headline", "value": "Welcome to Studio"},
        {"key": "mHjnXsgKbBlj_PZ-ctaLabel", "value": ""},
        {"key": "Wo-7Ly0xHXWsOXQ-title",    "value": "Studio Pro"},
      ],
      "textarea": [{"key": "mHjnXsgKbBlj_PZ-subhead", "value": "Visual composition for content teams — using the React components your engineering already built."}],
      "imageurl": [
        {"key": "mHjnXsgKbBlj_PZ-cover",  "value": ""},
        {"key": "Wo-7Ly0xHXWsOXQ-image", "value": ""},
      ],
      "href": [
        {"key": "mHjnXsgKbBlj_PZ-ctaHref", "value": ""},
        {"key": "Wo-7Ly0xHXWsOXQ-ctaHref", "value": "https://example.com"},
      ],
      "number":   [{"key": "Wo-7Ly0xHXWsOXQ-price",    "value": 49}],
      "choice":   [{"key": "Wo-7Ly0xHXWsOXQ-badge",    "value": []}],
      "array": [], "boolean": [], "any": [], "datestring": [],
      "json_rte": [], "html_rte": [], "object": [],
    },
    "ui": compressed,
  }
}

with open(sys.argv[1], "w") as f:
    json.dump(body, f)
```

Then POST with `curl -d @file` (never `-d "..."`, see [`author-composition-encoding`](author-composition-encoding.md) § Never pass the compressed `ui` inline via a shell variable):

```bash
# CS_AUTH: one auth header resolved per authenticate-cma
ENTRY_JSON=$(mktemp)
python3 build_entry.py "$ENTRY_JSON"
curl -X POST "https://<cma-host>/v3/content_types/<compositions-CT-uid>/entries" \
  -H "api_key: <stack-api-key>" -H "$CS_AUTH" \
  -H "Content-Type: application/json" \
  -d @"$ENTRY_JSON"
rm -f "$ENTRY_JSON"
```

Publish the entry after create. See [`author-composition-via-api`](author-composition-via-api.md) § Sanity-check the output.
