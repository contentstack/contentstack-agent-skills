#!/usr/bin/env bash
# Shared helpers for Contentful -> Contentstack migration evals.
# Each eval script sources this, then calls: begin / check / add_finding / require_present / finish | na
#
# Contract / exit codes (consumed by run-all.sh and by AI orchestrators):
#   PASS   -> exit 0   (no issues found)
#   FAIL   -> exit 1   (findings to review; for hard-gate evals this BLOCKS)
#   ERROR  -> exit 2   (the eval itself failed to run)
#   N/A    -> exit 3   (this approach is not used by the app; skip)
#   REPORT -> exit 0   (informational only, e.g. TODO listing)
#
# Findings are signals for a human/AI to triage, not proof of a bug. Static greps
# can produce false positives — every FAIL must be reasoned about. The build and
# secrets evals are authoritative.

set -uo pipefail

TARGET="${TARGET:-${1:-.}}"
TARGET="${TARGET%/}"

# Source-code file extensions to scan (language-agnostic across JS/TS frameworks).
CODE_EXT='js,jsx,ts,tsx,mjs,cjs,vue,svelte,astro'
EXCLUDE_DIRS='node_modules dist build .next .nuxt .svelte-kit out coverage .git .turbo .cache .vercel .output public/build'

if command -v rg >/dev/null 2>&1; then HAVE_RG=1; else HAVE_RG=0; fi

# search REGEX [GLOBS] -> prints "file:line:match"
search() {
  local regex="$1"; local globs="${2:-$CODE_EXT}"
  if [ "$HAVE_RG" -eq 1 ]; then
    local exargs=(); local d
    for d in $EXCLUDE_DIRS; do exargs+=(-g "!$d/**"); done
    rg --no-heading --line-number --color never "${exargs[@]}" -g "*.{$globs}" -e "$regex" "$TARGET" 2>/dev/null
  else
    local inc=() exc=() e d
    IFS=',' read -ra _exts <<< "$globs"
    for e in "${_exts[@]}"; do inc+=(--include="*.$e"); done
    for d in $EXCLUDE_DIRS; do exc+=(--exclude-dir="$d"); done
    grep -rEn "${inc[@]}" "${exc[@]}" -e "$regex" "$TARGET" 2>/dev/null
  fi
}

# files_with REGEX [GLOBS] -> unique file list
files_with() { search "$1" "${2:-$CODE_EXT}" | cut -d: -f1 | sort -u; }

# ---- reporting state ----
EVAL_NAME=""; EVAL_TITLE=""; FINDINGS=0; _TMP=""
begin() {
  EVAL_NAME="$1"; EVAL_TITLE="$2"; FINDINGS=0
  _TMP="$(mktemp)" || { echo "ERROR: mktemp failed"; exit 2; }
}

# add_finding "message" — record one issue
add_finding() { printf '  ▸ %s\n' "$1" >> "$_TMP"; FINDINGS=$((FINDINGS+1)); }

# check "description" REGEX [GLOBS] — flag every match of a pattern that should NOT exist
check() {
  local desc="$1" regex="$2" globs="${3:-$CODE_EXT}" out n
  out="$(search "$regex" "$globs")"
  if [ -n "$out" ]; then
    n="$(printf '%s\n' "$out" | grep -c .)"
    { printf '  ▸ %s  [%s hit(s)]\n' "$desc" "$n"; printf '%s\n' "$out" | sed 's/^/      /'; } >> "$_TMP"
    FINDINGS=$((FINDINGS+n))
  fi
}

# require_present "description" REGEX [GLOBS] — flag if a REQUIRED pattern is MISSING
require_present() {
  local desc="$1" regex="$2" globs="${3:-$CODE_EXT}"
  if [ -z "$(search "$regex" "$globs")" ]; then
    add_finding "MISSING (expected to be present): $desc"
  fi
}

# na "reason" — mark eval not-applicable and exit
na() {
  echo "### [$EVAL_NAME] $EVAL_TITLE"
  echo "STATUS: N/A — $1"
  echo "SUMMARY_JSON: {\"eval\":\"$EVAL_NAME\",\"status\":\"NA\",\"findings\":0}"
  [ -n "$_TMP" ] && rm -f "$_TMP"
  exit 3
}

# finish — print result and exit with PASS/FAIL code
finish() {
  echo "### [$EVAL_NAME] $EVAL_TITLE"
  if [ "$FINDINGS" -eq 0 ]; then
    echo "STATUS: PASS"
    echo "SUMMARY_JSON: {\"eval\":\"$EVAL_NAME\",\"status\":\"PASS\",\"findings\":0}"
    rm -f "$_TMP"; exit 0
  fi
  echo "STATUS: FAIL — $FINDINGS finding(s) to triage"
  cat "$_TMP"
  echo "SUMMARY_JSON: {\"eval\":\"$EVAL_NAME\",\"status\":\"FAIL\",\"findings\":$FINDINGS}"
  rm -f "$_TMP"; exit 1
}

# report — informational eval; always exits 0
report() {
  echo "### [$EVAL_NAME] $EVAL_TITLE"
  if [ "$FINDINGS" -eq 0 ]; then
    echo "STATUS: REPORT — nothing to list"
  else
    echo "STATUS: REPORT — $FINDINGS item(s) for human review"
    cat "$_TMP"
  fi
  echo "SUMMARY_JSON: {\"eval\":\"$EVAL_NAME\",\"status\":\"REPORT\",\"findings\":$FINDINGS}"
  rm -f "$_TMP"; exit 0
}
