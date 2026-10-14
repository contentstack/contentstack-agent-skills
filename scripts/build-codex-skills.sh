#!/usr/bin/env bash
# Regenerate codex/ from skills/.
#
# Emits:
#   codex/AGENTS.md         — router, copied from skills/CLAUDE.md with link paths rewritten
#   codex/<slug>/SKILL.md   — one per skill, frontmatter stripped, body only
#   codex/<slug>/*          — bundled skill assets such as references/ and scripts/
#
# Skills in IN_PLACE_SKILLS are not copied: codex/<slug>/SKILL.md links back to
# skills/<slug>/ for its bundled files, so the repo holds one copy of them.
set -euo pipefail

IN_PLACE_SKILLS="studio"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
OUT_DIR="$ROOT/codex"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# Router is already written with ./<slug>/ links relative to skills/; that also
# works relative to codex/ because the codex tree mirrors the skills tree.
cp "$SKILLS_DIR/CLAUDE.md" "$OUT_DIR/AGENTS.md"

for dir in "$SKILLS_DIR"/*/; do
  slug="$(basename "$dir")"
  skill_md="$dir/SKILL.md"
  [ -f "$skill_md" ] || continue

  mkdir -p "$OUT_DIR/$slug"
  {
    title="$(awk '/^name:/ {sub(/^name:[[:space:]]*/, ""); print; exit}' "$skill_md")"
    [ -z "$title" ] && title="$slug"
    printf '# %s\n\n' "$title"
    case " $IN_PLACE_SKILLS " in
      *" $slug "*)
        printf '> This skill'"'"'s files, including `skills-index.md` and every `<name>.md` it routes to, are in `../../skills/%s/` relative to this file. Resolve every relative path and skill name below against that folder, not against this file. If that folder is missing, the pack is installed without its files: say so and stop.\n\n' "$slug"
        awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$skill_md" |
          SLUG="$slug" perl -pe 's{\]\((?!(?:[a-z][a-z0-9+.-]*:|#|/))(?:\./)?}{](../../skills/$ENV{SLUG}/}gi'
        ;;
      *)
        awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$skill_md"
        ;;
    esac
  } > "$OUT_DIR/$slug/SKILL.md"

  case " $IN_PLACE_SKILLS " in *" $slug "*) continue ;; esac

  find "$dir" -mindepth 1 -maxdepth 1 ! -name "SKILL.md" ! -name "__pycache__" -exec cp -R {} "$OUT_DIR/$slug/" \;
  find "$OUT_DIR/$slug" \( -name "__pycache__" -type d -o -name "*.pyc" -type f \) -prune -exec rm -rf {} +
done

echo "Wrote codex tree to $OUT_DIR"
