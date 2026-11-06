#!/usr/bin/env python3
"""Verify a collision-safe brand ZIP against its embedded SHA-256 manifest.

Usage: python scripts/verify_branding_archive.py path/to/safe-import.zip
Standard library only. Does not extract or write files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

PREFIX = "branding/v1.4/"
MAX_TOTAL_UNCOMPRESSED = 50 * 1024 * 1024
MAX_FILES = 100


def verify(archive: Path) -> int:
    try:
        with zipfile.ZipFile(archive) as z:
            entries = [info for info in z.infolist() if not info.is_dir()]
            names = [info.filename for info in entries]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate ZIP paths")
            if len(entries) > MAX_FILES:
                raise ValueError("Too many ZIP entries")
            if sum(info.file_size for info in entries) > MAX_TOTAL_UNCOMPRESSED:
                raise ValueError("ZIP uncompressed size exceeds limit")
            for info in entries:
                name = PurePosixPath(info.filename)
                if (not info.filename.startswith(PREFIX) or name.is_absolute()
                        or ".." in name.parts or "\\" in info.filename):
                    raise ValueError(f"Unsafe ZIP entry: {info.filename}")
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError(f"Symlink entry: {info.filename}")

            manifest_path = PREFIX + "MANIFEST.json"
            if manifest_path not in names:
                raise ValueError("Missing MANIFEST.json")
            manifest = json.loads(z.read(manifest_path))
            files = manifest["files"]
            if not isinstance(files, dict) or manifest["file_count"] != len(files):
                raise ValueError("Invalid manifest file count")
            expected = {PREFIX + path for path in files} | {manifest_path}
            if set(names) != expected:
                raise ValueError(f"ZIP path mismatch: missing={sorted(expected - set(names))}, extra={sorted(set(names) - expected)}")
            for path, spec in sorted(files.items()):
                if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
                    raise ValueError(f"Unsafe manifest path: {path}")
                data = z.read(PREFIX + path)
                if len(data) != spec["size_bytes"]:
                    raise ValueError(f"Size mismatch: {path}")
                if hashlib.sha256(data).hexdigest() != spec["sha256"]:
                    raise ValueError(f"SHA-256 mismatch: {path}")
            if z.testzip() is not None:
                raise ValueError("ZIP CRC check failed")
            print(f"PASS: {len(files)} manifest files, {len(entries)} ZIP entries; sizes, SHA-256, CRC, and paths verified")
            return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/verify_branding_archive.py <archive.zip>")
        sys.exit(2)
    sys.exit(verify(Path(sys.argv[1])))
