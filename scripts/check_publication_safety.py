#!/usr/bin/env python3
"""Scan tracked public text files for high-confidence credential signatures.

This is a narrow prevention check, not a complete secret, privacy or history
audit. Only tracked, reasonably sized, UTF-8 text files are inspected.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".yml", ".yaml", ".html", ".css", ".svg", ".toml", ".ini", ".sh"}
MAX_BYTES = 2 * 1024 * 1024
PATTERNS = {
    "private-key-header": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    "github-classic-token": re.compile(r"ghp_[A-Za-z0-9]{36}\b"),
    "github-fine-grained-token": re.compile(r"github_pat_[A-Za-z0-9_]{60,}\b"),
    "openai-project-key": re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}\b"),
    "aws-access-key-id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "slack-bot-token": re.compile(r"xoxb-[0-9]{8,}-[0-9]{8,}-[A-Za-z0-9]{20,}\b"),
}


def scan(paths: list[Path], root: Path) -> tuple[int, list[str]]:
    root = root.resolve()
    examined = 0
    issues: list[str] = []
    for path in paths:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root) or path.is_symlink():
            issues.append(f"unsafe tracked path: {path}")
            continue
        if not path.is_file():
            issues.append(f"missing tracked text file: {path}")
            continue
        if path.stat().st_size > MAX_BYTES:
            issues.append(f"oversize tracked text file not scanned: {path}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            issues.append(f"tracked text file is not UTF-8: {path}")
            continue
        examined += 1
        for label, pattern in PATTERNS.items():
            if pattern.search(content):
                # Do not print the matching secret or its surrounding text.
                issues.append(f"possible {label} in {resolved.relative_to(root)}")
    return examined, issues


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        capture_output=True, check=True,
    )
    return [root / name.decode("utf-8") for name in result.stdout.split(b"\0") if name]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        count, errors = scan(tracked_files(root), root)
    except (OSError, subprocess.CalledProcessError, UnicodeError) as exc:
        print(f"FAIL: unable to enumerate tracked files: {type(exc).__name__}")
        return 1
    for error in errors:
        print("FAIL:", error)
    print(f"Publication safety scan: {count} tracked text files; findings: {len(errors)}")
    print("Scope: signature scan only; does not audit Git history or replace independent privacy review")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
