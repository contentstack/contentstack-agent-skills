---
name: migrate-ct-schema
description: "Change a live Content Type's schema — add fields, rename, retype, remove, extract to Global Field — safely. Every change classified by risk; safe changes (additive) applied directly, unsafe changes (rename, retype, remove) planned as dual-write + backfill + cutover. Dry-run mandatory before any live change. State file records every intended mutation so the run resumes on failure or reverts on demand."
allowed-tools: Read Grep Glob
---

## When to use

Change a live Content Type's schema — add fields, rename, retype, remove, extract to Global Field — safely. Every change classified by risk; safe changes (additive) applied directly, unsafe changes (rename, retype, remove) planned as dual-write + backfill + cutover. Dry-run mandatory before any live change. State file records every intended mutation so the run resumes on failure or reverts on demand.

Use when a live CT needs to evolve: field added post-launch, prop renamed to match new component signature, a group extracted into a reusable Global Field, a Reference retargeted from one CT to another. Phrases — "add a field to `blog_post`", "rename `title` to `headline`", "extract `hero` to a Global Field", "change `read_time` from string to number", "migrate CT schema". Do NOT use for initial CT creation (that's [`provision-studio-stack`](../provision-studio-stack/SKILL.md)) or for content-only migrations (that's [`import-content`](../import-content/SKILL.md)).

# Migrate a Content Type schema — dry-run planned, dual-write executed, rollback documented

> ## Verification status
>
> **Core mechanics runtime-verified against a live stack.** Some risk-table rows (destructive rename, incompatible retype) remain pattern-verified only — always dry-run on a staging stack before production.
>
> - ✅ CMA endpoints (`/v3/content_types/<uid>`, entry backfill endpoints) match existing verified skills.
> - ✅ Retry + state-file pattern matches `agent-idempotency` reference implementation.
> - ✅ **Safe additive (add optional field), dual-write pattern (add parallel field for rename), bulk entry backfill via PUT, and rollback via schema PUT are all runtime-verified end-to-end** against a live Contentstack stack. 17/17 structural claims pass — schema shape changes, entries survive rollback with core field data intact. Reproduce with `npx ts-node scripts/verify-migrate-ct-schema.ts` (requires `CS_API_KEY` + `CS_AUTH_TOKEN` in `.env`).
>
> **Best practice: always dry-run on a staging stack** with the exact CT + entries first. Never run a high-risk migration against production the first time. Incompatible-retype and in-place destructive renames are explicitly discouraged in the risk-classification table below in favour of the verified dual-write path. The 14-day cool-off is a suggested default; tune to your release cadence.

## Context

The three CT-schema failure modes an agent must not commit blind:

1. **Add a required field to a CT with entries.** Live entries have no value → Contentstack rejects the CT update. Silent failure or partial rollout.
2. **Rename a field.** Entries still carry the old field name; existing bindings on Sections point at the old name; the new name is empty. Live site breaks on first render.
3. **Retype a field.** Existing values don't match the new type → Contentstack drops them silently or rejects the update. Content vanishes.

Safe changes (additive-optional, help-text edits, choice-option additions) can commit directly. Unsafe changes need a **plan → dual-write → backfill → cutover** pattern documented per change class.

## Risk classification

| Change | Risk | Requires |
|---|---|---|
| Add optional field (any type) | 🟢 Safe | Direct commit + dry-run smoke test |
| Add required field | 🟡 Medium | Add as optional first, backfill all entries, then flip to required |
| Add option to a `choice` field | 🟢 Safe | Direct commit |
| Remove option from a `choice` field | 🟡 Medium | Backfill entries using the removed value first |
| Rename a field | 🔴 High | Dual-write (new name + old alias) → backfill → update every binding → cutover → remove alias |
| Retype a field (compatible: `single_line → multi_line`) | 🟡 Medium | Backfill probably-fine values; validate no truncation |
| Retype a field (incompatible: `text → number`) | 🔴 High | Add new field + backfill via transform + update bindings + remove old field |
| Remove a field | 🔴 High | Backfill any downstream dependency + update bindings + soft-delete first (rename to `<field>_deprecated`) → remove after N days |
| Extract a group to a Global Field | 🟡 Medium | Create GF → dual-write to both CT group + GF for one release → update bindings → remove CT group |
| Retarget a Reference field | 🔴 High | Backfill references (bulk update entries) + update bindings; may involve `import-content` if the target CT itself needs seeding |

## Task

### Step 1 — Read the intended change

The user says one of:

- *"Add a field `read_time` (number, optional) to `blog_post`."*
- *"Rename `blog_post.title` to `blog_post.headline`."*
- *"Extract `blog_post.hero` and `product.hero` into a Global Field."*

Parse: source CT + field(s) + intended mutation. Reject vague inputs — "clean up the schema" is not actionable; ask for a specific change.

### Step 2 — Fetch the current CT schema

Use CMA `/v3/content_types/<uid>` (stack management token from env). Store the current schema locally as `docs/_migration-state/<ct_uid>-before.json` — this is the rollback artefact. Never proceed without a snapshot.

### Step 3 — Classify + emit the migration plan

Match the requested change against the risk table. Emit a plan:

```
MIGRATION PLAN · blog_post.title → blog_post.headline
Risk: 🔴 HIGH (field rename)

Current entries in blog_post: 342 (fetched via CMA /entries?count=true).

Plan:
  1. Add new field `headline` (single_line, optional) alongside `title` — safe, no downtime.
  2. Backfill: for every entry, copy `title` value → `headline`. Idempotent (skip entries where `headline` already populated).
  3. Update Section bindings: enumerate every Section currently binding `title`. Report before applying — user confirms.
  4. Cutover: switch bound Sections to bind `headline`. Republish affected compositions.
  5. Cool-off: leave `title` in place for N days (default 14) — rollback window.
  6. Remove `title` after cool-off + verify no remaining bindings.

Rollback: docs/_migration-state/blog_post-before.json restores pre-change schema. Compositions with bindings to `title` restored via git revert of the composition changes committed in Step 4.

Dry-run: no changes applied yet. Approve to proceed?
```

Wait for explicit approval. Never mutate the CT without user go-ahead.

### Step 4 — Execute the plan step-by-step, with checkpoints

Update `docs/_migration-state/<ct_uid>-migration.json` after **every** completed step:

```json
{
  "ct_uid": "blog_post",
  "migration": "rename-title-to-headline",
  "steps": [
    { "id": "1-add-headline", "status": "completed", "at": "2026-..." },
    { "id": "2-backfill-headline", "status": "in-progress", "records_completed": 214, "records_total": 342 },
    { "id": "3-list-bindings", "status": "pending" },
    { "id": "4-cutover-bindings", "status": "pending" },
    { "id": "5-cooloff", "status": "pending", "cooloff_ends": "2026-..." },
    { "id": "6-remove-title", "status": "pending" }
  ]
}
```

Between destructive steps, **pause and require explicit user go-ahead**. Never remove a field automatically after the cool-off ends; wait for the user to invoke the skill again with `--continue --step=6-remove-title` (or equivalent). This protects against accidental destruction if a rollback is silently in progress.

### Step 5 — Rollback support

At any point, the user can invoke:

- *"Roll back the `title → headline` migration."*

Skill reads the state file + the `before.json` snapshot, walks back the completed steps in reverse:

- Step 6 completed → not applicable (already destroyed).
- Steps 1-5 completed → revert bindings, remove new field, unbackfill (if user wants — usually leaves headline values populated but bindings point back to title).

**If Step 6 (remove old field) already ran, rollback is destructive — the data is gone.** Report clearly + ask for confirmation before continuing.

## Inputs needed from the user

1. The change (specific — field name, source CT, target state).
2. Target stack UID + management token (from env or explicit).
3. Explicit approval after the migration plan is emitted (dry-run before commit).
4. Confirmation between destructive steps (backfill → cutover → remove).
5. Optional: cool-off period override (default 14 days).

## Acceptance

- [ ] Migration plan is emitted + explicitly approved before any CMA writes.
- [ ] `<ct>-before.json` snapshot captured before any mutation.
- [ ] `<ct>-migration.json` state file updated after every step.
- [ ] Between destructive steps (cutover, remove), user is prompted; the skill does not auto-continue.
- [ ] Every Section binding affected by the change is enumerated + updated. None left dangling.
- [ ] Rollback path documented in the plan + executable via a follow-up skill invocation.
- [ ] For medium/high-risk changes: cool-off period between backfill and destructive step.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Direct field rename via CMA `/v3/content_types/<uid>` PUT | CMA does rename the schema, but existing entries retain the old field name in `_data` → new bindings return null → live site breaks | Never rename directly. Always dual-write via new field + backfill + cutover. |
| Skipping the `<ct>-before.json` snapshot | Rollback becomes hand-crafted; may miss field metadata (mandatory flags, unique constraints, display names) | Snapshot mandatory. Never proceed without one. |
| Backfilling without idempotency check | Re-run overwrites in-progress author edits | Skip records where the target field is already populated by an author. |
| Auto-continuing after cool-off | Old field removed silently → downstream systems still expecting it break | Never auto-continue destructive steps. Manual re-invocation required. |
| Not updating Section bindings | Field renamed → Sections still bind old name → live site shows nothing | Enumerate every affected binding + update in the same run. Use `discover-sections` or grep composition JSON. |
| Treating "add required field" as safe | Live entries have no value → CT update rejects | Add as optional → backfill all entries → flip to required. Three-step, not one. |

## See also

- [`provision-studio-stack`](../provision-studio-stack/SKILL.md) — for initial CT creation. This skill picks up after that.
- [`import-content`](../import-content/SKILL.md) — used inside this skill for bulk entry backfills.
- `agent-idempotency` — canonical state-file + resume pattern this skill follows.
- [`discover-sections`](../discover-sections/SKILL.md) — enumerate Sections affected by a schema change; used inside Step 3.
- [`troubleshoot-data-binding`](../troubleshoot-data-binding/SKILL.md) — if the site breaks post-migration and bindings return empty, this troubleshoots the "bound to renamed field" failure mode.
