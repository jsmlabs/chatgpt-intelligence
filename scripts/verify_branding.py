#!/usr/bin/env python3
"""Verify an extracted ChatGPT Intelligence brand package against MANIFEST.json.

Usage: python scripts/verify_branding.py branding/v1.4 [--strict]
Requires Python 3.10+ and standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys


def verify(directory: pathlib.Path, strict: bool = False) -> int:
    base = directory.resolve()
    manifest_path = base / "MANIFEST.json"
    if not manifest_path.is_file():
        print(f"FAIL: missing manifest: {manifest_path}")
        return 1

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        declared = manifest["files"]
        expected_count = manifest["file_count"]
        if not isinstance(declared, dict) or len(declared) != expected_count:
            raise ValueError("Inconsistent manifest file count")
    except (ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: invalid manifest: {exc}")
        return 1

    failures: list[str] = []
    expected: set[pathlib.Path] = {manifest_path.resolve()}
    matching = 0
    for name, spec in sorted(declared.items()):
        path = pathlib.PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            failures.append(f"unsafe path: {name}")
            continue
        target = base.joinpath(*path.parts)
        resolved = target.resolve()
        if not resolved.is_relative_to(base) or target.is_symlink():
            failures.append(f"unsafe or symlinked target: {name}")
            continue
        expected.add(resolved)
        if not target.is_file():
            failures.append(f"missing: {name}")
            continue
        data = target.read_bytes()
        size_ok = len(data) == spec["size_bytes"]
        hash_ok = hashlib.sha256(data).hexdigest() == spec["sha256"]
        if not size_ok:
            failures.append(f"size mismatch: {name}")
        if not hash_ok:
            failures.append(f"sha256 mismatch: {name}")
        if size_ok and hash_ok:
            matching += 1

    # Optional strict mode is required for releases. Normal verification
    # preserves backward compatibility for development checkouts.
    extra = sorted(
        p.relative_to(base).as_posix()
        for p in base.rglob("*")
        if (p.is_file() or p.is_symlink()) and p.resolve() not in expected
    )
    if extra:
        if strict:
            failures.append("undeclared files in brand package: " + ", ".join(extra))
        else:
            print("NOTE: additional files not in manifest: " + ", ".join(extra))
    for issue in failures:
        print("FAIL:", issue)
    print(f"Verified {matching} matching entries against {len(declared)} manifest entries")
    if failures:
        return 1
    print("PASS: all declared sizes and SHA-256 hashes match")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=pathlib.Path)
    parser.add_argument("--strict", action="store_true", help="Reject extra files in the package directory")
    args = parser.parse_args()
    sys.exit(verify(args.directory, strict=args.strict))
