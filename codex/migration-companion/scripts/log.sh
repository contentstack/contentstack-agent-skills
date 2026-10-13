#!/usr/bin/env bash
# Verbose session logger for the Contentful -> Contentstack migration.
#
# NOT a pass/fail eval — an append-only AUDIT TRAIL of everything the migration touched:
# user inputs, AI actions & communications, decisions, eval results, commands, and exceptions.
# Writes both a human-readable log and a machine-readable JSONL stream, plus per-command output.
#
# Usage:
#   log.sh <target> <type> <message...>             # append one entry
#   log.sh <target> run "<label>" -- <cmd> [args…]  # run a command; capture output+exit; auto-log exceptions
#   log.sh <target> summary                         # counts by type + recent entries + exception list
#   log.sh <target> path                            # print the log directory
#
# <type> convention (free-form, but prefer one of):
#   user-input | ai-action | communication | decision | exception | command | eval | note
#
# Output (under <target>/.migration, override with MIG_LOG_DIR):
#   session.log            pretty, appended
#   session.jsonl          one JSON object per line
#   commands/NNNN-<label>.out   full stdout+stderr of each captured command
#
# Exceptions thrown by the AI/tooling are recorded by calling:
#   log.sh <target> exception "<what failed and why>"
# Command failures are recorded automatically by `run` (the command's exit code is preserved).

set -uo pipefail

TARGET="${1:-.}"; shift || true
TARGET="${TARGET%/}"
ACTION="${1:-note}"; shift || true

LOGDIR="${MIG_LOG_DIR:-$TARGET/.migration}"
if ! mkdir -p "$LOGDIR/commands" 2>/dev/null; then
  echo "log: cannot create log dir: $LOGDIR" >&2; exit 2
fi
PRETTY="$LOGDIR/session.log"
JSONL="$LOGDIR/session.jsonl"

ts() { date '+%Y-%m-%dT%H:%M:%S%z' 2>/dev/null || date; }

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"; s="${s//\"/\\\"}"
  s="${s//$'\t'/\\t}"; s="${s//$'\r'/\\r}"; s="${s//$'\n'/\\n}"
  printf '%s' "$s"
}

# append TYPE MESSAGE [extra-json-fields]
append() {
  local typ="$1" msg="$2" extra="${3:-}" t; t="$(ts)"
  printf '[%s] %-13s %s\n' "$t" "$typ" "$msg" >> "$PRETTY"
  printf '{"ts":"%s","type":"%s","message":"%s"%s}\n' \
    "$t" "$(json_escape "$typ")" "$(json_escape "$msg")" "${extra:+,$extra}" >> "$JSONL"
}

case "$ACTION" in
  run)
    label="${1:-command}"; shift || true
    [ "${1:-}" = "--" ] && shift || true
    if [ "$#" -eq 0 ]; then echo "log run: no command given (use: log.sh <t> run \"label\" -- cmd …)" >&2; exit 2; fi
    count="$(find "$LOGDIR/commands" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')"
    n="$(printf '%04d' "$((count + 1))")"
    safe="$(printf '%s' "$label" | tr -cs 'A-Za-z0-9._-' '-' | sed 's/-*$//')"
    outfile="$LOGDIR/commands/${n}-${safe:-cmd}.out"
    append "command" "START: $label :: $*" "\"output_file\":\"$(json_escape "$outfile")\""
    start="$(date +%s 2>/dev/null || echo 0)"
    ( cd "$TARGET" && "$@" ) >"$outfile" 2>&1
    code=$?
    end="$(date +%s 2>/dev/null || echo 0)"; dur=$((end - start))
    if [ "$code" -eq 0 ]; then
      append "command" "OK (exit 0, ${dur}s): $label" "\"exit_code\":0,\"duration_s\":$dur,\"output_file\":\"$(json_escape "$outfile")\""
    else
      append "exception" "FAILED (exit $code, ${dur}s): $label" "\"exit_code\":$code,\"duration_s\":$dur,\"output_file\":\"$(json_escape "$outfile")\""
      { echo "    ↳ last 40 lines of output ($outfile):"; tail -n 40 "$outfile" 2>/dev/null | sed 's/^/      /'; } >> "$PRETTY"
    fi
    exit $code
    ;;
  summary)
    if [ ! -f "$JSONL" ]; then echo "No session log yet at $JSONL"; exit 0; fi
    echo "Migration session log: $LOGDIR"
    echo "Entries by type:"
    sed -E 's/.*"type":"([^"]*)".*/\1/' "$JSONL" | sort | uniq -c | sort -rn | sed 's/^/  /'
    exc="$(grep -c '"type":"exception"' "$JSONL" 2>/dev/null || echo 0)"
    echo "Exceptions logged: $exc"
    if [ "$exc" != "0" ]; then echo "--- exceptions ---"; grep '"type":"exception"' "$JSONL" | sed -E 's/.*"message":"([^"]*)".*/  • \1/'; fi
    echo "--- last 20 entries ---"
    tail -n 20 "$PRETTY"
    exit 0
    ;;
  path) echo "$LOGDIR"; exit 0 ;;
  "") echo "log: missing <type> or action" >&2; exit 2 ;;
  *)
    msg="$*"
    [ -z "$msg" ] && { echo "log: empty message for type '$ACTION'" >&2; exit 2; }
    append "$ACTION" "$msg"
    ;;
esac
