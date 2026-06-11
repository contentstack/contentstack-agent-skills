#!/usr/bin/env bash
# HARD GATE. No Contentful SDK/host/dependency may remain after migration.
. "$(dirname "$0")/_lib.sh"
begin "residue" "No leftover Contentful surface"

# Source imports / requires
check "Contentful SDK import"            "from[[:space:]]+['\"]contentful['\"]"
check "contentful-management import"     "from[[:space:]]+['\"]contentful-management['\"]"
check "@contentful/* import"             "from[[:space:]]+['\"]@contentful/"
check "contentful require()"             "require\(['\"]contentful"
check "@contentful/rich-text import"     "@contentful/rich-text"
check "Contentful rich-text renderers"   "documentTo(HtmlString|ReactComponents)"

# Hosts / asset domains
check "Contentful CDA host"              "cdn\.contentful\.com"
check "Contentful preview host"          "preview\.contentful\.com"
check "Contentful GraphQL host"          "graphql\.contentful\.com"
check "Contentful asset domain"          "ctfassets\.net"

# Env var names
check "Contentful env vars"              "(CONTENTFUL_[A-Z_]+|CF_SPACE|CF_CDA[A-Z_]*|CF_CPA[A-Z_]*|CTFL_[A-Z_]+)" "js,jsx,ts,tsx,mjs,cjs,vue,svelte,astro,env,example,local,sample,yml,yaml"

# package.json must not depend on contentful, must depend on contentstack
check "contentful dependency in package.json"  "\"(contentful|contentful-management|@contentful/[^\"]+)\"[[:space:]]*:" "json"
require_present "@contentstack/delivery-sdk (or @contentstack/* read SDK) dependency" "@contentstack/(delivery-sdk|management)" "json"

finish
