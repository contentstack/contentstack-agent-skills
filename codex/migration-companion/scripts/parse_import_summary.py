#!/usr/bin/env python3
"""
parse_import_summary.py — Build a clean import summary from `csdx migrate:import` logs.

WHY
---
`csdx migrate:import` does not print a tidy per-module count table at the end. The counts
are scattered across the log as individual lines (`Created asset:`, `Created entry:`,
`Created locale:`, `Published the entry:`, …). This script scans the import log directory
(the path the import prints as "The log has been stored at: …/logs"), tallies those lines,
confirms the final success marker, and prints a summary table. Optionally it cross-checks
the imported counts against the original Contentful `export.json`.

USAGE
-----
    python3 parse_import_summary.py <log-dir-or-file>
    python3 parse_import_summary.py <log-dir-or-file> --export <path/to/export.json>

EXIT CODE
---------
    0  the "Successfully imported…" marker was found
    1  no success marker found (import likely failed or incomplete)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Ensure Unicode output (✓ ✗ ⚠) works on Windows cp1252 and non-UTF8 CI locales.
# errors="replace" prevents UnicodeEncodeError from flipping a successful import to exit 1.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATTERNS = {
    "Locales (created)":        re.compile(r"Created locale:", re.I),
    "Content types (seeded)":   re.compile(r"content type seeded", re.I),
    "Assets (created)":         re.compile(r"Created asset:", re.I),
    "Entries (created)":        re.compile(r"Created entry:", re.I),
    "Entries (localized)":      re.compile(r"Localized entry:", re.I),
    "Entries (published)":      re.compile(r"Published the entry:", re.I),
    "Assets (published)":       re.compile(r"published successfully", re.I),
}

SUCCESS_RE = re.compile(
    r"Successfully imported the content to the stack named (.+?) with the API key (\S+?)\s*\.?$",
    re.I,
)


def read_log_text(path: Path) -> list[str]:
    """Return all lines from a log file or every .log/.txt file under a log dir.

    No deduplication: identical lines (e.g. repeated "content type seeded" events)
    must each be counted — dropping them would collapse counts to 1.
    Binary/unrelated files are skipped by extension.
    """
    files: list[Path] = []
    if path.is_dir():
        for p in sorted(path.rglob("*")):
            if p.is_file() and p.suffix.lower() in {".log", ".txt", ""}:
                files.append(p)
    elif path.is_file():
        files.append(path)
    else:
        sys.exit(f"ERROR: log path not found: {path}")

    lines: list[str] = []
    for f in files:
        try:
            lines.extend(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            continue
    return lines


def count(lines: list[str]) -> dict[str, int]:
    return {label: sum(1 for ln in lines if rx.search(ln)) for label, rx in PATTERNS.items()}


def find_success(lines: list[str]) -> tuple[str, str] | None:
    for ln in lines:
        m = SUCCESS_RE.search(ln)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    return None


def export_counts(export_path: Path) -> dict[str, int]:
    """Best-effort counts from a Contentful export.json (schema varies; skip what's absent)."""
    try:
        data = json.loads(export_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"(could not read export.json for cross-check: {e})")
        return {}

    wanted = {
        "Content types": ("contentTypes", "content_types", "contenttypes"),
        "Entries": ("entries", "items"),
        "Assets": ("assets",),
        "Locales": ("locales",),
    }

    def find_list(obj, keys):
        # Check top-level keys first so a generic name like "items" in a nested
        # pagination block doesn't shadow the real top-level array.
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in keys and isinstance(v, list):
                    return v
        return None

    out: dict[str, int] = {}
    for label, keys in wanted.items():
        lst = find_list(data, set(k.lower() for k in keys))
        if lst is not None:
            out[label] = len(lst)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize a csdx migrate:import log.")
    ap.add_argument("log_path", help="Import log directory (or a single log file).")
    ap.add_argument("--export", help="Path to the Contentful export.json for a count cross-check.")
    args = ap.parse_args()

    lines = read_log_text(Path(args.log_path).expanduser())
    counts = count(lines)
    success = find_success(lines)
    exp = export_counts(Path(args.export).expanduser()) if args.export else {}

    width = max(len(k) for k in counts) + 2
    print("\nImport summary")
    print("-" * (width + 12))
    for label, n in counts.items():
        print(f"{label:<{width}} {n}")

    if exp:
        print("\nCross-check vs export.json")
        print("-" * 40)
        # Map import labels to export labels where comparable
        compare = {
            "Content types": counts.get("Content types (seeded)", 0),
            "Assets": counts.get("Assets (created)", 0),
            "Entries": counts.get("Entries (created)", 0),
            "Locales": counts.get("Locales (created)", 0),
        }
        for label, exported in exp.items():
            imported = compare.get(label, "—")
            flag = "" if imported == exported else "  ⚠ mismatch"
            print(f"{label:<16} exported={exported}  imported={imported}{flag}")

    print()
    if success:
        name, key = success
        print(f"✓ Import SUCCESS — stack \"{name}\" (API key {key})")
        sys.exit(0)
    else:
        print("✗ No success marker found — import may have failed or be incomplete.")
        print("  Check the log directory for ERROR lines.")
        sys.exit(1)


if __name__ == "__main__":
    main()
