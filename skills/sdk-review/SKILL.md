---
name: sdk-review
description: "Independent 3-pass code review for Contentstack management SDK implementations. Higher-capability model only — the model that wrote the code must NOT review its own work. Checks spec compliance, plan compliance, SDK conventions, return types, parameter naming, docstrings, deprecated endpoints, cross-SDK method parity, test quality, and regression. Use after implementing a feature in any management SDK, before committing."
allowed-tools: Read Bash Glob Grep
---

# sdk-review

## What This Skill Does

Three-pass independent code review for management SDK implementations. Produces structured findings with severity ratings. Only APPROVED implementations proceed to commit.

## Usage

```
/sdk-review <sdk-repo-path> <locked-plan-file>

Example:
/sdk-review repos/contentstack-management-python docs/plans/taxonomy-export/python-plan.md
```

## Model

**Higher-capability model (Pass 1 + Pass 2) · Any model (Pass 3)**

The model that wrote the code (lower model, Step 7) must NOT review its own work.

## Pass 1 — Source Code Review

Reads `git diff HEAD` — source files only (excludes test files).

### 1a — Spec compliance
- Correct HTTP verb + path per CMA spec
- Required params enforced, optional params truly optional

### 1b — Plan compliance
- Check `docs/plans/<slug>/<sdk>-plan.md` exists → verify plan was followed
- If plan missing → emit INFO: "Locked plan not found — skipping 1b"
- Unexpected new files → BLOCKER
- New class created that plan said wouldn't be → BLOCKER

### 1c — SDK convention compliance
- Naming follows this SDK's existing methods (read from unchanged methods)
- Method signature matches pattern from Step 5b
- Error handling matches pattern from Step 5c
- HTTP client usage matches pattern from Step 5d
- Header injection matches pattern from Step 5f

### 1d — No reference SDK copy
- Flag any idiom belonging to a different language
- e.g. `.then()` in Python, `async/await` in Java without proper syntax

### 1e — Redundancy check
- New class created that existing one could handle → MAJOR
- Duplicate methods doing the same thing → MAJOR

### 1f — Return type consistency
- New method must return same type as existing methods in same file
- Python → `requests.Response` · Java → `Call<ResponseBody>` · .NET → `ContentstackResponse` + `Task<ContentstackResponse>`
- Flag MAJOR if returning raw dict/JSON where existing methods return typed response
- Flag MAJOR if .NET async pair missing when existing methods have async pairs

### 1g — Parameter naming consistency
- Read 3 existing method signatures → extract naming convention
- New method params must match (e.g. all use `data`, not `body`)
- Check parameter ORDER matches existing conventions
- Flag MINOR

### 1h — Docstring consistency
- Read 5 existing methods → check for docstrings
- If existing have docstrings → new method MUST have one in same format
- If existing have none → new method must NOT add one
- Special case: first method in file → add docstring (sets the standard)
- Format: Python triple-quote · Java Javadoc `/** */` · .NET XML `/// <summary>` · JS JSDoc `/** @param */`
- Flag MAJOR if missing when required, MINOR if wrong format

### 1i — Deprecated endpoint handling
- Check each implemented endpoint against spec `deprecated: true` flag
- If deprecated → BLOCKER if no `@deprecated` in docstring
- If deprecated → MAJOR if SDK has logging but no runtime warning

### 1j — Cross-SDK method count verification
- Read other target SDKs' `feat/<slug>` branch diffs:
  ```bash
  git -C repos/<other-sdk> log --oneline -1 feat/<slug>
  git -C repos/<other-sdk> diff HEAD~1 HEAD --name-only
  ```
- Compare method counts — flag MAJOR if counts differ
- If other SDKs not yet implemented → skip, emit INFO

## Pass 2 — Test Quality Review

Reads `git diff HEAD` — test files only.

### 2a — Positive test cases
- Actually asserts URL, verb, headers, body — not just `assert response is not None`
- Covers happy path completely
- Tests optional params separately

### 2b — Negative test cases
- Missing UID test actually triggers the guard
- Invalid body test verifies correct error type
- Not just happy path with a misleading name

### 2c — Cross-SDK test parity
- Compare test count vs other SDKs that already have this feature
- Same negative paths must be covered in all SDKs — flag MAJOR if discrepancy

### 2d — Integration test completeness
- Positive (2xx) + Negative (401, 404, 422) paths written
- Follows ordering convention of existing integration test file

## Pass 3 — Regression Check

Run full existing test suite:
```bash
# Python
python3 -m pytest tests/unit/ -v --tb=short

# .NET
dotnet test --filter "Category!=Integration"

# Java
mvn test -q -Dgpg.skip=true

# JS
npm test
```

All existing tests must still pass. Any regression → BLOCKER with test name.

## Finding Format

Every finding must use this exact structure:

```
FINDING #N
Severity:  BLOCKER | MAJOR | MINOR | INFO
Pass:       Source | Tests | Regression
File:       <relative file path>
Line:       <approx line number>
Issue:      <one sentence — what is wrong>
Expected:   <what it should be>
Found:      <what it actually is>
Fix:        <exact change needed>
```

## Severity Definitions

| Severity | Action |
|----------|--------|
| BLOCKER | Must fix before commit |
| MAJOR | Must fix before commit |
| MINOR | Fix recommended, does not block |
| INFO | Observation only |

## Re-Review After Fix

If BLOCKER or MAJOR found:
1. Developer fixes all BLOCKER + MAJOR
2. Re-run `/sdk-review` — Pass 1 + Pass 2 only (regression already confirmed)
3. Must be clean before commit

## Review Summary Output

```
REVIEW SUMMARY — <SDK> — <feature>
════════════════════════════════════
Pass 1 (Source):     PASSED / N findings
Pass 2 (Tests):      PASSED / N findings
Pass 3 (Regression): PASSED / N failures

Blockers:  N
Majors:    N
Minors:    N

Status: APPROVED ✅ / CHANGES REQUIRED ❌
```
