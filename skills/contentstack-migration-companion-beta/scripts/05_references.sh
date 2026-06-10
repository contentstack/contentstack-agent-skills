#!/usr/bin/env bash
# References: not auto-resolved + resolve to ARRAYS. (doc §7, gotchas #3,4)
. "$(dirname "$0")/_lib.sh"
begin "references" "Reference resolution & array access"

# Contentful link residue
check "Contentful Link stub (sys.linkType / linkType: 'Entry')" "(sys\.linkType|linkType[[:space:]]*:[[:space:]]*['\"](Entry|Asset))"
check "Contentful nested ref access (.fields.x.fields.y)"       "\.fields\.[A-Za-z0-9_]+\.fields\."

# If references are requested, surface the field UIDs so each dereference can be checked for [0]/array handling.
refs="$(search "includeReference\(")"
if [ -n "$refs" ]; then
  echo "  (info) includeReference() call sites — verify each resolved field is accessed as an ARRAY (entry.field?.[0]?.x, or .map(...)):" 1>&2
  # Pull referenced field names and flag object-style dereference (.field. not followed by [ , ?.[ , .map, .length, .forEach)
  while IFS= read -r line; do
    # crude extraction of the first quoted arg
    fld="$(printf '%s' "$line" | grep -oE "includeReference\(['\"][A-Za-z0-9_]+" | head -1 | sed -E "s/.*['\"]//")"
    [ -z "$fld" ] && continue
    bad="$(search "\.${fld}\.[A-Za-z_]" )"
    if [ -n "$bad" ]; then
      add_finding "reference '${fld}' may be dereferenced as an object instead of an array (expected ${fld}?.[0]?.x):"
      printf '%s\n' "$bad" | sed 's/^/      /' >> "$_TMP"
    fi
  done <<< "$(printf '%s\n' "$refs" | sort -u)"
fi

finish
