#!/usr/bin/env python3
# scripts/sync_file_headers.py
"""
Synchronize "path header" comments at the top of source files.

- Adds missing headers
- Updates incorrect headers
- Skips third-party/generated/binary-ish areas
- Only touches: .py .js .css .html .yml .yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ALLOWED_EXTS = {".py", ".js", ".css", ".html", ".yml", ".yaml"}

# Directories to skip anywhere in the tree
SKIP_DIR_NAMES = {
    "migrations",
    "node_modules",
    ".venv",
    "venv",
    ".git",
    ".idea",
    "__pycache__",
    "static",
    "staticfiles",
    "media",
    "fonts",
    "icons",
    "images",
    "image",
    "img",
    "logs",
    "log",
    "dist",
    "build",
}

# Skip file suffixes (even if extension filtering would avoid most)
SKIP_SUFFIXES = {
    ".env",
    ".sqlite3",
    ".log",
    ".md",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
}

# Skip exact names
SKIP_FILENAMES = {
    "db.sqlite3",
    "Caddyfile",
    ".python-version",
    ".django-secret",
    ".gitignore",
    ".README",
}

# Skip patterns (example: vite config files)
SKIP_NAME_PATTERNS = [
    re.compile(r".*vite\.config\.js$", re.IGNORECASE),
]


# Header formats by extension
def header_for(path_rel_posix: str, ext: str) -> str:
    if ext in {".py", ".yml", ".yaml"}:
        return f"# {path_rel_posix}"
    if ext == ".js":
        return f"// {path_rel_posix}"
    if ext == ".css":
        return f"/* {path_rel_posix} */"
    if ext == ".html":
        return f"{{# {path_rel_posix} #}}"
    raise ValueError(f"Unsupported extension: {ext}")


# Recognize existing header lines we’re willing to replace (first “real” line)
HEADER_LINE_RE = re.compile(
    r"""^\s*(?:
        \#\s+.+ |
        //\s+.+ |
        /\*\s+.+\s+\*/ |
        \{\#\s+.+\s+\#\}
    )\s*$""",
    re.VERBOSE,
)

PY_CODING_RE = re.compile(r"^#.*coding[:=]\s*[-\w.]+", re.IGNORECASE)


@dataclass
class Result:
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0
    errors: int = 0


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    # fallback: current working directory
    return Path.cwd().resolve()


def should_skip_path(path: Path, repo_root: Path) -> bool:
    # Skip dotfiles (and dot-directories) by default
    # but allow dotfiles if they’re explicitly in ALLOWED_EXTS (rare). Your preference: exclude dot-starting.
    if path.name.startswith("."):
        return True

    if path.name in SKIP_FILENAMES:
        return True

    for pat in SKIP_NAME_PATTERNS:
        if pat.match(path.name):
            return True

    # Skip by suffix
    low = path.name.lower()
    for suf in SKIP_SUFFIXES:
        if low.endswith(suf):
            return True

    # Skip by directory membership (anywhere in path)
    try:
        rel_parts = path.resolve().relative_to(repo_root).parts
    except Exception:
        rel_parts = path.parts
    for part in rel_parts:
        if part in SKIP_DIR_NAMES:
            return True
        if part.startswith("."):  # dot-directories anywhere
            return True

    return False


def iter_files(repo_root: Path) -> Iterable[Path]:
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if should_skip_path(p, repo_root):
            continue
        if p.suffix.lower() not in ALLOWED_EXTS:
            continue
        yield p


def normalized_rel_posix(path: Path, repo_root: Path) -> str:
    rel = path.resolve().relative_to(repo_root)
    return rel.as_posix()


def compute_insert_index(lines: list[str], ext: str) -> int:
    """
    Return index in `lines` where header should live.
    For Python: after shebang and coding cookie (and optional blank line immediately after those).
    For JS: after shebang if present.
    For others: very first line (0).
    """
    i = 0
    if not lines:
        return 0

    # Shebang line
    if lines[0].startswith("#!"):
        i = 1

    if ext == ".py":
        # Coding cookie allowed in first 2 lines (after shebang)
        if i < len(lines) and PY_CODING_RE.match(lines[i]):
            i += 1
        # (Optional) allow a second comment line that is also a coding cookie (some people do both)
        if i < len(lines) and PY_CODING_RE.match(lines[i]):
            i += 1

    return i


def replace_or_insert_header(path: Path, repo_root: Path, dry_run: bool = False) -> bool:
    ext = path.suffix.lower()
    rel_posix = normalized_rel_posix(path, repo_root)
    desired = header_for(rel_posix, ext)

    text = path.read_text(encoding="utf-8", errors="replace")
    # Preserve file’s existing newline convention as best we can:
    newline = "\r\n" if "\r\n" in text and "\n" in text else "\n"
    lines = text.splitlines()

    insert_at = compute_insert_index(lines, ext)

    # Identify the “header slot”: first non-empty line at/after insert_at
    slot = None
    j = insert_at
    while j < len(lines):
        if lines[j].strip() == "":
            j += 1
            continue
        slot = j
        break

    changed = False

    if slot is not None and HEADER_LINE_RE.match(lines[slot]):
        # Replace existing recognized header with desired
        if lines[slot].strip() != desired:
            lines[slot] = desired
            changed = True
    else:
        # Insert desired header at insert_at (and keep spacing tidy)
        # If there’s a blank line right at insert_at, insert above it.
        if insert_at < len(lines) and lines[insert_at].strip() == "":
            lines.insert(insert_at, desired)
        else:
            lines.insert(insert_at, desired)
        changed = True

    if changed:
        out = newline.join(lines) + newline
        if not dry_run:
            path.write_text(out, encoding="utf-8")
    return changed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional file paths. If omitted, scans the repo.",
    )
    parser.add_argument("--all", action="store_true", help="Scan the entire repo (default if no paths).")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify files; just report.")
    args = parser.parse_args(argv)

    repo_root = find_repo_root(Path.cwd())

    result = Result()

    candidates: Iterable[Path]
    if args.paths:
        paths = [Path(p) for p in args.paths]
        # Normalize to repo-root absolute paths
        resolved = []
        for p in paths:
            p = (repo_root / p) if not p.is_absolute() else p
            resolved.append(p)
        candidates = resolved
    else:
        candidates = iter_files(repo_root)

    for p in candidates:
        try:
            if not p.exists() or not p.is_file():
                result.skipped += 1
                continue
            if should_skip_path(p, repo_root):
                result.skipped += 1
                continue
            if p.suffix.lower() not in ALLOWED_EXTS:
                result.skipped += 1
                continue

            changed = replace_or_insert_header(p, repo_root, dry_run=args.dry_run)
            if changed:
                result.updated += 1
                print(f"[headers] updated: {p.relative_to(repo_root).as_posix()}")
            else:
                result.unchanged += 1
        except Exception as e:
            result.errors += 1
            print(f"[headers] ERROR: {p} -> {e}", file=sys.stderr)

    print(f"[headers] done. updated={result.updated} unchanged={result.unchanged} " f"skipped={result.skipped} errors={result.errors}")

    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
