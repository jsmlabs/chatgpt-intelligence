#!/usr/bin/env python3
"""Check original branding PNG/SVG encoding, dimensions and static HTML assets.

This complements SHA-256 manifest checks. It cannot prove correct rendering,
visual accessibility, trademark clearance or interactive browser behavior.
Standard library only.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import struct
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zlib

PNG_HEADER = b"\x89PNG\r\n\x1a\n"
SVG_TAG = "{http://www.w3.org/2000/svg}svg"


def png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(PNG_HEADER):
        raise ValueError("invalid PNG signature")
    pos = 8
    dimensions = None
    done = False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        size = struct.unpack_from(">I", data, pos)[0]
        if size > len(data) - pos - 12:
            raise ValueError("invalid PNG chunk size")
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + size]
        crc = struct.unpack_from(">I", data, pos + 8 + size)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError("PNG chunk CRC mismatch")
        if pos == 8:
            if kind != b"IHDR" or size != 13:
                raise ValueError("first PNG chunk must be IHDR")
            dimensions = struct.unpack_from(">II", payload)
            if not all(dim > 0 for dim in dimensions):
                raise ValueError("invalid PNG dimensions")
        pos += size + 12
        if kind == b"IEND":
            if size != 0:
                raise ValueError("invalid IEND chunk")
            done = True
            break
    if not done or pos != len(data) or dimensions is None:
        raise ValueError("missing IEND or trailing PNG data")
    return dimensions


def svg_dimensions(data: bytes) -> tuple[int, int]:
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("SVG document type or entity declaration is prohibited")
    root = ET.fromstring(data)
    if root.tag != SVG_TAG:
        raise ValueError("invalid SVG root")
    if any(element.tag == "{http://www.w3.org/2000/svg}script"
           for element in root.iter()):
        raise ValueError("embedded SVG script is prohibited")
    try:
        return int(root.attrib["width"]), int(root.attrib["height"])
    except (KeyError, ValueError) as exc:
        raise ValueError("missing integer SVG width/height") from exc


class LocalReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths: list[str] = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for name in ("src", "href"):
            value = attributes.get(name)
            if value:
                self.paths.append(value)


def verify(directory: Path) -> tuple[dict[str, int], list[str]]:
    directory = directory.resolve()
    manifest = json.loads((directory / "MANIFEST.json").read_text(encoding="utf-8"))
    declared = manifest["files"]
    counts = {"png": 0, "svg": 0, "html": 0}
    errors: list[str] = []
    image_sizes: dict[str, tuple[int, int]] = {}

    for name in sorted(declared):
        if not name.endswith((".png", ".svg", ".html")):
            continue
        file = directory / name
        if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(directory):
            errors.append(f"{name}: missing or unsafe")
            continue
        data = file.read_bytes()
        try:
            if name.endswith(".png"):
                image_sizes[name] = png_dimensions(data)
                counts["png"] += 1
            elif name.endswith(".svg"):
                image_sizes[name] = svg_dimensions(data)
                counts["svg"] += 1
            else:
                parser = LocalReferences()
                parser.feed(data.decode("utf-8"))
                for ref in parser.paths:
                    url = urlsplit(ref)
                    if url.scheme or ref.startswith("//") or not url.path:
                        continue
                    target = (file.parent / unquote(url.path)).resolve()
                    if not target.is_relative_to(directory) or not target.is_file():
                        errors.append(f"{name}: broken local HTML asset: {ref}")
                counts["html"] += 1
        except (ValueError, UnicodeError, ET.ParseError, OSError) as exc:
            errors.append(f"{name}: {exc}")

    for name, dimensions in image_sizes.items():
        if not name.endswith(".svg"):
            continue
        png = name[:-4] + ".png"
        if png in image_sizes and image_sizes[png] != dimensions:
            errors.append(f"{name}: SVG/PNG dimensions disagree: {dimensions} != {image_sizes[png]}")
    return counts, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path, nargs="?", default=Path("branding/v1.4"))
    args = parser.parse_args()
    try:
        counts, issues = verify(args.directory)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: brand media preflight: {exc}")
        return 1
    for issue in issues:
        print("FAIL:", issue)
    print(f"Brand media: {counts['png']} PNG, {counts['svg']} SVG, "
          f"{counts['html']} HTML checked; errors: {len(issues)}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
