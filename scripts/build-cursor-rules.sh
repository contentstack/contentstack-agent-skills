#!/usr/bin/env bash
# Regenerate cursor/rules/ from skills/.
#
# Reads each skills/<slug>/SKILL.md, extracts its YAML frontmatter, and emits:
#   cursor/rules/00-router.mdc        — alwaysApply router, copied from skills/CLAUDE.md
#   cursor/rules/NN-<slug>.mdc        — one per skill, with cursor frontmatter
#
# A rule lives in cursor/rules/, not next to its skill's bundled files, so
# relative links in the body are rewritten to ../../skills/<slug>/, and a skill
# that bundles files gets a note naming the folder its relative paths resolve in.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
OUT_DIR="$ROOT/cursor/rules"

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

i=1
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

  nn="$(printf '%02d' "$i")"
  out="$OUT_DIR/$nn-$slug.mdc"

  {
    printf -- '---\n'
    printf 'description: %s\n' "$description"
    if [ -n "$paths" ]; then
      printf 'globs: %s\n' "$paths"
    fi
    printf 'alwaysApply: %s\n' "$always"
    printf -- '---\n\n'
    if [ -n "$(find "$dir" -mindepth 1 -maxdepth 1 ! -name SKILL.md -print -quit)" ]; then
      printf '> This skill'"'"'s bundled files are in `skills/%s/` at the root of the contentstack-agent-skills repo. Resolve every relative path below against that folder, not against this rule.\n\n' "$slug"
    fi
    # Body = SKILL.md with frontmatter stripped, relative link targets rewritten
    awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$skill_md" |
      SLUG="$slug" perl -pe 's{\]\((?!(?:[a-z][a-z0-9+.-]*:|#|/))(?:\./)?}{](../../skills/$ENV{SLUG}/}gi'
  } > "$out"

  i=$((i + 1))
done

echo "Wrote $((i - 1)) cursor rules to $OUT_DIR"
