#!/usr/bin/env bash
# Regenerate cursor/rules/ from skills/.
#
# Reads each skills/<slug>/SKILL.md, extracts its YAML frontmatter, and emits:
#   cursor/rules/00-router.mdc        — alwaysApply router, copied from skills/CLAUDE.md
#   cursor/rules/NN-<slug>.mdc        — one per skill, with cursor frontmatter
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
OUT_DIR="$ROOT/cursor/rules"

# Preserve existing slug->NN numbering so adding skills is additive (no renumber churn).
SNAP="$(mktemp)"
trap 'rm -f "$SNAP"' EXIT
maxn=0
if [ -d "$OUT_DIR" ]; then
  for f in "$OUT_DIR"/*.mdc; do
    [ -e "$f" ] || continue
    base="$(basename "$f" .mdc)"
    nn="${base%%-*}"; sl="${base#*-}"
    [ "$sl" = "router" ] && continue
    printf '%s %s\n' "$sl" "$nn" >> "$SNAP"
    n=$((10#$nn)); [ "$n" -gt "$maxn" ] && maxn=$n
  done
fi

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# Router: transform skills/CLAUDE.md links from ./<slug>/ to ../../skills/<slug>/
{
  printf -- '---\n'
  printf 'description: Contentstack skill router — pick the matching skill for the user'"'"'s request\n'
  printf 'alwaysApply: true\n'
  printf -- '---\n\n'
  sed 's|](\./|](../../skills/|g' "$SKILLS_DIR/CLAUDE.md"
} > "$OUT_DIR/00-router.mdc"

count=0
for dir in "$SKILLS_DIR"/*/; do
  slug="$(basename "$dir")"
  skill_md="$dir/SKILL.md"
  [ -f "$skill_md" ] || continue

  # Extract frontmatter fields for the cursor rule
  description="$(awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}' "$skill_md")"
  paths="$(awk '/^paths:/ {sub(/^paths:[[:space:]]*/, ""); print; exit}' "$skill_md")"
  disable="$(awk '/^disable-model-invocation:/ {sub(/^disable-model-invocation:[[:space:]]*/, ""); print; exit}' "$skill_md")"
  [ -z "$description" ] && description="Contentstack skill: $slug"
  [ "$disable" = "true" ] && always="true" || always="false"

  nn="$(awk -v s="$slug" '$1==s{print $2; exit}' "$SNAP")"
  if [ -z "$nn" ]; then maxn=$((maxn + 1)); nn="$(printf '%02d' "$maxn")"; fi
  out="$OUT_DIR/$nn-$slug.mdc"
  count=$((count + 1))

  {
    printf -- '---\n'
    printf 'description: %s\n' "$description"
    if [ -n "$paths" ]; then
      printf 'globs: %s\n' "$paths"
    fi
    printf 'alwaysApply: %s\n' "$always"
    printf -- '---\n\n'
    # Body = SKILL.md with frontmatter stripped
    awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$skill_md"
  } > "$out"

done

echo "Wrote $count cursor rules to $OUT_DIR"
