# Migration evals — Contentful → Contentstack

Independent, parallel-runnable checks that confirm a migration was done correctly. Each script
targets one class of mistake from the migration mapping (`reference/CONTENTFUL_TO_CONTENTSTACK_MIGRATION_CONTEXT.md`)
and is **runnable on its own**, so an AI can fan them out (one agent per eval) or use the runner.

## Run

```bash
# all evals, in parallel, against the migrated app
bash run-all.sh /path/to/migrated-app

# a subset (by number prefix)
bash run-all.sh /path/to/app 01 02 04 06

# skip the slow build eval (e.g. before deps are installed)
SKIP_BUILD=1 bash run-all.sh /path/to/app

# one eval directly
bash 02_field_access.sh /path/to/app
```

Install deps in the target first (`npm ci` / `pnpm i`) so eval 11 (build/typecheck) is meaningful.
Uses `ripgrep` if present, else falls back to `grep`.

## The evals

| # | eval | Gate | Catches (doc ref) |
|---|------|------|-------|
| 01 | `residue` | **HARD** | Any leftover Contentful import/host/dep; missing Contentstack dep (§1, gotcha 1) |
| 02 | `field-access` | **HARD** | `.fields.` / `.sys.*` / `.items` / `.total` not flattened (§6, gotchas 1-2,7) |
| 03 | `sdk-init` | **HARD** | `stack()` missing required `environment`/`apiKey`/`deliveryToken`; old keys; hardcoded creds (§3, gotcha 6) |
| 04 | `query-builder` | review | Contentful `[gte]`/`content_type:`/`include:N`/`order:`/`select:`; `.only`/`.except` after `.query()` (§4-5, gotchas 5,8) |
| 05 | `references` | review | Link stubs; references dereferenced as objects not arrays (§7, gotchas 3-4) |
| 06 | `richtext` | review | `@contentful/rich-text`; `path:` vs `paths:`; missing `includeEmbeddedItems()`/HTML sink (§9, gotchas 9,15,16) |
| 07 | `assets` | review | `fields.file.url`; protocol-relative fix; Contentful image params; `ImageTransform` root import (§10, gotchas 11,12,17) |
| 08 | `locales` | review | Uppercase locale codes; `locale:'*'`; query-param locale (§11, gotcha 10) |
| 09 | `graphql` | review* | Contentful GraphQL endpoint/auth/`xxxCollection`; missing Contentstack endpoint/`access_token` (§17) |
| 10 | `live-preview` | review* | Leftover `@contentful/live-preview`; missing `live_preview`/`onEntryChange`/edit tags (§18) |
| 11 | `build` | **HARD** | Typecheck / lint / build failures (authoritative) (§15.13) |
| 12 | `secrets` | **HARD** | Hardcoded tokens/keys; un-ignored `.env`; example env not updated (§15.2) |
| 13 | `todos` | report | Lists `TODO(migration)` and guessed UIDs for mandatory human review |

\* evals 09/10 return **N/A** (exit 3) when the app doesn't use that approach.

## Session logger (`log.sh`) — verbose audit trail

`log.sh` is **not** a pass/fail eval (the runner ignores it). It is an append-only audit log of the
whole migration — user inputs, AI actions & communications, decisions, eval results, commands, and
**every exception** — written to `<target>/.migration/` as both `session.log` (human-readable) and
`session.jsonl` (machine-readable), with full per-command output under `commands/`.

```bash
L=<skill-dir>/evals/log.sh

bash "$L" <target> user-input    "User asked: migrate Next.js app, GraphQL + live preview"
bash "$L" <target> decision      "Detected TS/Next.js/GraphQL(urql)+contentful live-preview"
bash "$L" <target> ai-action     "Rewrote lib/cms.ts queries to all_blog_post"
bash "$L" <target> communication "Asked user to confirm field-UID map"
bash "$L" <target> exception     "coverImage UID unknown -> guessed cover_image (TODO)"

# Run a command through the logger: captures stdout+stderr, preserves exit code,
# and auto-records a FAILED command as an exception:
bash "$L" <target> run "install" -- npm ci
bash "$L" <target> run "typecheck" -- npx tsc --noEmit

bash "$L" <target> summary   # counts by type + exception list + recent entries
bash "$L" <target> path      # print the log directory
```

`run-all.sh` automatically records its verdict to this log when present. Recommended type values:
`user-input | ai-action | communication | decision | exception | command | eval | note`.

## Exit codes

`0` PASS · `1` FAIL (findings) · `2` ERROR (eval crashed) · `3` N/A (approach not used).
`run-all.sh` verdict: `0` PASS, `1` REVIEW (non-gate findings), `2` BLOCK (a hard gate failed).

## How an AI should use these

1. After migrating, run `run-all.sh <target>` (or spawn one agent per `NN_*.sh` for max parallelism).
2. **Hard-gate FAIL/ERROR (01,02,03,11,12) ⇒ the migration is not done.** Fix and re-run.
3. For review evals, **triage every finding** — static greps flag *suspects*, not proven bugs.
   Open each `file:line`, decide true-positive vs false-positive, fix the real ones, and state why
   the rest are safe. Do not dismiss findings silently.
4. The build eval is authoritative: a green typecheck/build is necessary but **not sufficient** —
   it can't catch reference-array bugs, wrong field UIDs, or RTE output. Still smoke-test live
   queries against the real Contentstack stack (doc §15.13).
5. Report results in the migration summary: per-eval status, triaged findings, and remaining TODOs.

These checks are **necessary, not sufficient**. They guard against the known, mechanical mistakes;
they do not prove semantic correctness against your content model.
