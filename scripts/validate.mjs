#!/usr/bin/env node
// Validates skills/ against the Agent Skills spec and checks that every plugin manifest agrees.
// Usage: node scripts/validate.mjs
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];
const fail = (msg) => errors.push(msg);

// --- Skills ---------------------------------------------------------------
const NAME_RE = /^(?!.*--)[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$/;
const skillsDir = join(root, "skills");
const slugs = readdirSync(skillsDir).filter((d) => statSync(join(skillsDir, d)).isDirectory());

for (const slug of slugs) {
  const file = join(skillsDir, slug, "SKILL.md");
  if (!existsSync(file)) {
    fail(`skills/${slug}: missing SKILL.md`);
    continue;
  }
  const text = readFileSync(file, "utf8");
  const fm = text.match(/^---\n([\s\S]*?)\n---\n/);
  if (!fm) {
    fail(`skills/${slug}/SKILL.md: missing YAML frontmatter`);
    continue;
  }
  const field = (key) => {
    const m = fm[1].match(new RegExp(`^${key}:\\s*(.*)$`, "m"));
    if (!m) return undefined;
    const v = m[1].trim();
    // YAML block scalars (`>` folded, `|` literal): join the indented lines that follow.
    if (/^[>|][+-]?$/.test(v)) {
      const lines = fm[1].slice(m.index + m[0].length).split("\n").slice(1);
      const body = [];
      for (const line of lines) {
        if (line.trim() && !/^\s/.test(line)) break;
        body.push(line.trim());
      }
      return body.join(v.startsWith(">") ? " " : "\n").trim();
    }
    if (v.startsWith('"') && v.endsWith('"')) return v.slice(1, -1).replace(/\\"/g, '"');
    if (v.startsWith("'") && v.endsWith("'")) return v.slice(1, -1).replace(/''/g, "'");
    return v;
  };

  const name = field("name");
  if (!name) fail(`skills/${slug}: missing name`);
  else if (name !== slug) fail(`skills/${slug}: name "${name}" must match folder name`);
  else if (!NAME_RE.test(name)) fail(`skills/${slug}: name must be 1-64 chars of a-z, 0-9 and single hyphens`);

  const description = field("description");
  if (!description) fail(`skills/${slug}: missing description`);
  else if (description.length > 1024) fail(`skills/${slug}: description is ${description.length} chars (max 1024)`);
  else if (!/\bUse when\b/.test(description)) fail(`skills/${slug}: description should say "Use when ..." so agents know when to load it`);

  // Relative links in every markdown file of the skill must resolve.
  for (const md of markdownFiles(join(skillsDir, slug))) {
    const rel = md.slice(skillsDir.length + 1);
    for (const [, target] of readFileSync(md, "utf8").matchAll(/\]\((?!https?:|#|mailto:)([^)\s]+)\)/g)) {
      const path = target.split("#")[0];
      if (path && !existsSync(join(dirname(md), path))) fail(`skills/${rel}: broken link ${target}`);
    }
  }
}

function markdownFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? markdownFiles(join(dir, e.name)) : e.name.endsWith(".md") ? [join(dir, e.name)] : [],
  );
}

// --- Manifests ------------------------------------------------------------
const manifests = [
  ".claude-plugin/plugin.json",
  ".claude-plugin/marketplace.json",
  ".cursor-plugin/plugin.json",
  ".cursor-plugin/marketplace.json",
  ".agents/plugins/marketplace.json",
  "plugin.json",
  "gemini-extension.json",
];
const versions = new Map();
for (const rel of manifests) {
  let json;
  try {
    json = JSON.parse(readFileSync(join(root, rel), "utf8"));
  } catch (e) {
    fail(`${rel}: ${e.message}`);
    continue;
  }
  if (json.version) versions.set(rel, json.version);
  for (const p of json.plugins ?? []) if (p.version) versions.set(`${rel} (${p.name})`, p.version);
}
if (new Set(versions.values()).size > 1) {
  fail(`manifest versions disagree:\n${[...versions].map(([k, v]) => `    ${v}  ${k}`).join("\n")}`);
}

// --- Report ---------------------------------------------------------------
if (errors.length) {
  console.error(`✗ ${errors.length} problem(s):\n${errors.map((e) => `  - ${e}`).join("\n")}`);
  process.exit(1);
}
console.log(`✓ ${slugs.length} skills and ${manifests.length} manifests valid (version ${[...versions.values()][0]})`);
