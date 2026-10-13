#!/usr/bin/env bash
# HARD GATE. Contentful nests under sys/fields; Contentstack is flat. (doc §6, gotchas #1-2,7)
. "$(dirname "$0")/_lib.sh"
begin "field-access" "Flattened field & metadata access (no .fields./.sys.)"

# Strong residue: Contentful field/metadata addressing
check ".fields. field access (drop the prefix)"             "\.fields\."
check ".sys.<meta> access (map to flat uid/created_at/...)" "\.sys\.(id|createdAt|updatedAt|revision|version|locale|contentType)"
check "Contentful nested reference access (.fields.x.fields.y)" "\.fields\.[A-Za-z0-9_]+\.fields\."
check "metadata.tags (use entry.tags)"                      "\.metadata\.tags"

# Collection-shape residue — softer (could be unrelated arrays); flagged for verification
check "'.items' collection key (Contentstack uses .entries/.assets)" "\.items\b"
check "'.total' count key (Contentstack uses .count via includeCount())" "\.total\b"
check "Contentful includes sidecar (.includes.Entry/.Asset)" "\.includes\.(Entry|Asset)"

finish
