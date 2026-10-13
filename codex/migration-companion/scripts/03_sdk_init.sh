#!/usr/bin/env bash
# HARD GATE for REST SDK apps. Stack init must be correct & required fields present. (doc §3, gotcha #6)
. "$(dirname "$0")/_lib.sh"
begin "sdk-init" "Contentstack stack() initialization"

uses_sdk="$(search "@contentstack/delivery-sdk")"
inits="$(files_with "contentstack\.stack\(")"

if [ -z "$uses_sdk" ] && [ -z "$inits" ]; then
  na "app does not use @contentstack/delivery-sdk (GraphQL/raw-REST app — see evals 09/build)"
fi

if [ -z "$inits" ]; then
  add_finding "@contentstack/delivery-sdk is imported but no 'contentstack.stack({...})' init found"
else
  for f in $inits; do
    grep -q 'environment' "$f"   || add_finding "stack() init may be missing required 'environment': $f"
    grep -Eq 'apiKey'  "$f"      || add_finding "stack() init missing 'apiKey' (Contentful used 'space'): $f"
    grep -Eq 'deliveryToken' "$f"|| add_finding "stack() init missing 'deliveryToken' (Contentful used 'accessToken'): $f"
    grep -Eq 'space:|accessToken:' "$f" && add_finding "Contentful init keys (space/accessToken) still present: $f"
  done
fi

# Credentials must come from env, not be hardcoded literals
check "Hardcoded apiKey literal (use process.env)"        "apiKey[[:space:]]*:[[:space:]]*['\"][A-Za-z0-9]{6,}['\"]"
check "Hardcoded deliveryToken literal (use process.env)" "deliveryToken[[:space:]]*:[[:space:]]*['\"][A-Za-z0-9]{6,}['\"]"

finish
