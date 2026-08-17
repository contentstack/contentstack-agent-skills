---
name: sdk-feature
description: "Implement a feature across any Contentstack management SDK (JS, Python, Java, .NET). TDD approach — tests first, then implementation. CMA OpenAPI spec is the primary source of truth. Fully generic — works for any SDK language and any AI agent. Model separation enforced: higher model for thinking/design/review, lower model for code writing. Use when asked to implement SDK parity, add a new CMA feature to management SDKs, or replicate an existing feature across multiple SDK languages."
allowed-tools: Read Edit Write WebFetch Bash Glob Grep
---

# sdk-feature

## What This Skill Does

Implements a feature across any Contentstack management SDK using a structured, TDD-first pipeline. Reads local repos directly — no cached index needed.

## Usage

```
/sdk-feature "feature description"
             --docs <confluence-trd> <github-pr> <jira-ticket>
             --ref <sdk|sdk:branch|pr-url>
             --sdks <python|dotnet|java|js|all>
             --tickets <none|tasks|full>
```

## The One Rule

```
THINKING  →  Higher-capability model  (analysis, design, review)
WRITING   →  Lower-capability model   (code translation, after thinking is done)
```

## Pipeline (11 steps)

**Step 0 — Task Checklist**
Create tasks using TaskCreate before starting. Shared tasks first (Phase 1), per-SDK tasks after search confirms gaps (Phase 2).

```
TaskCreate({ subject: "Fetch API spec + search all repos", activeForm: "Fetching spec and searching repos", description: "..." })
TaskCreate({ subject: "[<SDK>] Architecture scan", activeForm: "Scanning <SDK> architecture", description: "..." })
```

**Step 1 — Parse Arguments**
Extract feature description, --docs URLs, --ref SDK, --sdks targets, --tickets mode.

**Step 2 — API Spec + Search 🔵 HIGHER MODEL**
1. Fetch CMA OpenAPI spec: `https://assets.contentstack.io/v3/assets/blt02f7b45378b008ee/blt85399a97399b4ecf/cma-openapi-3.json?v=3.0.1`
2. Scan ALL repos in `repos/contentstack-management-*/` on `origin/development`
3. Build gap table — which SDKs have the feature, which are missing
4. Create per-SDK tasks in Phase 2 based on actual gaps found

**Tier-1 gate:** if JS is also missing, implement JS first then lock others behind human gate.

**Step 3 — Build TRD 🔵 HIGHER MODEL**
- Confluence/product-wiki in --docs → use directly, skip spec file
- Only API docs → write `docs/specs/<feature-slug>.md`

**Step 4 — Tickets 🔵 HIGHER MODEL**
- `none` — skip. Read ticket URL from --docs as context.
- `tasks` — one Task per target SDK via Atlassian MCP (or markdown fallback)
- `full` — Epic → Spike → Task per SDK

**Step 5 — Architecture Scan 🔵 HIGHER MODEL** (mandatory per SDK, 12 sub-checks)
- 5a: Read resource file + base class + 2-3 recent methods
- 5b: Method signature consistency check
- 5c: Error handling pattern extraction
- 5d: HTTP client instantiation pattern
- 5e: Deprecated pattern detection (git log)
- 5f: Header injection pattern
- 5g: Test file pattern pre-read
- 5h: Recent PR scan for similar patterns
- 5i: Reuse check — existing base class, service, helper
- 5j: Rollback plan if new class unavoidable (ask for approval)
- 5k: Cross-SDK pattern comparison
- 5l: Confirm plan — write to `docs/plans/<slug>/<sdk>-plan.md`

**Rule:** Only create new class if nothing existing can handle it.

**Step 6 — TDD: Write Test Cases First 🔵 HIGHER MODEL**
Write ALL unit + integration tests BEFORE implementation. Tests must FAIL before Step 7.
- Unit: positive + negative paths (URL, verb, headers, body assertions)
- Integration: write but don't run (need live credentials)
- Cross-SDK parity: same test coverage across all target SDKs

**Step 7 — Implement 🟢 LOWER MODEL**
Context handoff via `docs/plans/<slug>/<sdk>-plan.md` (file persists across model switches).
- `git checkout development && git checkout -b feat/<slug>`
- Read locked plan — implement EXACTLY what it says
- Make failing tests pass

**Step 8 — Code Review 🔵 HIGHER MODEL**
Run `/sdk-review` — 3 passes. Must be APPROVED before proceeding.

**Step 9 — Security Checks**
Sequential within each SDK (avoids rate limits):
1. `talisman --staged` — no secrets in staged files
2. `snyk test` — no new high/critical vulnerabilities
3. `trufflehog git file://. --since-commit HEAD --only-verified` — no secrets in history

**Step 9b — Manual Review Gate 🟢 LOWER MODEL**
Present diff summary + checklist to developer. Wait for explicit per-SDK approval. Record `Reviewed-by:` in commit.

**Step 10 — Commit + PR**
- Commit: `feat: add <feature> to <sdk-name> management SDK`
- PR against `development` — never `main`/`master`
- Comment PR link on Jira ticket

**Step 11 — Final Summary**

## Consistency Rules

| Language | Convention | Example |
|----------|-----------|---------|
| JavaScript | camelCase | `publish()` |
| Python | snake_case | `publish()` |
| Java | camelCase | `publish()` |
| .NET | PascalCase + Async | `Publish()` + `PublishAsync()` |
| Any new SDK | Read from its existing methods | Follow its pattern |

- Same methods in every target SDK — no partial implementations
- Return type must match existing methods in same SDK
- Parameter naming must match existing methods in same SDK
- Docstrings: if existing methods have them → new method must have one
- Deprecated spec endpoints: add `@deprecated` notice in docstring

## Multi-SDK Agent Strategy

When running via `sdk-feature.js` workflow, each SDK gets an independent agent:
- Isolated context — no shared state with other SDKs
- State persisted to `docs/plans/<slug>/<sdk>-state.json`
- Independent error recovery — one SDK fails, others continue
- Sequential gates: Jira creation, human review (prevents race conditions)
- Agent identity in commits: `[agent:impl-<sdk>-<idx>]`

## Model Switch Instructions

| Platform | Higher model | Lower model |
|----------|-------------|-------------|
| Claude Code | `/config → Model → claude-opus-4-8` | `/config → Model → claude-sonnet-4-6` |
| Cursor | Model picker → highest available | Model picker → standard |
| CLI | `--model <highest-tier>` | `--model <standard>` |
| Other | Use most capable model | Use default model |
