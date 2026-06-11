#!/usr/bin/env bash
# Rich text rendering. (doc §9, gotchas #9,15,16)
. "$(dirname "$0")/_lib.sh"
begin "richtext" "RTE rendering via @contentstack/utils"

uses_rte="$(search "(jsonToHTML|renderContent|@contentstack/utils|documentTo(HtmlString|ReactComponents)|@contentful/rich-text)" )"
[ -z "$uses_rte" ] && na "no rich-text rendering detected"

# Residue
check "Contentful rich-text renderer call" "documentTo(HtmlString|ReactComponents)"
check "@contentful/rich-text import"       "@contentful/rich-text"

# VERIFIED bug: Utils.render / jsonToHTML option key is `paths` (plural), not `path`
check "RTE render uses 'path:' (must be 'paths:' plural array)" "(jsonToHTML|[^A-Za-z]render)\([^)]*\bpath[[:space:]]*:"

# Embeds require includeEmbeddedItems()
if [ -n "$(search "(jsonToHTML|[^A-Za-z]render)\(")" ]; then
  require_present ".includeEmbeddedItems() — needed when RTE renders embedded entries/assets" "includeEmbeddedItems\("
fi

# utils emits HTML strings -> need an injection sink in component code
if [ -n "$(search "(jsonToHTML|renderContent|[^A-Za-z]render)\(")" ]; then
  require_present "HTML injection sink (dangerouslySetInnerHTML / v-html / [innerHTML]) for rendered RTE HTML" "(dangerouslySetInnerHTML|v-html|\[innerHTML\]|innerHTML[[:space:]]*=)"
fi

finish
