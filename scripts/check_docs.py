#!/usr/bin/env python3
"""Check local Markdown links and project frontmatter without dependencies."""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from urllib.parse import unquote, urlsplit

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
STATUS = {"draft", "proposed", "accepted", "deprecated"}
CLASSIFICATION = {"verified-capability", "proposed-design", "experimental"}


def audit(root: pathlib.Path) -> tuple[int, int, list[str]]:
    files = sorted(root.rglob("*.md"))
    errors: list[str] = []
    links = 0
    for file in files:
        rel = file.relative_to(root)
        text = file.read_text(encoding="utf-8")
        fm = FRONTMATTER.match(text)
        if fm:
            fields = dict(re.findall(r"^([\w-]+):\s*(.*?)\s*$", fm.group(1), re.M))
            if fields.get("status") not in STATUS:
                errors.append(f"{rel}: invalid status")
            if "classification" in fields and fields["classification"] not in CLASSIFICATION:
                errors.append(f"{rel}: invalid classification")
        # Strip fenced code blocks before checking prose links.
        prose = re.sub(r"(?ms)^\s*`{3}[^\n]*\n.*?^\s*`{3}\s*$", "", text)
        for match in LINK.finditer(prose):
            target = match.group(1).strip().split(" ", 1)[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith(("//", "mailto:", "#")):
                continue
            if not parsed.path:
                continue
            links += 1
            candidate = (file.parent / unquote(parsed.path)).resolve()
            if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
                errors.append(f"{rel}: missing or outside target: {target}")
    return len(files), links, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    args = parser.parse_args()
    count, links, errors = audit(args.root.resolve())
    for issue in errors:
        print("FAIL:", issue)
    print(f"Markdown files: {count}; relative links checked: {links}; errors: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
