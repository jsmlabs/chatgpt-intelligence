#!/usr/bin/env python3
"""Install the verified v1.4 brand archive into a repository checkout.

Usage: python scripts/install_branding.py ARCHIVE.zip [--root .]
Does not overwrite existing files; verifies all archive bytes before writing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

PREFIX = "branding/v1.4/"
MAX_BYTES = 50 * 1024 * 1024
MAX_FILES = 100


def install(archive: Path, root: Path) -> int:
    root = root.resolve()
    destination = root / "branding" / "v1.4"
    if not (root / "ROADMAP.md").is_file() or not (root / "branding" / "README.md").is_file():
        print("FAIL: target does not appear to be the ChatGPT Intelligence repository root")
        return 1
    if destination.exists():
        print(f"FAIL: destination already exists; refusing overwrite: {destination}")
        return 1

    try:
        with zipfile.ZipFile(archive) as z:
            infos = [i for i in z.infolist() if not i.is_dir()]
            names = [i.filename for i in infos]
            if len(infos) > MAX_FILES or len(set(names)) != len(names):
                raise ValueError("Too many files or duplicate ZIP paths")
            if sum(i.file_size for i in infos) > MAX_BYTES:
                raise ValueError("ZIP exceeds uncompressed size limit")
            for info in infos:
                name = PurePosixPath(info.filename)
                if not info.filename.startswith(PREFIX) or name.is_absolute() or ".." in name.parts or "\\" in info.filename:
                    raise ValueError(f"Unsafe archive path: {info.filename}")
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError(f"Symlink ZIP entry: {info.filename}")
            manifest_name = PREFIX + "MANIFEST.json"
            if manifest_name not in names:
                raise ValueError("Missing manifest")
            manifest = json.loads(z.read(manifest_name))
            declared = manifest["files"]
            if not isinstance(declared, dict) or manifest["file_count"] != len(declared):
                raise ValueError("Invalid manifest file count")
            expected = {PREFIX + key for key in declared} | {manifest_name}
            if set(names) != expected:
                raise ValueError("Archive contents do not match manifest")
            payload: dict[str, bytes] = {}
            for name in sorted(expected):
                data = z.read(name)
                if name != manifest_name:
                    spec = declared[name[len(PREFIX):]]
                    if len(data) != spec["size_bytes"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
                        raise ValueError(f"Manifest mismatch: {name}")
                payload[name[len(PREFIX):]] = data
            if z.testzip() is not None:
                raise ValueError("ZIP CRC failure")
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(f"FAIL: preflight: {exc}")
        return 1

    # Preflight is complete. Never overwrite an existing directory or its files.
    try:
        destination.mkdir(parents=False, exist_ok=False)
    except OSError as exc:
        print(f"FAIL: cannot create destination: {exc}")
        return 1
    written: list[Path] = []
    try:
        for relative, data in payload.items():
            target = destination.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                written.append(target)
                stream.write(data)
        print(f"PASS: installed {len(written)} original files at {destination}")
        return 0
    except OSError as exc:
        for target in reversed(written):
            target.unlink(missing_ok=True)
        for directory in sorted(destination.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if directory.is_dir():
                try:
                    directory.rmdir()
                except OSError:
                    pass
        try:
            destination.rmdir()
        except OSError:
            pass
        print(f"FAIL: installation rolled back: {exc}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    sys.exit(install(args.archive, args.root))
