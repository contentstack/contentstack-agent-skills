---
name: author-composition-encoding
---

## When to use

Encoding rules for the `ui` tree: never pass the compressed spec inline through a shell variable, and preflight-validate the tree before publishing.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Never pass the compressed `ui` inline via a shell variable

A large `zlib:<base64>` blob inlined into a `curl -d "..."` string is fragile: JSON quoting and escaping mistakes, argument-length limits and copy-paste truncation all corrupt the payload. A corrupted `ui` tree fails silently: `hasSpec: true`, SSR looks fine, but if a structural key such as `"children"` is wrong, every child slot resolves empty and the canvas renders blank with **no error anywhere**. Background colors still paint (from `responsiveStyles`), masking the bug until you inspect the raw HTML.

Always build the payload in a file and POST with `-d @file`. Save the uncompressed tree as `ui.json` first, then:

```bash
python3 - <<'PY'
import json, zlib, base64
EXPECTED_SLOTS = 0  # set to the number of child slots you authored
raw = json.dumps(json.load(open("ui.json")))
assert raw.count('"children"') >= EXPECTED_SLOTS, "children count wrong"
compressed = "zlib:" + base64.b64encode(zlib.compress(raw.encode())).decode()
entry = json.load(open("entry-fields.json"))  # title, url, static_value, ...
entry["ui"] = compressed
json.dump({"entry": entry}, open("entry.json", "w"))
PY

curl -X POST "<cma-host>/v3/content_types/<uid>/entries" \
  -H "api_key: ..." -H "$CS_AUTH" \
  -H "Content-Type: application/json" \
  -d @entry.json
```

The count-assert catches a malformed tree **before** compression: once the tree is zlib+base64'd, the damage is opaque.

**Custom / private data center + Python.** Against a custom or private data center (hosts supplied by Contentstack; set every host explicitly), Python's `urllib`/`requests` can fail SSL verification (`SSLCertVerificationError: unable to get local issuer certificate`) when that host's chain isn't in the default Python CA store, but `curl` reads the system keychain and succeeds. Rule: use `curl` for the CMA POST/PUT itself. Use Python only to build/assert the payload. If Python HTTP is unavoidable, point it at the trusted CA bundle for that host (`ssl.create_default_context(cafile=...)` or `REQUESTS_CA_BUNDLE`). Never disable certificate or hostname verification: if the chain can't be verified, stop and report it.

## Preflight: validate the `ui` tree before publishing

The SDK's runtime renderer walks the composition node tree and throws on certain malformed shapes. An unpublishable error reaches the editor BEFORE you see it (`TypeError: Cannot read properties of undefined (reading 'slots')` + `Cannot find a descendant at path [...] in node`), and the entire composition's render aborts: every section after the throw goes blank. The most common cause is an empty Section Slot. Skill's duty is to **never emit one** in the first place.

Before calling `POST /v3/.../entries` (or `PUT` on update), walk the inflated `ui` tree and assert:

- [ ] **Every `slots[<slot_uid>]` value is a non-empty array**, no `{ "<uid>": [] }` entries. Either populate the slot with at least one node, OR remove the slot from the parent's `slots` object entirely. Two exceptions: a `section-slot` node keeps `slots: { "<its-own-uid>": [] }` until a template fills it, and the page-side `section-composition` node keeps an empty entry for each slot the template hasn't filled yet ([`author-composition-sections`](author-composition-sections.md) § `section-slot` node shape). Skip that shape in the check.
- [ ] **No node references a removed descendant**: every uid mentioned in a parent's `slots` array maps to an actual node in the tree. (Common when refactoring: removing a node but leaving its uid in a parent's slot array.)
- [ ] **Every Repeater has `metadata.mode: "preview"` AND a Condition Block child (for reference / modular block iteration).** Missing either silently renders zero iterations.
- [ ] **Every Section Slot inside the iteration has its child Section's node in place**. See `build-repeating-section` § Step 6.

Cross-check matches the renderer-side symptom row in [`troubleshoot-canvas`](troubleshoot-canvas.md) (the "Whole composition renders blank or partially blank" row). The runtime crash should never reach the user. That's a Studio bug, but emitting a clean tree avoids it deterministically.

If publishing through a script, gate the publish call behind these assertions and fail loudly. A composition with an empty slot is invalid. Do not emit one.
