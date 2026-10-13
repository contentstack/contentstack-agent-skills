#!/usr/bin/env bash
# CONDITIONAL. Live Preview / draft mode migration. (doc §18)
. "$(dirname "$0")/_lib.sh"
begin "live-preview" "Live Preview / draft mode reimplementation"

cf_preview="$(search "(@contentful/live-preview|ContentfulLivePreview|useContentfulLiveUpdates|useContentfulInspectorMode|preview\.contentful\.com)")"
cs_preview="$(search "(@contentstack/live-preview-utils|ContentstackLivePreview|livePreviewQuery|live_preview)")"

if [ -z "$cf_preview" ] && [ -z "$cs_preview" ]; then
  na "no Live Preview / draft mode usage detected"
fi

# Residue: Contentful preview must be gone
check "@contentful/live-preview import"        "@contentful/live-preview"
check "ContentfulLivePreview usage"            "ContentfulLivePreview"
check "useContentfulLiveUpdates hook"          "useContentfulLiveUpdates"
check "useContentfulInspectorMode hook"        "useContentfulInspectorMode"
check "Contentful preview host"                "preview\.contentful\.com"

# Positive: Contentstack Live Preview must be wired
require_present "@contentstack/live-preview-utils dependency/usage" "@contentstack/live-preview-utils"
require_present "ContentstackLivePreview.init(...)"                 "ContentstackLivePreview\.init"
require_present "live_preview config on stack init"                 "live_preview"
require_present "real-time updates via onEntryChange(...)"          "onEntryChange\("

# If source had click-to-edit, expect edit tags
if [ -n "$(search "useContentfulInspectorMode")" ]; then
  require_present "edit tags (addEditableTags / data-cslp) for click-to-edit parity" "(addEditableTags|data-cslp)"
fi

# Preview tokens must not be hardcoded in client code
check "Hardcoded preview/management token literal" "(preview_token|management_token)[[:space:]]*:[[:space:]]*['\"][A-Za-z0-9]{6,}['\"]"

finish
