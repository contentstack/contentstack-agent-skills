#!/usr/bin/env bash
# HARD GATE. No hardcoded credentials; tokens via env; example env updated. (doc §15 step 2)
. "$(dirname "$0")/_lib.sh"
begin "secrets" "No hardcoded credentials / env hygiene"

# Hardcoded Contentstack credential literals in source
check "Hardcoded delivery/preview/management token literal" \
      "(deliveryToken|preview_token|management_token|access_token)[[:space:]]*[:=][[:space:]]*['\"][A-Za-z0-9_-]{8,}['\"]"
check "Hardcoded apiKey literal"            "apiKey[[:space:]]*[:=][[:space:]]*['\"][A-Za-z0-9]{8,}['\"]"
# Contentstack token/key shapes appearing as literals
check "Contentstack-shaped token literal (cs.../blt...) in source" "['\"](cs[a-f0-9]{12,}|blt[a-z0-9]{12,})['\"]"

# A committed .env with real values is a leak risk
if [ -f "$TARGET/.env" ]; then
  if [ -f "$TARGET/.gitignore" ] && grep -Eq '(^|/)\.env($|[^.])' "$TARGET/.gitignore"; then :; else
    add_finding ".env present but not clearly git-ignored — verify it is not committed"
  fi
fi

# A migration log written inside the repo must not be committed. Check every location log.sh can
# use (MIG_LOG_DIR, then SESSION_DIR/migration-log, then <target>/.migration).
# Paths are checked even if log.sh hasn't created them yet (run-all.sh logs after the evals).
abs_path() {   # absolute, symlink-resolved path, even when the leaf doesn't exist yet
  local d="$1" rest=""
  case "$d" in /*) ;; *) d="$PWD/$d" ;; esac
  d="${d%/}"
  while [ ! -d "$d" ]; do rest="/$(basename "$d")$rest"; d="$(dirname "$d")"; done
  printf '%s%s\n' "$(cd "$d" && pwd -P)" "$rest"
}
target_abs="$(abs_path "$TARGET")"
for logdir in "${MIG_LOG_DIR:-}" "${SESSION_DIR:+$SESSION_DIR/migration-log}" "$TARGET/.migration"; do
  [ -n "$logdir" ] || continue
  # <target>/.migration is only used when neither override is set; skip it unless it exists.
  [ "$logdir" = "$TARGET/.migration" ] && [ ! -d "$logdir" ] && continue
  log_abs="$(abs_path "$logdir")"
  case "$log_abs/" in "$target_abs"/*) ;; *) continue ;; esac   # outside the repo: fine
  if git -C "$target_abs" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$target_abs" check-ignore -q "${log_abs#"$target_abs"/}/" && continue
  elif [ -f "$TARGET/.gitignore" ] && grep -Eq "^/?${log_abs#"$target_abs"/}/?$" "$TARGET/.gitignore"; then
    continue
  fi
  add_finding "migration log directory ${log_abs#"$target_abs"/}/ is inside the repo but not git-ignored — add it to .gitignore"
done

# Example env should advertise the new Contentstack vars
examples=()
for f in "$TARGET"/.env.example "$TARGET"/.env.sample "$TARGET"/.env.local.example; do
  [ -f "$f" ] && examples+=("$f")
done
if [ "${#examples[@]}" -gt 0 ]; then
  if ! grep -Eq 'CS_(API_KEY|DELIVERY_TOKEN|ENVIRONMENT)|CONTENTSTACK_' "${examples[@]}" 2>/dev/null; then
    add_finding "example env file exists but lists no Contentstack (CS_*/CONTENTSTACK_*) variables"
  fi
fi

finish
