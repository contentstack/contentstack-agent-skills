#!/usr/bin/env bash
# Locales / localization. (doc §11, gotcha #10)
. "$(dirname "$0")/_lib.sh"
begin "locales" "Locale casing & fallback"

# Applicability includes stray uppercase locale codes so they are never silently skipped.
uses_locale="$(search "(\.locale\(|locale[[:space:]]*:|setLocale\(|includeFallback\(|['\"][a-z]{2}-[A-Z]{2}['\"])")"
[ -z "$uses_locale" ] && na "no locale usage detected"

# Contentstack locale codes are lower-cased; flag Contentful-style 'en-US'/'fr-FR'
check "Uppercase locale code (Contentstack uses lower-case, e.g. 'en-us')" "['\"][a-z]{2}-[A-Z]{2}['\"]"
# Multi-locale shape not supported the same way
check "locale: '*' (re-architect to per-locale queries)" "locale[[:space:]]*:[[:space:]]*['\"]\*['\"]"
# Prefer the builder method over a query param
check "Contentful 'locale:' param (use .locale(...))" "[^.]locale[[:space:]]*:[[:space:]]*['\"][a-zA-Z]"

finish
