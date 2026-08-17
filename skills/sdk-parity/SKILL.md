---
name: sdk-parity
description: "Run a full parity audit across all Contentstack management SDKs. Uses the CMA OpenAPI spec as the source of truth — not hardcoded resource lists. Endpoint-based matching catches method aliases (query↔find, import↔imports). Generates an HTML parity report. Use when checking what's missing across JS, Python, Java, .NET management SDKs, or when deep-scanning a specific resource."
allowed-tools: Read Write WebFetch Bash Glob Grep
---

# sdk-parity

## What This Skill Does

Audits all management SDKs against the CMA OpenAPI spec. Reports gaps per SDK per resource. Generates a rich HTML report.

## Usage

```
/sdk-parity                    ← full audit: all resources from spec
/sdk-parity taxonomy           ← deep scan: one resource, endpoint-level detail
```

## Model

**Higher-capability model for entire skill** — pure analysis, no code writing.

## Source of Truth

CMA OpenAPI spec (always fetched first):
```
https://assets.contentstack.io/v3/assets/blt02f7b45378b008ee/blt85399a97399b4ecf/cma-openapi-3.json?v=3.0.1
```

The spec defines the resource list — no hardcoded "20 resources". If spec fetch fails → fallback to JS repo as baseline.

## Full Audit Flow

1. **Fetch spec** → extract all resource tags → canonical endpoint list + spec version
2. **Fetch all repos:** `git -C repos/contentstack-management-<sdk> fetch origin`
3. **Discover files dynamically** (no hardcoded paths):
   ```bash
   git -C repos/<sdk> grep -rl "<resource-name>" origin/development
   ```
4. **Endpoint-based matching** (not name matching):
   - Same HTTP verb + path → ✅ (show actual name with `*` if alias)
   - Known aliases auto-resolved: `query↔find`, `fetchAll↔findAll`, `import↔imports`
   - Spec endpoint absent in SDK → ❌ MISSING
   - JS also missing a spec endpoint → JS flagged ❌ too
   - Method in SDK not in spec → flagged as extra/diverged
5. **Output gap report** — resource × SDK table with endpoint per row
6. **Generate HTML report** from `sdk-automation/templates/sdk-parity-report.template.html`

## Deep Scan Flow

For `/sdk-parity <resource>`:
1. Fetch spec → filter by resource keyword
2. Find source files via grep
3. Match every spec endpoint against each SDK
4. Show: JS method + HTTP endpoint + actual method per SDK

## HTML Report

Generated at `docs/sdk-parity-report.html`. Template at `sdk-automation/templates/sdk-parity-report.template.html`.

Fill these placeholders:
- `SPEC_VERSION_PLACEHOLDER` — from spec `info.version`
- `RUN_DATE_PLACEHOLDER` — today's date
- `PREV_RUN_DATE_PLACEHOLDER` — previous run date (for delta)
- `SDK_NAMES_PLACEHOLDER` — array of SDK display names
- `SDK_KEYS_PLACEHOLDER` — array of data keys e.g. `["js","py","jv","nt"]`
- `SDK_VERSIONS_PLACEHOLDER` — object with version per SDK key
- `SDK_COLORS_PLACEHOLDER` — array of hex colors (one per SDK, cycle palette if >6)
- `DELTA_CLOSED_PLACEHOLDER` — gaps closed since last run
- `DELTA_FOUND_PLACEHOLDER` — new gaps found since last run
- `SPEC_NEW_PLACEHOLDER` — new spec endpoints count
- `SPEC_CHANGELOG_PLACEHOLDER` — array of new endpoint strings
- `DATA_PLACEHOLDER` — full resource data object

## Data Object Schema

```javascript
{
  resourceName: {
    lastModified: { js: "2 days ago", py: "3 months ago", ... },
    subResources: ["terms"],
    actionCmd: "/sdk-feature \"resource export\" --sdks python --ref js",
    extras: { js: [], py: ["validate_uid()"], jv: [], nt: [] },
    methods: [
      {
        js: "export()",
        ep: "GET /resource/:uid/export",
        py: "❌ MISSING",
        jv: "❌ MISSING",
        nt: "✅ Export",
        tests: { py: "❌", jv: "❌", nt: "✅" },
        effort: { py: "Easy", jv: "Easy" }
      }
    ]
  }
}
```

Status strings: `"✅ name"` · `"✅ name *"` (alias) · `"❌ MISSING"` · `"— "` (not in spec)
Effort: `"Easy"` / `"Medium"` / `"Hard"` — for missing SDKs only
