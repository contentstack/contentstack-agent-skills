#!/usr/bin/env bash
# Run every Contentful->Contentstack migration eval IN PARALLEL against a target repo.
#
#   bash run-all.sh /path/to/migrated-app      # all evals
#   bash run-all.sh /path/to/app 01 04 06       # only selected evals (by number prefix)
#   SKIP_BUILD=1 bash run-all.sh /path/to/app   # skip the (slow) build eval
#
# Exit: 0 = all clear, 1 = review needed (non-gate findings), 2 = BLOCK (a hard gate failed/errored).

set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-.}"; shift || true
export TARGET
SEL="$*"

# Hard gates: a FAIL/ERROR here BLOCKS the migration sign-off.
HARD="residue field-access sdk-init build secrets"

RESDIR="$(mktemp -d)"; trap 'rm -rf "$RESDIR"' EXIT

scripts=()
for s in "$DIR"/[0-9][0-9]_*.sh; do
  base="$(basename "$s")"; num="${base%%_*}"
  if [ -n "$SEL" ]; then case " $SEL " in *" $num "*) ;; *) continue;; esac; fi
  [ -n "${SKIP_BUILD:-}" ] && [ "$num" = "11" ] && continue
  scripts+=("$s")
done

echo "▶ Running ${#scripts[@]} evals in parallel against: $TARGET"
echo

for s in "${scripts[@]}"; do
  base="$(basename "$s")"
  ( bash "$s" "$TARGET" >"$RESDIR/$base.out" 2>&1; echo $? >"$RESDIR/$base.code" ) &
done
wait

# Per-eval output
for s in "${scripts[@]}"; do
  base="$(basename "$s")"
  cat "$RESDIR/$base.out"; echo
done

echo "================================ SUMMARY ================================"
overall=0
printf "%-16s %-8s %-8s %s\n" "EVAL" "STATUS" "FINDINGS" "GATE"
for s in "${scripts[@]}"; do
  base="$(basename "$s")"
  json="$(grep -h 'SUMMARY_JSON:' "$RESDIR/$base.out" 2>/dev/null | sed 's/.*SUMMARY_JSON: //')"
  name="$(printf '%s' "$json"   | sed -E 's/.*"eval":"([^"]*)".*/\1/')"
  status="$(printf '%s' "$json" | sed -E 's/.*"status":"([^"]*)".*/\1/')"
  finds="$(printf '%s' "$json"  | sed -E 's/.*"findings":([0-9]+).*/\1/')"
  [ -z "$name" ] && name="$base"
  [ -z "$status" ] && status="ERROR"
  code="$(cat "$RESDIR/$base.code" 2>/dev/null || echo 2)"
  [ "$code" = "2" ] && status="ERROR"
  gate="-"; case " $HARD " in *" $name "*) gate="HARD";; esac
  printf "%-16s %-8s %-8s %s\n" "$name" "$status" "${finds:-0}" "$gate"
  AGG="${AGG:-} $name:$status"
  if [ "$status" = "FAIL" ] || [ "$status" = "ERROR" ]; then
    if [ "$gate" = "HARD" ]; then overall=2; elif [ "$overall" -lt 1 ]; then overall=1; fi
  fi
done
echo "========================================================================"
case "$overall" in
  0) echo "✅ VERDICT: PASS — no findings. (Still review TODOs/REPORT items and smoke-test live.)";;
  1) echo "⚠️  VERDICT: REVIEW — non-gate findings to triage (possible false positives).";;
  2) echo "⛔ VERDICT: BLOCK — a HARD-GATE eval failed/errored. Do NOT sign off until fixed.";;
esac
echo "Note: static evals flag SUSPECTS, not proven bugs — reason about each finding. Build & secrets are authoritative."

# Record the run in the session audit log (best-effort).
if [ -f "$DIR/log.sh" ]; then
  vtext=$([ "$overall" = 0 ] && echo PASS || { [ "$overall" = 1 ] && echo REVIEW || echo BLOCK; })
  bash "$DIR/log.sh" "$TARGET" eval "run-all verdict=$vtext;${AGG:-}" >/dev/null 2>&1 || true
fi
exit $overall
