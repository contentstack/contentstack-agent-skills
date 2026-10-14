#!/usr/bin/env node
// Validates skills/ against the Agent Skills spec and checks that every plugin manifest agrees.
// Usage: node scripts/validate.mjs
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];
const fail = (msg) => errors.push(msg);

const read = (file) => readFileSync(file, "utf8").replace(/\r\n?/g, "\n");
const FRONTMATTER = /^---\n([\s\S]*?)\n---(?:\n|$)/;
// Markdown with fenced and inline code removed, so examples inside code aren't treated as content.
const withoutCode = (text) => text.replace(/^(```|~~~)[\s\S]*?^\1/gm, "").replace(/`[^`\n]*`/g, "");

function markdownFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? markdownFiles(path) : name.endsWith(".md") ? [path] : [];
  });
}

// --- Skills ---------------------------------------------------------------
const NAME_RE = /^(?!.*--)[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$/;
const skillsDir = join(root, "skills");
const slugs = readdirSync(skillsDir).filter((d) => statSync(join(skillsDir, d)).isDirectory());

for (const slug of slugs) {
  const skillDir = join(skillsDir, slug);
  const file = join(skillDir, "SKILL.md");
  if (!existsSync(file)) {
    fail(`skills/${slug}: missing SKILL.md`);
    continue;
  }
  const text = read(file);
  const fm = text.match(FRONTMATTER);
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
    return v.replace(/\s+#.*$/, ""); // plain scalar: drop a trailing YAML comment
  };

  const name = field("name");
  if (!name) fail(`skills/${slug}: missing name`);
  else if (name !== slug) fail(`skills/${slug}: name "${name}" must match folder name`);
  else if (!NAME_RE.test(name)) fail(`skills/${slug}: name must be 1-64 chars of a-z, 0-9 and single hyphens`);

  const description = field("description");
  if (!description) fail(`skills/${slug}: missing description`);
  else if (description.length > 1024) fail(`skills/${slug}: description is ${description.length} chars (max 1024)`);
  else if (!/\bUse when\b/.test(description)) fail(`skills/${slug}: description should say "Use when ..." so agents know when to load it`);

  const security = withoutCode(text).split(/^## Security\b.*$/m)[1]?.split(/^## /m)[0];
  if (security === undefined) fail(`skills/${slug}/SKILL.md: missing the mandatory "## Security" section`);
  else {
    for (const sub of ["Defaults", "Destructive Actions", "Secrets", "Environment Variables"]) {
      if (!new RegExp(`^### ${sub}\\b`, "m").test(security)) fail(`skills/${slug}/SKILL.md: "## Security" is missing "### ${sub}"`);
    }
  }

  // Relative links in every markdown file of the skill must resolve, and stay inside the skill
  // folder so the skill still works when installed on its own.
  for (const md of markdownFiles(skillDir)) {
    const rel = md.slice(skillsDir.length + 1);
    const body = withoutCode(read(md));
    for (const [, angled, plain] of body.matchAll(/\]\((?:<([^>]+)>|((?!https?:|#|mailto:)[^)\s]+))\)/g)) {
      const target = angled ?? plain;
      if (/^(https?:|mailto:|#)/.test(target)) continue;
      const path = decodeURIComponent(target.split("#")[0]);
      if (!path) continue;
      const abs = resolve(dirname(md), path);
      if (!existsSync(abs)) fail(`skills/${rel}: broken link ${target}`);
      else if (!abs.startsWith(skillDir + sep)) fail(`skills/${rel}: link ${target} leaves the skill folder`);
    }
  }
}

// --- Frontmatter in skills/ and docs/ -------------------------------------
// A plain (unquoted) YAML value can't contain ": " or " #"; strict parsers reject the whole file.
for (const md of [...markdownFiles(skillsDir), ...markdownFiles(join(root, "docs"))]) {
  const fm = read(md).match(FRONTMATTER);
  for (const [, key, value] of fm?.[1].matchAll(/^([A-Za-z_-]+):[ \t]+(.+)$/gm) ?? []) {
    if (/^["'>|[{]/.test(value)) continue;
    if (/: /.test(value) || value.endsWith(":")) {
      fail(`${md.slice(root.length + 1)}: frontmatter "${key}" must be quoted (contains ": ")`);
    }
  }
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
// These carry the release version; the Cursor and Codex marketplaces point at the plugin instead.
const versioned = new Set([".claude-plugin/plugin.json", ".cursor-plugin/plugin.json", "plugin.json", "gemini-extension.json"]);
const versions = new Map();
for (const rel of manifests) {
  let json;
  try {
    json = JSON.parse(read(join(root, rel)));
  } catch (e) {
    fail(`${rel}: ${e.message}`);
    continue;
  }
  if (json.version) versions.set(rel, json.version);
  else if (versioned.has(rel)) fail(`${rel}: missing "version"`);
  for (const p of json.plugins ?? []) {
    if (p.version) versions.set(`${rel} (${p.name})`, p.version);
    else if (rel === ".claude-plugin/marketplace.json") fail(`${rel}: plugin "${p.name}" is missing "version"`);
  }
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
