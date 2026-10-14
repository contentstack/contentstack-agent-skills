#!/usr/bin/env bash
# Regenerate cursor/rules/ from skills/.
#
# Reads each skills/<slug>/SKILL.md, extracts its YAML frontmatter, and emits:
#   cursor/rules/00-router.mdc        — alwaysApply router, copied from skills/CLAUDE.md
#   cursor/rules/NN-<slug>.mdc        — one per skill, with cursor frontmatter
#
# Skills in IN_PLACE_SKILLS keep their bundled files in skills/<slug>/ only.
# Their rule's relative links are rewritten to ../../skills/<slug>/, and a note
# says where relative paths resolve, since a rule does not sit next to them.
set -euo pipefail

IN_PLACE_SKILLS="studio"

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
    # Body = SKILL.md with frontmatter stripped
    case " $IN_PLACE_SKILLS " in
      *" $slug "*)
        printf '> This skill'"'"'s files, including `skills-index.md` and every `<name>.md` it routes to, are in `../../skills/%s/` relative to this rule. Resolve every relative path and skill name below against that folder, not against this rule. If that folder is missing, the pack is installed without its files: say so and stop.\n\n' "$slug"
        awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$skill_md" |
          SLUG="$slug" perl -pe 's{\]\((?!(?:[a-z][a-z0-9+.-]*:|#|/))(?:\./)?}{](../../skills/$ENV{SLUG}/}gi'
        ;;
      *)
        awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$skill_md"
        ;;
    esac
  } > "$out"

  i=$((i + 1))
done

echo "Wrote $((i - 1)) cursor rules to $OUT_DIR"
