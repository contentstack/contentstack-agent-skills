#!/usr/bin/env bash
# Regenerate codex/ from skills/.
#
# Emits:
#   codex/AGENTS.md         — router, copied from skills/CLAUDE.md with link paths rewritten
#   codex/<slug>/SKILL.md   — one per skill, frontmatter stripped, body only
#   codex/<slug>/*          — bundled skill assets such as references/ and scripts/
set -euo pipefail

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
    awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$skill_md"
  } > "$OUT_DIR/$slug/SKILL.md"

  find "$dir" -mindepth 1 -maxdepth 1 ! -name "SKILL.md" ! -name "__pycache__" -exec cp -R {} "$OUT_DIR/$slug/" \;
  find "$OUT_DIR/$slug" \( -name "__pycache__" -type d -o -name "*.pyc" -type f \) -prune -exec rm -rf {} +
done

echo "Wrote codex tree to $OUT_DIR"
