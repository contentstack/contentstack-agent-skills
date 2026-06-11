#!/usr/bin/env bash
# Query builder correctness. (doc §4, §5, gotchas #5,8 + verified .only/.except placement)
. "$(dirname "$0")/_lib.sh"
begin "query-builder" "Query/operator/pagination translation"

# Contentful query syntax that must be gone
check "Contentful bracket operator (e.g. fields.x[gte])" "\[(gte|lte|gt|lt|ne|nin|in|exists|match|all|near|within)\]"
check "Contentful 'content_type' query param (use stack.contentType(uid))" "content_type[[:space:]]*:"
check "Contentful reference depth 'include: N' (use includeReference)"     "include[[:space:]]*:[[:space:]]*[0-9]"
check "Contentful 'order:' sort (use orderByAscending/Descending)"          "order[[:space:]]*:[[:space:]]*['\"]"
check "Contentful 'select:' (use .only([...]))"                             "select[[:space:]]*:[[:space:]]*['\"]"

# VERIFIED bug: .only()/.except() are NOT on .query() — they live on .entry()/.entries()
check ".only()/.except() chained after .query() (invalid — call before .query())" "\.query\([^)]*\)\.(only|except)\("

# Count must be requested explicitly
if [ -n "$(search "\.count\b")" ]; then
  require_present ".includeCount() — code reads res.count but never calls includeCount()" "includeCount\("
fi

finish
