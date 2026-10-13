#!/usr/bin/env bash
# INFORMATIONAL. Surface migration TODOs and guessed UIDs for mandatory human review.
. "$(dirname "$0")/_lib.sh"
begin "todos" "Migration TODOs & guessed-UID review list"

check "TODO(migration) markers"      "TODO\(migration\)"
check "Generic migration FIXMEs"     "FIXME|XXX|@migration"
check "Guessed/placeholder UIDs"     "(GUESS|PLACEHOLDER|REPLACE_ME|<content_type_uid>|your_[a-z_]*_uid)"

report
