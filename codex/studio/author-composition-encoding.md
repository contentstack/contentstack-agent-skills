---
name: author-composition-encoding
---

## When to use

Encoding rules for the `ui` tree: never pass the compressed spec inline through a shell variable, and preflight-validate the tree before publishing.

Part of the API-authoring set. Start at [`author-composition-via-api`](author-composition-via-api.md), which routes to this one.

## Never pass the compressed `ui` inline via a shell variable

Silent-corruption trap. The `zlib:<base64>` blob is binary-ish. Interpolating it into a `curl -d "..."` string via a shell variable mutates one byte and the SDK renders a blank canvas with **no error anywhere**: `hasSpec: true`, spec present, SSR looks fine, and every child slot silently resolves empty because the key `"children"` was corrupted to `"c1ildren"` (or similar) throughout the tree. Background colors still paint (from `responsiveStyles`), masking the bug until you inspect the raw HTML.

Always write the full payload to a temp file and POST with `-d @file`:

```bash
python3 -c "import json,zlib,base64; \
  raw = json.dumps(ui_tree); \
  assert '\"c1ildren\"' not in raw, 'corrupt key'; \
  assert raw.count('\"children\"') >= <expected slot count>, 'children count wrong'; \
  compressed = 'zlib:' + base64.b64encode(zlib.compress(raw.encode())).decode(); \
  open('/tmp/entry.json','w').write(json.dumps({'entry': {'ui': compressed, ...}}))"

curl -X POST "<cma-host>/v3/content_types/<uid>/entries" \
  -H "api_key: ..." -H "$CS_AUTH" \
  -H "Content-Type: application/json" \
  -d @/tmp/entry.json
```

The count-assert catches shell corruption **before** compression: once the tree is zlib+base64'd, the corruption is opaque.

**Non-prod hosts + Python.** Against a non-prod data center, Python's `urllib`/`requests` fail SSL verification (`SSLCertVerificationError: unable to get local issuer certificate`), the non-prod chain isn't in the default Python CA store, but `curl` reads the system keychain and succeeds. Rule: use `curl` for the CMA POST/PUT itself. Use Python only to build/assert the payload. If Python HTTP is unavoidable (dev tooling only, never app code), pass a permissive SSL context: `ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; urllib.request.urlopen(req, context=ctx)`.

## Preflight: validate the `ui` tree before publishing

The SDK's runtime renderer walks the composition node tree and throws on certain malformed shapes. An unpublishable error reaches the editor BEFORE you see it (`TypeError: Cannot read properties of undefined (reading 'slots')` + `Cannot find a descendant at path [...] in node`), and the entire composition's render aborts: every section after the throw goes blank. The most common cause is an empty Section Slot. Skill's duty is to **never emit one** in the first place.

Before calling `POST /v3/.../entries` (or `PUT` on update), walk the inflated `ui` tree and assert:

- [ ] **Every `slots[<slot_uid>]` value is a non-empty array**, no `{ "<uid>": [] }` entries. Either populate the slot with at least one node, OR remove the slot from the parent's `slots` object entirely.
- [ ] **No node references a removed descendant**: every uid mentioned in a parent's `slots` array maps to an actual node in the tree. (Common when refactoring: removing a node but leaving its uid in a parent's slot array.)
- [ ] **Every Repeater has `metadata.mode: "preview"` AND a Condition Block child (for reference / modular block iteration).** Missing either silently renders zero iterations.
- [ ] **Every Section Slot inside the iteration has its child Section's node in place**. See `build-repeating-section` § Step 6.

Cross-check matches the renderer-side symptom row in [`troubleshoot-canvas`](troubleshoot-canvas.md) (the "Whole composition renders blank or partially blank" row). The runtime crash should never reach the user. That's a Studio bug, but emitting a clean tree avoids it deterministically.

If publishing through a script, gate the publish call behind these assertions and fail loudly. A composition with an empty slot is invalid. Do not emit one.
