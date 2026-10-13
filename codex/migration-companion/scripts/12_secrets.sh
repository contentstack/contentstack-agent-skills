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

# Example env should advertise the new Contentstack vars
if ls "$TARGET"/.env.example "$TARGET"/.env.sample "$TARGET"/.env.local.example >/dev/null 2>&1; then
  if ! grep -Eqr 'CS_(API_KEY|DELIVERY_TOKEN|ENVIRONMENT)|CONTENTSTACK_' "$TARGET"/.env.* 2>/dev/null; then
    add_finding "example env file exists but lists no Contentstack (CS_*/CONTENTSTACK_*) variables"
  fi
fi

finish
