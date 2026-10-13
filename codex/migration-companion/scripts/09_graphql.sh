#!/usr/bin/env bash
# CONDITIONAL. GraphQL Content API migration. (doc §17)
. "$(dirname "$0")/_lib.sh"
begin "graphql" "GraphQL endpoint/auth/schema migration"

signal="$(search "(graphql\.contentful\.com|graphql\.contentstack\.com|@apollo/client|urql|graphql-request|gql\`)" "js,jsx,ts,tsx,mjs,cjs,vue,svelte,astro,graphql,gql")"
[ -z "$signal" ] && na "no GraphQL data-access detected"

# Residue
check "Contentful GraphQL endpoint" "graphql\.contentful\.com" "js,jsx,ts,tsx,mjs,cjs,vue,svelte,astro,graphql,gql,json,env,example"
check "Contentful 'xxxCollection' query naming (Contentstack uses all_<ct_uid>)" "[A-Za-z0-9_]+Collection[[:space:]]*\(" "js,jsx,ts,tsx,mjs,cjs,graphql,gql"
check "Authorization: Bearer header (Contentstack uses access_token header)" "Authorization['\"]?[[:space:]]*:[[:space:]]*[\`'\"]?Bearer"

# Positive: must point at Contentstack GraphQL with the right auth
require_present "Contentstack GraphQL endpoint (graphql.contentstack.com)" "graphql\.contentstack\.com" "js,jsx,ts,tsx,mjs,cjs,vue,svelte,astro,graphql,gql,json,env,example"
require_present "access_token header for Contentstack GraphQL" "access_token"

finish
