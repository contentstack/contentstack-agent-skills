#!/usr/bin/env bash
# HARD GATE & AUTHORITATIVE. Typecheck / lint / build must pass. (doc §15 step 13)
# Runs in the TARGET dir. Assumes deps are installed (run `npm ci` / `pnpm i` first if needed).
. "$(dirname "$0")/_lib.sh"
begin "build" "Typecheck / lint / build"

[ -f "$TARGET/package.json" ] || na "no package.json (not a JS/TS app, or wrong target dir)"

# Pick a package manager
PM="npm"
[ -f "$TARGET/pnpm-lock.yaml" ] && command -v pnpm >/dev/null 2>&1 && PM="pnpm"
[ -f "$TARGET/yarn.lock" ] && command -v yarn >/dev/null 2>&1 && PM="yarn"
[ -f "$TARGET/bun.lockb" ] && command -v bun >/dev/null 2>&1 && PM="bun"

has_script() { grep -Eq "\"$1\"[[:space:]]*:" "$TARGET/package.json"; }
run() {  # run LABEL CMD...
  local label="$1"; shift
  echo "  --- $label: $* ---" >> "$_TMP"
  if ( cd "$TARGET" && "$@" ) >>"$_TMP" 2>&1; then
    echo "  ✓ $label passed" ; return 0
  else
    add_finding "$label FAILED (see output below)"; return 1
  fi
}

ran_any=0

# Typecheck (preferred signal)
if [ -f "$TARGET/tsconfig.json" ]; then
  ran_any=1
  if has_script "typecheck"; then run "typecheck" $PM run typecheck
  elif command -v npx >/dev/null 2>&1; then run "tsc --noEmit" npx -y tsc --noEmit
  fi
fi

# Lint (non-fatal signal, but reported)
if has_script "lint"; then ran_any=1; run "lint" $PM run lint || true; fi

# Build (authoritative)
if has_script "build"; then ran_any=1; run "build" $PM run build; fi

[ "$ran_any" -eq 0 ] && na "no tsconfig/typecheck/lint/build script found to run"

# Emit captured command output for triage
echo "### [$EVAL_NAME] $EVAL_TITLE"
if [ "$FINDINGS" -eq 0 ]; then
  echo "STATUS: PASS (pkg manager: $PM)"
  echo "SUMMARY_JSON: {\"eval\":\"build\",\"status\":\"PASS\",\"findings\":0}"
  rm -f "$_TMP"; exit 0
fi
echo "STATUS: FAIL (pkg manager: $PM) — $FINDINGS step(s) failed"
cat "$_TMP"
echo "SUMMARY_JSON: {\"eval\":\"build\",\"status\":\"FAIL\",\"findings\":$FINDINGS}"
rm -f "$_TMP"; exit 1
